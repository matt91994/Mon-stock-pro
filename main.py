import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦", layout="centered")

# --- RÉCUPÉRATION DES SECRETS ---
try:
    MON_EMAIL = st.secrets["MON_EMAIL"]
    MON_CODE_SECRET = st.secrets["MON_CODE_SECRET"]
    URL_BRUTE = st.secrets["GSHEET_URL"]
    
    # Transformation du lien pour l'export CSV
    if "/edit" in URL_BRUTE:
        CSV_URL = URL_BRUTE.split("/edit")[0] + "/export?format=csv"
    else:
        CSV_URL = URL_BRUTE
except Exception as e:
    st.error("⚠️ Erreur : Les noms dans vos 'Secrets' Streamlit sont incorrects.")
    st.info("Vérifiez que vous avez bien mis : MON_EMAIL, MON_CODE_SECRET et GSHEET_URL.")
    st.stop()

# --- FONCTION D'ENVOI DE MAIL ---
def envoyer_mail(destinataire, liste_manquants):
    msg = EmailMessage()
    corps = "Bonjour,\n\nVoici les produits à commander :\n\n" + "\n".join(liste_manquants)
    msg.set_content(corps)
    msg['Subject'] = "⚠️ COMMANDE STOCK"
    msg['From'] = MON_EMAIL
    msg['To'] = destinataire

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MON_EMAIL, MON_CODE_SECRET)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi : {e}")
        return False

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=5)
def charger_stock(url):
    try:
        # On ajoute un timestamp unique pour forcer la mise à jour
        return pd.read_csv(f"{url}&t={int(time.time())}")
    except Exception as e:
        return None

# --- INTERFACE ---
st.title("📦 Gestion de Stock")

df = charger_stock(CSV_URL)

if df is None:
    st.error("❌ Impossible de lire la Google Sheet.")
    st.stop()

# --- AFFICHAGE ---
st.subheader("📊 État actuel")
manquants = []

with st.sidebar:
    st.header("⚙️ Réglages")
    seuil_alerte = st.slider("Seuil d'alerte", 1, 15, 3)
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()

if df.empty:
    st.warning("Le tableau Google Sheet est vide.")
else:
    for index, row in df.iterrows():
        try:
            nom = str(row['nom']).capitalize()
            qte = int(row['quantite'])
            unite = str(row['unite'])
            
            col1, col2 = st.columns([3, 1])
            alerte = qte < seuil_alerte
            icone = "🔴" if alerte else "🟢"
            
            if alerte:
                manquants.append(f"- {nom} : {qte} {unite}")
                
            with col1:
                st.markdown(f"{icone} **{nom}**")
                st.caption(f"Unité : {unite}")
            with col2:
                st.markdown(f"### {qte}")
        except:
            continue

# --- SECTION MAIL ---
st.divider()
if manquants:
    st.warning(f"Il y a {len(manquants)} article(s) en alerte.")
    mail_dest = st.text_input("Envoyer la commande à :", value=MON_EMAIL)
    
    if st.button("🚀 Envoyer le mail"):
        if envoyer_mail(mail_dest, manquants):
            st.success("📧 Envoyé avec succès !")
else:
    st.success("✅ Stock OK.")

st.sidebar.divider()
st.sidebar.markdown(f"🔗 [Lien Google Sheet]({URL_BRUTE})")
