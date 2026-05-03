import os
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://stageboard_user:2fE4dmgpmSRl2QmcwPj4oAOrhncu0c@db:3306/stageboard_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,             # Détection connexions mortes
        "pool_recycle": 3600,              # Recyclage connexions
        "connect_args": {"ssl": {"ssl_mode": "REQUIRED"}}  # TLS MySQL
    }

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cle-jwt-ultra-secrete")
    WTF_CSRF_ENABLED = False
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
    JWT_COOKIE_SECURE = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)