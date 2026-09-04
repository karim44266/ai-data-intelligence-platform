"""
load_warehouse.py
==================
Remplit le Data Warehouse (star schema) a partir des tables OLTP
deja peuplees en Phase 2. C'est un ETL "interne" (base -> base),
pas CSV -> base comme en Phase 2.
"""

from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg://ecommerce_user:ecommerce_pass@localhost:5455/ecommerce"


def run():
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        # DIM_DATE : generee une fois, couvre une plage large.
        conn.execute(text("""
            INSERT INTO dim_date (date_key, full_date, year, month, month_name, quarter, day_of_week)
            SELECT
                TO_CHAR(d, 'YYYYMMDD')::INT,
                d::DATE,
                EXTRACT(YEAR FROM d)::INT,
                EXTRACT(MONTH FROM d)::INT,
                TO_CHAR(d, 'Month'),
                EXTRACT(QUARTER FROM d)::INT,
                TO_CHAR(d, 'Day')
            FROM generate_series('2023-01-01'::DATE, '2027-12-31'::DATE, '1 day') AS d
            ON CONFLICT (date_key) DO NOTHING
        """))

        conn.execute(text("""
            INSERT INTO dim_customer (customer_id, full_name, country, signup_date)
            SELECT customer_id, first_name || ' ' || last_name, country, signup_date
            FROM customers
            ON CONFLICT (customer_id) DO NOTHING
        """))

        conn.execute(text("""
            INSERT INTO dim_product (product_id, product_name, category)
            SELECT product_id, product_name, category
            FROM products
            ON CONFLICT (product_id) DO NOTHING
        """))

        conn.execute(text("""
            INSERT INTO fact_sales (date_key, customer_key, product_key, quantity, unit_price, line_total)
            SELECT
                TO_CHAR(o.order_date, 'YYYYMMDD')::INT,
                dc.customer_key,
                dp.product_key,
                oi.quantity,
                oi.unit_price,
                oi.quantity * oi.unit_price
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            JOIN dim_customer dc ON dc.customer_id = o.customer_id
            JOIN dim_product dp ON dp.product_id = oi.product_id
            WHERE o.status != 'cancelled'
        """))
    print("Data Warehouse rempli avec succes.")


if __name__ == "__main__":
    run()
