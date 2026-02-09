import os
import psycopg2
import pdfkit
import numpy as np
import pandas as pd
import streamlit as st
from psycopg2 import sql
from dotenv import load_dotenv
import streamlit.components.v1 as components

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

# Connexion DB
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def insert_total_facturation(conn, id_total, montant_fact):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COALESCE(SUM(facture), 0) AS montant_calc,
            COALESCE(SUM(quantite), 0) AS quantite
        FROM facturation
        WHERE id_total = %s
    """, (id_total,))
    result = cursor.fetchone()
    montant_calc, quantite = result

    boni_mali = montant_fact - montant_calc

    cursor.execute("""
        INSERT INTO total_facturation (
            montant_calc,
            montant_fact,
            boni_mali,
            id_total,
            quantité
        ) VALUES (%s, %s, %s, %s, %s)
    """, (montant_calc, montant_fact, boni_mali, id_total, quantite))

    conn.commit()

st.subheader("Édition de facture")

conn = get_connection()
cursor = conn.cursor()

tab1, tab2 = st.tabs(['Saisie de montant facturé', 'Impression de facture'])

###############################################################################################
# ONGLET SAISIE DE MONTANT
###############################################################################################

with tab1 :
    cursor.execute("SELECT DISTINCT nom_client FROM clients ORDER BY nom_client;")
    clients_choice = [row[0] for row in cursor.fetchall()]

    col1, col2, _, col3, _ = st.columns([2, 2, 1, 2, 10])

    with col1:
         # init clés de session
        if "id_total" not in st.session_state:
            st.session_state.id_total = None
        if "client" not in st.session_state:
            st.session_state.client = None
        if "mission" not in st.session_state:
            st.session_state.mission = None
        
        # Sélections
        client = st.selectbox("Client", clients_choice, key="client")
        
        mission_choice = []
        if client:
            cursor.execute("""
                SELECT m.matricule_mission
                FROM missions m
                JOIN dossiers d ON m.id_dossier = d.id
                JOIN clients c ON d.client_id = c.id
                WHERE c.nom_client = %s AND m.statut = 'Clôturé'
                ORDER BY m.matricule_mission
            """, (client,))
            mission_choice = [r[0] for r in cursor.fetchall()]

        with col2:
            mission = st.selectbox("Mission", mission_choice, placeholder="Choisissez une mission", key="mission")

    if st.button("✅ Valider") and mission:
        cursor.execute("""
            SELECT ft.id_total
            FROM facturation ft
            WHERE ft.client = %s AND ft.mission = %s
            GROUP BY ft.id_total
            ORDER BY MAX(ft.date_cloture) DESC
            LIMIT 1
        """, (client, mission))
        row = cursor.fetchone()
        if not row:
            st.warning("Aucun identifiant trouvé pour ce client/mission.")
            st.session_state.id_total = None
        else:
            st.session_state.id_total = row[0]
            st.success(f"identifiant sélectionné : {st.session_state.id_total}")

    if st.session_state.id_total:

        with st.form("saisie_montant"):

            montant = st.number_input("💰 Montant facturé (€)", min_value=0.0, step=0.01)

            submit = st.form_submit_button("💾 Enregistrer")

            if submit:
                insert_total_facturation(conn, st.session_state.id_total, montant)

                st.success(f"Total facturation créé / mis à jour pour id_total = {st.session_state.id_total}")

###############################################################################################
# ONGLET IMPRESSION
###############################################################################################
with tab2 :

    try:
        cola, _, colb = st.columns(3)
    
        cursor.execute("""
        SELECT DISTINCT id_total
        FROM facturation
        ORDER BY id_total
        """)
    
        date_fact = cursor.fetchall()
        date_fact = [row[0] for row in date_fact]
    
        with cola :
            id_total = st.selectbox("Matricule de facture", date_fact, placeholder="Nom de mission + date de clôture")
    
            if id_total:
                cursor.execute("""
                    SELECT date, code, nom, tache, libelle, quantite, facture
                    FROM facturation
                    WHERE id_total = %s
                    ORDER BY date
                """, (id_total,))
    
                rows = cursor.fetchall()
    
                cols = [desc[0] for desc in cursor.description]
                facturation = pd.DataFrame(rows, columns=cols)
    
            html_1 = facturation.to_html(index=False)
    
            config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial; }}
                    h2 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 40px; }}
                    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h2>ETAT DE PREFACTURATION</h2>
                {html_1}
            </body>
            </html>
            """
    
            components.html(html_content, height=600, scrolling=True)
    
            télécharger_p1 = st.button("📥 Télécharger en pdf")
    
            if télécharger_p1 :
                pdfkit.from_string(html_content, r"C:/Users/ubamiot/Scripts/Application_GI/test_facturation.pdf", configuration=config)

    except:
        st.warning("Pas de ligne de facturation")