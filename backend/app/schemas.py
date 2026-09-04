"""
schemas.py
==========
Schemas Pydantic : definissent EXACTEMENT la forme des donnees
qui entrent et sortent de l'API.

Pourquoi separer ca des modeles SQLAlchemy (models.py) : un modele
ORM represente la table telle qu'elle existe en base, mais on ne
veut pas forcement exposer TOUTES ses colonnes a l'exterieur (ex:
on pourrait avoir un mot de passe hache en base qu'on ne veut
jamais renvoyer dans une reponse API). Separer modele et schema
donne ce controle precis sur ce qui sort.

`from_attributes = True` dans chaque Config permet a Pydantic de
lire directement un objet SQLAlchemy (customer.first_name) au lieu
d'exiger un dictionnaire -- sans ca, on devrait convertir
manuellement chaque objet avant de le renvoyer.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CustomerOut(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    email: str
    country: str | None
    signup_date: date

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    product_id: int
    product_name: str
    category: str
    price: Decimal
    stock_quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    order_id: int
    customer_id: int
    order_date: datetime
    status: str
    total_amount: Decimal

    class Config:
        from_attributes = True


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float
