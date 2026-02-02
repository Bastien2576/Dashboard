import os
import json
import datetime
import uuid
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
from dateutil.relativedelta import relativedelta
from Database.insert_logic import insert_non_fact, insert_fact, update_non_fact, update_fact, insert_af

# Chargement des variables d'environnement
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

# Dates limites
today = datetime.date.today()
first_day = (today.replace(day=1) - relativedelta(months=1))
last_day = today.replace(day=31) if today.month == 12 else (
    today.replace(day=1, month=today.month + 1) - datetime.timedelta(days=1)
)

tab1, tab2, tab3, tab4 = st.tabs(["Saisie des heures", "Modification des saisies", "Déplacement", "Autres frais"])

# 🧠 Identifiant utilisateur (présumé déjà stocké dans session_state)
user_id = st.session_state.get("utilisateur_id")
if user_id is None:
    st.error("⚠️ Aucun utilisateur identifié. Veuillez vous connecter.")
    st.stop()

# 📁 Chemin du fichier spécifique à l'utilisateur
USER_DATA_FILE = os.path.join(BASE_DIR, f"data_user_{user_id}.json")

# 🔁 Chargement automatique à l'ouverture
if "saisie_editor" not in st.session_state:
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            st.session_state["saisie_editor"] = json.load(f)
    else:
        st.session_state["saisie_editor"] = []

# Chargement de données depuis la DB pour les SelectboxColumns
na = ['N/A']

conn = get_connection()
clients_df = pd.read_sql("SELECT DISTINCT nom_client FROM clients ORDER BY nom_client", conn)
mission_df = pd.read_sql("SELECT DISTINCT matricule_mission FROM missions ORDER BY matricule_mission", conn)
code_df = pd.read_sql("SELECT code FROM activites ORDER BY code", conn)
conn.close()
cli = clients_df["nom_client"].to_list()
mission_list = mission_df["matricule_mission"].to_list()
code_list = code_df["code"].to_list()
na.extend(cli)

#####################################################################################################
# ONGLET 1 : Tableau principal
#####################################################################################################

