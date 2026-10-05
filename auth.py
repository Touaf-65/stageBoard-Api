"""
auth.py - Gestion de l'authentification
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from extensions import db, mail, blacklist
from models import Users
from forms import RegisterForm, LoginForm
from config import Frontend_Config

auth_bp = Blueprint('auth', __name__)

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
        if Users.query.filter_by(email=form.email.data).first():
            return jsonify({"msg": "Cet email est déjà utilisé"}), 400

        hashed_pw = generate_password_hash(form.password.data)
        user = Users(
            email=form.email.data,
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
    - Génère un token JWT si les informations sont correctes.
    - Retourne le token, l'email et l'ID utilisateur.
    """
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()

        if not user or not check_password_hash(user.mot_de_passe, form.password.data):
            return jsonify({"msg": "Email ou mot de passe incorrect"}), 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email}
        )

        return jsonify({
            "token": access_token,
            "email": user.email,
            "userId": user.id
        }), 200

    return jsonify({"errors": form.errors}), 400


# ============================
# MOT DE PASSE OUBLIÉ - DEMANDE
# ============================
@auth_bp.route('/reset-password-request', methods=['POST'])
def reset_password_request():
    """
    Envoie un email de réinitialisation de mot de passe.

    - Reçoit un email en JSON.
    - Vérifie si l'utilisateur existe (mais ne révèle pas l'info pour la sécurité).
    - Génère un token JWT valable 10 minutes (identity = user.id en string).
    - Envoie un lien de réinitialisation par email.
    - Retourne un message JSON de confirmation.
    """
    data = request.get_json()
    email = data.get("email")

    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "Si cet email existe, vous recevrez un lien"}), 200

    # purpose "reset" : refusé comme token d'accès (voir extensions.check_if_token_revoked)
    reset_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=10),
        additional_claims={"purpose": "reset"}
    )
    reset_link = f"{Frontend_Config.URL}/auth/new-password?token={reset_token}"

    msg = Message(
        subject="Réinitialisation de mot de passe - StageBoard",
        recipients=[email]
    )
    msg.body = f"""
Bonjour,

Vous avez demandé à réinitialiser votre mot de passe.
Cliquez sur ce lien pour continuer : {reset_link}

Ce lien expire dans 10 minutes.
"""
    mail.send(msg)

    return jsonify({"msg": "Lien de réinitialisation envoyé par email"}), 200


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
    data = request.get_json() or {}
    token = data.get("token")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not token or not new_password:
        return jsonify({"msg": "Token et nouveau mot de passe requis"}), 400
    if len(new_password) < 6:
        return jsonify({"msg": "Le mot de passe doit contenir au moins 6 caractères."}), 400
    if confirm_password is not None and confirm_password != new_password:
        return jsonify({"msg": "Les mots de passe ne correspondent pas."}), 400

    import jwt
    from flask import current_app

    try:
        secret = current_app.config['JWT_SECRET_KEY']
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        user_id = payload.get('sub')
        if not user_id:
            return jsonify({"msg": "Token invalide (pas d'identifiant)"}), 400
        user_id = int(user_id)  # conversion en entier
    except jwt.ExpiredSignatureError:
        return jsonify({"msg": "Le lien a expiré. Refaites une demande."}), 400
    except jwt.InvalidTokenError as e:
        return jsonify({"msg": f"Lien invalide : {str(e)}"}), 400

    # Un token de session ne doit pas permettre de changer le mot de passe,
    # et un lien de réinitialisation ne sert qu'une fois
    if payload.get("purpose") != "reset" or payload.get('jti') in blacklist:
        return jsonify({"msg": "Lien invalide ou déjà utilisé. Refaites une demande."}), 400

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"msg": "Utilisateur introuvable"}), 404

    user.mot_de_passe = generate_password_hash(new_password)
    db.session.commit()
    blacklist.add(payload['jti'])

    return jsonify({"msg": "Mot de passe réinitialisé avec succès"}), 200


# ============================
# ROUTE DECONNEXION
# ============================
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte l'utilisateur en invalidant son token JWT.

    - Récupère l'identifiant unique du token (jti).
    - Ajoute ce jti à une blacklist.
    - Retourne un message JSON de confirmation.
    """
    jti = get_jwt()["jti"]  
    blacklist.add(jti)
    return jsonify({"msg": "Déconnecté avec succès"}), 200
