# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Pourquoi python:3.12-slim et pas python:3.12 (l'image complete) :
# l'image complete inclut des outils de compilation et des
# librairies dont on n'a pas besoin en production -- slim reduit
# la taille de l'image finale de plusieurs centaines de Mo, ce qui
# accelere le deploiement et reduit la surface d'attaque.

WORKDIR /app

# On copie D'ABORD requirements.txt seul, PUIS on installe, PUIS
# seulement ensuite on copie le reste du code. Pourquoi cet ordre
# precis : Docker met en cache chaque etape (layer). Si on copiait
# tout le code avant d'installer les dependances, le moindre
# changement dans un fichier .py obligerait a tout reinstaller.
# En separant, `pip install` ne se relance que si requirements.txt
# change -- les rebuilds during dev sont donc bien plus rapides.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ .

# Le modele ML entraine en Phase 5 doit etre present pour que
# l'endpoint /ml/churn fonctionne. Comme le contexte de build est
# maintenant la racine du projet (voir docker-compose.yml), ce
# chemin est relatif a la racine, pas au dossier backend/.
COPY ml/models/churn_model.joblib /app/ml_models/churn_model.joblib

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
