import os
import datetime
import uuid
from io import BytesIO
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
from Database.insert_logic import insert_non_fact, insert_fact, wide_to_long, week_processing

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

user_id = st.session_state.get("utilisateur_id")
if user_id is None:
    st.error("⚠️ Aucun utilisateur identifié. Veuillez vous connecter.")
    st.stop()

file = st.file_uploader("Importer des données",
                       accept_multiple_files=False, type="xlsx")

dfs = {}

if file is not None:
    xls = pd.ExcelFile(file)

    week = [s for s in xls.sheet_names if s.startswith("Semaine")]

    Semaines = st.multiselect(
        "",
        options=week,
        placeholder="Choisir les semaines à importer",
        max_selections=5
    )

    dfs = {s: pd.read_excel(xls, sheet_name=s, header=4)
          for s in Semaines}

if st.button("⚙️ Traitement"):
    with st.spinner("Traitement en cours..."):
        fact_dict, nfact_dict = week_processing(dfs)
        st.session_state['fact_dict'] = fact_dict
        st.session_state['nfact_dict'] = nfact_dict

    st.success("Traitement terminé ✅")

if "fact_dict" in st.session_state:
    st.subheader("Heures facturables")
    for name, df_fact in st.session_state['fact_dict'].items():
        if df_fact is None or df_fact.empty:
            pass
        else:
            with st.expander(f"{name} - Facturable"):
                    st.dataframe(df_fact, use_container_width=True)

if "nfact_dict" in st.session_state:
    st.subheader("Heures non facturables")
    for name, df_nfact in st.session_state['nfact_dict'].items():
        if df_fact is None or df_nfact.empty:
            pass
        else:
            with st.expander(f"{name} - Non facturable"):
                st.dataframe(df_nfact, use_container_width=True)

col_val, _ = st.columns([8, 80])

with col_val:
    valider = st.button("✅ Valider", key="valider")

if valider and dfs:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)

    # conn = get_connection()
    # try:
    #     for _, ligne in fact.iterrows():
    #         insert_fact(
    #             conn=conn,
    #             utilisateur_id=user_id,
    #             date=ligne["Date"],
    #             type_heure="Facturable",
    #             nom_du_client=ligne["Nom du client"],
    #             matricule_mission=ligne["Mission"],
    #             tache=ligne["Tâche"],
    #             commentaire=ligne["Détail"],
    #             duree_heures=ligne["Heures"],
    #         )
    #     for _, ligne in nfact.iterrows():
    #         insert_non_fact(
    #             conn=conn,
    #             utilisateur_id=user_id,
    #             date=ligne["Date"],
    #             type_heure="Non facturable",
    #             nom_du_client=ligne["Nom du client"],
    #             matricule_mission=ligne["Mission"],
    #             tache=ligne["Tâche"],
    #             commentaire=ligne["Détail"],
    #             duree_heures=ligne["Heures"]
    #         )

    #     st.success("✅ Données enregistrées en base.")
    # except Exception as e:
    #     st.error(f"Erreur lors de l'enregistrement : {e}")
    # finally:
    #     conn.close()

################################################################################################################################################################

# with st.expander("Rappel des codes d'activité"):

#     st.markdown("""
#         | Code  | Activité |
#         |-------|---------------|
#         | `100`	| Travaux comptables courants	                     |
#         | `102`	| FIDES	                                             |
#         | `109`	| Travaux comptables exceptionnels	                 |
#         | `200`	| Audit légal	                                     |
#         | `201`	| Audit contractuel	                                 |
#         | `202`	| Comptes consolidés CAC	                         |
#         | `203`	| Audit Déplacement	                                 |
#         | `209`	| Transfert GED CEGID -> Revisaudit	                 |
#         | `300`	| Mission de conseil social	                         |
#         | `309`	| Conseil social exceptionnel	                     |
#         | `310`	| Travaux paie exceptionnels	                     |
#         | `400`	| Travaux de paie	                                 |
#         | `401`	| Travaux de maladie	                             |
#         | `402`	| Travaux comptable	                                 |
#         | `403`	| Mise en place dossier                              |
#         | `404`	| Travaux dossiers ROBOT	                         |
#         | `405`	| Gestion organisme	                                 |
#         | `409`	| Travaux paie exceptionnels	                     |
#         | `501`	| Travaux juridiques	                             |
#         | `502`	| Travaux secrétariat	                             |
#         | `503`	| Travaux expertises judiciaires	                 |
#         | `600`	| Fiscalité personnelle (IR + ISF)	                 |
#         | `601`	| Etude fiscale particulière	                     |
#         | `602`	| Formation clients	                                 |
#         | `700`	| Conseil juridique	                                 |
#         | `800`	| Expertise judiciaire	                             |
#         | `901`	| Journée de Formation (intra ou Extra)	             |
#         | `902`	| Formation interne reçue / donnée	                 |
#         | `904`	| Documentation	                                     |
#         | `910`	| Planning Gestion des Temps	                     |
#         | `911`	| Administration	                                 |
#         | `913`	| Comité Technique préparation	                     |
#         | `914`	| Réunion Interne	                                 |
#         | `971`	| Instances Professionnelles NF (Assoc)	             |
#         | `972`	| Clubs & Projets structurants	                     |
#         | `973`	| Relations Publiques	                             |
#         | `974`	| Recrutement - Entretien des Collaborateurs (Assoc) |
#         | `978`	| Appel d'offre / Prospect	                         |
#         | `980`	| Informatique interne (DV)	                         |
#         """)