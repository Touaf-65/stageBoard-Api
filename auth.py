"""
auth.py - Gestion de l'authentification
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, decode_token, get_jwt, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from flask import current_app
from extensions import db, mail
from models import Users, find_user_by_email, is_token_revoked, revoke_token
from forms import RegisterForm, LoginForm, json_body, normalize_email, PASSWORD_MIN, PASSWORD_MAX
from config import Frontend_Config

auth_bp = Blueprint('auth', __name__)

# Hash factice : la connexion avec un email inconnu prend le même temps qu'avec un
# email existant (sinon le temps de réponse révèle quels comptes existent)
_DUMMY_HASH = generate_password_hash("mot-de-passe-factice")

RESET_REQUEST_MSG = "Si un compte est associé à cet email, un lien de réinitialisation vient d'être envoyé."


# ============================
# ROUTE INSCRIPTION
# ============================
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit un nouvel utilisateur.

    - Vérifie si l'email existe déjà.
    - Hash le mot de passe avec Werkzeug.
    - Crée un nouvel utilisateur en base.
    - Retourne un message JSON de succès ou d'erreur.
    """
    form = RegisterForm()

    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        # Message explicite gardé pour l'ergonomie ; l'énumération est freinée
        # par la limite de débit de nginx sur /api/auth/register (3/min par IP)
        if find_user_by_email(email):
            return jsonify({"msg": "Cet email est déjà utilisé"}), 400

        hashed_pw = generate_password_hash(form.password.data)
        user = Users(
            email=email,
            mot_de_passe=hashed_pw,
            nom="",
            prenom=""
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({"msg": "Utilisateur créé avec succès"}), 201

    return jsonify({"errors": form.errors}), 400


# ============================
# ROUTE CONNEXION
# ============================
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte un utilisateur existant.

    - Vérifie l'email et le mot de passe.
    - Génère un token JWT si les informations sont correctes et le pose dans un cookie
      HttpOnly (illisible par JavaScript), avec le cookie CSRF associé.
    - Retourne l'email, l'ID utilisateur et l'expiration de la session (timestamp en
      secondes), mais pas le token.
    """
    form = LoginForm()

    if form.validate_on_submit():
        user = find_user_by_email(form.email.data)

        password_ok = check_password_hash(user.mot_de_passe if user else _DUMMY_HASH, form.password.data)
        if not user or not password_ok:
            return jsonify({"msg": "Email ou mot de passe incorrect"}), 401

        # "pwd" : empreinte du mot de passe, la session est révoquée s'il change
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email, "pwd": user.password_fingerprint}
        )

        response = jsonify({
            "email": user.email,
            "userId": user.id,
            "expiresAt": decode_token(access_token)["exp"]
        })
        # Cookies de même durée que le token (sinon 1 an par défaut avec JWT_SESSION_COOKIE = False)
        max_age = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
        set_access_cookies(response, access_token, max_age=max_age)
        return response, 200

    return jsonify({"errors": form.errors}), 400


# ============================
# MOT DE PASSE OUBLIÉ - DEMANDE
# ============================
@auth_bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    """
    Envoie un email de réinitialisation de mot de passe.

    - Reçoit un email en JSON.
    - Répond toujours le même message, que le compte existe ou non (pas d'énumération).
    - Génère un token JWT valable 10 minutes (identity = user.id en string).
    - Envoie un lien de réinitialisation par email.
    """
    user = find_user_by_email(json_body().get("email"))
    if not user:
        return jsonify({"msg": RESET_REQUEST_MSG}), 200

    # purpose "reset" : refusé comme token d'accès (voir extensions.check_if_token_revoked)
    # pwd : le lien devient invalide dès que le mot de passe a changé (usage unique)
    reset_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=10),
        additional_claims={"purpose": "reset", "pwd": user.password_fingerprint}
    )
    reset_link = f"{Frontend_Config.URL}/auth/new-password?token={reset_token}"

    msg = Message(
        subject="Réinitialisation de mot de passe - StageBoard",
        recipients=[user.email]
    )
    msg.body = f"""
Bonjour,

Vous avez demandé à réinitialiser votre mot de passe.
Cliquez sur ce lien pour continuer : {reset_link}

Ce lien expire dans 10 minutes.
"""
    try:
        mail.send(msg)
    except Exception:
        # Erreur SMTP journalisée côté serveur, même réponse au client
        current_app.logger.exception("Envoi de l'email de réinitialisation impossible")

    return jsonify({"msg": RESET_REQUEST_MSG}), 200


# ============================
# MOT DE PASSE OUBLIÉ - RÉINITIALISATION
# ============================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Réinitialise le mot de passe d'un utilisateur.

    - Reçoit le token et le nouveau mot de passe en JSON.
    - Décode le token JWT manuellement avec la clé secrète.
    - Vérifie que le token est valide, non expiré, destiné à la réinitialisation (purpose "reset") et pas déjà utilisé.
    - Vérifie le nouveau mot de passe (6 caractères min., identique à la confirmation).
    - Hash le nouveau mot de passe avec Werkzeug et met à jour l'utilisateur.
    - Invalide le token (usage unique).
    - Retourne un message JSON de succès ou d'erreur.
    """
    data = json_body()
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not isinstance(token, str) or not isinstance(new_password, str) or not token or not new_password:
        return jsonify({"msg": "Token et nouveau mot de passe requis"}), 400
    if not PASSWORD_MIN <= len(new_password) <= PASSWORD_MAX:
        return jsonify({"msg": f"Le mot de passe doit contenir entre {PASSWORD_MIN} et {PASSWORD_MAX} caractères."}), 400
    if confirm_password is not None and confirm_password != new_password:
        return jsonify({"msg": "Les mots de passe ne correspondent pas."}), 400

    import jwt

    try:
        secret = current_app.config['JWT_SECRET_KEY']
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = payload.get('sub')
        if not user_id:
            return jsonify({"msg": "Token invalide (pas d'identifiant)"}), 400
        user_id = int(user_id)  # conversion en entier
    except jwt.ExpiredSignatureError:
        return jsonify({"msg": "Le lien a expiré. Refaites une demande."}), 400
    except (jwt.InvalidTokenError, ValueError):
        return jsonify({"msg": "Lien invalide. Refaites une demande."}), 400

    # Un token de session ne doit pas permettre de changer le mot de passe,
    # et un lien de réinitialisation ne sert qu'une fois : son empreinte "pwd"
    # ne correspond plus dès que le mot de passe a été changé
    user = db.session.get(Users, user_id)
    if (payload.get("purpose") != "reset" or is_token_revoked(payload.get('jti'))
            or not user or payload.get("pwd") != user.password_fingerprint):
        return jsonify({"msg": "Lien invalide ou déjà utilisé. Refaites une demande."}), 400

    # Nouveau mot de passe et révocation du lien dans la même transaction
    user.mot_de_passe = generate_password_hash(new_password)
    revoke_token(payload, commit=False)
    db.session.commit()

    return jsonify({"msg": "Mot de passe réinitialisé avec succès"}), 200


# ============================
# ROUTE DECONNEXION
# ============================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Déconnecte l'utilisateur en invalidant son token JWT.

    - Si le token est valide, l'enregistre (jti, expiration) dans la table
      revoked_tokens : il est refusé par tous les workers, y compris après un redémarrage.
    - Supprime toujours les cookies, même si le token est déjà expiré ou révoqué
      (sinon le navigateur garderait un cookie inutilisable).
    - Retourne un message JSON de confirmation.
    """
    try:
        verify_jwt_in_request()
        revoke_token(get_jwt())
    except (JWTExtendedException, PyJWTError):
        pass  # token absent, expiré ou déjà révoqué : rien à révoquer

    response = jsonify({"msg": "Déconnecté avec succès"})
    unset_jwt_cookies(response)
    return response, 200