with tab1:
    st.subheader("Renseignez vos heures dans le tableau ci-dessous :", anchor=False)

    col1, col2, col3, col4 = st.columns([8, 8, 30, 8], vertical_alignment="bottom")

    with col4:
        date = st.date_input("🗓️ Date", value=today, min_value=first_day, max_value=last_day, key="date_picker")

    with col1:
        if st.button("**+** Ajout Facturable", key="fact2"):
            st.session_state["saisie_editor"].append({
                "Date": str(date),
                "Type": "Facturables",
                "Durée (h)": 0.0,
                "Mission": "",
                "Client": "",
                "Code": "",
                "Commentaire": ""
            })

    with col2:
        if st.button("**+** Ajout Non facturable", key="nf2"):
            st.session_state["saisie_editor"].append({
                "Date": str(date),
                "Type": "Non facturables",
                "Durée (h)": 0.0,
                "Mission": "",
                "Client": na[0],
                "Code": "",
                "Commentaire": ""
            })

    # 🖋️ Edition dans DataFrame interactif
    df_saisie = pd.DataFrame(st.session_state["saisie_editor"])

    # 🔁 Conversion de la colonne Date en datetime.date si nécessaire
    if not df_saisie.empty and df_saisie["Date"].dtype == object:
        try:
            df_saisie["Date"] = pd.to_datetime(df_saisie["Date"]).dt.date
        except Exception as e:
            st.warning(f"⚠️ Erreur de conversion des dates : {e}")

    df_edited = st.data_editor(
        df_saisie,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Type": st.column_config.SelectboxColumn("Type", options=["Facturables", "Non facturables"]),
            "Mission": st.column_config.SelectboxColumn("Mission", options=mission_list),
            "Client": st.column_config.SelectboxColumn("Client", options=na),
            "Code": st.column_config.SelectboxColumn("Code d'Activité", options=code_list),
            "Durée (h)": st.column_config.NumberColumn("Durée (h)", step=0.25, format="%.2f"),
            "Date": st.column_config.DateColumn("Date", format="DD-MM-YYYY"),
        },
        hide_index=True
    )

    col_val, col_rei, _, col_enr = st.columns([8, 10, 70, 8])

    ##########################################
    # ✅ BOUTON : VALIDER => Sauvegarde JSON
    ##########################################
    with col_val:
        if st.button("✅ Valider", key="valider"):
            try:
                with open(USER_DATA_FILE, "w") as f:
                    json.dump(df_edited.to_dict(orient="records"), f, indent=4, default=str)
                st.session_state["saisie_editor"] = df_edited.to_dict(orient="records")
                st.success("✅ Données sauvegardées pour la session suivante.")
            except Exception as e:
                st.error(f"❌ Erreur de sauvegarde : {e}")
            st.rerun()

    ##########################################
    # 🔄 BOUTON :REINITIALISER => Clear JSON
    ##########################################
    with col_rei:
        if st.button("🔄 Réinitialiser"):
            st.session_state["saisie_editor"].clear()
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)

            st.rerun()

    ##########################################
    # 💾 BOUTON : ENREGISTRER => DB + Clear
    ##########################################
    with col_enr:
        enregistrer = st.button("💾 Enregistrer", key="reg2")

    if enregistrer:
        conn = get_connection()
        try:
            for ligne in df_edited.to_dict("records"):
                if ligne["Type"] == "Facturables":
                    insert_fact(
                        conn=conn,
                        utilisateur_id=user_id,
                        date=ligne["Date"],
                        duree_heures=ligne["Durée (h)"],
                        type_heure=ligne["Type"],
                        nom_du_client=ligne["Client"],
                        matricule_mission=ligne["Mission"],
                        code=ligne["Code"],
                        commentaire=ligne["Commentaire"]
                    )
                elif ligne["Type"] == "Non facturables":
                    insert_non_fact(
                        conn=conn,
                        utilisateur_id=user_id,
                        type_heure=ligne["Type"],
                        date=ligne["Date"],
                        duree_heures=ligne["Durée (h)"],
                        code=ligne["Code"],
                        commentaire=ligne["Commentaire"]
                    )

            st.session_state["saisie_editor"].clear()
            if os.path.exists(USER_DATA_FILE):
                os.remove(USER_DATA_FILE)

            st.success("✅ Données enregistrées en base.")
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement : {e}")
        finally:
            conn.close()

    with st.expander("Rappel des codes d'activité"):

        st.markdown("""
            | Code  | Activité |
            |-------|---------------|
            | `100`	| Travaux comptables courants	                     |
            | `102`	| FIDES	                                             |
            | `109`	| Travaux comptables exceptionnels	                 |
            | `200`	| Audit légal	                                     |
            | `201`	| Audit contractuel	                                 |
            | `202`	| Comptes consolidés CAC	                         |
            | `203`	| Audit Déplacement	                                 |
            | `209`	| Transfert GED CEGID -> Revisaudit	                 |
            | `300`	| Mission de conseil social	                         |
            | `309`	| Conseil social exceptionnel	                     |
            | `310`	| Travaux paie exceptionnels	                     |
            | `400`	| Travaux de paie	                                 |
            | `401`	| Travaux de maladie	                             |
            | `402`	| Travaux comptable	                                 |
            | `403`	| Mise en place dossier                              |
            | `404`	| Travaux dossiers ROBOT	                         |
            | `405`	| Gestion organisme	                                 |
            | `409`	| Travaux paie exceptionnels	                     |
            | `501`	| Travaux juridiques	                             |
            | `502`	| Travaux secrétariat	                             |
            | `503`	| Travaux expertises judiciaires	                 |
            | `600`	| Fiscalité personnelle (IR + ISF)	                 |
            | `601`	| Etude fiscale particulière	                     |
            | `602`	| Formation clients	                                 |
            | `700`	| Conseil juridique	                                 |
            | `800`	| Expertise judiciaire	                             |
            | `901`	| Journée de Formation (intra ou Extra)	             |
            | `902`	| Formation interne reçue / donnée	                 |
            | `904`	| Documentation	                                     |
            | `910`	| Planning Gestion des Temps	                     |
            | `911`	| Administration	                                 |
            | `913`	| Comité Technique préparation	                     |
            | `914`	| Réunion Interne	                                 |
            | `971`	| Instances Professionnelles NF (Assoc)	             |
            | `972`	| Clubs & Projets structurants	                     |
            | `973`	| Relations Publiques	                             |
            | `974`	| Recrutement - Entretien des Collaborateurs (Assoc) |
            | `978`	| Appel d'offre / Prospect	                         |
            | `980`	| Informatique interne (DV)	                         |
            """)

    st.info("Attention : Le bouton ✅ Valider ne permet pas d'enregistrer vos heures, mais seulement de les garder en mémoire")
    st.info("Pensez à appuyer sur le bouton 💾 Enregistrer lorsque vous avez terminé votre saisie")
