"""
train_churn_model.py
=====================
Entraine un classifieur binaire (churn / pas churn) sur les
features extraites par churn_features.py.

Pourquoi RandomForest et pas une regression logistique (souvent
le premier reflexe en cours) :
- Nos features ont des echelles tres differentes (total_spent en
  milliers, tenure_days en centaines, frequency en unites) --
  RandomForest ne demande pas de normaliser ces echelles, contrairement
  a la regression logistique qui y est sensible.
- Il donne directement une importance des features (quelle colonne
  pese le plus dans la decision), utile pour EXPLIQUER une
  prediction a quelqu'un (rappelle-toi le mockup du projet : on veut
  dire POURQUOI un client est a risque, pas juste un pourcentage brut).
"""

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from churn_features import extract_features

FEATURES = ["frequency", "total_spent", "tenure_days", "avg_order_value"]
# IMPORTANT : recency_days est volontairement EXCLU des features.
# C'est la colonne qui sert a DEFINIR le label is_churned (voir
# churn_features.py : is_churned = recency_days > 90). L'inclure
# dans les features serait de la "fuite de donnees" (data leakage) :
# le modele n'aurait qu'a redecouvrir ce seuil au lieu d'apprendre
# un vrai pattern de comportement. On veut qu'il apprenne a partir
# de SIGNAUX INDIRECTS (frequence, depense, anciennete) -- ceux
# qu'on aurait encore si on devait predire un risque AVANT que le
# client ne soit deja officiellement churne.
MODEL_PATH = "models/churn_model.joblib"


def train():
    df = extract_features()

    # On entraine UNIQUEMENT sur les clients dont on a un label fiable
    # (donc pas les inscrits recents, exclus dans churn_features.py).
    labeled = df.dropna(subset=["is_churned"]).copy()
    labeled["is_churned"] = labeled["is_churned"].astype(int)

    X = labeled[FEATURES]
    y = labeled["is_churned"]

    # stratify=y : garde la meme proportion de churn/non-churn dans
    # train et test. Important quand une classe est minoritaire --
    # sinon un split au hasard pourrait mettre presque tous les
    # "churned" dans un seul des deux ensembles.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        # max_depth limite volontairement la profondeur des arbres.
        # Avec seulement ~280 clients, un arbre sans limite de
        # profondeur peut "apprendre par coeur" les donnees
        # d'entrainement (overfitting) au lieu de generaliser.
        random_state=42,
        class_weight="balanced",
        # class_weight="balanced" : compense automatiquement si une
        # classe (churned/non-churned) est plus rare que l'autre,
        # pour eviter que le modele ne predise "jamais churne" par
        # facilite (ce qui donnerait une bonne accuracy mais un
        # modele inutile).
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("=" * 60)
    print("EVALUATION DU MODELE")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=["Non-churn", "Churn"]))
    print("Matrice de confusion (lignes=reel, colonnes=predit) :")
    print(confusion_matrix(y_test, y_pred))

    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
    print("\nImportance des features :")
    print(importances)

    import os
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModele sauvegarde : {MODEL_PATH}")

    return model, df


def explain_reasons(row):
    """Genere des raisons lisibles pour un client a risque, en
    comparant ses valeurs a des seuils simples. Ce n'est PAS le
    modele lui-meme qui "explique" (RandomForest ne le fait pas
    nativement) -- ce sont des regles metier separees, ecrites a
    la main, qui s'appuient sur les memes features. C'est une
    approche simple et transparente, suffisante pour un projet
    portfolio (des librairies comme SHAP existent pour une vraie
    explicabilite du modele, mais c'est hors scope ici).
    """
    reasons = []
    if row["recency_days"] > 120:
        reasons.append(f"Aucun achat depuis {int(row['recency_days'])} jours")
    if row["frequency"] <= 2:
        reasons.append("Tres peu de commandes au total")
    if row["avg_order_value"] < 100:
        reasons.append("Faible valeur moyenne de commande")
    if not reasons:
        reasons.append("Combinaison de plusieurs facteurs mineurs")
    return reasons


def show_top_risk_customers(model, df, top_n=5):
    X_all = df[FEATURES]
    df = df.copy()
    df["churn_probability"] = model.predict_proba(X_all)[:, 1]

    # On exclut les clients trop recents de ce classement : meme si
    # le modele peut leur assigner un score, ce score n'a pas de
    # sens metier pour eux (voir churn_features.py).
    eligible = df[df["tenure_days"] >= 90].sort_values("churn_probability", ascending=False)

    print("\n" + "=" * 60)
    print(f"TOP {top_n} CLIENTS A RISQUE")
    print("=" * 60)
    for _, row in eligible.head(top_n).iterrows():
        reasons = explain_reasons(row)
        print(f"\nClient #{int(row['customer_id'])}")
        print(f"  Probabilite de churn : {row['churn_probability']:.0%}")
        print(f"  Raisons :")
        for r in reasons:
            print(f"    - {r}")


if __name__ == "__main__":
    model, df = train()
    show_top_risk_customers(model, df)
