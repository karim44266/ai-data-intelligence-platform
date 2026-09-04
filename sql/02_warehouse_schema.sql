-- ============================================================
-- PHASE 3 : DATA WAREHOUSE - SCHEMA EN ETOILE
-- ============================================================
-- FACT_SALES = un evenement mesurable (une ligne vendue).
-- DIM_* = le contexte descriptif de chaque fait.
-- Contrairement au schema OLTP (Phase 1), on tolere ici de la
-- redondance (ex: nom du produit repete) car l'objectif est la
-- VITESSE DE LECTURE, pas l'integrite d'ecriture.

CREATE TABLE dim_customer (
    customer_key    SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL UNIQUE, -- reference vers la source OLTP
    full_name       VARCHAR(200),
    country         VARCHAR(100),
    signup_date     DATE
);

CREATE TABLE dim_product (
    product_key     SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL UNIQUE,
    product_name    VARCHAR(255),
    category        VARCHAR(100)
);

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,   -- format YYYYMMDD
    full_date       DATE NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    quarter         INTEGER NOT NULL,
    day_of_week     VARCHAR(20) NOT NULL
);

CREATE TABLE fact_sales (
    sale_id         SERIAL PRIMARY KEY,
    date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key    INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    line_total      NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
