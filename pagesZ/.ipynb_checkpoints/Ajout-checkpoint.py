import datetime
import os
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from Database.insert_logic import insert_client, insert_dossier, insert_mission, create_fact

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

user_id = st.session_state["utilisateur_id"] or "6"

tab1, tab2, tab3 = st.tabs(["🏢 Client", "📂 Dossier", "🛠️ Mission"])

##################################################################################
# AJOUT CLIENT
##################################################################################

with tab1 :
    if "confirm_save" not in st.session_state:
        st.session_state.confirm_save = False

    st.markdown("""
    <div style='text-decoration: underline;
    font-style: normal;
    font-size: 28px;
    font-weight: 300;
    '>Ajouter un nouveau client</div>""",
                unsafe_allow_html=True)
    st.write("""

    """)

    cursor.execute("""
    SELECT nom || ' ' || prenom AS associe, nom_service
    FROM utilisateurs
    WHERE nom_service = 'Expert comptable associé'
    ORDER BY nom
    """)

    client_query = [row[0] for row in cursor.fetchall()]

    with st.form("Ajouter un client", clear_on_submit=True):
        nom_client = st.text_input("Nom du client", placeholder="Entrez le nom du client ici")
        code_client = st.text_input("Code du client", placeholder="Entrez le code du client ici")
        associe = st.selectbox("Nom de l'associé rattaché",
                               client_query,
                               placeholder="Entrez le nom d'associé ici")
        distance_km = st.number_input("Distance SECNO - client", placeholder="Distance en kilomètre aller-retour", step=1)

        submitted = st.form_submit_button("💾 Enregistrer")

        if submitted:
            if nom_client=="":
                st.warning("Veuillez renseigner un nom pour le client")
            elif code_client=="":
                st.warning("Veuillez renseigner un code pour le client")
            elif distance_km=="" or distance_km==0:
                st.warning("Veuillez renseigner une distance")
            else:
                cursor.execute(
                """
                INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                VALUES (NOW(), %s, 'Ajout', 'Ajout_nouveau_client', %s)
                """,
                (user_id, f"Ajout du client {nom_client} (rattaché à {associe})"))

                insert_client(
                    conn=conn,
                    nom_client=nom_client,
                    code_client=code_client,
                    associe=associe,
                    distance_km=distance_km
                )

                st.success("✅ Données enregistrées !")
                st.rerun()

##################################################################################
# AJOUT DOSSIER
##################################################################################

with tab2 :
    st.markdown("""
    <div style='text-decoration: underline;
    font-style: normal;
    font-size: 28px;
    font-weight: 300;
    '>Ajouter un nouveau dossier</div>""",
                unsafe_allow_html=True)

    st.write("""

    """)

    cursor.execute("""
    SELECT nom || ' ' || prenom AS associe, nom_service
    FROM utilisateurs
    WHERE nom_service = 'Expert comptable associé'
    ORDER BY nom
    """)

    folder_query = [row[0] for row in cursor.fetchall()]

    clients_df = pd.read_sql("SELECT DISTINCT nom_client FROM clients", conn)

    with st.form("Ajouter un dossier", clear_on_submit=True):
        nom_client = st.selectbox("Nom du client", clients_df)
        mat_dossier = st.text_input("Matricule de dossier", max_chars=8, placeholder="Entrez le matricule du dossier ici")
        nom_dossier = st.text_input("Nom du dossier", placeholder="Entrez le nom du dossier ici")
        associe = st.selectbox("Nom de l'associé rattaché",
                               client_query,
                               placeholder="Entrez le nom de l'associé rattaché ici")

        submitted = st.form_submit_button("💾 Enregistrer")

        if submitted:
            if nom_client=="":
                st.warning("⚠️ Veuillez renseigner un nom pour le client")
            elif mat_dossier=="":
                st.warning("⚠️ Veuillez renseigner un matricule pour le dossier")
            elif nom_dossier=="":
                st.warning("⚠️ Veuillez renseigner un nom pour le dossier")
            else:
                cursor.execute(
                """
                INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                VALUES (NOW(), %s, 'Ajout', 'Ajout_nouvelle_dossier', %s)
                """,
                (user_id, f"Ajout du dossier {mat_dossier} pour le client {nom_client}"))

                insert_dossier(
                    conn=conn,
                    nom_client=nom_client,
                    code_dossier=mat_dossier,
                    nom_dossier=nom_dossier,
                    associe=associe
                )

                st.success("✅ Données enregistrées !")
                st.rerun()

##################################################################################
# AJOUT MISSION
##################################################################################

