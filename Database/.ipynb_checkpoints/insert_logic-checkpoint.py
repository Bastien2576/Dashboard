import psycopg2
import os
import pandas as pd
import numpy as np
import datetime
from datetime import datetime
from dotenv import load_dotenv
from psycopg2 import sql
import streamlit as st

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path)

conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
cursor = conn.cursor()

##########################################################################################
# Insertion Heures Non Facturables
##########################################################################################

def insert_non_fact(conn, utilisateur_id, type_heure, date, duree_heures, tache, commentaire=None):
    cursor = conn.cursor()

    cursor.execute("SELECT activite FROM activites WHERE code = %s", (tache,))
    activite_result = cursor.fetchone()
    if activite_result is None:
        raise ValueError(f"L'activité '{tache}' est introuvable.")
    activite_nom = activite_result[0]

    mission_id = None

    cursor.execute("""
        INSERT INTO heures_saisies (utilisateur_id, type, date, duree_heures, mission_id, activite, commentaire, code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (utilisateur_id, type_heure, date, duree_heures, mission_id, activite_nom, commentaire, tache))
    conn.commit()

##########################################################################################
# Insertion Heures Facturables
##########################################################################################

def insert_fact(conn, utilisateur_id, date, duree_heures, type_heure, nom_du_client, matricule_mission, tache, commentaire=None):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (nom_du_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"La mission '{matricule_mission}' est introuvable.")
    client_id = client_result[0]

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s AND id_client = %s", (matricule_mission, client_id))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{matricule_mission}' avec le client {id_client} est introuvable.")
    mission_id = mission_result[0]

    cursor.execute("""
        INSERT INTO heures_saisies (utilisateur_id, date, duree_heures, type, nom_du_client, mission_id, client_id, commentaire, code)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (utilisateur_id, date, duree_heures, type_heure, nom_du_client, mission_id, client_id, commentaire, tache))
    conn.commit()

##########################################################################################
# Insertion Frais Kilométriques
##########################################################################################

def insert_frais_km(conn, utilisateur_id, date, distance_km, matricule_mission):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s", (matricule_mission,))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{matricule_mission}' est introuvable.")
    mission_id = mission_result[0]

    cursor.execute("""
        INSERT INTO frais_km (utilisateur_id, date, distance_km, mission_id)
        VALUES (%s, %s, %s, %s)
    """, (utilisateur_id, date, distance_km, mission_id))
    conn.commit()

##########################################################################################
# Création d'un Nouveau Client
##########################################################################################

def insert_client(conn, code_client, nom_client, associe, distance_km):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM utilisateurs WHERE CONCAT(nom, ' ', prenom) = %s", (associe,))
    associe_result = cursor.fetchone()
    if associe_result is None:
        raise ValueError(f"{associe} est introuvable.")
    id_associe = associe_result[0]

    cursor.execute("""
        INSERT INTO clients (code_client, nom_client, id_associe, distance_km)
        VALUES (%s, %s, %s, %s)
    """, (code_client, nom_client, id_associe, distance_km))
    conn.commit()

##########################################################################################
# Création d'un Nouveau Dossier
##########################################################################################

def insert_dossier(conn, nom_client, code_dossier, nom_dossier, associe):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM utilisateurs WHERE CONCAT(nom, ' ', prenom) = %s", (associe,))
    associe_result = cursor.fetchone()
    if associe_result is None:
        raise ValueError(f"{associe} est introuvable.")
    id_associe = associe_result[0]

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (nom_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"{nom_client} est introuvable.")
    client_id = client_result[0]

    cursor.execute("""
        INSERT INTO dossiers (client_id, matricule_dossier, nom_dossier, id_associe)
        VALUES (%s, %s, %s, %s)
    """, (client_id, code_dossier, nom_dossier, id_associe))
    conn.commit()

##########################################################################################
# Création d'une Nouvelle Mission
##########################################################################################

