from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()

# Blacklist pour les tokens invalidés
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """
    Vérifie si le token JWT est dans la blacklist.
    Retourne True si le token est invalide (déconnecté).

    Un token de réinitialisation de mot de passe (purpose "reset") est aussi refusé :
    il ne doit servir qu'à /auth/reset-password, jamais à accéder à l'API.
    """
    return jwt_payload["jti"] in blacklist or jwt_payload.get("purpose") == "reset"
