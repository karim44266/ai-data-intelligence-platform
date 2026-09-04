"""
routers/customers.py
=====================
Pourquoi un fichier par domaine (customers, products, orders...)
plutot qu'un seul gros fichier main.py : a 5-10 endpoints, un seul
fichier est encore lisible. A 50+, un fichier unique devient
ingerable. On prend l'habitude de separer des maintenant --
c'est aussi plus facile a tester independamment.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Customer
from schemas import CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerOut])
def list_customers(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    # le=200 : plafonne la taille de page cote serveur. Sans ca,
    # un client de l'API pourrait demander limit=1000000 et
    # surcharger la base -- on garde le controle cote serveur,
    # jamais confiance dans ce que le client demande.
    country: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if country:
        query = query.filter(Customer.country == country)
    return query.offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        # 404 explicite plutot que de renvoyer None silencieusement --
        # le client de l'API doit pouvoir distinguer "trouve mais
        # vide" de "n'existe pas du tout".
        raise HTTPException(status_code=404, detail="Client introuvable")
    return customer
