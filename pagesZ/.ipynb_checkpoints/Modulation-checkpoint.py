import pandas as pd
import streamlit as st
import os
import numpy as np
import datetime
import psycopg2
from psycopg2 import sql
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import holidays
import locale
locale.setlocale(locale.LC_TIME, "French_France.1252") 

# ------------------------------
# 🔐 Chargement de l'environnement
# ------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

# ------------------------------
# 🔑 Session utilisateur
# ------------------------------
user_id = st.session_state["utilisateur_id"]

if st.session_state.get("heures_hebdo", 0) != 42.25:
    st.subheader("Compteur d'heures modulées")
else:
    st.error("⛔️ Accès refusé : cette section est réservée aux utilisateurs avec un quota d’heures hebdomadaire.")
    st.stop()

# ------------------------------
# 🔌 Connexion DB
# ------------------------------
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

conn = get_connection()
cursor = conn.cursor()
today_year = datetime.today().year

# ------------------------------
# ⏱️ Récupération heures hebdo
# ------------------------------
cursor.execute("SELECT heures_hebdo FROM utilisateurs WHERE id = %s", (user_id,))
user_hebdo = cursor.fetchone()[0]

# ------------------------------
# 📅 Jours fériés & congés
# ------------------------------
jours_feries = set(holidays.France(years=today_year).keys())

query_conges = """
SELECT date_depart, date_retour
FROM conges
WHERE utilisateur_id = %s
AND EXTRACT(YEAR FROM date_depart) = %s
"""
df_conges = pd.read_sql_query(query_conges, conn, params=(user_id, today_year))

jours_conges = set()
for _, row in df_conges.iterrows():
    jours = pd.date_range(start=row["date_depart"], end=row["date_retour"])
    jours_conges.update(jours.date)

# ------------------------------
# 🕒 Heures saisies (filtrées)
# ------------------------------
query_heures = """
SELECT date, type, duree_heures
FROM heures_saisies
WHERE utilisateur_id = %s
AND EXTRACT(YEAR FROM date) = %s
"""
df_heures = pd.read_sql_query(query_heures, conn, params=(user_id, today_year))
conn.close()

df_heures["date"] = pd.to_datetime(df_heures["date"])
df_heures["est_ferie"] = df_heures["date"].dt.date.isin(jours_feries)
df_heures["est_conge"] = df_heures["date"].dt.date.isin(jours_conges)
df_heures["est_valide"] = ~df_heures["est_ferie"] & ~df_heures["est_conge"]

df_valid = df_heures[df_heures["est_valide"]].copy()

# ------------------------------
# 📊 Agrégation hebdomadaire
# ------------------------------
df_valid["semaine"] = df_valid["date"].dt.to_period("W").apply(lambda r: r.start_time)
df_hebdo = df_valid.groupby("semaine", as_index=False)["duree_heures"].sum()
df_hebdo.rename(columns={"duree_heures": "heures_travaillees"}, inplace=True)
df_hebdo["semaine_debut"] = df_hebdo["semaine"]
df_hebdo["semaine_fin"] = df_hebdo["semaine_debut"] + pd.Timedelta(days=6)
df_hebdo["jours_ouvres"] = 0
df_hebdo["quota_ajuste"] = 0.0

for i, row in df_hebdo.iterrows():
    semaine = pd.date_range(start=row["semaine_debut"], end=row["semaine_fin"])
    
    # Jours ouvrés (lundi à vendredi)
    jours_ouvres = [d for d in semaine if d.weekday() < 5]
    
    # Retirer les jours fériés + jours de congé
    jours_ouvres_valides = [
        d for d in jours_ouvres
        if d.date() not in jours_feries and d.date() not in jours_conges
    ]

    nb_jours_valides = len(jours_ouvres_valides)
    quota = nb_jours_valides * (user_hebdo / 5)

    df_hebdo.at[i, "jours_ouvres"] = nb_jours_valides
    df_hebdo.at[i, "quota_ajuste"] = round(quota, 2)

# 🔄 Mise à jour de la colonne Modulation (en fonction du quota ajusté)
df_hebdo["Modulation"] = df_hebdo["heures_travaillees"] - df_hebdo["quota_ajuste"]
df_hebdo["Modulation"] = df_hebdo["Modulation"].fillna(0)

# ------------------------------
# 📅 Mise en forme visuelle
# ------------------------------
df_hebdo["semaine_debut"] = pd.to_datetime(df_hebdo["semaine"])
df_hebdo["S_num"] = df_hebdo["semaine_debut"].dt.isocalendar().week
df_hebdo["Semaine_label"] = (
    "S" + df_hebdo["S_num"].astype(str) + " : " +
    df_hebdo["semaine_debut"].dt.strftime("%d %B") + " - " +
    df_hebdo["semaine_fin"].dt.strftime("%d %B")
)

# ------------------------------
# 📈 Affichage Streamlit
# ------------------------------
col1, _, col3 = st.columns([7, 3, 3])

with col1:
    st.dataframe(df_hebdo[["Semaine_label", "heures_travaillees", "Modulation"]], use_container_width=True)

with _:
    with st.expander("Voir les explications :"):
        st.info("""
        - **⏱️ Total Heures** affiche les heures totales effectuées depuis le début de l'année.
        - L'indicateur indique les heures supplémentaires effectuées.
        - Si positif, les heures indiquées sont modulées.
        - Si négatif, les heures indiquées sont à rattraper.

        - **📅 Cette semaine** affiche les heures effectuées dans la semaine en cours.
        """)

with col3:
    if not df_hebdo.empty:
        last_week = df_hebdo.iloc[-1]
        st.metric("⏱️ Total Heures",
                  value=round(df_hebdo["heures_travaillees"].sum(), 2),
                  delta=round(df_hebdo["Modulation"].sum(), 2),
                  border=True)
        st.metric("📅 Cette semaine", 
                  f"{round(last_week['Modulation'], 2)}h",
                  border=True)
    else:
        st.warning("Aucune donnée d'heures saisie disponible.")