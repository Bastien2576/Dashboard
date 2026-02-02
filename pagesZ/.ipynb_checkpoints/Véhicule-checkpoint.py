import datetime
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import sql

st.subheader("Ajouter un nouveau véhicule", anchor=False)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path)

user_id = st.session_state["utilisateur_id"]

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

with st.form("form_saisie", clear_on_submit=True):

    col1, col3, col2 = st.columns([6,1,6])

    today = datetime.date.today()

    with col1:

        colm, coln = st.columns([27,16])

        with colm:
            type_vehicule = st.selectbox("Type de véhicule", ["Automobile", "Motocyclette", "Cyclomoteur"])

            immat = st.text_input("Immatriculation")

    with col3:
        st.write(" ")

    with col2:
        cv = st.number_input("Puissance CV", step=1)

    submitted = st.form_submit_button("💾 Enregistrer le véhicule")

    if submitted:
        cursor.execute("""
        INSERT INTO vehicule (id_utilisateur, date, immatriculation, cv, type_vehicule)
        VALUES (%s, %s, %s, %s,%s, %s)
        """, (user_id, today, immat, cv, type_vehicule))

        cursor.execute(
        """
        INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
        VALUES (NOW(), %s, 'vehicule', 'Ajout_vehicule', %s)
        """,
        (user_id, f"Ajout d'un véhicule {type_vehicule} immatriculé {immat}"))
        conn.commit()
        st.rerun()

st.info("""
- Si votre véhicule est une automobile avec CV > 13, renseignez '13 CV'
- Si votre véhicule est une motocyclette avec CV > 6, renseignez '6 CV'
""")