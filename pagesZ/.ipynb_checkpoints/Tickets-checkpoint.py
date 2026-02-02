import os
import io
import locale
import psycopg2
import openpyxl
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from Database.insert_logic import insert_tr

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path)

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # Linux/Mac

user_id = st.session_state["utilisateur_id"]

st.subheader("Suivi des Tickets Restaurant")

col1, _, col2 = st.columns([6, 1, 3])
with col2:
    annee = st.selectbox("Année", list(range(2024, datetime.today().year + 1)), index=1)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cursor = conn.cursor()

query = """
SELECT mois, annee, tr_pris
FROM tickets_resto
WHERE utilisateur_id = %s AND annee = %s
"""

df_tickets = pd.read_sql(query, conn, params=(user_id, annee))

mois_list = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet",
             "Aout", "Septembre", "Octobre", "Novembre", "Decembre"]

df_base = pd.DataFrame({"Mois": mois_list, "Tickets souhaités": [None] * 12})

for _, row in df_tickets.iterrows():
    matching = df_base[df_base["Mois"] == row["mois"]]
    if not matching.empty:
        idx = matching.index[0]
        df_base.at[idx, "Tickets souhaités"] = row["tr_pris"]

with col1:
    cola, colb = st.columns(2)
    with cola:
        mois = datetime.today().strftime("%B").capitalize()

        tr_s = st.number_input("Nombre de tickets souhaité pour le mois en cours", 0, 20, step=1)

    if st.button("💾 Enregistrer"):
        if not any((df_tickets["mois"] == mois) & (df_tickets["annee"] == annee)):
            insert_tr(conn, user_id, mois, annee, tr_s)

            cursor.execute(
            """
            INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
            VALUES (NOW(), %s, 'tickets', 'Ajout_souhait_tickets', %s)
            """,
            (user_id, f'Demande de {tr_s} tickets restaurant pour le mois de {mois}'))
            conn.commit()

            st.success(f"🎫 {tr_s} tickets enregistrés pour {mois} {annee}")
            st.rerun()
        else:
            st.error("⛔ Une saisie existe déjà pour ce mois")

    st.subheader("Historique personnel")
    st.dataframe(df_base, use_container_width=True)

today_month = datetime.today().strftime("%m")
today_year = datetime.today().year

query_h = f"""
SELECT date, SUM(duree_heures) AS heures_travaillees
FROM heures_saisies
WHERE utilisateur_id = {user_id}
  AND TO_CHAR(date, 'YYYY') = '{today_year}'
GROUP BY date
ORDER BY date
"""

df = pd.read_sql_query(query_h, conn)
conn.close()

df["date"] = pd.to_datetime(df["date"])
df["jour_formaté"] = df["date"].dt.strftime('%A %d %B').str.capitalize()

df["tickets_eligibles"] = df["heures_travaillees"].apply(lambda x: 1 if x >= 4 else 0)
tickets_total = df["tickets_eligibles"].sum()
diff = tickets_total - df_base['Tickets souhaités'].sum()

output = io.BytesIO()
df.to_excel(output, index=False, engine='openpyxl')

st.download_button(
    label="📥 Télécharger en XLS",
    data=output,
    file_name="Solde tickets.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

with col2 :
    st.metric(
        "Solde Tickets restaurants :",
        value=f'{tickets_total} tickets cumulés',
        delta=f'{diff} tickets restants',
        border=True
    )

    with st.expander("Voir l'explication ci-dessous :"):
        st.write("- Les **tickets cumulés** représentent tous les tickets ayant été cumulés depuis le début de l'année")
        st.write("- Les **tickets restants** correspondent à la différence entre les tickets cumulés et les tickets renseignés dans le tableau ci-contre")
        st.write(" Exemple : ")
        seuil = st.slider("Tickets restants", -5, 5, 1)
        seuil_abs = abs(seuil)

        if seuil < 0:
            st.warning(f"Votre déficit est de {seuil_abs} tickets")
        elif seuil > 0:
            st.success(f"Il vous reste {seuil} tickets à récupérer")
        else:
            st.info("Votre solde est à 0")