with tab3 :
    with st.expander("Ajouter une nouvelle mission"):
    
        if "saisie" not in st.session_state:
            st.session_state.saisie = []

        clients_df = pd.read_sql("SELECT DISTINCT nom_client FROM clients", conn)

        with st.form("form_saisie", clear_on_submit=True):

            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()

            col1, col3, col2 = st.columns([6,1,6])

            today = datetime.date.today()
            first_day = (today.replace(day=1) - relativedelta(months=1))
            last_day = today.replace(day=31) if today.month == 12 else (
                today.replace(day=1, month=today.month + 1) - datetime.timedelta(days=1)
            )

            with col1:
                st.markdown("""
                <div style='text-decoration: underline;
                font-style: normal;
                font-size: 18px;
                font-weight: 300;
                '>Renseignez les informations ci-dessous :</div>""",
                            unsafe_allow_html=True)

                colm, coln = st.columns([27,16])

                with colm:
                    st.write(" ")
                    nom_clt = st.selectbox("Nom du client", clients_df)

            with col3:
                st.write(" ")

            with col2:
                st.write(" ")
                st.write(" ")
                st.write(" ")              
                cola, colb, colc, cold, cole, colf = st.columns([8,1,8,1,8,16])

                with cola:
                    type_f = st.selectbox("Type de mission", ["C", "A", "J", "P", "L"],
                                         placeholder="C pour Comptabilité, ...")
                with colb:
                    st.write(" ")
  
                with colc:
                    annee_f = st.selectbox("Année", ["2020", "2021", "2022", "2023", "2024", "2025"])

                with cold:
                    st.markdown("""
                    <div style='
                    height: 135px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-size: 5px;
                    '>
                    <h2 style='color: #909090;'>-</h2>
                    """, unsafe_allow_html=True)

                with cole:
                    mois_f = st.selectbox("Mois",
                                          ["01", "02", "03", "04", "05", "06",
                                          "07", "08", "09", "10", "11", "12"])
            mat_m = type_f+annee_f+"-"+mois_f

            submitted = st.form_submit_button("💾 Enregistrer")

            if submitted:
                if type_f=="C":
                    nom_m = 'Comptabilité'
                elif type_f=="A":
                    nom_m = 'Audit'
                elif type_f=="J":
                    nom_m = 'Juridique'
                elif type_f=="P":
                    nom_m = 'Paie'
                else:
                    nom_m = 'Conseil'

                insert_mission(
                    conn=conn,
                    matricule_mission=mat_m,
                    nom_mission=nom_m,
                    nom_client=nom_clt
                )

                cursor.execute(
                """
                INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                VALUES (NOW(), %s, 'Ajout', 'Ajout_nouvelle_mission', %s)
                """,
                (user_id, f"Ajout de la mission {mat_m} pour le client {nom_clt}"))
                conn.commit()

                st.success("✅ Données enregistrées !")
                st.rerun()

