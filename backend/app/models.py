"""
models.py
=========
Modeles ORM (Object-Relational Mapping) : chaque classe Python
represente une table existante (creee en Phase 1). L'ORM permet
d'ecrire `db.query(Customer).filter(...)` au lieu du SQL brut --
plus sur (SQLAlchemy echappe automatiquement les valeurs, ce qui
protege contre l'injection SQL) et plus facile a maintenir.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    country = Column(String)
    signup_date = Column(Date)


class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String)
    category = Column(String)
    price = Column(Numeric)
    stock_quantity = Column(Integer)


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    order_date = Column(DateTime)
    status = Column(String)
    total_amount = Column(Numeric)
    items = relationship("OrderItem", backref="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer)
    unit_price = Column(Numeric)
