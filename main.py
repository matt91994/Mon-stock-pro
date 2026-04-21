import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦", layout="centered")

# --- RÉCUPÉRATION DES SECRETS (LE COFFRE-FORT) ---
try:
    # On récupère les infos depuis les Secrets Streamlit (pas en clair ici !)
    MON_EMAIL = st.secrets["MON_EMAIL"]
    MON_CODE_SECRET = st.secrets["MON_CODE_SECRET"]
    URL_BRUTE = st.secrets["GSHEET_URL"]
    
    # Transformation automatique du lien pour l'export CSV
    if "/edit" in URL_BRUTE:
        CSV_URL = URL_BRUTE.split("/edit")[0] + "/export?format=csv"
    else:
        CSV_URL = URL_BRUTE
except Exception as e:
    st.error("⚠️ Erreur de configuration : Les noms dans vos 'Secrets' Streamlit ne correspondent pas.")
    st.info("Vérifiez que vous avez bien : MON_EMAIL, MON_CODE_SECRET et GSHEET_URL (en MAJUSCULES).")
    st.stop()

# --- FONCTION D'ENVOI DE MAIL ---
def envoyer_mail(destinataire, liste_manquants):
    msg = EmailMessage()
    corps = "Bonjour,\n\nVoici les produits à commander en priorité :\n\n" + "\n".join(liste_manquants)
    msg.set_content(corps)
    msg['Subject'] = "⚠️ COMMANDE STOCK : Liste à prévoir"
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
@st.cache_data(ttl=10) # Rafraîchissement toutes les 10 secondes
def charger_stock(url):
    try:
        # On ajoute un timestamp pour éviter que Google ne serve une version périmée (cache)
        return pd.read_csv(f"{url}&nocache={time.time()}")
    except Exception as e:
        return None

# --- INTERFACE PRINCIPALE ---
st.title("📦 Gestion de Stock")

# Tentative de lecture de la Google Sheet
df = charger_stock(CSV_URL)

if df is None:
    st.error("❌ Impossible de lire la Google Sheet.")
    st.markdown("""
    **Vérifiez deux choses :**
    1. Le bouton **Partager** dans Google Sheets est bien sur "Tous les utilisateurs disposant du lien".
    2. Le lien dans vos Secrets est le bon.
    """)
    st.stop()

# --- AFFICHAGE DU STOCK ---
st.subheader("📊 État des produits")
manquants = []

# Barre latérale
with st.sidebar:
    st.header("⚙️ Réglages")
    seuil_alerte = st.slider("Seuil d'alerte", 1, 15, 3)
    st.divider()
    if st.button("🔄 Forcer l'actualisation"):
        st.cache_data.clear()
        st.rerun()

# Vérification si le tableau est vide
if df.empty:
    st.warning("Votre Google Sheet semble vide ou les colonnes sont mal nommées (nom, quantite, unite).")
else:
    # On affiche chaque article
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
        except Exception:
            continue # Saute la ligne si elle est mal remplie dans Google Sheets

# --- SECTION MAIL ---
st.divider()
st.subheader("📧 Envoyer une commande")

if manquants:
    st.warning(f"Il y a {len(manquants)} article(s) sous le seuil.")
    mail_dest = st.text_input("Envoyer à :", value=MON_EMAIL)
    
    if st.button("🚀 Envoyer la liste par mail"):
        with st.spinner("Envoi en cours..."):
            if envoyer_mail(mail_dest, manquants):
                st.success("📧 Mail envoyé avec succès !")
else:
    st.success("✅ Tout est en stock.
               
