"""
users.py - Gestion des utilisateurs
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Users, find_user_by_email
from forms import ProfileForm, json_body, normalize_email

users_bp = Blueprint('users', __name__)


def email_conflict(user, new_email):
    """
    Retourne une réponse 409 si new_email est déjà utilisé par un autre compte,
    sinon None. Évite l'erreur 500 levée par la contrainte d'unicité en base.
    """
    other = find_user_by_email(new_email) if new_email else None
    if other and other.id != user.id:
        return jsonify({"msg": "Cet email est déjà utilisé par un autre compte"}), 409
    return None


# Les routes GET /api/users/ (liste de tous les comptes) et POST /api/users/
# (création de compte par n'importe quel utilisateur connecté) ont été supprimées :
# elles exposaient les données des autres stagiaires. L'inscription passe par /api/auth/register.


# ============================
# GET un utilisateur spécifique
# ============================
@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Récupère un utilisateur par son ID.

    - Vérifie l'identité via JWT : seul son propre compte est accessible.
    - Retourne les informations détaillées de l'utilisateur en JSON.
    """
    if int(get_jwt_identity()) != user_id:
        return jsonify({"msg": "Vous ne pouvez consulter que votre propre profil"}), 403
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

    conflict = email_conflict(user, normalize_email(json_body().get('email')))
    if conflict:
        return conflict

    form = ProfileForm()

    if form.validate():
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.email = normalize_email(form.email.data) or user.email
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

    conflict = email_conflict(user, normalize_email(json_body().get('email')))
    if conflict:
        return conflict

    form = ProfileForm()

    if form.validate():
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.email = normalize_email(form.email.data) or user.email
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
