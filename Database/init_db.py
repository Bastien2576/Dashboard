import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

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

# 1. Journal de logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    date_saisie TIMESTAMP NOT NULL,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    page TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT
);
""")

# 2. Utilisateurs
cursor.execute("""
CREATE TABLE IF NOT EXISTS utilisateurs (
    id SERIAL PRIMARY KEY,
    matricule TEXT UNIQUE NOT NULL,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    nom_service TEXT NOT NULL,
    heures_hebdo REAL NOT NULL,
    mail VARCHAR UNIQUE NOT NULL
);
""")

# 3. Taux de facturation
cursor.execute("""
CREATE TABLE IF NOT EXISTS taux_facturation (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    nom TEXT NOT NULL,
    taux REAL NOT NULL,
    date DATE NOT NULL
);
""")

# 4. Clients
cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    code_client TEXT UNIQUE NOT NULL,
    nom_client TEXT UNIQUE NOT NULL,
    id_associe INTEGER REFERENCES utilisateurs(id)
);
""")

# 5. Dossiers
cursor.execute("""
CREATE TABLE IF NOT EXISTS dossiers (
    id SERIAL PRIMARY KEY,
    matricule_dossier TEXT UNIQUE NOT NULL,
    nom_dossier TEXT NOT NULL,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    id_associe INTEGER REFERENCES utilisateurs(id)
);
""")

# 6. Missions
cursor.execute("""
CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,
    matricule_mission VARCHAR(8) UNIQUE,
    nom_mission TEXT NOT NULL,
    id_dossier INTEGER NOT NULL REFERENCES dossiers(id)
);
""")

# 7. Heures saisies
cursor.execute("""
CREATE TABLE IF NOT EXISTS heures_saisies (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    date DATE NOT NULL,
    duree_heures REAL NOT NULL,
    type TEXT CHECK(type IN ('Facturable', 'Non facturable')) NOT NULL,
    nom_du_client TEXT,
    client_id INTEGER REFERENCES clients(id),
    mission_id VARCHAR(8) REFERENCES missions(id),
    activite TEXT,
    commentaire TEXT,
    code TEXT
);
""")

# 8. Congés
cursor.execute("""
CREATE TABLE IF NOT EXISTS conges (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    titre TEXT,
    date_depart TIMESTAMP NOT NULL,
    date_retour TIMESTAMP NOT NULL,
    type TEXT CHECK(type IN ('Réservation de salle', 'Normal', 'Exceptionnel', 'Récupération d''heures', 'Maladie')),
    resource_id TEXT,
    commentaire TEXT
);
""")

# 9. Tickets resto
cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets_resto (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    tr_pris INTEGER CHECK(tr_pris BETWEEN 0 AND 20),
    mois TEXT NOT NULL,
    annee INTEGER NOT NULL
);
""")

# 10. Modulations
cursor.execute("""
CREATE TABLE IF NOT EXISTS modulations (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    mois INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    heures_reelles REAL NOT NULL,
    heures_facturables REAL DEFAULT 0,
    heures_non_facturables REAL DEFAULT 0,
    modulation_globale REAL NOT NULL
);
""")

# 11. Frais kilométriques
cursor.execute("""
CREATE TABLE IF NOT EXISTS frais_km (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    date DATE NOT NULL,
    distance_km REAL NOT NULL,
    distance_cc REAL NOT NULL,
    indemnite REAL,
    mission_id INTEGER NOT NULL REFERENCES missions(id)
);
""")

# 12. Frais repas
cursor.execute("""
CREATE TABLE IF NOT EXISTS frais_repas (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    date DATE NOT NULL,
    montant REAL NOT NULL,
    type TEXT CHECK(type IN ('rembourse_cabinet', 'rembourse_client')) NOT NULL,
    mission_id INTEGER NOT NULL REFERENCES missions(id),
    commentaire TEXT
);
""")

# 13. Barèmes kilométriques
cursor.execute("""
CREATE TABLE IF NOT EXISTS baremes_km (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    type_vehicule TEXT NOT NULL,
    annee INTEGER NOT NULL,
    montant_par_km REAL NOT NULL
);
""")

# 14. Activités
cursor.execute("""
CREATE TABLE IF NOT EXISTS activites (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL,
    activite TEXT NOT NULL
);
""")

# 15. Véhicule
cursor.execute("""
CREATE TABLE IF NOT EXISTS vehicule (
    id SERIAL PRIMARY KEY,
    id_utilisateur INTEGER NOT NULL REFERENCES utilisateurs(id),
    date DATE NOT NULL,
    immatriculation VARCHAR(7),
    cv INTEGER,
    type_vehicule TEXT CHECK(type_vehicule IN ('automobile', 'motocyclette', 'cyclomoteur')) NOT NULL
);
""")

# 16. Facturation
cursor.execute("""
CREATE TABLE IF NOT EXISTS facturation (
    id SERIAL PRIMARY KEY,
    id_utilisateur INTEGER NOT NULL REFERENCES utilisateurs(id),
    id_client INTEGER NOT NULL REFERENCES clients(id),
    id_dossier INTEGER NOT NULL REFERENCES dossiers(id),
    id_mission INTEGER NOT NULL REFERENCES missions(id),
    id_fraiskm INTEGER REFERENCES frais_km(id),
    id_fraisrep INTEGER REFERENCES frais_repas(id),
    id_hs INTEGER REFERENCES heures_saisies(id),
    date DATE NOT NULL,
    client TEXT NOT NULL,
    dossier TEXT NOT NULL,
    mission TEXT NOT NULL,
    code VARCHAR(3),
    nom TEXT,
    tache VARCHAR(4) NOT NULL,
    libelle TEXT,
    quantite INTEGER,
    facture INTEGER,
    date_cloture DATE NOT NULL
);
""")

# 17. Facturation totale
cursor.execute("""
CREATE TABLE IF NOT EXISTS total_facturation (
    id SERIAL PRIMARY KEY,
    id_fact INTEGER NOT NULL REFERENCES facturation(id),
    id_taux INTEGER NOT NULL REFERENCES taux_facturation(id),
    montant_calc REAL NOT NULL,
    montant_fact REAL NOT NULL,
    boni_mali REAL NOT NULL
);
""")

# Sauvegarde et fermeture
conn.commit()
cursor.close()
conn.close()