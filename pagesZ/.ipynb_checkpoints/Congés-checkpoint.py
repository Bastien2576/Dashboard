import os
import streamlit as st
from streamlit_calendar import calendar
from dotenv import load_dotenv
import datetime
import psycopg2
import pandas as pd

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

today = datetime.date.today()

user_id = st.session_state.get("utilisateur_id")
if user_id is None:
    st.error("⚠️ Aucun utilisateur identifié. Veuillez vous connecter.")
    st.stop()

st.subheader("Ajouter un évènement au calendrier")

with st.container(border=False):
    display = st.selectbox(
        " ",
        (
            "Standard",
            "Planning Hebdomadaire",
            "Planning Annuel",
        ),
    )

def get_conges(utilisateur_id: int, mode: str):
    query = """
        SELECT id, titre AS title, date_depart AS start, date_retour AS end,
        'rgba(61,157,243,0.8)'::TEXT AS color, resource_id
        FROM conges
    """
    if utilisateur_id:
        query += " WHERE utilisateur_id = %s"
        cursor.execute(query, (utilisateur_id,))
    else:
        cursor.execute(query)
    return cursor.fetchall()

calendar_resources = [
    {"id": "a", "title": "Salle Bleu"},
    {"id": "b", "title": "Salle Vert"},
    {"id": "c", "title": "Salle Coursive"},
    {"id": "d", "title": "Salle de Conférence"},
    {"id": "e", "title": "Salle CODIR"}
]

calendar_options = {
    "editable": "true",
    "navLinks": "true",
    "resources": calendar_resources,
    "selectable": "true",
}

if "Salle" in display:
    calendar_options = {
        **calendar_options,
        "initialDate": f"{today}",
        "initialView": "resourceTimeGridDay"
    }

else:
    if display == "Standard":
        calendar_options = {
            **calendar_options,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridDay,dayGridWeek,dayGridMonth",
            },
            "initialDate": f"{today}",
            "initialView": "dayGridMonth",
        }
    elif display == "Planning Hebdomadaire":
        calendar_options = {
            **calendar_options,
            "initialView": "timeGridWeek",
        }
    elif display == "Planning Annuel":
        calendar_options = {
            **calendar_options,
            "initialView": "multiMonthYear",
        }

events = [
    {
        "id":row[0],
        "title": row[1],
        "start": row[2].isoformat(),
        "end": row[3].isoformat(),
        "color": row[4],
        "resourceId": row[5],
    }
    for row in get_conges(user_id, mode=display)
]

with st.expander("Ajouter un évènement :"):
    with st.form("form_ajout_conge"):
        titre = st.text_input("Titre")
        type_conge = st.selectbox("Type d'évènement", ['Normal', 'Exceptionnel', "Récupération d'heures",
                                                       'Maladie', 'Télétravail'])

        col1, _, col2 = st.columns([3,4,2])

        with col1:
            date_debut = st.date_input("Date de début")

        with col2:
            date_fin = st.date_input("Date de fin (dernier jour inclus)")

        commentaire = st.text_area("Commentaire (optionnel)")

        submit = st.form_submit_button("Ajouter")

        if submit:
            cursor.execute(
                """
                INSERT INTO conges (utilisateur_id, titre, date_depart, date_retour, type, resource_id, commentaire)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    titre,
                    date_debut,
                    date_fin,
                    type_conge,
                    None,
                    commentaire,
                )
            )

            cursor.execute(
                """
                INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
                VALUES (NOW(), %s, 'calendrier', 'ajout_conge', %s)
                """,
                (user_id, f"{titre} du {date_debut} au {date_fin}")
            )

            conn.commit()
            st.success("Congé enregistré !")
            st.rerun()

state = calendar(
        events=st.session_state.get("events", events),
        options=calendar_options,
        custom_css="""
        .fc-event-past {
            opacity: 0.8;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc-event-title {
            font-weight: 700;
        }
        .fc-toolbar-title {
            font-size: 2rem;
        }
        """,
        key=display,
    )

if state and state.get("eventChange"):
    event = state["eventChange"]["event"]
    event_id = event.get("id")
    new_start = event.get("start")
    new_end = event.get("end")

    if event_id and new_start and new_end:
        cursor.execute(
            """
            UPDATE conges
            SET date_depart = %s, date_retour = %s
            WHERE id = %s AND utilisateur_id = %s
            """,
            (new_start, new_end, event_id, user_id)
        )
        cursor.execute(
            """
            INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
            VALUES (NOW(), %s, 'calendrier', 'modification_event', %s)
            """,
            (user_id, f"Événement {event_id} déplacé au {new_start} → {new_end}")
        )
        conn.commit()
        st.success("📝 Événement mis à jour")