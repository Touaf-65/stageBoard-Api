"""
echeances.py - Gestion des échéances
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Echeances, Users
from app.forms import DeadlineForm

# Création du module "échéances" avec Blueprint
echeances_bp = Blueprint('echeances', __name__)

# ============================
# GET toutes les échéances
# ============================
@echeances_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_echeances():
    """
    Récupère toutes les échéances de l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Filtre les échéances par user_id.
    - Retourne une liste JSON avec id, titre, description, date_limite et statut.
    """
    user_id = get_jwt_identity()
    echeances = Echeances.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": e.id,
        "titre": e.titre,
        "description": e.description,
        "date_limite": e.date_limite.isoformat(),
        "statut": e.statut
    } for e in echeances])


# ============================
# POST créer une nouvelle échéance
# ============================
@echeances_bp.route('/', methods=['POST'])
@jwt_required()
def create_echeance():
    """
    Crée une nouvelle échéance pour l'utilisateur connecté.

    - Récupère l'identité via JWT.
    - Valide les données avec DeadlineForm.
    - Vérifie que la date est comprise entre date_debut et date_fin du stage.
    - Insère l'échéance en base et retourne un message JSON avec l'id créé.
    """
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)

    form = DeadlineForm(data=request.json)
    form.start_date = user.date_debut
    form.end_date = user.date_fin

    if form.validate():
        nouvelle = Echeances(
            titre=form.title.data,
            description=form.description.data,
            date_limite=form.due_date.data,
            statut=form.statut.data,
            user_id=user_id
        )
        db.session.add(nouvelle)
        db.session.commit()
        return jsonify({"msg": "Échéance créée", "id": nouvelle.id}), 201
    return jsonify({"errors": form.errors}), 400


# ============================
# PUT modifier une échéance existante
# ============================
@echeances_bp.route('/<int:echeance_id>', methods=['PUT'])
@jwt_required()
def update_echeance(echeance_id):
    """
    Met à jour une échéance existante.

    - Vérifie que l'échéance appartient à l'utilisateur connecté.
    - Valide les nouvelles données avec DeadlineForm.
    - Met à jour titre, description, date_limite et statut.
    - Retourne un message JSON de confirmation.
    """
    user_id = int(get_jwt_identity())
    echeance = Echeances.query.get_or_404(echeance_id)
    if echeance.user_id != user_id:
        return jsonify({"msg": "Non autorisé"}), 403

    user = Users.query.get(user_id)
    form = DeadlineForm(data=request.json)
    form.start_date = user.date_debut
    form.end_date = user.date_fin

    if form.validate():
        echeance.titre = form.title.data
        echeance.date_limite = form.due_date.data
        echeance.description = form.description.data or echeance.description
        echeance.statut = form.statut.data or echeance.statut
        db.session.commit()
        return jsonify({"msg": "Échéance mise à jour"}), 200
    return jsonify({"errors": form.errors}), 400


# ============================
# DELETE supprimer une échéance
# ============================
@echeances_bp.route('/<int:echeance_id>', methods=['DELETE'])
@jwt_required()
def delete_echeance(echeance_id):
    """
    Supprime une échéance existante.

    - Vérifie que l'échéance appartient à l'utilisateur connecté.
    - Supprime l'échéance de la base.
    - Retourne un message JSON de confirmation.
    """
    user_id = int(get_jwt_identity())
    echeance = Echeances.query.get_or_404(echeance_id)
    if echeance.user_id != user_id:
        return jsonify({"msg": "Non autorisé"}), 403

    db.session.delete(echeance)
    db.session.commit()
    return jsonify({"msg": "Échéance supprimée"}), 200
