"""
main.py
=======
Point d'entree de l'API. Lance avec : uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import customers, products, analytics, auth_router, ml

app = FastAPI(
    title="AI Data Intelligence Platform API",
    description="API pour explorer les clients, produits, ventes et predictions ML",
    version="1.0.0",
)

# CORS : sans ca, un frontend React tournant sur un port different
# (ex: localhost:3000) verrait ses requetes vers l'API (localhost:8000)
# bloquees par le navigateur (politique de securite "same-origin").
# En Phase 6.2 (frontend), c'est ce middleware qui rendra la
# communication possible.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # a restreindre a l'URL exacte du frontend en production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(auth_router.router)
app.include_router(ml.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
