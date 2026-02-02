import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

user_id = st.session_state.get("utilisateur_id")

st.markdown("""
    <div style='text-decoration: underline;
    font-size: 28px;
    font-weight: 300;
    '>Table des taux de facturation des collaborateurs</div>""",
            unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cursor = conn.cursor()

user_query = """
SELECT u.matricule, u.nom, u.prenom, u.nom_service, tf.taux, tf.date
FROM utilisateurs u
INNER JOIN taux_facturation tf ON tf.utilisateur_id = u.id
ORDER BY nom
"""
df = pd.read_sql(user_query, conn)

df_pivot = df.pivot_table(
    index=["matricule", "nom", "prenom", "nom_service"],
    columns="date",
    values="taux",
    aggfunc="last"
).reset_index()

df_pivot = df_pivot.sort_values("nom")

if "show_new_taux" not in st.session_state:
    st.session_state["show_new_taux"] = False

with col1:
    if st.button("Ajouter un nouveau taux"):
        st.session_state["show_new_taux"] = True

    if st.session_state["show_new_taux"]:
        if "Nouveau taux" not in df.columns:
            df_pivot["Nouveau taux"] = None
    
    edit_df = st.data_editor(df_pivot,
                             num_rows="dynamic",
                             hide_index=True
                            )

    if st.button("💾 Enregistrer"):
        date_taux = pd.Timestamp.today().strftime('%Y-%m-%d')
        taux_saisis = edit_df[edit_df["Nouveau taux"].notnull()] if "Nouveau taux" in edit_df.columns else pd.DataFrame()

        if not taux_saisis.empty:
            for _, row in taux_saisis.iterrows():
                matricule = row["matricule"]
                taux = row["Nouveau taux"]
                nom = row["nom"]
                prenom = row['prenom']

                cursor.execute("SELECT id FROM utilisateurs WHERE matricule = %s", (matricule,))
                result = cursor.fetchone()

                if result:
                    utilisateur_id = result[0]
                    cursor.execute("""
                        INSERT INTO taux_facturation (utilisateur_id, taux, date, nom, prenom)
                        VALUES (%s, %s, NOW(), %s, %s)
                        ON CONFLICT (utilisateur_id, date) DO UPDATE
                        SET taux = EXCLUDED.taux
                    """, (utilisateur_id, taux, nom, prenom))

            conn.commit()
            st.success("✅ Les taux ont été enregistrés avec succès.")

            cursor.execute(
            """
            INSERT INTO logs (date_saisie, utilisateur_id, page, action, details)
            VALUES (NOW(), %s, 'Taux facturation', 'Ajout_taux_de_facturation', %s)
            """,
            (user_id, f"Ajout d'un nouveau taux de facturation"))
            conn.commit()
            st.rerun()

        else:
            st.warning("⚠️ Aucun taux à enregistrer.")
