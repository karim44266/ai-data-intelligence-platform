# Phase 1 — Fondation PostgreSQL

## Comment lancer la base

```bash
docker-compose up -d
```

Ça télécharge PostgreSQL 16, crée le conteneur, et exécute automatiquement
`sql/01_schema.sql` au premier démarrage (grâce au volume monté sur
`/docker-entrypoint-initdb.d`).

## Comment vérifier que ça a marché

```bash
docker exec -it ecommerce_db psql -U ecommerce_user -d ecommerce -c "\dt"
```

`\dt` liste les tables. Tu dois voir : customers, products, orders,
order_items, payments, reviews.

Pour explorer une table :
```bash
docker exec -it ecommerce_db psql -U ecommerce_user -d ecommerce -c "\d customers"
```
`\d nom_table` montre les colonnes, types, et contraintes (PK, FK, CHECK...)
— utile pour vérifier que le schéma correspond à ce qu'on a écrit.

## Ce que tu dois comprendre avant de passer à la Phase 2

1. **Pourquoi `order_items` existe** — sans elle, impossible de savoir
   quels produits sont dans quelle commande (relation N-N).
2. **La différence entre PK et FK** — une PK identifie une ligne de
   façon unique dans SA table ; une FK pointe vers la PK d'une AUTRE
   table pour créer un lien.
3. **Pourquoi `unit_price` est dupliqué dans `order_items`** au lieu
   d'aller chercher `products.price` — pour figer le prix au moment
   de l'achat (l'historique ne doit jamais changer rétroactivement).
4. **Pourquoi les CHECK constraints** (`price >= 0`, `rating BETWEEN 1
   AND 5`) sont dans la base et pas seulement dans le code Python —
   défense en profondeur : même un bug ou un accès direct à la base
   ne peut pas insérer des données invalides.

## Prochaine étape

Une fois que tu as lancé `docker-compose up -d` et vérifié les 6 tables
avec `\dt`, dis-le moi et on passe à la **Phase 2 : générer/charger le
dataset e-commerce, puis écrire le pipeline ETL Python** (load → clean →
validate → transform → save).
