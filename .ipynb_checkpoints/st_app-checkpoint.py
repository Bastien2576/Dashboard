import os
import streamlit as st
from dotenv import load_dotenv
import psycopg2

st.set_page_config(
    page_title="Parsing temps",
    page_icon="🗂️",
    initial_sidebar_state="collapsed",
    layout="wide",
)

load_dotenv()

def get_db_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

st.session_state.setdefault("authenticated", True)
st.session_state.setdefault("role", "admin")

role = st.session_state["role"]

respond_1 = st.Page(
    "pagesZ/Dépôt.py",
    title="Test dépôt Excel",
    icon=":material/add_notes:",
)

admin_1 = st.Page(
    "pagesZ/Dashboard.py",
    title="Tableau de bord",
    icon=":material/analytics:",
    default=(role == "admin"),
)

admin_2 = st.Page(
    "pagesZ/Taux_fact.py",
    title="Taux de facturation",
    icon=":material/wallet:",
)

admin_3 = st.Page(
    "pagesZ/Ajout.py",
    title="Ajouter",
    icon=":material/create_new_folder:",
)

admin_4 = st.Page(
    "pagesZ/add_fact.py",
    title="Éditer une facturation",
    icon=":material/contract:",
)

st.logo("images/horizontal_blue.png", icon_image="images/secno_icon.png")

page_dict = {}
admin_pages = [admin_1, admin_2, admin_4]

if role == "admin":
    page_dict["Espace Administrateur"] = admin_pages

pg = st.navigation(page_dict)
pg.run()