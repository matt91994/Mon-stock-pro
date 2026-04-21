import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦", layout="centered")

# --- RÉCUPÉRATION DES SECRETS ---
try:
    MON_EMAIL = st.secrets["matthieuwach@gmail.com"]
    MON_CODE_SECRET = st.secrets["zgjrweclcmmezrho"]
    URL_BRUTE = st.secrets["GSHEET_URL"]
    
    # Transformation du lien pour forcer l'export en CSV
    # Cela permet de lire la feuille sans bibliothèque complexe
    if "/edit" in URL_BRUTE:
        CSV_URL = URL_BRUTE.split("/edit")[0] + "/export?format=csv"
    else:
        CSV_URL = URL_BRUTE
except Exception as e:
    st.error("⚠️ Erreur dans les Secrets Streamlit. Vérifiez MON_EMAIL, MON_CODE_SECRET et GSHEET_URL.")
    st.stop()

# --- FONCTIONS ---
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
# On ajoute un horodatage à l'URL pour éviter que Google ne donne de vieilles données (cache)
@st.cache_data(ttl=10)
def charger_stock(url):
    try:
        return pd.read_csv(f"{url}&nocache={time.time()}")
    except Exception as e:
        return None

# --- INTERFACE UTILISATEUR ---
st.title("📦 Gestion de Stock (Sync Google)")

df = charger_stock(CSV_URL)

if df is None:
    st.error("❌ Impossible de lire la Google Sheet.")
    st.info("Vérifiez que votre fichier Google Sheet est bien partagé en mode : 'Tous les utilisateurs disposant du lien' -> 'Lecteur'.")
    st.stop()

# --- AFFICHAGE DU STOCK ---
st.subheader("📊 État des stocks")
manquants = []

# Barre latérale pour le réglage du seuil
with st.sidebar:
    st.header("⚙️ Réglages")
    seuil_alerte = st.slider("Seuil d'alerte", 1, 15, 3)
    st.divider()
    st.info("💡 Pour modifier les quantités ou ajouter des articles, éditez directement votre fichier Google Sheets. L'appli se met à jour automatiquement.")
    if st.button("🔄 Actualiser maintenant"):
        st.cache_data.clear()
        st.rerun()

# Affichage des articles
if df.empty:
    st.warning("Le tableau est vide. Ajoutez des lignes dans Google Sheets (nom, quantite, unite).")
else:
    # On parcourt le tableau récupéré de Google
    for index, row in df.iterrows():
        # Vérification des colonnes pour éviter les crashs si mal nommées
        nom = str(row.get('nom', 'Inconnu')).capitalize()
        qte = row.get('quantite', 0)
        unite = str(row.get('unite', 'Unité(s)'))
        
        col1, col2 = st.columns([3, 1])
        
        alerte = qte < seuil_alerte
        icone = "🔴" if alerte else "🟢"
        
        if alerte:
            manquants.append(f"- {nom} : {qte} {unite}")
            
        with col1:
            st.markdown(f"{icone} **{nom}**")
            st.caption(f"Type : {unite}")
        with col2:
            st.markdown(f"**{qte}**")

# --- SECTION COMMANDE ---
st.divider()
st.subheader("📧 Commander")

if manquants:
    st.warning(f"Il y a {len(manquants)} article(s) en alerte.")
    mail_dest = st.text_input("Envoyer la liste à :", value=MON_EMAIL)
    
    if st.button("🚀 Envoyer le mail de commande"):
        with st.spinner("Envoi..."):
            if envoyer_mail(mail_dest, manquants):
                st.success("📧 Liste envoyée avec succès !")
else:
    st.success("✅ Tout est en stock.")

# Lien direct vers la sheet pour faciliter la modif
st.sidebar.markdown(f"[🔗 Ouvrir la Google Sheet]({URL_BRUTE})")

