import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦")

# On récupère l'URL de la Sheet et on la transforme en lien de téléchargement direct CSV
try:
    raw_url = st.secrets["GSHEET_URL"]
    # Cette ligne transforme le lien de partage en lien de données pures
    csv_url = raw_url.replace('/edit?usp=sharing', '/export?format=csv').replace('/edit#gid=0', '/export?format=csv')
    
    MON_EMAIL = st.secrets["MON_EMAIL"]
    MON_CODE_SECRET = st.secrets["MON_CODE_SECRET"]
except:
    st.error("Vérifiez vos Secrets (GSHEET_URL, MON_EMAIL, MON_CODE_SECRET)")
    st.stop()

# Lecture simple des données
@st.cache_data(ttl=10) # Rafraîchit toutes le 10 secondes
def load_data(url):
    return pd.read_csv(url)

try:
    df = load_data(csv_url)
except:
    st.error("Impossible de lire la Google Sheet. Vérifiez qu'elle est bien en mode 'Tous les utilisateurs disposant du lien : Lecteur'")
    st.stop()

st.title("📦 Mon Inventaire")

# Affichage simple
st.table(df)

st.info("💡 Note : Cette version simplifiée est en lecture seule pour tester la connexion.")