###############################################################################################################
# MODIFICATION DE MISSION
###############################################################################################################

    st.markdown("""
    <div style='text-decoration: underline;
    font-style: normal;
    font-size: 26px;
    font-weight: 300;
    '>Filtres :</div>""",
                unsafe_allow_html=True)

    if "saisie" not in st.session_state:
        st.session_state.saisie = []

    clients_df = pd.read_sql("SELECT DISTINCT nom_client FROM clients", conn)

    col1, col3, col2 = st.columns([6,1,6])

    today = datetime.date.today()
    first_day = (today.replace(day=1) - relativedelta(months=1))
    last_day = today.replace(day=31) if today.month == 12 else (
        today.replace(day=1, month=today.month + 1) - datetime.timedelta(days=1)
    )

    with col1:

        clients_df = clients_df['nom_client'].tolist()
        nom_client = st.multiselect("Nom du client", clients_df,
                                    placeholder="Client...")

        filtre_etat = st.multiselect("Statut de la mission",
                                     ["En cours", "Clôturé", "En cours de clôture"],
                                     default=[],
                                     placeholder="En cours, Clôturée, etc...", key="Filtre_etat")

        cola, colb, colc, cold, cole, colf = st.columns([8,1,8,1,8,16])

        with cola:
            filtre_type_f = st.multiselect("Type de mission", ["C", "A", "J", "P", "L"],
                                           default=[],
                                           placeholder="C, A, J, ...", key="Filtre_type")
        with colb:
            st.write(" ")

        with colc:
            filtre_annee_f = st.multiselect("Année", ["2020", "2021", "2022", "2023", "2024", "2025"],
                                            default=[],
                                            placeholder="Année...",
                                            key="Filtre_annee")

        with cold:
            st.markdown("""
            <div style='
            height: 135px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 5px;
            '>
            <h2 style='color: #909090;'>-</h2>
            """, unsafe_allow_html=True)

        with cole:
            filtre_mois_f = st.multiselect("Mois",
                                           ["01", "02", "03", "04", "05", "06",
                                            "07", "08", "09", "10", "11", "12"],
                                           default=[],
                                           placeholder="Mois...",
                                           key="Filtre_mois")

    with col3:
        st.write(" ")

    with col2:
        with st.expander("Modifier les missions"):
            etat = st.selectbox("Statut de la mission",
                               ["--", "En cours", "Clôturé", "En cours de clôture"]
                               )

            cola, colb, colc, cold, cole, colf = st.columns([8,1,8,1,8,16])

            with cola:
                type_f = st.selectbox("Type de mission", ["--","C", "A", "J", "P", "L"])
            with colb:
                st.write(" ")

            with colc:
                annee_f = st.selectbox("Année", ["--", "2020", "2021", "2022", "2023", "2024", "2025"])

            with cold:
                st.markdown("""
                <div style='
                height: 135px;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 5px;
                '>
                <h2 style='color: #909090;'>-</h2>
                """, unsafe_allow_html=True)

            with cole:
                mois_f = st.selectbox("Mois",
                                      ["--", "01", "02", "03", "04", "05", "06",
                                      "07", "08", "09", "10", "11", "12"])

    dup, cld, sup, _= st.columns([3,4,3,13], gap="small")

    with dup:
        duplicate_button = st.button("Dupliquer la sélection")

    with cld:
        cloture_button = st.button("Clôturer / Ouvrir la sélection")

    with sup:
        delete_button = st.button("Supprimer la sélection")

    get_missions="""
    SELECT m.id, c.nom_client, m.matricule_mission, m.nom_mission, m.statut
    FROM missions m
    LEFT JOIN clients c ON m.id_client = c.id
    ORDER BY m.matricule_mission
    """
    dmis = pd.read_sql(get_missions, conn)

    if nom_client:
        filtered_df = dmis[
            dmis["nom_client"].isin(nom_client)
        ]

    else:
        filtered_df = dmis.copy()

    if filtre_etat:
        filtered_df = filtered_df[filtered_df["statut"].isin(filtre_etat)]

    if filtre_type_f:
        filtered_df = filtered_df[filtered_df["nom_mission"].str[0].isin(filtre_type_f)]

    if filtre_annee_f:
        filtered_df = filtered_df[filtered_df["matricule_mission"].str[1:5].isin(filtre_annee_f)]

    if filtre_mois_f:
        filtered_df = filtered_df[filtered_df["matricule_mission"].str[-2:].isin(filtre_mois_f)]

    column_configuration={
            "id": st.column_config.Column(
                "Id mission",
                width="small"
            ),
            "nom_client": st.column_config.TextColumn(
                "Client",
                help="Nom du client"
            ),
            "matricule_mission": st.column_config.TextColumn(
                "Mission",
                help="Matricule unique de la mission"
            ),
            "nom_mission": st.column_config.TextColumn(
                "Type de mission",
                help="Comptabilité, Audit, etc."
            ),
            "etat": st.column_config.TextColumn(
                "Statut",
            ),
        }

    st.write("""

    """)

    df_modif = st.dataframe(
        filtered_df,
        column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row"
    )

    rows_s = df_modif.selection.rows
    selected_rows = filtered_df.iloc[rows_s]

    if duplicate_button:
        if selected_rows.empty:
            st.warning("⚠️ Aucune mission sélectionnée.")
        else:
            for _, row in selected_rows.iterrows():
                ancien_mat = row["matricule_mission"]
                lettre_orig, reste = ancien_mat[0], ancien_mat[1:]
                annee_orig, mois_orig = reste.split("-")

                lettre = type_f if "--" not in type_f else lettre_orig
                annee = annee_f if "--" not in annee_f else annee_orig
                mois = mois_f if "--" not in mois_f else mois_orig

                nouveau_mat = f"{lettre}{annee}-{mois}"

                cursor.execute("""
                    INSERT INTO missions (matricule_mission, nom_mission, statut, id_dossier, id_client)
                    SELECT %s, nom_mission, statut, id_dossier, id_client
                    FROM missions
                    WHERE matricule_mission = %s
                """, (f"{nouveau_mat}", row["matricule_mission"]))

                cursor.execute("""
                    INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                    VALUES (NOW(), %s, 'Ajout', 'Duplication_mission', %s)
                """,
                (user_id, f"Mission {row["matricule_mission"]} dupliquée"))

            conn.commit()
            st.rerun()

    if cloture_button:
        if selected_rows.empty:
            st.warning("⚠️ Aucune mission sélectionnée.")
        else:
            for _, row in selected_rows.iterrows():

                etat_orig = row["statut"]
                mission_mat = row["matricule_mission"]
                client = row["nom_client"]
                nouveau_statut = etat if "--" not in etat else etat_orig

                cursor.execute("""
                    UPDATE missions
                    SET statut = %s
                    WHERE statut = %s AND id = %s
                """, (f"{nouveau_statut}", etat_orig, row["id"]))

                cursor.execute("""
                    INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                    VALUES (NOW(), %s, 'Ajout', 'Modification_cloture_mission', %s)
                """,
                (user_id, f"Changement de statut de {row["statut"]} à {filtre_etat} pour la mission {row["matricule_mission"]}"))

                if etat=="Clôturé":
                    create_fact(
                        conn=conn,
                        client=client,
                        mission_mat=mission_mat
                    )

            conn.commit()
            st.rerun()

    if delete_button:
        if selected_rows.empty:
            st.warning("⚠️ Aucune mission sélectionnée.")

        else:
            for _, row in selected_rows.iterrows():
                cursor.execute("DELETE FROM missions WHERE id = %s", (row["id"],))

                cursor.execute("""
                    INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                    VALUES (NOW(), %s, 'Ajout', 'Suppression_mission', %s)
                """,
                (user_id, f"Mission {row["matricule_mission"]} du client {row["nom_client"]} supprimée"))

        conn.commit()
        st.success("✅ Missions supprimées avec succès !")
        st.rerun()