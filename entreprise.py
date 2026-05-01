"""
entreprise.py - Gestion des fiches entreprise
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Entreprise, Users
from forms import EntrepriseForm

entreprise_bp = Blueprint('entreprise', __name__)

# ============================
# GET - voir la fiche entreprise de l’utilisateur connecté
# ============================
@entreprise_bp.route('/', methods=['GET'])
@jwt_required()
def get_entreprise():
    """
    Récupère la fiche entreprise de l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Cherche l'entreprise liée à l'utilisateur.
    - Retourne les informations de l'entreprise en JSON.
    - Retourne 404 si aucune entreprise n'est trouvée.
    """
    current_user_id = int(get_jwt_identity())
    entreprise = Entreprise.query.filter_by(user_id=current_user_id).first()
    if not entreprise:
        return jsonify({"msg": "Aucune entreprise trouvée"}), 404
    return jsonify({
        "id": entreprise.id,
        "nom": entreprise.nom,
        "secteur": entreprise.secteur,
        "adresse": entreprise.adresse,
        "telephone": entreprise.telephone,
        "email_tuteur": entreprise.email_tuteur,
        "nom_tuteur": entreprise.nom_tuteur
    })


# ============================
# POST - créer une fiche entreprise
# ============================
@entreprise_bp.route('/', methods=['POST'])
@jwt_required()
def create_entreprise():
    """
    Crée une nouvelle fiche entreprise pour l'utilisateur connecté.

    - Valide les données avec EntrepriseForm.
    - Associe l'entreprise au user_id du JWT.
    - Insère l'entreprise en base.
    - Retourne un message JSON avec l'id créé.
    """
    form = EntrepriseForm(data=request.json)
    if form.validate():
        current_user_id = int(get_jwt_identity())
        entreprise = Entreprise(
            nom=form.nom.data,
            secteur=form.secteur.data,
            adresse=form.adresse.data,
            telephone=form.telephone.data,
            email_tuteur=form.email_tuteur.data,
            nom_tuteur=form.nom_tuteur.data,
            user_id=current_user_id
        )
        db.session.add(entreprise)
        db.session.commit()
        return jsonify({"msg": "Entreprise créée", "id": entreprise.id}), 201
    return jsonify({"errors": form.errors}), 400


# ============================
# PUT - modifier la fiche entreprise
# ============================
@entreprise_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_entreprise(id):
    """
    Met à jour la fiche entreprise de l'utilisateur connecté.

    - Vérifie que l'entreprise appartient à l'utilisateur.
    - Valide les nouvelles données avec EntrepriseForm.
    - Met à jour les champs (nom, secteur, adresse, téléphone, email_tuteur, nom_tuteur).
    - Retourne un message JSON de confirmation.
    """
    entreprise = Entreprise.query.get_or_404(id)
    current_user_id = int(get_jwt_identity())
    if entreprise.user_id != current_user_id:
        return jsonify({"msg": "Vous ne pouvez modifier que votre propre entreprise"}), 403

    form = EntrepriseForm(data=request.json)
    if form.validate():
        entreprise.nom = form.nom.data
        entreprise.secteur = form.secteur.data
        entreprise.adresse = form.adresse.data
        entreprise.telephone = form.telephone.data
        entreprise.email_tuteur = form.email_tuteur.data
        entreprise.nom_tuteur = form.nom_tuteur.data
        db.session.commit()
        return jsonify({"msg": "Entreprise mise à jour"}), 200
    return jsonify({"errors": form.errors}), 400


# ============================
# DELETE - supprimer la fiche entreprise
# ============================
@entreprise_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_entreprise(id):
    """
    Supprime la fiche entreprise de l'utilisateur connecté.

    - Vérifie que l'entreprise appartient à l'utilisateur.
    - Supprime l'entreprise de la base.
    - Retourne un message JSON de confirmation.
    """
    entreprise = Entreprise.query.get_or_404(id)
    current_user_id = int(get_jwt_identity())
    if entreprise.user_id != current_user_id:
        return jsonify({"msg": "Vous ne pouvez supprimer que votre propre entreprise"}), 403

    db.session.delete(entreprise)
    db.session.commit()
    return jsonify({"msg": "Entreprise supprimée"}), 200
