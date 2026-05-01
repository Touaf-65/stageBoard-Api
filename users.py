"""
users.py - Gestion des utilisateurs
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Users
from werkzeug.security import generate_password_hash
from forms import RegisterForm, LoginForm, ProfileForm   

users_bp = Blueprint('users', __name__)

# ============================
# GET tous les utilisateurs
# ============================
@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Récupère tous les utilisateurs en base.

    - Vérifie l'identité via JWT.
    - Retourne une liste JSON avec id, nom, prénom, email, filiere, annee et type_stage.
    """
    users = Users.query.all()
    return jsonify([{
        "id": u.id,
        "nom": u.nom,
        "prenom": u.prenom,
        "email": u.email,
        "filiere": u.filiere,
        "annee": u.annee,
        "type_stage": u.type_stage
    } for u in users])


# ============================
# GET un utilisateur spécifique
# ============================
@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Récupère un utilisateur par son ID.

    - Vérifie l'identité via JWT.
    - Retourne les informations détaillées de l'utilisateur en JSON.
    """
    user = Users.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "filiere": user.filiere,
        "annee": user.annee,
        "type_stage": user.type_stage,
        "date_debut": user.date_debut.isoformat() if user.date_debut else None,
        "date_fin": user.date_fin.isoformat() if user.date_fin else None
    })


# ============================
# POST créer un utilisateur (admin)
# ============================
@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    """
    Crée un nouvel utilisateur (réservé à un rôle admin).

    - Valide les données avec RegisterForm.
    - Vérifie si l'email existe déjà.
    - Hash le mot de passe avec Werkzeug.
    - Crée l'utilisateur avec placeholders pour nom/prénom.
    - Retourne un message JSON avec l'id créé.
    """
    form = RegisterForm()

    if form.validate_on_submit():
        if Users.query.filter_by(email=form.email.data).first():
            return jsonify({"msg": "Email déjà utilisé"}), 400

        hashed_pw = generate_password_hash(form.password.data)
        user = Users(
            email=form.email.data,
            mot_de_passe=hashed_pw,
            nom="Nom",
            prenom="Prénom"
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"msg": "Utilisateur créé", "id": user.id}), 201

    return jsonify({"errors": form.errors}), 400


# ============================
# PUT modifier un utilisateur (profil)
# ============================
@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """
    Met à jour le profil d'un utilisateur.

    - Vérifie que l'utilisateur connecté modifie son propre profil.
    - Valide les données avec ProfileForm.
    - Met à jour nom, prénom, email, filiere, annee, type_stage, date_debut et date_fin.
    - Retourne un message JSON de confirmation.
    """
    user = Users.query.get_or_404(user_id)
    current_user_id = int(get_jwt_identity())
    if current_user_id != user_id:
        return jsonify({"msg": "Vous ne pouvez modifier que votre propre profil"}), 403

    form = ProfileForm(data=request.json)

    if form.validate():
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.email = request.json.get('email', user.email)
        user.filiere = form.filiere.data
        user.annee = form.annee.data
        user.type_stage = form.type_stage.data
        user.date_debut = form.date_debut.data
        user.date_fin = form.date_fin.data

        db.session.commit()
        return jsonify({"msg": "Profil mis à jour"}), 200
    return jsonify({"errors": form.errors}), 400


# ============================
# DELETE supprimer un utilisateur
# ============================
@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """
    Supprime un utilisateur.
    - Vérifie que l'utilisateur connecté supprime son propre compte.
    - Supprime l'utilisateur de la base.
    - Retourne un message JSON de confirmation.
    """
    user = Users.query.get_or_404(user_id)
    current_user_id = int(get_jwt_identity())
    if current_user_id != user_id:
        return jsonify({"msg": "Vous ne pouvez supprimer que votre propre compte"}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "Utilisateur supprimé"}), 200


# ============================
# GET profil de l'utilisateur connecté
# ============================
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Récupère le profil de l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Retourne les informations détaillées du profil utilisateur.
    """
    user_id = int(get_jwt_identity())
    user = Users.query.get_or_404(user_id)
    
    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "filiere": user.filiere,
        "annee": user.annee,
        "type_stage": user.type_stage,
        "date_debut": user.date_debut.isoformat() if user.date_debut else None,
        "date_fin": user.date_fin.isoformat() if user.date_fin else None
    }), 200


# ============================
# PUT modifier le profil de l'utilisateur connecté
# ============================
@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Met à jour le profil de l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Valide les données avec ProfileForm.
    - Met à jour nom, prénom, email, filiere, annee, type_stage, date_debut et date_fin.
    - Retourne un message JSON de confirmation avec les données mises à jour.
    """
    user_id = int(get_jwt_identity())
    user = Users.query.get_or_404(user_id)
    
    form = ProfileForm(data=request.json)

    if form.validate():
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.email = request.json.get('email', user.email)
        user.filiere = form.filiere.data
        user.annee = form.annee.data
        user.type_stage = form.type_stage.data
        user.date_debut = form.date_debut.data
        user.date_fin = form.date_fin.data

        db.session.commit()
        
        return jsonify({
            "msg": "Profil mis à jour avec succès",
            "profile": {
                "id": user.id,
                "nom": user.nom,
                "prenom": user.prenom,
                "email": user.email,
                "filiere": user.filiere,
                "annee": user.annee,
                "type_stage": user.type_stage,
                "date_debut": user.date_debut.isoformat() if user.date_debut else None,
                "date_fin": user.date_fin.isoformat() if user.date_fin else None
            }
        }), 200
    
    return jsonify({"errors": form.errors}), 400
