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

ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "")

# def login_screen():
#     col1, col2, col3 = st.columns([2, 5, 2])
#     with col2:
#         st.title("Tempno")
#         st.subheader("_Parsing feuilles de temps_", divider="grey")
#         st.info("Connectez-vous avec votre compte Microsoft pour accéder à votre espace personnel")
#         st.button("Se connecter avec Microsoft", on_click=st.login, kwargs={"provider": "microsoft"})

def get_db_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

# is_logged_in = getattr(st.user, "is_logged_in", False)

# if not is_logged_in:
#     login_screen()
#     st.stop()

st.session_state.setdefault("authenticated", True)
st.session_state.setdefault("role", "user")
st.session_state.setdefault("utilisateur_id", None)

email = "bastien.amiot@secno.fr"
st.session_state["role"] = "admin" if email in ADMIN_EMAILS else "user"
role = st.session_state["role"]

conn = get_db_conn()
# try:
#     full_name = (st.user.name or "").strip()
#     if " " in full_name:
#         prenom, nom = full_name.split(" ", 1)
#     else:
#         prenom, nom = full_name, ""

#     with conn.cursor() as cursor:
#         cursor.execute("SELECT id FROM utilisateurs WHERE mail = %s", (email,))
#         result = cursor.fetchone()

#         if not result:
#             st.warning("Profil introuvable. Merci de compléter vos informations pour activer votre compte.")

#             with st.form("creation_profil"):
#                 matricule = st.text_input("Code collaborateur", max_chars=3)
#                 heures_hebdo = st.selectbox("Heures contractuelles hebdomadaires", ["35", "39", "42.25"])
#                 nom_service = st.selectbox(
#                     "Nom de service",
#                     [
#                         "Audit", "Surveillance", "Tenue", "Social / Paie",
#                         "Secrétariat", "Expert comptable associé"
#                     ],
#                 )
#                 submitted = st.form_submit_button("Créer mon profil")

#                 if submitted:
#                     cursor.execute(
#                         """
#                         INSERT INTO utilisateurs (matricule, nom, prenom, nom_service, heures_hebdo, mail)
#                         VALUES (%s, %s, %s, %s, %s, %s)
#                         RETURNING id
#                         """,
#                         (matricule, nom, prenom, nom_service, heures_hebdo, email),
#                     )
#                     utilisateur_id = cursor.fetchone()[0]
#                     conn.commit()

#                     cursor.execute(
#                         """
#                         INSERT INTO taux_facturation (utilisateur_id, taux, date, nom, prenom)
#                         VALUES (%s, 0, NOW(), %s, %s)
#                         """,
#                         (utilisateur_id, nom, prenom),
#                     )
#                     conn.commit()

#                     st.session_state["utilisateur_id"] = utilisateur_id
#                     st.success("Profil créé avec succès !")
#                     st.rerun()

#             st.stop()
#         st.session_state["utilisateur_id"] = result[0]

# finally:
#     conn.close()

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
respond_pages = [respond_1]
admin_pages = [admin_1, admin_2, admin_3, admin_4]

if role in ["user", "admin"]:
    page_dict["Espace Collaborateur"] = respond_pages
if role == "admin":
    page_dict["Espace Administrateur"] = admin_pages

pg = st.navigation(page_dict)
pg.run()

st.sidebar.divider()
# if st.sidebar.button("Se déconnecter", icon=":material/logout:"):
#     st.logout()

# if getattr(st.user, "is_logged_in", False):
#     display_name = getattr(st.user, "name", None) or getattr(st.user, "email", None) or "inconnu"
#     st.sidebar.success(f"Connecté(e) en tant que : {display_name} ({role})")