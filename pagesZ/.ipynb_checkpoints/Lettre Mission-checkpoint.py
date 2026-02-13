import os
import pdfkit
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import streamlit.components.v1 as components
from Database.utils_sirene import get_company_sirene
# from Database.utils_rcs import get_company_rcs

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

siren = st.text_input("Entrée le SIREN")

genre = st.radio("Civilité :",
                ["Monsieur", "Madame", "Ne pas préciser"]
                )

associes = ["LEVASSEUR Antoine", "Lecomte Reynald",
            "DUCLOS Franck", "BERLEMEONT Rodolphe", "Boudier Loïc"]

ec = st.selectbox("Associé en charge", associes)

debut = st.date_input("Date de début de la mission", value="today", format="DD/MM/YYYY")
fin= st.date_input("Date de fin de la mission", format="DD/MM/YYYY")

services = ["Paie", "Tenue", "Surveillance", "Audit", "Secrétariat Juridique"]
type_mission = st.selectbox("Type de mission", services)

situation = st.radio("Titre à définir", ["Situation intermédiaire", "Tableaux de bord"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    compl = st.checkbox("Mission complémentaire")

if st.button("⚙️ Générer la lettre de mission"):
    infos_siren = get_company_sirene(siren)
    infos_siren
    # info_rcs = get_company_rcs(siren)
