import streamlit as st
import pandas as pd
import numpy as np

# --- Données utilisateurs séparées ---
ADMIN_CREDENTIALS = {
    "admin": "wqrS78Mlj4*",
    "superuser": "superpass"
}

USER_CREDENTIALS = {
    "bob": "bobpass",
    "alice": "alicepass"
}

# --- Initialisation session_state ---
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# --- Fonction de connexion ---
def login():
    st.title("🔐 Connexion")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    login_button = st.button("Se connecter")

    if login_button:
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            st.session_state['authentication_status'] = True
            st.session_state['username'] = username
            st.session_state['role'] = 'admin'
            st.success(f"Bienvenue administrateur {username} 🎉")
        elif username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state['authentication_status'] = True
            st.session_state['username'] = username
            st.session_state['role'] = 'user'
            st.success(f"Bienvenue {username} 🎉")
        else:
            st.session_state['authentication_status'] = False
            st.error("Nom d'utilisateur ou mot de passe incorrect.")

# --- Fonction de déconnexion ---
def logout():
    st.session_state['authentication_status'] = None
    st.session_state['username'] = ''
    st.session_state['role'] = ''
    st.rerun()

# --- Interface principale selon rôle ---
def admin_dashboard():
    st.title("👑 Tableau de bord Administrateur")
    st.write("Contenu réservé aux administrateurs.")

def user_dashboard():
    st.title("🏠 Tableau de bord Utilisateur")
    st.write("Contenu réservé aux utilisateurs connectés.")

# --- Affichage principal selon état ---
if st.session_state['authentication_status'] is True:
    st.sidebar.success(f"Connecté en tant que {st.session_state['username']} ({st.session_state['role']})")
    st.sidebar.button("Se déconnecter", on_click=logout)

    if st.session_state['role'] == 'admin':
        admin_dashboard()
    elif st.session_state['role'] == 'user':
        user_dashboard()
        
elif st.session_state['authentication_status'] is False:
    login()
    
else:
    login()