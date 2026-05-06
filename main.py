import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Gestion de Stock", page_icon="📦")

# ── Connexion Google Sheet ──────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["sheet_url"]).sheet1

# ── Sidebar Réglages ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Réglages")
    seuil_global = st.slider("Seuil d'alerte global", 1, 20, 3)
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("[🔗 Lien Google Sheet](%s)" % st.secrets.get("sheet_url", "#"))

# ── Chargement données ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # Normalise les noms de colonnes
    df.columns = [c.strip().lower() for c in df.columns]
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Erreur de connexion au Google Sheet : {e}")
    st.stop()

# Colonnes attendues : categorie, produit, quantite, seuil (optionnel)
required_cols = {"categorie", "produit", "quantite"}
if not required_cols.issubset(set(df.columns)):
    st.error(
        f"Colonnes manquantes dans le Sheet. Colonnes trouvées : {list(df.columns)}\n"
        f"Colonnes requises : {list(required_cols)}"
    )
    st.stop()

df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce").fillna(0).astype(int)

# Utilise seuil individuel si la colonne existe, sinon seuil global
if "seuil" in df.columns:
    df["seuil"] = pd.to_numeric(df["seuil"], errors="coerce").fillna(seuil_global).astype(int)
else:
    df["seuil"] = seuil_global

df["alerte"] = df["quantite"] < df["seuil"]

# ── Interface principale ────────────────────────────────────────────────────
st.title("📦 Gestion de Stock")

categories = df["categorie"].unique()

for cat in categories:
    df_cat = df[df["categorie"] == cat]
    nb_alertes_cat = df_cat["alerte"].sum()

    label = f"📁 {cat}"
    if nb_alertes_cat > 0:
        label += f" 🔴 {nb_alertes_cat} alerte(s)"

    with st.expander(label, expanded=True):
        for _, row in df_cat.iterrows():
            col1, col2 = st.columns([3, 1])
            dot = "🔴" if row["alerte"] else "🟢"
            cond = row["conditionnement"] if "conditionnement" in df.columns else ""
            with col1:
                st.markdown(f"{dot} **{row['produit']}**")
            with col2:
                st.markdown(f"**{row['quantite']}** {cond}")

# ── Récap alertes & envoi mail ──────────────────────────────────────────────
alertes = df[df["alerte"]]

if not alertes.empty:
    st.warning(f"⚠️ Il y a **{len(alertes)}** article(s) en alerte.")

    with st.expander("Voir les articles en alerte"):
        for _, row in alertes.iterrows():
            st.markdown(f"- **{row['categorie']}** › {row['produit']} : {row['quantite']} unités (seuil : {row['seuil']})")

    st.markdown("**Envoyer la commande à :**")
    email_dest = st.text_input("Email", value="matthieuwach@gmail.com", label_visibility="collapsed")

    if st.button("🚀 Envoyer le mail"):
        lignes = "\n".join(
            f"- [{row['categorie']}] {row['produit']} : {row['quantite']} unités (seuil : {row['seuil']})"
            for _, row in alertes.iterrows()
        )
        corps = f"Bonjour,\n\nLes articles suivants sont sous le seuil d'alerte :\n\n{lignes}\n\nMerci de passer commande."

        try:
            smtp_cfg = st.secrets["smtp"]
            msg = MIMEText(corps)
            msg["Subject"] = "⚠️ Alerte Stock"
            msg["From"] = smtp_cfg["user"]
            msg["To"] = email_dest

            with smtplib.SMTP_SSL(smtp_cfg["host"], smtp_cfg.get("port", 465)) as server:
                server.login(smtp_cfg["user"], smtp_cfg["password"])
                server.sendmail(smtp_cfg["user"], email_dest, msg.as_string())

            st.success("✅ Mail envoyé avec succès !")
        except Exception as e:
            st.error(f"Erreur envoi mail : {e}")
else:
    st.success("✅ Tous les stocks sont au-dessus du seuil.")
