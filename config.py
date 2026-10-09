import os
import warnings
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# FLASK_ENV=production est défini dans le Dockerfile
IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"


def setting(name, dev_default):
    """
    Valeur d'une variable d'environnement. En production elle est obligatoire :
    aucune valeur par défaut écrite dans le code (et donc publique sur GitHub)
    ne peut servir de secret ou d'accès à la base.
    """
    value = os.getenv(name)
    if value:
        return value
    if IS_PRODUCTION:
        raise RuntimeError(f"Variable d'environnement {name} manquante : obligatoire en production.")
    return dev_default


class Config:
    SECRET_KEY = setting("SECRET_KEY", "dev-uniquement-secret-key")
    DEBUG = False
    TESTING = False
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 Mo : au-delà, réponse 413 sans lire le corps
    SQLALCHEMY_DATABASE_URI = setting("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,             # Détection connexions mortes
        "pool_recycle": 3600,              # Recyclage connexions
    }
    if SQLALCHEMY_DATABASE_URI.startswith("mysql"):
        # TLS MySQL (option non supportée par SQLite, utilisé en local)
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"ssl": {"ssl_mode": "REQUIRED"}}

    # Avec une clé connue, n'importe qui peut fabriquer un token valide pour n'importe quel compte
    JWT_SECRET_KEY = setting("JWT_SECRET_KEY", "dev-uniquement-jwt-ne-jamais-utiliser-en-production")
    if len(JWT_SECRET_KEY) < 32:
        warnings.warn("JWT_SECRET_KEY fait moins de 32 caractères : utilisez une clé aléatoire plus longue.")
    WTF_CSRF_ENABLED = False
    WTF_I18N_ENABLED = False  # traductions WTForms intégrées (voir BaseForm.Meta.locales)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # ============================
    # CONFIGURATION EMAIL
    # ============================
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")


    SESSION_COOKIE_SECURE = True    # cookie HTTPS uniquement
    SESSION_COOKIE_HTTPONLY = True    # pas accessible en JS
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ── JWT durci ─────────────────────────────────────────────
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # ── JWT dans un cookie HttpOnly ───────────────────────────
    # Le navigateur envoie le token sans que JavaScript puisse le lire : une faille XSS
    # ne permet plus de le voler (il était auparavant dans le localStorage).
    # "headers" reste accepté pour les scripts et les tests (Authorization: Bearer).
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_ACCESS_COOKIE_PATH = "/api/"         # envoyé uniquement aux appels de l'API
    JWT_COOKIE_SAMESITE = "Strict"           # jamais envoyé depuis un autre site
    JWT_COOKIE_SECURE = IS_PRODUCTION        # HTTPS en production ; http://localhost en développement
    JWT_SESSION_COOKIE = False               # cookie persistant, durée alignée sur le token (voir auth.login)
    # Protection CSRF par double soumission, en plus de SameSite : le cookie
    # csrf_access_token (lisible par le front) doit être renvoyé dans l'en-tête X-CSRF-TOKEN
    # pour toute requête qui modifie des données (POST, PUT, DELETE…)
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_CSRF_COOKIE_PATH = "/"        # lisible depuis toutes les pages du front
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"


class Frontend_Config:
    # URL du front utilisée dans les liens envoyés par email
    # (dev : http://localhost:4200, prod : https://stagebroad.com)
    URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
