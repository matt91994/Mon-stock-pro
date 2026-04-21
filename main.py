import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION ET SECRETS ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦")

try:
    MON_EMAIL = st.secrets["MON_EMAIL"]
    MON_CODE_SECRET = st.secrets["MON_CODE_SECRET"]
    GSHEET_URL = st.secrets["GSHEET_URL"]
except Exception:
    st.error("⚠️ Erreur : Les secrets ne sont pas configurés (MON_EMAIL, MON_CODE_SECRET, GSHEET_URL).")
    st.stop()

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Lit les données et force les types pour éviter les erreurs
    data = conn.read(spreadsheet=GSHEET_URL, ttl="0") # ttl=0 pour avoir les données en temps réel
    return data

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
        st.error(f"Erreur mail : {e}")
        return False

# --- CHARGEMENT ---
df = load_data()

# --- INTERFACE ---
st.title("📦 Inventaire Connecté (Google Sheets)")

with st.sidebar:
    st.header("⚙️ Paramètres")
    seuil = st.slider("Seuil d'alerte", 1, 20, 5)
    st.divider()
    st.subheader("➕ Nouvel Article")
    n_nom = st.text_input("Nom").lower().strip()
    n_unite = st.radio("Type", ["Unité(s)", "Carton(s)"], horizontal=True)
    if st.button("Ajouter"):
        if n_nom and n_nom not in df['nom'].values:
            new_row = pd.DataFrame([{"nom": n_nom, "quantite": 0, "unite": n_unite}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(spreadsheet=GSHEET_URL, data=updated_df)
            st.success("Ajouté !")
            st.rerun()

# --- LISTE DES STOCKS ---
manquants = []
st.subheader("📊 État actuel")

for index, row in df.iterrows():
    col1, col2, col3 = st.columns([3, 2, 1])
    
    alerte = row['quantite'] < seuil
    couleur = "🔴" if alerte else "🟢"
    if alerte:
        manquants.append(f"- {row['nom']} : {row['quantite']} {row['unite']}")

    with col1:
        st.write(f"{couleur} **{row['nom'].capitalize()}**")
        st.caption(f"({row['unite']})")
    
    with col2:
        # Modification de la quantité
        val = st.number_input("Qté", value=int(row['quantite']), key=f"q_{index}", label_visibility="collapsed")
        if val != row['quantite']:
            df.at[index, 'quantite'] = val
            conn.update(spreadsheet=GSHEET_URL, data=df)
            st.rerun()
            
    with col3:
        if st.button("🗑️", key=f"del_{index}"):
            df = df.drop(index)
            conn.update(spreadsheet=GSHEET_URL, data=df)
            st.rerun()

# --- SECTION MAIL ---
st.divider()
if manquants:
    st.warning(f"Attention : {len(manquants)} articles en rupture !")
    target = st.text_input("Envoyer à :", value=MON_EMAIL)
    if st.button("🚀 Commander maintenant"):
        if envoyer_mail(target, manquants):
            st.success("Mail envoyé !")
else:
    st.success("✅ Stock OK")
    
