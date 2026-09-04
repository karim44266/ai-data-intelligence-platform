# syntax=docker/dockerfile:1

# ETAPE 1 : build. On utilise une image Node complete UNIQUEMENT
# pour compiler le projet (npm install + npm run build produit
# des fichiers HTML/CSS/JS statiques).
FROM node:20-slim AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# ETAPE 2 : servir. Pourquoi une image separee (multi-stage build) :
# Node et tous les outils de compilation ne sont plus necessaires
# une fois le build termine -- seuls les fichiers statiques generes
# (dossier dist/) doivent partir en production. nginx:alpine est une
# image minuscule (quelques Mo) dediee a servir des fichiers
# statiques, contre plusieurs centaines de Mo pour l'image Node
# complete. Cette technique reduit drastiquement la taille finale
# de l'image (et donc le temps de deploiement).
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
