"""
database.py
===========
Point unique de connexion a PostgreSQL pour toute l'API.

Pourquoi un seul fichier pour ca : si demain l'URL de connexion
change (nouveau serveur, autre mot de passe), un seul endroit a
modifier. Tous les routers importent `get_db` d'ici.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Meme principe que pour MODEL_PATH (voir routers/ml.py) : le defaut
# fonctionne pour le developpement local, la variable d'environnement
# prend le relais dans Docker Compose (Phase 7), ou "localhost" ne
# designe plus le bon hote une fois dans un conteneur separe.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://ecommerce_user:ecommerce_pass@localhost:5455/ecommerce",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Fournit une session DB a chaque requete, et la ferme
    automatiquement apres -- meme si une erreur survient (le
    'finally' garantit ca). Sans cette fermeture systematique, les
    connexions s'accumuleraient et finiraient par epuiser le pool
    de connexions de PostgreSQL.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
