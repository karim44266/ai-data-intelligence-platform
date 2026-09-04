"""
etl.py
======
Pipeline ETL : CSV bruts -> PostgreSQL propre.

ARCHITECTURE : pourquoi 5 fonctions séparées et pas une seule
grosse fonction qui fait tout ?
------------------------------------------------------------------
Principe de responsabilité unique (Single Responsibility Principle) :
chaque fonction fait UNE chose et peut être testée, débuggée et
comprise indépendamment des autres.

    load_data()      -> lit le CSV, ne fait AUCUNE logique métier
    clean_data()      -> corrige la forme (espaces, casse, types)
    validate_data()   -> vérifie le fond (règles métier, cohérence)
    transform_data()  -> adapte au schéma final (renommage, calculs)
    save_to_database()-> écrit dans PostgreSQL, dans le bon ORDRE

Si demain la validation doit changer, tu modifies UNE fonction
sans toucher au reste. Si le pipeline plante, le nom de la
fonction dans la stack trace te dit direct OU chercher.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Pourquoi mettre la config ici et pas en dur dans chaque fonction :
# un seul endroit à changer si le mot de passe/port change.
DB_CONFIG = {
    "user": "ecommerce_user",
    "password": "ecommerce_pass",
    "host": "localhost",
    "port": 5455,
    "database": "ecommerce",
}
DB_URL = (
    f"postgresql+psycopg://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
# Driver utilise : psycopg (version 3), pas psycopg2 ni pg8000.
# Historique de debug (pour comprendre pourquoi ce choix) :
#   - psycopg2  : plante avec une UnicodeDecodeError sur certaines
#     configs Windows + Python recent (bug cote encodage systeme).
#   - pg8000    : la connexion echouait avec "authentification par
#     mot de passe echouee", alors que les identifiants etaient
#     verifies corrects (testes avec psql en ligne de commande).
#     Cause probable : bug d'encodage cote pg8000 sur Windows lors
#     du calcul de la preuve SCRAM (le mot de passe transite mal).
#   - psycopg (v3) : version modernisee, maintenue activement,
#     meilleure gestion multiplateforme de l'encodage -> resout
#     les deux problemes precedents.


# ============================================================
# 1. LOAD (Extract) — lire le CSV tel quel, sans le modifier
# ============================================================
def load_data(filename: str) -> pd.DataFrame:
    """Lit un CSV brut en DataFrame pandas.

    Pourquoi ne rien nettoyer ici : si tu mélanges lecture et
    nettoyage, tu ne peux plus savoir si un bug vient du CSV
    source ou de ta logique de nettoyage. On sépare toujours
    "récupérer" de "transformer".
    """
    path = RAW_DIR / filename
    df = pd.read_csv(path)
    print(f"[LOAD] {filename} : {len(df)} lignes chargées")
    return df


# ============================================================
# 2. CLEAN — corriger la FORME des données (pas la logique métier)
# ============================================================
def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    # .str.strip() enlève les espaces en début/fin -> corrige
    # "  email@x.com  "
    df["email"] = df["email"].str.strip().str.lower()
    # Pourquoi .lower() et pas .upper() : email@X.COM et
    # email@x.com doivent être considérés comme LE MEME email
    # pour respecter la contrainte UNIQUE de la base -> on
    # normalise toujours vers une seule casse de référence.

    df["first_name"] = df["first_name"].str.strip()
    df["last_name"] = df["last_name"].str.strip()

    # signup_date arrive du CSV comme texte ("2025-03-09"). psycopg2
    # laissait PostgreSQL le convertir implicitement en DATE, mais
    # pg8000 est plus strict et exige un vrai type Python date/datetime
    # cote client. On convertit donc explicitement ici -- c'est de
    # toute facon une meilleure pratique de ne jamais laisser une
    # date "trainer" en string dans un pipeline de donnees.
    df["signup_date"] = pd.to_datetime(df["signup_date"]).dt.date

    # Valeurs manquantes ("") -> vrai NaN, puis on remplace par
    # une valeur explicite "Unknown" plutôt que de laisser vide.
    # Pourquoi : NULL en base peut casser des agrégations (COUNT
    # vs COUNT(colonne) se comportent différemment avec NULL) ;
    # un "Unknown" explicite est plus facile à filtrer/analyser.
    df["country"] = df["country"].fillna("Unknown")
    df.loc[df["country"].str.strip() == "", "country"] = "Unknown"

    # doublons exacts (même customer_id répété dans le CSV)
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"])
    removed = before - len(df)
    if removed:
        print(f"[CLEAN] customers : {removed} doublon(s) de customer_id supprimé(s)")

    # Cas différent et plus subtil : deux clients DIFFERENTS
    # (customer_id différents) peuvent finir avec le même email
    # normalisé -- ici, deux prénoms/noms identiques par hasard.
    # C'est un vrai cas de collision qu'on a rencontré en testant
    # ce pipeline. On ne peut pas les insérer tous les deux, car
    # la contrainte UNIQUE(email) de la base les rejetterait de
    # toute façon. On garde la première occurrence et on logue
    # celles qu'on écarte (en production, on les enverrait plutôt
    # dans une file de "rejets" pour revue manuelle).
    before = len(df)
    df = df.drop_duplicates(subset=["email"], keep="first")
    removed = before - len(df)
    if removed:
        print(f"[CLEAN] customers : {removed} collision(s) d'email supprimée(s)")

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    # price est parfois une string "228,52" (virgule FR) au lieu
    # d'un float -> on convertit systématiquement.
    df["price"] = (
        df["price"].astype(str).str.replace(",", ".", regex=False).astype(float)
    )
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    df["paid_at"] = pd.to_datetime(df["paid_at"])
    return df


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df["comment"] = df["comment"].fillna("")
    df["review_date"] = pd.to_datetime(df["review_date"])
    return df


# ============================================================
# 3. VALIDATE — vérifier les règles METIER (le fond, pas la forme)
# ============================================================
# Pourquoi valider en Python EN PLUS des CHECK constraints SQL :
# si on laisse la base rejeter les lignes invalides une par une,
# on ne le découvre qu'au moment de l'insertion, avec un message
# d'erreur SQL brut. Valider AVANT en Python permet de repérer
# TOUTES les lignes invalides d'un coup et de les logger proprement,
# avant même de toucher la base.
def validate_customers(df: pd.DataFrame) -> pd.DataFrame:
    # email doit contenir un "@" -> sinon ligne rejetée
    valid_mask = df["email"].str.contains("@", na=False)
    invalid = (~valid_mask).sum()
    if invalid:
        print(f"[VALIDATE] customers : {invalid} email(s) invalide(s) rejeté(s)")
    return df[valid_mask]


def validate_products(df: pd.DataFrame) -> pd.DataFrame:
    valid_mask = df["price"] >= 0
    invalid = (~valid_mask).sum()
    if invalid:
        print(f"[VALIDATE] products : {invalid} prix négatif(s) rejeté(s)")
    return df[valid_mask]


def validate_orders(df: pd.DataFrame, valid_customer_ids: set) -> pd.DataFrame:
    # cohérence référentielle vérifiée COTE PYTHON avant d'aller
    # en base -> anticipe ce que la FK aurait rejeté de toute façon.
    valid_mask = df["customer_id"].isin(valid_customer_ids)
    invalid = (~valid_mask).sum()
    if invalid:
        print(f"[VALIDATE] orders : {invalid} commande(s) avec client inconnu rejetée(s)")
    return df[valid_mask]


# ============================================================
# 4. TRANSFORM — adapter au schéma final (renommage, dérivation)
# ============================================================
def transform_orders(orders_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame:
    """Calcule total_amount de chaque commande à partir de order_items.

    Pourquoi calculer ici plutôt que de le stocker tel quel dans
    le CSV brut : c'est une DONNEE DERIVEE (elle se déduit d'autres
    données). La calculer dans le pipeline garantit qu'elle est
    toujours cohérente avec le détail des lignes de commande.
    """
    items_df = items_df.copy()
    items_df["line_total"] = items_df["quantity"] * items_df["unit_price"]
    totals = items_df.groupby("order_id")["line_total"].sum().reset_index()
    totals = totals.rename(columns={"line_total": "total_amount"})

    orders_df = orders_df.merge(totals, on="order_id", how="left")
    orders_df["total_amount"] = orders_df["total_amount"].fillna(0).round(2)
    return orders_df


def transform_payments(payments_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
    """Dérive payments.amount à partir de orders.total_amount.

    Pourquoi ne PAS stocker amount dans le CSV brut de payments :
    le montant payé doit toujours correspondre au total de la
    commande. Si on le stockait séparément dans deux endroits
    différents (orders.total_amount et payments.amount), un bug
    ou une correction manuelle pourrait les faire diverger. On
    calcule donc amount UNE SEULE FOIS (dans transform_orders)
    et on le réutilise ici -- une seule source de vérité.
    """
    payments_df = payments_df.merge(
        orders_df[["order_id", "total_amount"]], on="order_id", how="left"
    )
    payments_df = payments_df.rename(columns={"total_amount": "amount"})
    payments_df["amount"] = payments_df["amount"].fillna(0)
    return payments_df


# ============================================================
# 5. SAVE — écrire en base, DANS LE BON ORDRE
# ============================================================
def save_to_database(tables: dict):
    """Insère chaque DataFrame dans PostgreSQL.

    Pourquoi l'ORDRE est critique ici :
    customers doit être inséré AVANT orders (FK), orders AVANT
    order_items et payments, et products AVANT order_items et
    reviews. Si on insère dans le mauvais ordre, PostgreSQL
    rejette l'insertion avec une erreur de clé étrangère (FK
    violation) -- ce n'est pas juste une bonne pratique, c'est
    une contrainte imposée par le schéma qu'on a créé en Phase 1.
    """
    engine = create_engine(DB_URL)

    insertion_order = [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "reviews",
    ]

    with engine.begin() as conn:
        # engine.begin() = transaction : soit TOUT s'insère avec
        # succès, soit RIEN n'est inséré (rollback automatique en
        # cas d'erreur). Pourquoi c'est important : sans ça, un
        # crash à mi-chemin laisserait la base dans un état
        # incohérent (customers insérés mais pas orders, par ex.)
        for table_name in insertion_order:
            df = tables[table_name]
            df.to_sql(table_name, conn, if_exists="append", index=False)
            print(f"[SAVE] {table_name} : {len(df)} lignes insérées")


# ============================================================
# ORCHESTRATION — assemble les étapes dans l'ordre
# ============================================================
def run_pipeline():
    print("=" * 60)
    print("DEMARRAGE DU PIPELINE ETL")
    print("=" * 60)

    # --- LOAD ---
    customers = load_data("customers_raw.csv")
    products = load_data("products_raw.csv")
    orders = load_data("orders_raw.csv")
    order_items = load_data("order_items_raw.csv")
    payments = load_data("payments_raw.csv")
    reviews = load_data("reviews_raw.csv")

    # --- CLEAN ---
    customers = clean_customers(customers)
    products = clean_products(products)
    orders = clean_orders(orders)
    order_items = clean_order_items(order_items)
    payments = clean_payments(payments)
    reviews = clean_reviews(reviews)

    # --- VALIDATE ---
    customers = validate_customers(customers)
    products = validate_products(products)
    valid_customer_ids = set(customers["customer_id"])
    orders = validate_orders(orders, valid_customer_ids)

    # on ne garde que les order_items/payments/reviews dont la
    # commande a survécu à la validation
    valid_order_ids = set(orders["order_id"])
    order_items = order_items[order_items["order_id"].isin(valid_order_ids)]
    payments = payments[payments["order_id"].isin(valid_order_ids)]
    reviews = reviews[reviews["customer_id"].isin(valid_customer_ids)]

    # --- TRANSFORM ---
    orders = transform_orders(orders, order_items)
    payments = transform_payments(payments, orders)

    # --- SAVE ---
    tables = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "reviews": reviews,
    }
    save_to_database(tables)

    print("=" * 60)
    print("PIPELINE TERMINE AVEC SUCCES")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