##########################################################################################################################
# Deuxième onglet
##########################################################################################################################
with tab2:

    def lire_saisies_mois(utilisateur_id):
        today = date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=31) if today.month == 12 else \
                   today.replace(day=1, month=today.month + 1) - pd.Timedelta(days=1)

        with get_connection() as conn:
            query = """
            SELECT hs.id, hs.date, hs.type, hs.duree_heures, m.matricule_mission, c.nom_client, hs.code, hs.commentaire
            FROM heures_saisies AS hs
            LEFT JOIN missions m ON hs.mission_id = m.id
            LEFT JOIN clients c ON hs.client_id = c.id
            WHERE hs.utilisateur_id = %s AND hs.date BETWEEN %s AND %s
            ORDER BY hs.date
            """
            df = pd.read_sql(query, conn, params=(utilisateur_id, first_day, last_day))
        return df

    df = lire_saisies_mois(user_id)

    df_modif = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "type": st.column_config.SelectboxColumn("Type", options=["Facturables", "Non facturables"]),
            "matricule_mission": st.column_config.SelectboxColumn("Mission", options=mission_list),
            "nom_client": st.column_config.SelectboxColumn("Client", options=na),
            "code": st.column_config.SelectboxColumn("Code d'Activité", options=code_list),
            "duree_heures": st.column_config.NumberColumn("Durée (h)", step=0.25, format="%.2f"),
            "date": st.column_config.DateColumn("Date", format="DD-MM-YYYY"),
        },
        column_order=("date", "type", "duree_heures", "matricule_mission", "nom_client", "code", "commentaire"),
        key="modif_editor",
        hide_index=True
    )

    if st.button("💾 Enregistrer les modifications"):
        conn = get_connection()
        cur = conn.cursor()

        try:
            for ligne in df_modif.to_dict("records"):
                if ligne["duree_heures"] in [None, "", "NaN", 0]:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM heures_saisies WHERE id = %s AND utilisateur_id = %s", (ligne["id"], user_id))

                else:
                    if ligne["type"] == "Facturables":
                        update_fact(
                            conn=conn,
                            saisie_id=ligne["id"],
                            utilisateur_id=user_id,
                            type_heure=ligne["type"],
                            date=ligne["date"],
                            duree_heures=ligne["duree_heures"],
                            nom_du_client=ligne["nom_client"],
                            matricule_mission=ligne["matricule_mission"],
                            code=ligne["code"],
                            commentaire=ligne["commentaire"]
                        )
                    else:
                        update_non_fact(
                            conn=conn,
                            saisie_id=ligne["id"],
                            utilisateur_id=user_id,
                            type_heure=ligne["type"],
                            date=ligne["date"],
                            duree_heures=ligne["duree_heures"],
                            code=ligne["code"],
                            commentaire=ligne["commentaire"]
                        )
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
        finally:
            conn.close()
            st.success("✅ Modifications enregistrées.")

    col, col2 = st.columns([6,4])

    with col2:
        with st.container():
            st.info("Afin de supprimer une ligne du tableau ci-dessus, il faut se placer dans la colonne **Durée (h)** de la ligne en question, y saisir **0** \
            puis enregistrer les modifications. \
            \
            Supprimer une ligne en la cochant ne supprimera pas de la base de données une saisie déjà effectuée !")

