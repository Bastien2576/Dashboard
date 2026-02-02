import streamlit as st
import sys
import os
import io
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2 import sql
from datetime import date
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
import openpyxl
import locale
import datetime

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

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

st.subheader("Tableau de bord", anchor=False)

tab1, tab2, tab3 = st.tabs(['Statistiques globales', 'Statistiques par collaborateur', 'Liste pour tickets restaurant'])

with tab1:
##################################################################################
# KPIs
##################################################################################

    today = date.today()

    annee = today.year
    mois = today.month
    annee_prec = (today.replace(day=1) - timedelta(days=1)).year
    mois_prec = (today.replace(day=1) - timedelta(days=1)).month

    def heures_service(service=None, conn=None, annee=None, mois=None):
        query = """
            SELECT u.nom_service, SUM(hs.duree_heures) AS total_heures
            FROM heures_saisies hs
            JOIN utilisateurs u ON hs.utilisateur_id = u.id
            WHERE EXTRACT(YEAR FROM hs.date) = %s
            AND EXTRACT(MONTH FROM hs.date) = %s
        """

        params = [annee, mois]

        if service:
            query += " AND u.nom_service = %s"
            params.append(service)

        query += " GROUP BY u.nom_service ORDER BY total_heures DESC"

        df = pd.read_sql(query, conn, params=params)
        return df

    df_mois = heures_service(conn=conn, annee=annee, mois=mois)
    df_prec = heures_service(conn=conn, annee=annee_prec, mois=mois_prec)

    df_kpi = pd.merge(
        df_mois,
        df_prec,
        on="nom_service",
        how="outer",
        suffixes=("_actuel", "_precedent")
    ).fillna(0)

    df_kpi["evol"] = (
        (df_kpi["total_heures_actuel"] - df_kpi["total_heures_precedent"]) *100 / df_kpi["total_heures_precedent"].replace(0, 10000000000000)
    )
    # df_kpi["evol"] = df_kpi["evol"].round(2)

    st.markdown("""
        <div style='text-decoration: underline;
        font-size: 22px;
        font-weight: 200;
        '>Récapitulatif des heures du mois par service</div>""",
                unsafe_allow_html=True)
    st.write("""

    """)

    col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,2])

    with col1:
        if not df_kpi[df_kpi["nom_service"] == "Audit"].empty:
            st.metric(
                "Audit",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Audit", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Audit", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Audit",
                value='0 h',
                delta='0 %',
                border=True
            )

    with col2:
        if not df_kpi[df_kpi["nom_service"] == "Expert comptable associé"].empty:
            st.metric(
                "Expertise Comptable",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Expert comptable associé", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Expert comptable associé", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Expertise Comptable",
                value='0 h',
                delta='0 %',
                border=True
            )                

    with col3:
        if not df_kpi[df_kpi["nom_service"] == "Secrétariat"].empty:
            st.metric(
                "Secrétariat",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Secrétariat", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Secrétariat", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Secrétariat",
                value='0 h',
                delta='0 %',
                border=True
            )

    with col4:
        if not df_kpi[df_kpi["nom_service"] == "Social / Paie"].empty:
            st.metric(
                "Social / Paie",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Social / Paie", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Social / Paie", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Social / Paie",
                value='0 h',
                delta='0 %',
                border=True
            )

    with col5:
        if not df_kpi[df_kpi["nom_service"] == "Surveillance"].empty:
            st.metric(
                "Surveillance",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Surveillance", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Surveillance", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Surveillance",
                value='0 h',
                delta='0 %',
                border=True
            )

    with col6:
        if not df_kpi[df_kpi["nom_service"] == "Tenue"].empty:
            st.metric(
                "Tenue",
                value=f'{df_kpi.loc[df_kpi["nom_service"] == "Tenue", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["nom_service"] == "Tenue", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Tenue",
                value='0 h',
                delta='0 %',
                border=True
            )

    with st.expander("Voir tableau :"):
        st.dataframe(df_kpi)

    st.divider()

