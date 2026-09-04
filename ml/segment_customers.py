"""
segment_customers.py
=====================
Clustering non-supervise (K-Means) pour regrouper les clients en
segments coherents, sans leur donner d'etiquette au depart.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from churn_features import extract_features

FEATURES = ["frequency", "total_spent", "recency_days", "avg_order_value"]
# Note : ici, PAS de probleme de fuite de donnees a eviter (contrairement
# au churn) puisqu'il n'y a pas de label a "proteger" -- on cherche juste
# a decrire les clients, pas a predire un evenement futur. recency_days
# est donc une feature totalement legitime ici.

N_CLUSTERS = 4


def show_elbow_method(X_scaled):
    """Affiche l'inertie (a quel point les clients sont proches du
    centre de leur cluster) pour differentes valeurs de K. La
    "methode du coude" consiste a chercher le point ou ajouter un
    cluster de plus n'ameliore plus beaucoup l'inertie -- au-dela,
    on decoupe juste le bruit plus finement, sans vrai gain.
    C'est informatif, mais on garde 4 pour la raison metier expliquee
    plus haut (pas seulement mathematique).
    """
    print("Methode du coude (informatif) :")
    for k in range(2, 8):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        print(f"  k={k} : inertie={km.inertia_:,.0f}")


def name_clusters(cluster_stats: pd.DataFrame) -> dict:
    """Attribue un nom lisible a chaque cluster en se basant sur ses
    caracteristiques moyennes, plutot que de coder en dur "cluster 0
    = VIP" (l'ordre des clusters change a chaque execution de K-Means,
    ce serait donc faux la moitie du temps).
    """
    names = {}
    remaining = cluster_stats.copy()

    # 1. Le cluster avec le plus de recency_days (n'a pas achete
    #    depuis longtemps) = "At-risk", peu importe le reste.
    at_risk_id = remaining["recency_days"].idxmax()
    names[at_risk_id] = "At-risk"
    remaining = remaining.drop(at_risk_id)

    # 2. Parmi les autres, celui qui depense le plus = "VIP"
    vip_id = remaining["total_spent"].idxmax()
    names[vip_id] = "VIP"
    remaining = remaining.drop(vip_id)

    # 3. Parmi les 2 restants, celui qui achete le plus souvent =
    #    "Regular", l'autre = "Occasional"
    regular_id = remaining["frequency"].idxmax()
    names[regular_id] = "Regular"
    remaining = remaining.drop(regular_id)
    for last_id in remaining.index:
        names[last_id] = "Occasional"

    return names


def run():
    df = extract_features()
    X = df[FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    show_elbow_method(X_scaled)

    model = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df["cluster"] = model.fit_predict(X_scaled)

    cluster_stats = df.groupby("cluster")[FEATURES].mean()
    cluster_stats["n_customers"] = df.groupby("cluster").size()

    names = name_clusters(cluster_stats)
    df["segment"] = df["cluster"].map(names)

    print("\n" + "=" * 60)
    print("PROFIL DE CHAQUE SEGMENT")
    print("=" * 60)
    for cluster_id, name in names.items():
        row = cluster_stats.loc[cluster_id]
        print(f"\n{name} ({int(row['n_customers'])} clients)")
        print(f"  Frequence moyenne      : {row['frequency']:.1f} commandes")
        print(f"  Depense totale moyenne : {row['total_spent']:,.0f}")
        print(f"  Jours depuis achat     : {row['recency_days']:.0f}")
        print(f"  Panier moyen           : {row['avg_order_value']:,.0f}")

    print("\n" + "=" * 60)
    print("REPARTITION")
    print("=" * 60)
    print(df["segment"].value_counts())

    return df


if __name__ == "__main__":
    run()