##########################################################################################################################
# Troisième onglet
##########################################################################################################################
with tab3:

    conn = get_connection()

    query_c="""
    SELECT DISTINCT nom_client FROM clients
    ORDER BY nom_client
    """

    df_c = pd.read_sql(query_c, conn)

    query_m ="""
    SELECT DISTINCT matricule_mission FROM missions
    ORDER BY matricule_mission
    """

    df_m = pd.read_sql(query_m, conn)

    if "formulaires" not in st.session_state:
        st.session_state.formulaires = [{"date" : "", "nom": "", "mission": ""}]

    if st.button("Ajouter une saisie"):
        st.session_state.formulaires.append({"date": "", "nom": "", "mission": "", "immatriculation": "", "valorisé": ""})
        st.rerun()

    with st.container(border=True):
        for i, ligne in enumerate(st.session_state.formulaires):
            col1, col2, col3, _, col6 = st.columns([2,3,3,9,1], vertical_alignment="bottom")

            show_label = i == 0

            with col1:
                ligne["date"] = st.date_input("Date du déplacement", value=today, max_value=last_day, key=f"dplcmt_key_{i}")
            with col2:
                ligne["client"] = st.selectbox("Nom du client", df_c, key=f"client_key_{i}")
            with col3:
                ligne["mission"] = st.selectbox("Nom de la mission", df_m, key=f"mission_key_{i}")

            with col6:
                if st.button("❌", key=f"delete_{i}"):
                    st.session_state.formulaires.pop(i)
                    st.rerun()

    if st.button ("💾 Enregistrer"):
        for ligne in st.session_state.formulaires:
            cursor = conn.cursor()
            date_depl = ligne["date"]
            client_nom = ligne["client"]
            mission = ligne["mission"]

            user_id = st.session_state["utilisateur_id"]

            query_vehicule = f"""
            SELECT *
            FROM vehicule
            WHERE id_utilisateur = {user_id}
            ORDER BY date DESC
            LIMIT 1
            """
            vehicule = pd.read_sql(query_vehicule, conn).iloc[0]
            cv = vehicule["cv"]
            v_type = vehicule["type_vehicule"]

            query_distance = f"""
            SELECT distance_km
            FROM clients
            WHERE nom_client = '{client_nom}'
            """
            distance_km = pd.read_sql(query_distance, conn).iloc[0]["distance_km"]

            cursor.execute(f"""
            SELECT id FROM missions
            WHERE matricule_mission = %s
            """, (mission,))

            mission_id = cursor.fetchone()[0]

            query_bareme = f"""
            SELECT montant_par_km
            FROM baremes_km
            WHERE type_vehicule = '{v_type}'
              AND cv = {cv}

              AND {distance_km} BETWEEN borne_inf AND borne_sup
            LIMIT 1
            """
            tarif = pd.read_sql(query_bareme, conn).iloc[0]["montant_par_km"]

            indemnites = distance_km * tarif

            user_id = int(user_id)
            mission_id = int(mission_id)
            distance_km = float(distance_km)
            indemnites = float(indemnites)

            insert_query = """
            INSERT INTO frais_km (utilisateur_id, date, distance_km, mission_id, indemnite)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_id, date_depl, distance_km, mission_id, indemnites))
            conn.commit()

            st.success("✅ Données enregistrées")

##########################################################################################################################
# Quatrième onglet
##########################################################################################################################

with tab4:
    conn = get_connection()

    query_c="""
    SELECT DISTINCT nom_client FROM clients
    ORDER BY nom_client
    """

    df_c = pd.read_sql(query_c, conn)

    query_m ="""
    SELECT DISTINCT matricule_mission FROM missions
    ORDER BY matricule_mission
    """

    df_m = pd.read_sql(query_m, conn)

    if "formulaires" not in st.session_state:
        st.session_state.formulaires = []

    def ajouter_ligne(type_frais):
        st.session_state.formulaires.append({
            "date": today,
            "type": type_frais,
            "client": "",
            "mission": "",
            "montant": "",
            "TVA": 0.0
        })
        st.rerun()

    col1, _, col2 = st.columns([3,2,10])
    with col1:
        with st.container(border=True):
            st.write("Ajouter des frais de :")
            cola, colb = st.columns(2)
            with cola:
                if st.button(" **+** Logement", key="add_logement"): ajouter_ligne("Logement")
                if st.button(" **+** Parking", key="add_parking"): ajouter_ligne("Parking")
                if st.button(" **+** Repas", key="add_repas"): ajouter_ligne("Repas")
            with colb:
                if st.button(" **+** Fourniture", key="add_fourniture"): ajouter_ligne("Fourniture")
                if st.button(" **+** Péage", key="add_peage"): ajouter_ligne("Peage")

    with col2:
        frais_list = ["Logement", "Parking","Repas", "Fourniture","Peage"]

        with st.container(border=True):
            for i, ligne in enumerate(st.session_state.formulaires):
                ligne.setdefault("type", "Logement")
                ligne.setdefault("client", "")
                ligne.setdefault("mission", "")
                ligne.setdefault("montant", 0.0)
                ligne.setdefault("TVA", 0.0)

                col1, col2, col3, col4, col5, col6, _, col7 = st.columns([2,3,3,3,3,3,1,1], vertical_alignment="bottom")

                with col1:
                    ligne["date"] = st.date_input("Date", value=ligne["date"], max_value=last_day, key=f"fr_key_{i}")
                with col2:
                    ligne["client"] = st.selectbox("Client", df_c["nom_client"], key=f"client_af_key_{i}")
                with col3:
                    ligne["mission"] = st.selectbox("Mission", df_m["matricule_mission"], key=f"mission_af_key_{i}")
                with col4:
                    ligne["type"] = st.selectbox("Type de frais", frais_list, index=frais_list.index(ligne["type"]), key=f"type_af_key_{i}")
                with col5:
                    ligne["montant"] = st.number_input("Montant", key=f"mt_af_key_{i}")

                with col6:
                    ligne["TVA"] = st.number_input("TVA", step=0.5, key=f"tva_af_key_{i}")

                with col7:
                     if st.button("❌", key=f"delete_af_{i}"):
                        st.session_state.formulaires.pop(i)
                        st.rerun()

        if st.button ("💾 Enregistrer", key="fr"):
            for ligne in st.session_state.formulaires:
                date_frais = ligne["date"]
                client_nom = ligne["client"]
                mission = ligne["mission"]
                type_fr = ligne["type"]
                mt_fr = ligne["montant"]
                tva = ligne["TVA"]

                insert_af(
                    conn=conn,
                    utilisateur_id=user_id,
                    date=date_frais,
                    nom_mission=mission,
                    type_fr=type_fr,
                    montant=mt_fr,
                    tva=tva,
                    nom_client=client_nom
                )

                st.success("✅ Données enregistrées")
                st.rerun()