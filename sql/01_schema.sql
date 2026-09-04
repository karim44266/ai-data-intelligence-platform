-- ============================================================
-- PHASE 1 : SCHEMA RELATIONNEL - E-COMMERCE
-- ============================================================
-- Principe directeur : NORMALISATION
-- Chaque fait est stocké UNE SEULE FOIS. On ne répète jamais
-- une information (ex: l'email d'un client) dans plusieurs
-- lignes. On la stocke une fois dans "customers" et on y fait
-- référence ailleurs via une clé étrangère (customer_id).
--
-- Pourquoi c'est important : si tu dupliques les données et
-- qu'un client change d'email, tu dois le changer à 50 endroits
-- au lieu d'un seul -> source de bugs et d'incohérences.
-- ============================================================

-- ------------------------------------------------------------
-- TABLE: customers
-- ------------------------------------------------------------
-- Chaque client existe UNE fois. C'est la table "racine" dont
-- dépendent les commandes et les avis.
CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    -- SERIAL = entier auto-incrémenté. On l'utilise comme clé
    -- primaire (PK) plutôt que l'email, car un email peut
    -- techniquement changer, alors qu'un ID ne change jamais.
    -- Une PK doit être stable et immuable.
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    -- UNIQUE : deux clients ne peuvent pas avoir le même email.
    -- C'est une contrainte d'intégrité, pas juste une bonne
    -- pratique : la base REFUSERA d'insérer un doublon.
    country         VARCHAR(100),
    signup_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- TABLE: products
-- ------------------------------------------------------------
CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    product_name    VARCHAR(255) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    price           NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    -- NUMERIC(10,2) plutôt que FLOAT : pour de l'argent, on
    -- évite les flottants (erreurs d'arrondi binaire type
    -- 0.1 + 0.2 != 0.3). NUMERIC est exact.
    -- CHECK (price >= 0) : contrainte métier direct dans la
    -- base -> impossible d'insérer un prix négatif, même si le
    -- code Python a un bug.
    stock_quantity  INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- TABLE: orders
-- ------------------------------------------------------------
-- Une commande APPARTIENT à un client -> clé étrangère customer_id.
CREATE TABLE orders (
    order_id        SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    -- REFERENCES = clé étrangère (FK). Elle dit à PostgreSQL :
    -- "cette valeur DOIT exister dans customers.customer_id".
    -- Si tu essaies d'insérer une commande pour un client
    -- inexistant, la base refuse. C'est l'intégrité référentielle.
    order_date      TIMESTAMP NOT NULL DEFAULT NOW(),
    status          VARCHAR(50) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','paid','shipped','delivered','cancelled')),
    -- CHECK avec liste de valeurs = équivalent d'un ENUM.
    -- Empêche d'avoir status = 'blah' par erreur de frappe.
    total_amount    NUMERIC(10, 2) NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- TABLE: order_items (table de JONCTION)
-- ------------------------------------------------------------
-- C'est la table la plus importante à comprendre : elle résout
-- la relation N-N entre orders et products.
-- Une commande a PLUSIEURS lignes de produits, et un produit
-- apparaît dans PLUSIEURS commandes. Sans cette table, tu ne
-- pourrais pas savoir QUELS produits sont dans QUELLE commande.
CREATE TABLE order_items (
    order_item_id   SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10, 2) NOT NULL,
    -- On COPIE le prix ici au moment de l'achat (unit_price),
    -- plutôt que d'aller chercher products.price à chaque fois.
    -- Pourquoi : si le prix du produit change demain, une
    -- commande d'hier doit garder le prix PAYÉ à l'époque.
    -- C'est un exemple volontaire de "dénormalisation" justifiée.
    UNIQUE (order_id, product_id)
    -- Empêche d'avoir deux lignes séparées pour le même produit
    -- dans la même commande (on augmenterait plutôt la quantity).
);

-- ------------------------------------------------------------
-- TABLE: payments
-- ------------------------------------------------------------
CREATE TABLE payments (
    payment_id      SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL UNIQUE REFERENCES orders(order_id),
    -- UNIQUE ici = relation 1-1 : une commande a AU PLUS un paiement.
    payment_method  VARCHAR(50) NOT NULL,
    amount          NUMERIC(10, 2) NOT NULL,
    paid_at         TIMESTAMP,
    payment_status  VARCHAR(50) NOT NULL DEFAULT 'pending'
                    CHECK (payment_status IN ('pending','completed','failed','refunded'))
);

-- ------------------------------------------------------------
-- TABLE: reviews
-- ------------------------------------------------------------
CREATE TABLE reviews (
    review_id       SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    review_date     TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id)
    -- Un client ne laisse qu'un seul avis par produit (règle métier
    -- courante). S'il veut le modifier, on fait un UPDATE, pas un
    -- nouvel INSERT.
);

-- ============================================================
-- INDEXES : pourquoi maintenant et pas plus tard ?
-- ============================================================
-- Une clé étrangère n'est PAS automatiquement indexée par
-- PostgreSQL (contrairement à la PK, qui l'est toujours).
-- Sans index, chaque JOIN sur customer_id ou product_id doit
-- scanner TOUTE la table -> lent dès que tu as des milliers
-- de lignes. On les crée dès le départ car ce sont les colonnes
-- qu'on va utiliser le plus dans les JOINs et les agrégations
-- (Phase 3 - Data Warehouse en dépend directement).

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_reviews_product_id ON reviews(product_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
-- Cet index sur order_date sert les futures requêtes du type
-- "ventes du mois dernier" (Phase 3/4).
