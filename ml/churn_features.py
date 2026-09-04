"""
churn_features.py
==================
Transforme les donnees relationnelles (customers/orders) en une
table "une ligne = un client, plusieurs colonnes = ses caracteristiques"
-- c'est ce qu'on appelle le FEATURE ENGINEERING, l'etape la plus
importante (et la plus longue) de tout projet ML. Un modele n'est
jamais meilleur que les features qu'on lui donne.

Pourquoi ces features precises et pas d'autres :
--------------------------------------------------
- recency_days   : nombre de jours depuis le dernier achat.
  C'est LE signal le plus fort pour predire un churn -- un client
  qui n'a rien achete depuis longtemps est, presque par definition,
  en train de partir.
- frequency      : nombre total de commandes. Un client qui achete
  souvent a plus de "momentum" et churn moins facilement qu'un
  client qui n'a achete qu'une fois.
- total_spent    : montant total depense. Utile pour distinguer un
  client "gros" en risque de churn (grosse perte potentielle) d'un
  petit client occasionnel.
- avg_order_value: total_spent / frequency. Un client qui depense
  beaucoup par commande mais rarement a un profil different d'un
  client qui achete souvent mais peu a chaque fois.
- tenure_days    : anciennete du compte. Necessaire pour ne pas
  confondre "client fidele qui vient de s'arreter" avec "client
  tout nouveau qui n'a pas encore eu le temps de re-acheter".
"""

import pandas as pd
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg://ecommerce_user:ecommerce_pass@localhost:5455/ecommerce"

# Seuil au-dela duquel on considere un client "churne". 90 jours
# est un choix METIER, pas une verite mathematique -- en e-commerce,
# 3 mois sans achat est un seuil courant, mais ca varie selon le
# secteur (un supermarche en ligne aurait un seuil bien plus court
# qu'un vendeur de meubles).
CHURN_THRESHOLD_DAYS = 90


def extract_features():
    engine = create_engine(DB_URL)
    query = """
        SELECT
            c.customer_id,
            c.signup_date,
            COUNT(o.order_id)                         AS frequency,
            COALESCE(SUM(o.total_amount), 0)           AS total_spent,
            MAX(o.order_date)                          AS last_order_date,
            (SELECT MAX(order_date) FROM orders)       AS reference_date
        FROM customers c
        LEFT JOIN orders o
            ON o.customer_id = c.customer_id
            AND o.status != 'cancelled'
        GROUP BY c.customer_id, c.signup_date
    """
    df = pd.read_sql(query, engine)

    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["last_order_date"] = pd.to_datetime(df["last_order_date"])
    df["reference_date"] = pd.to_datetime(df["reference_date"])

    # tenure_days : anciennete du compte au moment de reference
    df["tenure_days"] = (df["reference_date"] - df["signup_date"]).dt.days

    # recency_days : jours depuis le dernier achat. Si le client n'a
    # JAMAIS achete (last_order_date est NaT), on utilise tenure_days
    # -- un client qui n'a jamais achete depuis son inscription a une
    # "recence" egale a son anciennete.
    df["recency_days"] = (df["reference_date"] - df["last_order_date"]).dt.days
    df["recency_days"] = df["recency_days"].fillna(df["tenure_days"])

    df["avg_order_value"] = df["total_spent"] / df["frequency"].replace(0, pd.NA)
    df["avg_order_value"] = df["avg_order_value"].fillna(0)

    # LABEL : est-ce que ce client est churne ?
    # On exclut les clients trop recents (< 90 jours d'anciennete)
    # du calcul du label -- on ne peut pas dire qu'ils ont "churne"
    # s'ils n'ont meme pas encore eu le temps de revenir acheter.
    # C'est un choix explicite pour eviter d'entrainer le modele
    # sur un label bruite/faux.
    df["is_churned"] = (df["recency_days"] > CHURN_THRESHOLD_DAYS).astype(int)
    df.loc[df["tenure_days"] < CHURN_THRESHOLD_DAYS, "is_churned"] = pd.NA

    return df


if __name__ == "__main__":
    df = extract_features()
    print(df[["customer_id", "frequency", "total_spent", "recency_days",
              "tenure_days", "avg_order_value", "is_churned"]].head(10))
    print(f"\nTotal clients : {len(df)}")
    print(f"Clients exclus (trop recents) : {df['is_churned'].isna().sum()}")
    print(f"Taux de churn (parmi les eligibles) : {df['is_churned'].mean():.1%}")
