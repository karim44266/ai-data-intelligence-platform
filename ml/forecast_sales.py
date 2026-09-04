"""
forecast_sales.py
==================
Predit le revenu du mois suivant a partir de l'historique mensuel.

REGLE D'OR DES SERIES TEMPORELLES : ne JAMAIS split train/test au
hasard. Contrairement au churn (Phase 5.1) ou chaque client est
independant des autres, ici chaque mois depend de l'evolution dans
le temps. Un split aleatoire mettrait par exemple "Janvier 2026"
dans le train et "Decembre 2025" dans le test -- le modele aurait
alors appris sur le futur pour predire le passe, ce qui est
impossible en production (on n'a jamais les donnees de demain pour
predire hier). Le split doit toujours respecter l'ordre du temps :
les N derniers mois servent de test, tout le reste sert de train.
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg://ecommerce_user:ecommerce_pass@localhost:5455/ecommerce"
N_TEST_MONTHS = 3  # on teste sur les 3 derniers mois disponibles


def load_monthly_revenue():
    engine = create_engine(DB_URL)
    query = """
        SELECT
            DATE_TRUNC('month', order_date)::DATE AS month_start,
            SUM(total_amount) AS revenue
        FROM orders
        WHERE status != 'cancelled'
        GROUP BY month_start
        ORDER BY month_start
    """
    df = pd.read_sql(query, engine)
    return df


def build_features(df):
    df = df.copy()
    df["month_index"] = range(1, len(df) + 1)
    df["month_of_year"] = pd.to_datetime(df["month_start"]).dt.month

    # lag_1 / lag_2 : revenu des mois precedents. shift(1) decale la
    # colonne d'une ligne vers le bas -- la ligne de "Mars" contient
    # alors le revenu de "Fevrier". C'est la maniere standard de
    # construire des features de type "valeur passee" en pandas.
    df["lag_1"] = df["revenue"].shift(1)
    df["lag_2"] = df["revenue"].shift(2)
    df["rolling_mean_3"] = df["revenue"].shift(1).rolling(window=3).mean()

    # Les premieres lignes n'ont pas assez d'historique pour calculer
    # lag_2/rolling_mean_3 (ex: le tout premier mois n'a pas de mois
    # precedent) -> on les retire, on ne peut pas les utiliser.
    df = df.dropna().reset_index(drop=True)
    return df


def train_and_evaluate():
    raw = load_monthly_revenue()
    print(f"Historique disponible : {len(raw)} mois")
    df = build_features(raw)
    print(f"Mois utilisables apres creation des features : {len(df)}")

    features = ["month_index", "month_of_year", "lag_1", "lag_2", "rolling_mean_3"]
    X, y = df[features], df["revenue"]

    # SPLIT CHRONOLOGIQUE : les N derniers mois -> test, le reste -> train.
    # PAS de train_test_split(shuffle=True) ici, contrairement au churn.
    X_train, X_test = X.iloc[:-N_TEST_MONTHS], X.iloc[-N_TEST_MONTHS:]
    y_train, y_test = y.iloc[:-N_TEST_MONTHS], y.iloc[-N_TEST_MONTHS:]

    model = RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)

    print("\n" + "=" * 60)
    print("EVALUATION SUR LES 3 DERNIERS MOIS (donnees jamais vues)")
    print("=" * 60)
    for i, (real, pred) in enumerate(zip(y_test, y_pred)):
        month_label = df["month_start"].iloc[-N_TEST_MONTHS + i]
        print(f"  {month_label} : reel={real:,.0f}  predit={pred:,.0f}")
    print(f"\nErreur absolue moyenne (MAE)  : {mae:,.0f}")
    print(f"Erreur en pourcentage (MAPE)  : {mape:.1%}")

    # Prediction du MOIS SUIVANT (au-dela des donnees connues)
    last_row = df.iloc[-1]
    next_features = pd.DataFrame([{
        "month_index": last_row["month_index"] + 1,
        "month_of_year": (last_row["month_of_year"] % 12) + 1,
        "lag_1": last_row["revenue"],
        "lag_2": last_row["lag_1"],
        "rolling_mean_3": df["revenue"].tail(3).mean(),
    }])
    next_pred = model.predict(next_features)[0]
    print(f"\nPrevision du mois suivant : {next_pred:,.0f}")

    return model, df


if __name__ == "__main__":
    train_and_evaluate()