##################################################################################
# HEURES FACTURABLES MENSUELLES PAR ASSOCIÉ
##################################################################################

    def heure_fact_associe(annee, mois, conn):
        query = """
        SELECT u.nom || ' ' || u.prenom AS associe,
               SUM(hs.duree_heures) AS total_heures
        FROM heures_saisies hs
        JOIN missions m ON hs.mission_id = m.id
        JOIN dossiers d ON m.id_dossier = d.id
        JOIN utilisateurs u ON d.id_associe = u.id
        WHERE hs.type = 'Facturables'
          AND TO_CHAR(hs.date, 'YYYY') = %s
          AND TO_CHAR(hs.date, 'MM') = %s
        GROUP BY u.id
        ORDER BY total_heures DESC
        """

        df = pd.read_sql(query, conn, params=(annee, f"{int(mois):02d}"))
        return df

    query = """
    SELECT DISTINCT TO_CHAR(date, 'YYYY') AS annee,
                    TO_CHAR(date, 'MM') AS mois
    FROM heures_saisies
    ORDER BY annee DESC, mois DESC
    """
    df_dates = pd.read_sql_query(query, conn)

    mois_disponibles = sorted(df_dates["mois"].unique(), key=int)
    annees_disponibles = sorted(df_dates["annee"].unique(), reverse=True)

    mois_fr = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ]

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(f"""
            <div style='
                padding: 10px 0px;
                border-left: 0px;
                border-radius: 6px;
                margin-top: 18px;
                font-size: 18px;
                font-weight: 500;
            '>
                Rapport des heures facturables mensuelles par associé
            </div>
            """, unsafe_allow_html=True)
    
            colh, colm = st.columns(2)
            with colh:
                Mois = st.selectbox(
                    "Mois",
                    mois_disponibles,
                    format_func=lambda m: mois_fr[int(m) - 1]
                )
            with colm:
                Annee = st.selectbox("Année", annees_disponibles)

            df_heures = heure_fact_associe(Annee, Mois, conn)

            fig = px.pie(df_heures,
                         names="associe",
                         values="total_heures",
                         hole=0.4
                        )

            fig.update_traces(textinfo="percent+label")
            fig.update_layout(showlegend=True,
                              annotations=[dict(text=f"Total : {sum(df_heures['total_heures'])}h",
                                                x=0.5, y=0.5, font_size=18, showarrow=False, xanchor="center")])

            st.plotly_chart(fig)

            with st.expander("Voir le tableau"):
                st.dataframe(df_heures, use_container_width=True)

            output = io.BytesIO()

            df_heures.to_excel(output, index=False, engine='openpyxl')

            output.seek(0)

            st.download_button(
                label="📥 Télécharger en XLS",
                data=output,
                file_name=f"Heures_par_associe_{Mois}_{Annee}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
##################################################################################
# COURBE SUIVI DES HEURES FACTURABLES (PAR MOIS)
##################################################################################
    import locale
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

    def heure_fact(conn):
        query = """
        SELECT date, SUM(hs.duree_heures) AS total_heures
        FROM heures_saisies hs
        WHERE hs.type = 'Facturables'
        GROUP BY hs.date
        ORDER BY total_heures DESC
        """
        df = pd.read_sql(query, conn)
        return df

    with col2:
        with st.container(border=True):
            st.markdown(f"""
                <div style='
                    padding: 10px 0px;
                    border-left: 0px;
                    border-radius: 6px;
                    margin-top: 18px;
                    font-size: 18px;
                    font-weight: 500;
                '>
                    Suivi mensuel des heures facturables
                </div>
                """, unsafe_allow_html=True)

            df_somme = heure_fact(conn)
            df_somme["date"] = pd.to_datetime(df_somme["date"])

            df_somme["annee"] = df_somme["date"].dt.year
            df_somme["mois"] = df_somme["date"].dt.month

            mois_fr = {
                1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
            }

            df_somme["mois_nom"] = df_somme["mois"].map(mois_fr)

            # Regroupement par an + nom du mois
            df_mensuel = df_somme.groupby(["annee", "mois", "mois_nom"], as_index=False)["total_heures"].sum()

            # Ordonner les mois dans le bon ordre (1-12)
            df_mensuel.sort_values(by=["annee", "mois"], inplace=True)

            # Graphique avec noms de mois
            line_chart = px.line(
                df_mensuel,
                x="mois_nom",
                y="total_heures",
                color="annee",
                markers=True,
                labels={
                    "mois_nom": "Mois",
                    "total_heures": "Heures facturables",
                    "annee": "Année"
                }
            )

            st.plotly_chart(line_chart)

            with st.expander("Voir le tableau"):
                st.dataframe(df_mensuel, use_container_width=True)

    st.write("---")

##################################################################################
# HISTOGRAMME DE RÉPARTITION DES HEURES NON FACTURABLES
##################################################################################
    with col1:
        def heures_nf(conn):
            query = """
                SELECT u.nom_service, SUM(hs.duree_heures) AS total_heures
                FROM heures_saisies hs
                JOIN utilisateurs u ON hs.utilisateur_id = u.id
                WHERE hs.type = 'Non facturables'
                GROUP BY u.nom_service
                """

            df = pd.read_sql(query, conn)
            return df

        with st.container(border=True):
            st.markdown(f"""
                <div style='
                    padding: 10px 0px;
                    border-left: 0px;
                    border-radius: 6px;
                    margin-top: 18px;
                    font-size: 18px;
                    font-weight: 500;
                '>
                    Suivi mensuel des heures non facturables
                </div>
                """, unsafe_allow_html=True)

            df_nf = heures_nf(conn)

            colors = ['lightslategray'] * len(df_nf)
            colors[0] = '#8DA58D'
            colors[1] = '#e77701 '
            colors[2] = '#5dadd2'
            colors[3] = '#1da70a'
            colors[4] = '#edf31b'
            colors[5] = '#efa3f3'

            bar = go.Figure(
                data=[
                    go.Bar(
                        x=df_nf["nom_service"],
                        y=df_nf["total_heures"],
                        marker_color=colors
                    )
                ]
            )

            st.plotly_chart(bar)

            with st.expander("Voir le tableau"):
                st.dataframe(df_nf, use_container_width=True)

    st.write("---")

##################################################################################
# HEURES TOTALES PAR MOIS + PONDERATION
##################################################################################
    query_month="""
    SELECT 
    DATE_TRUNC('month', hs.date) AS mois,
    SUM(hs.duree_heures) AS total_heures
    FROM heures_saisies hs
    GROUP BY DATE_TRUNC('month', hs.date)
    ORDER BY mois DESC
    """

    month_df = pd.read_sql(query_month, conn)

    with col2:
        with st.container(border=True):
            st.markdown(f"""
            <div style='
                padding: 10px 0px;
                border-left: 0px;
                border-radius: 6px;
                margin-top: 18px;
                font-size: 18px;
                font-weight: 500;
            '>
                Total des heures par mois
            </div>
            """, unsafe_allow_html=True)

            fig = px.bar(month_df,
                         x='mois', y='total_heures')
            st.plotly_chart(fig)

##################################################################################
# DIAGRAMME COMPARATIF DES HEURES PAR TYPE DE MISSION
##################################################################################
    query = """
    SELECT
        hs.date,
        m.nom_mission, 
        hs.duree_heures 
    FROM heures_saisies hs
    LEFT JOIN missions m ON hs.mission_id = m.id
    WHERE DATE_TRUNC('month', hs.date) = DATE_TRUNC('month', CURRENT_DATE)
    """

    col1, _, col2 = st.columns([6,2,3])

    with st.container(border=True):
        with col2:
            df_missions = pd.read_sql(query, conn)

            if not df_missions.empty:
                df_missions["nom_mission"] = df_missions["nom_mission"].fillna("Non facturable")
    
                pivot = df_missions.pivot_table(
                    index="nom_mission",
                    values="duree_heures",
                    aggfunc="sum",
                    fill_value=0
                ).reset_index()
    
                st.dataframe(pivot, use_container_width=True, hide_index=True)
    
                with col1:
                    fig = px.pie(pivot, values='duree_heures',
                             names='nom_mission', color_discrete_sequence=px.colors.sequential.RdBu)
                    st.plotly_chart(fig)
            else:
                st.write ("")

##################################################################################
# TABLEAU DES HEURES PAR COLLABORATEUR
##################################################################################
with tab2:
    query_col = """
    SELECT nom || ' ' || prenom
    FROM utilisateurs
    ORDER BY nom
    """

    df_col = pd.read_sql(query_col, conn)

    collab = st.selectbox("Nom du collaborateur", df_col)

    today = date.today()

    annee = today.year
    mois = today.month
    annee_prec = (today.replace(day=1) - timedelta(days=1)).year
    mois_prec = (today.replace(day=1) - timedelta(days=1)).month

    def heures_collab(collab, conn=None, annee=None, mois=None):

        query = """
            SELECT hs.type, SUM(hs.duree_heures) AS total_heures, u.nom || ' ' || u.prenom AS Nom
            FROM heures_saisies hs
            JOIN utilisateurs u ON hs.utilisateur_id = u.id
            WHERE EXTRACT(YEAR FROM hs.date) = %s
            AND EXTRACT(MONTH FROM hs.date) = %s
        """

        params = [annee, mois]

        query += " GROUP BY hs.type, u.nom, u.prenom ORDER BY total_heures DESC"

        df = pd.read_sql(query, conn, params=params)
        df = df.loc[df['nom'] == collab]
        return df

    df_mois = heures_collab(collab, conn=conn, annee=annee, mois=mois)
    df_prec = heures_collab(collab, conn=conn, annee=annee_prec, mois=mois_prec)

    df_kpi = pd.merge(
        df_mois,
        df_prec,
        on="type",
        how="outer",
        suffixes=("_actuel", "_precedent")
    ).fillna(0)

    df_kpi["evol"] = (
        (df_kpi["total_heures_actuel"] - df_kpi["total_heures_precedent"]) *100 / df_kpi["total_heures_precedent"].replace(0, 10000000000000)
    )
    # df_kpi["evol"] = df_kpi["evol"].round(2)

    st.markdown("""
        <div style='text-decoration: underline;
        font-size: 22px;
        font-weight: 200;
        '>Récapitulatif des heures du mois par collaborateur</div>""",
                unsafe_allow_html=True)
    st.write("""

    """)

    col1, col2, _= st.columns([2,2,8])

    with col1:
        if not df_kpi[df_kpi["type"] == "Facturables"].empty:
            st.metric(
                "Facturables",
                value=f'{df_kpi.loc[df_kpi["type"] == "Facturables", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["type"] == "Facturables", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Facturables",
                value=0,
                delta=0,
                border=True
            )

    with col2:
        if not df_kpi[df_kpi["type"] == "Non facturables"].empty:
            st.metric(
                "Non facturables",
                value=f'{df_kpi.loc[df_kpi["type"] == "Non facturables", "total_heures_actuel"].iloc[0]} h',
                delta=f'{df_kpi.loc[df_kpi["type"] == "Non facturables", "evol"].iloc[0]:.2f} %',
                border=True
            )
        else:
            st.metric(
                "Non facturables",
                value=0,
                delta=0,
                border=True
            )

    st.divider()

#####################################################################
# LISTE TICKETS RESTAURANT
#####################################################################

with tab3:

    st.subheader("🎫 Liste de distribution des tickets restaurant")

    col1, _ = st.columns(2)
    with col1:
        mois = st.selectbox("Mois", ['Janvier', 'Février', 'Mars', 'Avril',
                                     'Mai', 'Juin', 'Juillet', 'Août', 'Septembre',
                                     'Octobre', 'Novembre', 'Décembre']
                           )

        cursor.execute("""
        SELECT u.nom || ' ' || u.prenom AS Collaborateur, tr.tr_pris AS Tickets_souhaités
        FROM tickets_resto tr
        INNER JOIN utilisateurs u ON tr.utilisateur_id = u.id
        WHERE tr.mois = %s
        AND tr.annee = %s
        ORDER BY Collaborateur
        """, (mois, annee,)
                      )
        tr_result = cursor.fetchall()

        df_tick = pd.DataFrame(tr_result, columns=["Collaborateur", "Tickets souhaités"])
        st.dataframe(df_tick.reset_index(drop=True), use_container_width=True)

        output = io.BytesIO()

        df_tick.to_excel(output, index=False, engine='openpyxl')

        output.seek(0)

        st.download_button(
            label="📥 Télécharger en XLS",
            data=output,
            file_name=f"TR_{Mois}_{annee}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )