import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Gestion de Stock", page_icon="📦")

# ── Sidebar Réglages ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Réglages")
    seuil_global = st.slider("Seuil d'alerte global", 1, 20, 3)
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    sheet_url = st.secrets.get("sheet_url", "")
    if sheet_url:
        st.markdown(f"[🔗 Lien Google Sheet]({sheet_url})")

# ── Chargement données via CSV public ──────────────────────────────────────
def get_csv_url(url):
    sheet_id = url.split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    csv_url = get_csv_url(st.secrets["sheet_url"])
    df = pd.read_csv(csv_url)
    df.columns = [c.strip().lower().replace("é", "e").replace("è", "e").replace("ê", "e") for c in df.columns]
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Erreur de chargement du Google Sheet : {e}")
    st.stop()

required_cols = {"categorie", "produit", "quantite"}
if not required_cols.issubset(set(df.columns)):
    st.error(
        f"Colonnes manquantes. Colonnes trouvées : {list(df.columns)}\n"
        f"Colonnes requises : {list(required_cols)}"
    )
    st.stop()

df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce").fillna(0).astype(int)

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
        label += f"  🔴 {nb_alertes_cat} alerte(s)"

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
            cond = row["conditionnement"] if "conditionnement" in df.columns else "unités"
            st.markdown(f"- **{row['categorie']}** › {row['produit']} : {row['quantite']} {cond} (seuil : {row['seuil']})")

    st.markdown("**Envoyer la commande à :**")
    email_dest = st.text_input("Email", value="matthieuwach@gmail.com", label_visibility="collapsed")

    if st.button("🚀 Envoyer le mail"):
        lignes = "\n".join(
            f"- [{row['categorie']}] {row['produit']} : {row['quantite']} {row.get('conditionnement', 'unités')} (seuil : {row['seuil']})"
            for _, row in alertes.iterrows()
        )
        corps = f"Bonjour,\n\nLes articles suivants sont sous le seuil d'alerte :\n\n{lignes}\n\nMerci de passer commande."

        try:
            smtp_cfg = st.secrets["smtp"]
            msg = MIMEText(corps)
            msg["Subject"] = "⚠️ Alerte Stock"
            msg["From"] = smtp_cfg["user"]
            msg["To"] = email_dest

            with smtplib.SMTP_SSL(smtp_cfg["host"], int(smtp_cfg.get("port", 465))) as server:
                server.login(smtp_cfg["user"], smtp_cfg["password"])
                server.sendmail(smtp_cfg["user"], email_dest, msg.as_string())

            st.success("✅ Mail envoyé avec succès !")
        except Exception as e:
            st.error(f"Erreur envoi mail : {e}")
else:
    st.success("✅ Tous les stocks sont au-dessus du seuil.")
