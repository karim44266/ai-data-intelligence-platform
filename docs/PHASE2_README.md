# Phase 2 — Dataset + Pipeline ETL

## Comment lancer

```bash
pip install -r requirements.txt

# 1. Générer les CSV bruts (avec imperfections volontaires)
python etl/generate_data.py

# 2. Lancer le pipeline ETL (lit les CSV -> nettoie -> valide -> transforme -> insère)
python etl/etl.py
```

Assure-toi que le conteneur PostgreSQL de la Phase 1 tourne
(`docker-compose up -d`) avant de lancer `etl.py`.

## Comment vérifier que ça a marché

```bash
docker exec -it ecommerce_db psql -U ecommerce_user -d ecommerce -c "
SELECT 'customers' AS table_name, COUNT(*) FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews;
"
```

Tu dois voir des centaines/milliers de lignes dans chaque table (le nombre
exact varie légèrement, car de vraies données sont rejetées par la
validation — c'est normal et voulu, voir plus bas).

## Bugs réels rencontrés en testant ce pipeline (gardés volontairement)

En construisant ce projet, je l'ai fait tourner sur une vraie base
PostgreSQL avant de te le donner — et j'ai trouvé deux bugs réels que
je n'avais pas anticipés. Je les documente ici parce que **savoir
lire une erreur SQL et la corriger est une compétence aussi importante
que d'écrire le pipeline au premier coup** :

1. **`UniqueViolation` sur `customers.email`** — deux clients différents
   (deux `customer_id` distincts) ont généré le même email normalisé,
   car Faker a pioché deux fois le même prénom+nom sur seulement 300
   personnes. Solution : dans `clean_customers()`, en plus de dédupliquer
   par `customer_id`, on déduplique aussi par `email` (on garde la
   première occurrence). C'est un vrai cas de collision de données, pas
   un bug de mon code — et ça t'apprend que "unique en théorie" et
   "unique en pratique" sont deux choses différentes.

2. **`NotNullViolation` sur `payments.amount`** — le CSV brut de paiements
   ne contenait pas de montant. Plutôt que de le générer artificiellement
   dans `generate_data.py`, je l'ai dérivé dans `transform_payments()`
   à partir de `orders.total_amount` (déjà calculé). Raison : le montant
   payé DOIT toujours égaler le total de la commande — le calculer à
   partir d'une seule source de vérité évite que les deux valeurs
   divergent un jour.

## Ce que tu dois comprendre avant la Phase 3

1. **Pourquoi LOAD ne fait aucune transformation** — séparer lecture et
   logique évite de mélanger "erreur de source" et "erreur de traitement".
2. **La différence entre CLEAN et VALIDATE** — clean corrige la *forme*
   (casse, espaces, types) ; validate vérifie le *fond* (règles métier,
   cohérence référentielle). Une ligne peut être bien formée mais quand
   même invalide (ex: email bien formaté mais rattaché à un client qui
   n'existe pas).
3. **Pourquoi l'insertion se fait dans une transaction** (`engine.begin()`)
   — pour garantir que la base ne se retrouve jamais dans un état à
   moitié cohérent si une erreur survient en cours de route.
4. **Pourquoi `total_amount` et `payments.amount` sont calculés, pas
   stockés en dur** — une donnée dérivée doit toujours venir d'une seule
   source de vérité.

## Prochaine étape

Une fois que tu as lancé le pipeline et vérifié les compteurs de lignes,
on passe à la **Phase 3 : construire le Data Warehouse** (schéma en
étoile avec `FACT_SALES`, `DIM_CUSTOMER`, `DIM_PRODUCT`, `DIM_DATE`) pour
répondre à de vraies questions business (ventes mensuelles, top produits,
top clients...).
