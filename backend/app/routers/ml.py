"""
routers/ml.py
==============
Sert les predictions du modele de churn (Phase 5.1) via l'API.

Pourquoi recalculer les features ici plutot que de les lire dans
une table deja remplie : en production, on veut une prediction a
jour au moment de l'appel, pas une valeur figee calculee la veille.
On refait donc le meme calcul que dans churn_features.py, mais
directement en SQL pour un seul client (plus rapide que de charger
tout un DataFrame pandas pour une seule ligne).

Pourquoi le modele est charge une seule fois (variable globale
_model) et pas a chaque requete : charger un fichier .joblib depuis
le disque prend du temps (quelques dizaines de millisecondes). Le
refaire a CHAQUE appel API ralentirait inutilement chaque requete --
on le charge une fois au premier appel, puis on le reutilise.
"""

import os

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import require_role
from database import get_db

router = APIRouter(prefix="/ml", tags=["ml"])

# Chemin configurable via variable d'environnement : en local, le
# defaut (chemin relatif) fonctionne tel quel avec la structure de
# dossiers du projet. Dans le conteneur Docker (Phase 7), le
# Dockerfile place le modele ailleurs et fixe CHURN_MODEL_PATH en
# consequence -- le code n'a pas besoin de changer entre les deux
# environnements, seule la variable d'environnement differe.
MODEL_PATH = os.environ.get("CHURN_MODEL_PATH", "../../ml/models/churn_model.joblib")
FEATURES = ["frequency", "total_spent", "tenure_days", "avg_order_value"]

_model = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


@router.get("/churn/{customer_id}")
def predict_churn(
    customer_id: int,
    db: Session = Depends(get_db),
    # require_role(["admin"]) : seul un utilisateur avec le role
    # "admin" peut appeler cet endpoint. Un "viewer" authentifie
    # recevra un 403, pas un 401 -- il EST identifie, il n'a juste
    # pas la permission.
    user: dict = Depends(require_role(["admin"])),
):
    row = db.execute(text("""
        SELECT
            c.signup_date,
            COUNT(o.order_id) AS frequency,
            COALESCE(SUM(o.total_amount), 0) AS total_spent,
            MAX(o.order_date)::DATE AS last_order_date,
            (SELECT MAX(order_date)::DATE FROM orders) AS reference_date
        FROM customers c
        LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.status != 'cancelled'
        WHERE c.customer_id = :cid
        GROUP BY c.customer_id, c.signup_date
    """), {"cid": customer_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Client introuvable")

    tenure_days = (row["reference_date"] - row["signup_date"]).days
    recency_days = (
        (row["reference_date"] - row["last_order_date"]).days
        if row["last_order_date"] else tenure_days
    )
    frequency = row["frequency"] or 0
    total_spent = float(row["total_spent"] or 0)
    avg_order_value = total_spent / frequency if frequency else 0

    X = pd.DataFrame([{
        "frequency": frequency,
        "total_spent": total_spent,
        "tenure_days": tenure_days,
        "avg_order_value": avg_order_value,
    }])
    model = get_model()
    proba = float(model.predict_proba(X[FEATURES])[0][1])

    # Memes regles de lisibilite que dans train_churn_model.py --
    # on duplique volontairement cette petite logique plutot que de
    # faire dependre l'API du dossier ml/ (l'API ne doit dependre
    # que du modele entraine, pas du code d'entrainement).
    reasons = []
    if recency_days > 120:
        reasons.append(f"Aucun achat depuis {recency_days} jours")
    if frequency <= 2:
        reasons.append("Tres peu de commandes au total")
    if avg_order_value < 100:
        reasons.append("Faible valeur moyenne de commande")
    if not reasons:
        reasons.append("Combinaison de plusieurs facteurs mineurs")

    return {
        "customer_id": customer_id,
        "churn_probability": round(proba, 3),
        "reasons": reasons,
    }