def insert_mission(conn, matricule_mission, nom_mission, nom_client):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (nom_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"{nom_client} est introuvable.")
    client_id = client_result[0]

    try:
        cursor.execute("SELECT id FROM dossiers WHERE client_id = %s", (client_id,))
        folder_result = cursor.fetchone()
        if folder_result is None:
            raise ValueError(f"Le dossier pour le client {nom_client} est introuvable.")
        id_dossier = folder_result[0]

        cursor.execute("""
            INSERT INTO missions (matricule_mission, nom_mission, id_dossier, id_client, statut)
            VALUES (%s, %s, %s, %s, 'En cours')
        """, (matricule_mission, nom_mission, id_dossier, client_id))

    except:
        conn.rollback()
        st.error(f"Dossier pour {nom_client} inexistant, veuillez en créer un")

##########################################################################################
# Insertion Frais Kilométriques (dossier)
##########################################################################################

"""
A REVOIR
"""

def insert_dossier_km(conn, nom_client, nom_dossier, matricule_dossier):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM client WHERE nom_client = %s", (nom_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"Le client '{nom_client}' est introuvable.")
    client_id = client_result[0]

    cursor.execute("SELECT id FROM utilisateurs WHERE matricule_dossier = %s", (matricule_dossier,))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{matricule_dossier}' est introuvable.")
    associe_id = mission_result[0]

    cursor.execute("""
        INSERT INTO frais_km (conn, nom_client, nom_dossier, matricule_dossier)
        VALUES (%s, %s, %s, %s)
    """, (utilisateur_id, date, distance_km, mission_id))
    conn.commit()

##########################################################################################
# Insertion Frais Kilométriques (mission)
##########################################################################################

def insert_mission_km(conn, utilisateur_id, date, distance_km, matricule_mission):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s", (matricule_mission,))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{matricule_mission}' est introuvable.")
    mission_id = mission_result[0]

    cursor.execute("""
        INSERT INTO frais_km (utilisateur_id, date, distance_km, mission_id)
        VALUES (%s, %s, %s, %s)
    """, (utilisateur_id, date, distance_km, mission_id))
    conn.commit()

##########################################################################################
# Insertion de frais autres
##########################################################################################

def insert_af(conn, utilisateur_id, date, nom_mission, type_fr, montant, tva, nom_client):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s", (nom_mission,))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"{nom_mission} est introuvable.")
    id_mission = mission_result[0]

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (nom_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"{nom_client} est introuvable.")
    id_client = client_result[0]

    cursor.execute("""
        INSERT INTO frais_repas (utilisateur_id, date, mission_id, type_fr, montant, tva, client_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (utilisateur_id, date, id_mission, type_fr, montant, tva, id_client))
    conn.commit()

##########################################################################################
# Insertion Souhait Tickets Restaurant
##########################################################################################

def insert_tr(conn, user_id, mois, annee, tr_s):
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets_resto (utilisateur_id, mois, annee, tr_pris)
        VALUES (%s, %s, %s, %s)
    """, (user_id, mois, annee, tr_s))
    conn.commit()

##########################################################################################
# MaJ Heures Saisies (deuxième onglet, non facturable)
##########################################################################################

def update_non_fact(conn, saisie_id, utilisateur_id, type_heure, date, duree_heures, code, commentaire=None):
    cursor = conn.cursor()

    cursor.execute("SELECT activite FROM activites WHERE code = %s", (code,))
    activite_result = cursor.fetchone()
    if activite_result is None:
        raise ValueError(f"L'activité '{code}' est introuvable.")
    activite_nom = activite_result[0]

    cursor.execute("""
        UPDATE heures_saisies
        SET type = %s,
            date = %s,
            duree_heures = %s,
            code = %s,
            activite = %s,
            commentaire = %s
        WHERE id = %s AND utilisateur_id = %s
    """, (
        type_heure,
        date,
        duree_heures,
        code,
        activite_nom,
        commentaire,
        saisie_id,
        utilisateur_id
    ))

    conn.commit()

