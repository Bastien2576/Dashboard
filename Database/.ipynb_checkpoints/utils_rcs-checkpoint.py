import pandas as pd
import numpy as np
import requests, os
import streamlit as st
from dotenv import load_dotenv

def siren_fetch_api(siren: str):

    API_KEY = os.getenv("API_KEY")
    
    url = f"https://api.insee.fr/api-sirene/3.11/siren/{siren}"
    headers = {
        "X-INSEE-Api-Key-Integration": API_KEY,
        "Accept": "application/json",
    }
    
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["uniteLegale"]

def get_current_period(periodes: list[dict]) -> dict | None:
    for p in periodes:
        if p.get("dateFinPeriodeUniteLegale") is None:
            return p
    return None

def map_sirene_to_client(unite):
    return {
        "siren": unite["siren"],
        "denomination": unite.get("denominationUniteLegale"),
        "code_ape": unite.get("activitePrincipaleUniteLegale"),
        "date_creation": unite.get("dateCreationUniteLegale"),
        "statut": unite.get("etatAdministratifUniteLegale"),
        "date_debut": unite.get("dateDebut"),
        "date_fin": unite.get("dateFin"),
        "denomination": unite.get("denominationUniteLegale"),
        "categorie_juridique": unite.get("categorieJuridiqueUniteLegale"),
        "activite_principale": unite.get("activitePrincipaleUniteLegale"),
        "nic_siege": unite.get("nicSiegeUniteLegale"),
        "economie_sociale_solidaire": unite.get("economieSocialeSolidaireUniteLegale"),
    }

def request_sirene_api(siren: int) -> dict:
    
    unite = siren_fetch_api(siren)

    current_period = get_current_period(unite.get("periodesUniteLegale", []))
    
    if current_period is None:
        etat = "F"
    else:
        etat = current_period.get("etatAdministratifUniteLegale", "A")

    merged = unite | (current_period or {})

    return map_sirene_to_client(merged)

@st.cache_data(ttl=3600)
def get_company_sirene(siren: str):
    return request_sirene_api(siren)