import pandas as pd
import numpy as np
import requests, os
import streamlit as st
from dotenv import load_dotenv

def fetch_token_RNE(username, password):

    url = "https://registre-national-entreprises.inpi.fr/api"
    
    payload= {
        "username": username,
        "password": password
    }
    
    response = requests.post(
        f"{url}/sso/login",
        json=payload,
        timeout=30
    )
    
    response.raise_for_status()
    token = response.json()['token']
    return token
username = os.getenv("username")
password = os.getenv("password")
token = fetch_token_RNE(username, password)

def rcs_fetch_api(siren, bearer_token=token):

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    url = f"https://registre-national-entreprises.inpi.fr/api/companies/{siren}"    

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    
    data = r.json()
    return data

rcs = rcs_fetch_api("301482543")

def deep_get(obj, *keys, default=None):
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        elif isinstance(obj, list) and isinstance(key, int):
            if 0 <= key < len(obj):
                obj = obj[key]
            else:
                return default
        else:
            return default

        if obj is None:
            return default

    return obj

def extract_rcs_adresse(rcs):
    return deep_get(
        rcs,
        "formality",
        "content",
        "personneMorale",
        "adresseEntreprise",
        "adresse",
        default={}
    )

adresse = extract_rcs_adresse(rcs)

def extract_rcs_dir(rcs):
    return deep_get(
        rcs,
        "formality",
        "content",
        "personneMorale",
        "composition",
        "pouvoirs",
        0,
        "individu",
        "descriptionPersonne",
        default={}
    )

dirigeant = extract_rcs_dir(rcs)

def format_adresse(adresse: dict) -> str:
    if not adresse:
        return ""

    parts = [
        " ".join(filter(None, [
            adresse.get("numVoie"),
            adresse.get("typeVoie"),
            adresse.get("voie"),
        ])),
        " ".join(filter(None, [
            adresse.get("codePostal"),
            adresse.get("commune"),
        ])),
        " ".join(filter(None, [
            adresse.get("complementLocalisation"),
        ])),
        adresse.get("pays"),
    ]

    return ", ".join(filter(None, parts))

def format_dir(dirigeant: dict) -> str:
    if not dirigeant:
        return ""

    parts = [
        " ".join(filter(None, [
            dirigeant.get("nom"),
            dirigeant.get("prenoms")[0]
        ])),
    ]
    return ", ".join(filter(None, parts))

adresse = format_adresse(adresse)
dirigeant = format_dir(dirigeant)
capit = rcs_fetch_api(siren)['formality']['content']['personneMorale']['identite']['description']['montantCapital']
rais_soc = rcs_fetch_api(siren)['formality']['content']['personneMorale']['identite']['description']['sigle']

@st.cache_data(ttl=3600)
def get_company_sirene(siren: str):
    return request_sirene_api(siren)