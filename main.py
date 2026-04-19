import streamlit as st
import json
import os
import smtplib
from email.message import EmailMessage

# --- RÉCUPÉRATION DES SECRETS ---
try:
    MON_EMAIL = st.secrets["MON_EMAIL"]
    MON_CODE_SECRET = st.secrets["MON_CODE_SECRET"]
except Exception:
    st.error("⚠️ Erreur : Les secrets 'MON_EMAIL' et 'MON_CODE_SECRET' ne sont pas configurés.")
    st.stop()

FICHIER_STOCK = "stock.json"

# --- FONCTIONS TECHNIQUES ---
def charger_stock():
    if os.path.exists(FICHIER_STOCK):
        try:
            with open(FICHIER_STOCK, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def sauvegarder_stock(stock):
    with open(FICHIER_STOCK, "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=4, ensure_ascii=False)

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

# --- INTERFACE UTILISATEUR ---
st.set_page_config(page_title="Mon Stock Pro", page_icon="📦", layout="centered")

st.title("📦 Gestion de Stock Professionnelle")

# Charger les données
stock = charger_stock()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("⚙️ Contrôle")
    seuil_alerte = st.slider("Seuil d'alerte (Rouge)", 1, 15, 3)
    
    st.divider()
    
    st.subheader("➕ Ajouter un article")
    nom_art = st.text_input("Désignation").lower().strip()
    type_unite = st.radio("Type", ["Unité(s)", "Carton(s)"], horizontal=True)
    
    if st.button("Ajouter à la liste"):
        if nom_art:
            if nom_art not in stock:
                stock[nom_art] = {"qte": 0, "unite": type_unite}
                sauvegarder_stock(stock)
                st.success(f"'{nom_art}' ajouté !")
                st.rerun()
            else:
                st.warning("Cet article est déjà dans la liste.")

# --- AFFICHAGE DU STOCK ---
st.subheader("📊 État des stocks")
manquants = []

if not stock:
    st.info("Aucun article en stock. Utilisez le menu à gauche pour commencer.")
else:
    c_head1, c_head2, c_head3 = st.columns([2, 2, 1])
    c_head1.write("**Article (Type)**")
    c_head2.write("**Quantité**")
    c_head3.write("**Suppr.**")

    for nom, info in sorted(stock.items()):
        c1, c2, c3 = st.columns([2, 2, 1])
        
        unite_texte = info.get('unite', 'Unité(s)')
        alerte = info['qte'] < seuil_alerte
        
        if alerte:
            manquants.append(f"- {nom.capitalize()} : {info['qte']} {unite_texte}")
            nom_affiche = f"🔴 {nom.capitalize()}"
        else:
            nom_affiche = f"🟢 {nom.capitalize()}"

        with c1:
            st.markdown(f"**{nom_affiche}**")
            st.caption(f"({unite_texte})") # <--- L'unité s'affiche ici maintenant
        
        with c2:
            n_qte = st.number_input(
                f"Qté de {nom}", 
                min_value=0, 
                value=info['qte'], 
                key=f"input_{nom}",
                label_visibility="collapsed"
            )
            if n_qte != info['qte']:
                stock[nom]['qte'] = n_qte
                sauvegarder_stock(stock)
                st.rerun()

        with c3:
            if st.button("🗑️", key=f"del_{nom}"):
                del stock[nom]
                sauvegarder_stock(stock)
                st.rerun()

# --- SECTION COMMANDE ---
st.divider()
st.subheader("📧 Envoyer une demande de commande")

if manquants:
    st.warning(f"Il y a {len(manquants)} article(s) sous le seuil d'alerte.")
    mail_dest = st.text_input("Envoyer à l'adresse :", placeholder="exemple@gmail.com")
    
    if st.button("🚀 Envoyer le mail maintenant"):
        if mail_dest = st.text_input("Envoyer à l'adresse :", value="matthieuwach@gmail.com")
            with st.spinner("Envoi du mail en cours..."):
                if envoyer_mail(mail_dest, manquants):
                    st.success(f"📧 Liste envoyée avec succès à {mail_dest} !")
        else:
            st.error("Veuillez saisir une adresse mail valide.")
else:
    st.success("✅ Tout est en stock. Pas de commande nécessaire.")
    