##########################################################################################
# MaJ Heures Saisies (deuxième onglet, facturable)
##########################################################################################

def update_fact(conn, saisie_id, utilisateur_id, type_heure, date, duree_heures, nom_du_client, matricule_mission, code, commentaire=None):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (nom_du_client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"Le client '{nom_du_client}' est introuvable.")
    client_id = client_result[0]

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s AND id_client = %s", (matricule_mission, client_id))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{matricule_mission}' avec le client {id_client} est introuvable.")
    mission_id = mission_result[0]

    cursor.execute("""
        UPDATE heures_saisies
        SET type = %s,
            date = %s,
            duree_heures = %s,
            nom_du_client = %s,
            client_id = %s,
            mission_id = %s,
            code = %s,
            commentaire = %s
        WHERE id = %s AND utilisateur_id = %s
    """, (
        type_heure,
        date,
        duree_heures,
        nom_du_client,
        client_id,
        mission_id,
        code,
        commentaire,
        saisie_id,
        utilisateur_id
    ))

    conn.commit()

##########################################################################################
# Insertion facturation
##########################################################################################

def create_fact(conn, client, mission_mat):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM clients WHERE nom_client = %s", (client,))
    client_result = cursor.fetchone()
    if client_result is None:
        raise ValueError(f"Le client '{client}' est introuvable.")
    client_id = client_result[0]

    cursor.execute("SELECT id FROM missions WHERE matricule_mission = %s AND id_client = %s", (mission_mat, client_id))
    mission_result = cursor.fetchone()
    if mission_result is None:
        raise ValueError(f"La mission '{mission_mat}' avec le client {client_id} est introuvable.")
    mission_id = mission_result[0]

    cursor.execute("""
        SELECT hs.utilisateur_id, hs.id AS saisie_id, hs.client_id, hs.duree_heures, hs.date, hs.mission_id, hs.code AS tache,
               hs.duree_heures * COALESCE(tf.taux, 0) AS montant, hs.commentaire, d.id AS dossier_id, d.matricule_dossier,
               km.id AS frais_km_id, fr.id AS frais_repas_id, c.nom_client, m.matricule_mission, u.nom AS utilisateur_nom, u.matricule AS utilisateur_matricule
        FROM heures_saisies hs
        LEFT JOIN utilisateurs u ON hs.utilisateur_id = u.id
        LEFT JOIN clients c ON hs.client_id = c.id
        LEFT JOIN dossiers d ON d.client_id = c.id
        LEFT JOIN missions m ON hs.mission_id = m.id
        LEFT JOIN frais_km km ON hs.utilisateur_id = km.utilisateur_id AND hs.mission_id = km.mission_id
        LEFT JOIN frais_repas fr ON hs.utilisateur_id = fr.utilisateur_id AND hs.mission_id = fr.mission_id
        LEFT JOIN LATERAL (
        SELECT taux
        FROM taux_facturation tf
        WHERE tf.utilisateur_id = hs.utilisateur_id
        ORDER BY tf.date DESC
        LIMIT 1
        ) tf ON true
        WHERE hs.client_id = %s
          AND hs.mission_id = %s
    """, (client_id, mission_id))

    results = cursor.fetchall()
    st.write(f"Nombre de lignes trouvées pour {mission_mat} / {client} : {len(results)}")

    if not results:
        st.warning(f"⚠️ Aucune heure saisie trouvée ou aucun taux applicable pour {mission_mat}.")

    for row in results:
        id_total = f"{mission_mat}_{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"

        (utilisateur_id, saisie_id, client_id, duree_heures, date_saisie, mission_id, tache,
         montant, commentaire, dossier_id, matricule_dossier, frais_km_id, frais_repas_id,
         nom_client, matricule_mission, utilisateur_nom, utilisateur_matricule) = row

        cursor.execute("""
            INSERT INTO facturation (
                id_utilisateur,
                id_client,
                id_dossier,
                id_mission,
                id_fraiskm,
                id_fraisrep,
                id_hs,
                date,
                client,
                dossier,
                mission,
                code,
                nom,
                tache,
                libelle,
                quantite,
                facture,
                date_cloture,
                id_total
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (
            utilisateur_id,
            client_id,
            dossier_id,
            mission_id,
            frais_km_id,
            frais_repas_id,
            saisie_id,
            date_saisie,
            nom_client,
            matricule_dossier,
            matricule_mission,
            utilisateur_matricule,
            utilisateur_nom,
            tache,
            commentaire,
            duree_heures,
            montant,
            id_total
        ))

    conn.commit()

##########################################################################################
# Parsing feuille de temps
##########################################################################################

def wide_to_long(df: pd.DataFrame, fixed_cols_n: int = 6) -> pd.DataFrame:
    fixed_cols = list(df.columns[:fixed_cols_n])
    day_cols = list(df.columns[fixed_cols_n:])

    df2 = df.copy()
    df2.columns = [str(c) for c in df2.columns]

    fixed_cols = [str(c) for c in fixed_cols]
    day_cols = [str(c) for c in day_cols]

    long_df = df2.melt(
        id_vars=fixed_cols,
        value_vars=day_cols,
        var_name="Date",
        value_name="Heures",
    )

    long_df["Heures"] = pd.to_numeric(long_df["Heures"], errors="coerce")

    long_df = long_df.drop(columns=['Total du mois'])
    long_df = long_df.dropna(subset=["Heures"])
    long_df = long_df[long_df["Heures"] != 0]

    long_df = long_df[['Date', 'N° Client', 'Nom du client', 'Mission', 'Tâche', 'Détail', 'Heures']]

    return long_df.reset_index(drop=True)

##########################################################################################
# Traitement semaines feuille de temps
##########################################################################################

def week_processing(dfs):
    d_fact = {}
    d_nfact = {}

    for name, df in dfs.items():
        df = df.copy()

        dates = df.columns[6:13]
        df.rename(columns={c: pd.to_datetime(c, errors="coerce") for c in dates}, inplace=True)
        df.rename(
            columns={
                c: c.strftime("%Y-%m-%d")
                for c in df.columns[6:13]
                if isinstance(c, pd.Timestamp)
            },
            inplace=True,
        )

        df = df.rename(columns={"du": "N° Client", "du.1": "Total du mois"})

        fact = df.iloc[1:40, :13].copy()
        fact.iloc[:, 6:13] = fact.iloc[:, 6:13].astype(float)
        fact = fact.dropna(subset="N° Client")

        try:
            fact = wide_to_long(fact, 6)
            fact["Date"] = pd.to_datetime(fact["Date"], dayfirst=False).dt.strftime('%Y-%m-%d')
            fact['Détail'] = fact['Détail'].fillna("")
            d_fact[name] = fact
        except Exception:
            d_fact[name] = None

        nfact = df.iloc[41:54, :13].copy()
        nfact = nfact.loc[nfact["Total du mois"] != 0].copy()

        empty_date_cols = [c for c in nfact.columns[6:13] if nfact[c].isna().all()]
        nfact = nfact.drop(columns=empty_date_cols).fillna(0)

        nfact_date_cols = [c for c in nfact.columns if isinstance(c, str) and c[:4].isdigit()]
        nfact.iloc[:, 6:13] = nfact.iloc[:, 6:13].astype(float)

        try:
            nfact = wide_to_long(nfact, 6)
            nfact["Date"] = pd.to_datetime(nfact["Date"], dayfirst=False).dt.strftime('%Y-%m-%d')
            nfact["Détail"].replace(0, "", inplace=True)
            d_nfact[name] = nfact
        except Exception:
            d_nfact[name] = None

    return d_fact, d_nfact