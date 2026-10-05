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

    Sont aussi refusés :
    - un token de réinitialisation de mot de passe (purpose "reset") : il ne sert
      qu'à /auth/reset-password, jamais à accéder à l'API ;
    - le token d'un compte supprimé ;
    - un token émis avant le dernier changement de mot de passe (claim "pwd"
      différent de l'empreinte actuelle) : changer son mot de passe ferme les
      autres sessions. Un token sans claim "pwd" (émis avant ce contrôle) est refusé.
    """
    if jwt_payload["jti"] in blacklist or jwt_payload.get("purpose") == "reset":
        return True

    from models import Users  # import local : models importe extensions
    try:
        user = db.session.get(Users, int(jwt_payload["sub"]))
    except (KeyError, TypeError, ValueError):
        return True
    return user is None or jwt_payload.get("pwd") != user.password_fingerprint
