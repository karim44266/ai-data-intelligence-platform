"""
auth.py
=======
Authentification par JWT (JSON Web Token) + controle d'acces par
role (RBAC).

Pourquoi des utilisateurs "en dur" ici (FAKE_USERS_DB) : en vrai
projet, ce serait une table `users` en base avec des mots de passe
HACHES (jamais stockes en clair). On simplifie ici pour rester
concentre sur le mecanisme d'authentification lui-meme, qui est
identique quelle que soit la source des utilisateurs.
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# En production, SECRET_KEY doit venir d'une variable d'environnement,
# jamais du code source -- sinon n'importe qui avec acces au code
# (ou au repo GitHub) pourrait forger des tokens valides.
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-only-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    # bcrypt directement plutot que via passlib : certaines versions
    # recentes de la librairie bcrypt cassent la couche de compatibilite
    # de passlib (bug connu). Utiliser bcrypt sans intermediaire evite
    # ce probleme, pour un resultat strictement equivalent.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Mots de passe HACHES au demarrage, jamais stockes en clair meme ici.
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
    },
    "viewer": {
        "username": "viewer",
        "hashed_password": hash_password("viewer123"),
        "role": "viewer",
    },
}


def authenticate_user(username: str, password: str):
    user = FAKE_USERS_DB.get(username)
    # On ne compare JAMAIS deux mots de passe en clair avec `==`,
    # car ce serait vulnerable aux attaques par timing et supposerait
    # qu'on stocke le mot de passe original (ce qu'il ne faut jamais faire).
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expires",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"username": username, "role": role}


def require_role(allowed_roles: list[str]):
    """Retourne une dependance FastAPI qui verifie le role de
    l'utilisateur APRES avoir verifie son identite. Deux etapes
    distinctes et volontairement separees : 401 (pas identifie) est
    une erreur differente de 403 (identifie, mais pas autorise) --
    un vrai client d'API a besoin de cette distinction pour reagir
    correctement (redemander une connexion vs afficher "acces refuse").
    """
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Ce role ({user['role']}) n'a pas acces a cette ressource",
            )
        return user
    return role_checker
