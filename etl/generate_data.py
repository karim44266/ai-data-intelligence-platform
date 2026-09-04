"""
generate_data.py
=================
ETAPE "EXTRACT" (simulée) du pipeline.

Pourquoi un script séparé pour générer les données ?
------------------------------------------------------
Dans un vrai projet, l'étape Extract lit des données qui existent
DEJA quelque part (une API, un CSV fourni par le métier, une autre
base). Ici, on n'a pas cette source externe, donc on la simule :
ce script joue le rôle de "source de données brutes" en écrivant
des CSV dans data/raw/. Le pipeline ETL (etl.py) ne saura JAMAIS
que ces données ont été générées par Faker -- il les traitera
exactement comme s'il les recevait d'un système externe.

Pourquoi des imperfections volontaires ?
------------------------------------------------------
Si je générais des données déjà parfaites, ton étape clean_data()
ne servirait à rien et tu n'apprendrais pas à nettoyer de la vraie
donnée. On injecte donc :
  - des emails avec casse incohérente et espaces ("  John@Mail.COM ")
  - quelques valeurs manquantes (country vide)
  - quelques doublons de lignes
  - quelques types "sales" (prix en string avec virgule au lieu du point)
"""

import csv
import random
from datetime import timedelta
from pathlib import Path

from faker import Faker

# SEED FIXE : pourquoi c'est important
# --------------------------------------
# random.seed(42) et Faker.seed(42) forcent le générateur
# pseudo-aléatoire à produire TOUJOURS la même séquence de résultats.
# Sans ça, relancer ce script donnerait des données différentes à
# chaque fois, et tu ne pourrais jamais comparer deux exécutions ou
# reproduire un bug. En data engineering, la reproductibilité est
# une exigence, pas un détail.
SEED = 42
random.seed(SEED)
Faker.seed(SEED)
fake = Faker()

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

N_CUSTOMERS = 300
N_PRODUCTS = 50
N_ORDERS = 1500
CATEGORIES = ["Electronics", "Home & Kitchen", "Fashion", "Books", "Sports", "Beauty"]
COUNTRIES = ["Tunisia", "France", "Germany", "USA", "Canada", "Morocco", "Spain"]


def messy_email(first, last):
    """Génère un email avec une casse/espacement incohérents,
    comme on en trouve souvent dans de vrais exports CSV."""
    email = f"{first}.{last}@{fake.free_email_domain()}"
    if random.random() < 0.3:
        email = email.upper()
    if random.random() < 0.15:
        email = f"  {email}  "  # espaces parasites
    return email


def generate_customers():
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        first = fake.first_name()
        last = fake.last_name()
        signup = fake.date_between(start_date="-2y", end_date="-30d")
        country = random.choice(COUNTRIES)
        # 5% de valeurs manquantes volontaires sur "country"
        if random.random() < 0.05:
            country = ""
        rows.append({
            "customer_id": i,
            "first_name": first,
            "last_name": last,
            "email": messy_email(first, last),
            "country": country,
            "signup_date": signup.isoformat(),
        })
    # On duplique volontairement 3 lignes au hasard, comme un
    # export CSV bugué qui répéterait des lignes.
    for _ in range(3):
        rows.append(random.choice(rows[:N_CUSTOMERS]))
    return rows


def generate_products():
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        category = random.choice(CATEGORIES)
        price = round(random.uniform(5, 500), 2)
        rows.append({
            "product_id": i,
            "product_name": f"{fake.word().capitalize()} {category.split()[0]}",
            "category": category,
            # Prix stocké en string avec virgule pour 10% des lignes
            # -> simulate un export depuis un tableur en locale FR.
            "price": str(price).replace(".", ",") if random.random() < 0.1 else price,
            "stock_quantity": random.randint(0, 500),
        })
    return rows


def generate_orders(customers):
    rows = []
    valid_customer_ids = list({c["customer_id"] for c in customers})
    statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
    weights = [0.05, 0.15, 0.15, 0.60, 0.05]
    for i in range(1, N_ORDERS + 1):
        cust_id = random.choice(valid_customer_ids)
        # on retrouve la date d'inscription de ce client pour que
        # la commande soit forcément APRES son signup (cohérence
        # temporelle -> important pour la validation plus tard)
        cust = next(c for c in customers if c["customer_id"] == cust_id)
        signup = fake.date_object() if not cust["signup_date"] else \
            __import__("datetime").date.fromisoformat(cust["signup_date"])
        order_date = fake.date_time_between(start_date=signup, end_date="now")
        rows.append({
            "order_id": i,
            "customer_id": cust_id,
            "order_date": order_date.isoformat(),
            "status": random.choices(statuses, weights=weights, k=1)[0],
        })
    return rows


def generate_order_items(orders, products):
    rows = []
    item_id = 1
    for order in orders:
        n_items = random.randint(1, 5)
        chosen_products = random.sample(products, n_items)
        for p in chosen_products:
            price = p["price"]
            price = float(str(price).replace(",", ".")) if isinstance(price, str) else price
            rows.append({
                "order_item_id": item_id,
                "order_id": order["order_id"],
                "product_id": p["product_id"],
                "quantity": random.randint(1, 4),
                "unit_price": price,
            })
            item_id += 1
    return rows


def generate_payments(orders):
    rows = []
    methods = ["credit_card", "paypal", "bank_transfer"]
    for order in orders:
        if order["status"] == "pending":
            continue  # une commande "pending" n'a pas encore de paiement
        rows.append({
            "payment_id": order["order_id"],
            "order_id": order["order_id"],
            "payment_method": random.choice(methods),
            "payment_status": "completed" if order["status"] != "cancelled" else "refunded",
            "paid_at": order["order_date"],
        })
    return rows


def generate_reviews(orders, order_items, products):
    rows = []
    review_id = 1
    seen_pairs = set()
    delivered_orders = [o for o in orders if o["status"] == "delivered"]
    for order in delivered_orders:
        if random.random() > 0.4:  # tout le monde ne laisse pas d'avis
            continue
        items = [oi for oi in order_items if oi["order_id"] == order["order_id"]]
        if not items:
            continue
        item = random.choice(items)
        pair = (order["customer_id"], item["product_id"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        rows.append({
            "review_id": review_id,
            "customer_id": order["customer_id"],
            "product_id": item["product_id"],
            "rating": random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.05, 0.15, 0.35, 0.40])[0],
            "comment": fake.sentence() if random.random() < 0.6 else "",
            "review_date": order["order_date"],
        })
        review_id += 1
    return rows


def write_csv(rows, filename):
    path = RAW_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {filename} : {len(rows)} lignes écrites")


if __name__ == "__main__":
    print("Génération des données brutes (avec imperfections volontaires)...")
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)
    payments = generate_payments(orders)
    reviews = generate_reviews(orders, order_items, products)

    write_csv(customers, "customers_raw.csv")
    write_csv(products, "products_raw.csv")
    write_csv(orders, "orders_raw.csv")
    write_csv(order_items, "order_items_raw.csv")
    write_csv(payments, "payments_raw.csv")
    write_csv(reviews, "reviews_raw.csv")
    print(f"\nTerminé. Fichiers dans : {RAW_DIR}")
