import streamlit as st
import pandas as pd
import numpy as np
import os
import locale
from dotenv import load_dotenv
import time
import psycopg2

st.set_page_config(page_title="Parsing temps", page_icon="🗂️", initial_sidebar_state="collapsed", layout="wide")

load_dotenv()

ADMIN = os.getenv("ADMIN_EMAILS")

def login_screen():
    st.button("Se connecter avec Microsoft", on_click=st.login)

if not st.user.is_logged_in:
    col1, col2, col3 = st.columns([2, 5, 2])

    with col2:
        st.title("Tempno")
        st.subheader("_Parsing feuilles de temps_", divider="grey")
    
        st.info("Connectez-vous avec votre compte Microsoft pour accéder à votre espace personnel")
        login_screen()
else:
    st.session_state["authenticated"] = True
    st.session_state["role"] = "admin" if st.user.email in ADMIN else "user"

def get_or_create_user(conn, nom, prenom, matricule, nom_service, heures_hebdo=35, type_vehicule=None):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilisateurs WHERE matricule = %s", (matricule,))
    result = cursor.fetchone()

    if result:
        return result[0]
    
    cursor.execute("""
        INSERT INTO utilisateurs (matricule, nom, prenom, nom_service, heures_hebdo, type_vehicule)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (matricule, nom, prenom, nom_service, heures_hebdo, type_vehicule))
    conn.commit()
    return cursor.fetchone()[0]

try:
    role = st.session_state.role
    utilisateur_id = st.session_state.get("utilisateur_id")
except:
    pass

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
try:
    email = st.user.email
    prenom, nom = st.user.name.split(" ", 1)

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM utilisateurs WHERE mail = %s", (email,))
    result = cursor.fetchone()
    
    if not result:
        st.warning("Profil introuvable. Merci de compléter vos informations pour activer votre compte.")
        with st.form("creation_profil"):
            matricule = st.text_input("Code collaborateur", max_chars=3)
            heures_hebdo = st.selectbox("Heures contractuelles hebdomadaires", ["35", "39", "42.25"])
            nom_service = st.selectbox("Nom de service", ["Audit", "Surveillance",
                                                          "Tenue", "Social / Paie",
                                                          "Secrétariat", "Expert comptable associé"])
    
            submitted = st.form_submit_button("Créer mon profil")
    
            if submitted:
                cursor.execute("""
                    INSERT INTO utilisateurs (matricule, nom, prenom, nom_service, heures_hebdo, mail)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (matricule, nom, prenom, nom_service, heures_hebdo, email))
    
                conn.commit()
                utilisateur_id = cursor.fetchone()[0]
    
                cursor.execute("""
                    INSERT INTO taux_facturation (utilisateur_id, taux, date, nom, prenom)
                    VALUES (%s, 0, NOW(), %s, %s)
                """, (utilisateur_id, nom, prenom))
                conn.commit()
    
                st.session_state["utilisateur_id"] = utilisateur_id
                st.success("Profil créé avec succès !")
                st.rerun()
        st.stop()
    else:
        st.session_state["utilisateur_id"] = result[0]

except:
    pass

respond_1 = st.Page(
    "pagesZ/Dépôt.py",
    title="Test dépôt Excel",
    icon=":material/add_notes:"
)

admin_1 = st.Page(
    "pagesZ/Dashboard.py",
    title="Tableau de bord",
    icon=":material/analytics:",
    default=(role == "admin")
)

admin_2 = st.Page(
    "pagesZ/Taux_fact.py",
    title="Taux de facturation",
    icon=":material/wallet:"
)

admin_3 = st.Page(
    "pagesZ/Ajout.py",
    title="Ajouter",
    icon=":material/create_new_folder:"
)

admin_4 = st.Page(
    "pagesZ/add_fact.py",
    title="Éditer une facturation",
    icon=":material/contract:"
)

logout_page = st.Page(
    st.logout,
    title="Se déconnecter",
    icon=":material/logout:"
)

respond_pages = [respond_1]
admin_pages = [admin_1, admin_2, admin_3, admin_4]
account_pages = [logout_page]

st.logo("images/horizontal_blue.png", icon_image="images/secno_icon.png")
page_dict = {}

if st.session_state.role in ["user", "admin"]:
    page_dict["Espace Collaborateur"] = respond_pages
if st.session_state.role == "admin":
    page_dict["Espace Administrateur"] = admin_pages

pg = st.navigation({"Compte": account_pages} | page_dict)
pg.run()

st.sidebar.success(f"Connecté(e) en tant que : {st.user.name} ({role})")