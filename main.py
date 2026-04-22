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
    
    if "/edit" in URL_BRUTE:
        CSV_URL = URL_BRUTE.split("/edit")[0] + "/export?format=csv"
    else:
        CSV_URL = URL_BRUTE
except Exception as e:
    st.error("⚠️ Erreur de configuration dans les Secrets.")
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
        return pd.read_csv(f"{url}&t={int(time.time())}")
    except:
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
    # On crée un container pour que les lignes soient bien regroupées
    container = st.container()
    
    for index, row in df.iterrows():
        try:
            nom = str(row['nom']).capitalize()
            qte = int(row['quantite'])
            unite = str(row['unite'])
            
            texte_quantite = f"{qte} {unite}"
            
            # --- DÉBUT DE LA LIGNE PRODUIT ---
            col1, col2 = st.columns([2, 1])
            alerte = qte < seuil_alerte
            icone = "🔴" if alerte else "🟢"
            
            if alerte:
                manquants.append(f"- {nom} : {texte_quantite}")
                
            with col1:
                # Texte un peu plus gros pour le nom
                st.markdown(f"{icone} &nbsp; **{nom}**")
            with col2:
                # Alignement visuel de la quantité
                st.markdown(f"**{texte_quantite}**")
            
            # AJOUT DU TRAIT DE SÉPARATION
            st.divider() 
            # --- FIN DE LA LIGNE PRODUIT ---
            
        except:
            continue

# --- SECTION MAIL ---
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
