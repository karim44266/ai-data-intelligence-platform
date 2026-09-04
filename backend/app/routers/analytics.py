"""
routers/analytics.py
=====================
Pourquoi ces endpoints interrogent fact_sales (le Data Warehouse,
Phase 3) et pas orders/order_items directement : meme raison qu'en
Phase 4 pour Power BI -- le warehouse est deja optimise pour ce
genre d'agregation, pas besoin de refaire les jointures a chaque
appel API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/monthly-revenue")
def monthly_revenue(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT dd.year, dd.month, ROUND(SUM(fs.line_total), 2) AS revenue
        FROM fact_sales fs
        JOIN dim_date dd ON dd.date_key = fs.date_key
        GROUP BY dd.year, dd.month
        ORDER BY dd.year, dd.month
    """)).fetchall()
    return [{"year": r.year, "month": r.month, "revenue": float(r.revenue)} for r in rows]


@router.get("/top-products")
def top_products(limit: int = 10, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT dp.product_name, SUM(fs.line_total) AS revenue
        FROM fact_sales fs
        JOIN dim_product dp ON dp.product_key = fs.product_key
        GROUP BY dp.product_name
        ORDER BY revenue DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()
    return [{"product_name": r.product_name, "revenue": float(r.revenue)} for r in rows]
