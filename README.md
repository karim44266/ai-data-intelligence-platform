# AI-Powered Data Intelligence Platform

Plateforme e-commerce de bout en bout : d'une base de données relationnelle brute jusqu'à des prédictions de Machine Learning servies via une API sécurisée et une interface web — le tout orchestré par Docker.

Projet construit pour couvrir le profil **GLID** (Génie Logiciel & Informatique Décisionnelle) : ingénierie logicielle, bases de données, informatique décisionnelle (BI), science des données / IA, et DevOps.

## Architecture

```
 DATA SOURCES (Faker)
         |
         v
   ETL PIPELINE (Python / pandas)
         |
         v
   POSTGRESQL (schema OLTP normalise)
         |
         +----------------------------+
         v                            v
   DATA WAREHOUSE               MODELES ML
   (schema en etoile)           (churn, ventes, segmentation)
         |                            |
         v                            v
     POWER BI                   FASTAPI (REST + JWT/RBAC)
                                       |
                                       v
                                 REACT (dashboard web)

Tout le stack (DB + backend + frontend) est conteneurise via
Docker Compose et verifie automatiquement par CI/CD (GitHub Actions).
```

## Stack technique

| Domaine | Technologies |
|---|---|
| Base de données | PostgreSQL 16, schéma OLTP normalisé + Data Warehouse en étoile |
| ETL | Python, pandas, SQLAlchemy |
| BI | Power BI |
| Machine Learning | scikit-learn (classification, régression, clustering) |
| Backend | FastAPI, JWT (authentification), RBAC (rôles admin/viewer) |
| Frontend | React (Vite), Recharts |
| Infrastructure | Docker, Docker Compose, GitHub Actions (CI) |

## Fonctionnalités

- **Pipeline ETL** robuste : extraction, nettoyage, validation et chargement de données e-commerce, avec gestion des doublons, valeurs manquantes et incohérences
- **Data Warehouse** en schéma étoile (`fact_sales`, `dim_customer`, `dim_product`, `dim_date`) pour des requêtes analytiques rapides
- **3 modèles de Machine Learning** :
  - Prédiction de churn (classification, avec raisons explicables)
  - Prévision des ventes mensuelles (série temporelle)
  - Segmentation clients en 4 profils (VIP / Regular / Occasional / At-risk)
- **API REST sécurisée** avec authentification JWT et contrôle d'accès par rôle (les prédictions de churn sont réservées aux comptes admin)
- **Dashboard web** consommant l'API en temps réel

## Lancer le projet

Prérequis : [Docker](https://www.docker.com/) et Docker Compose.

```bash
git clone <url-du-repo>
cd data-intelligence-platform
docker-compose up --build
```

- Frontend : http://localhost:5173
- API + documentation interactive : http://localhost:8000/docs
- Comptes de test : `admin` / `admin123` (accès complet) ou `viewer` / `viewer123` (accès restreint)

## Structure du projet

```
data-intelligence-platform/
├── sql/          # Schemas PostgreSQL (OLTP + Data Warehouse)
├── etl/          # Generation de donnees + pipeline ETL
├── ml/           # Entrainement des modeles (churn, ventes, segmentation)
├── backend/      # API FastAPI (auth JWT, RBAC, endpoints ML)
├── frontend/     # Interface React (Vite)
├── docs/         # Notes techniques par phase
└── .github/      # Pipeline CI (GitHub Actions)
```

## CI/CD

Chaque `push` déclenche automatiquement :
- le démarrage du backend contre une vraie base PostgreSQL (smoke test)
- le build de production du frontend

Voir `.github/workflows/ci.yml`.
