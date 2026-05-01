"""
journal.py - Gestion du journal de bord
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Journal, Users
from forms import JournalForm

# Création du module "journal" avec Blueprint
journal_bp = Blueprint('journal', __name__)

# ============================
# GET toutes les entrées du journal
# ============================
@journal_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_entries():
    """
    Récupère toutes les entrées du journal de l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Récupère les entrées du journal triées par date (desc).
    - Retourne une liste JSON avec id, date_entree, taches, competences et difficultes.
    """
    user_id = get_jwt_identity()
    entries = Journal.query.filter_by(user_id=user_id).order_by(Journal.date_entree.desc()).all()
    return jsonify([{
        "id": e.id,
        "titre": e.titre,
        "description": e.description,
        "date_entree": e.date_entree.isoformat(),
        "taches": e.taches,
        "competences": e.competences,
        "difficultes": e.difficultes
    } for e in entries])


# ============================
# POST créer une nouvelle entrée
# ============================
@journal_bp.route('/', methods=['POST'])
@jwt_required()
def create_entry():
    """
    Crée une nouvelle entrée de journal pour l'utilisateur connecté.

    - Vérifie l'identité via JWT.
    - Valide les données avec JournalForm.
    - Vérifie que la date est comprise entre date_debut et date_fin du stage.
    - Insère l'entrée en base et retourne un message JSON avec l'id créé.
    """
    user_id = int(get_jwt_identity())
    user = Users.query.get(user_id)

    form = JournalForm(data=request.json)
    form.start_date = user.date_debut
    form.end_date = user.date_fin

    if form.validate():
        entry = Journal(
            titre=form.titre.data,
            description=form.description.data,
            date_entree=form.date_entree.data,
            taches=form.taches.data,
            competences=form.competences.data,
            difficultes=form.difficultes.data,
            user_id=user_id
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"msg": "Entrée ajoutée", "id": entry.id}), 201
    return jsonify({"errors": form.errors}), 400


# ============================
# PUT modifier une entrée existante
# ============================
@journal_bp.route('/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_entry(entry_id):
    """
    Met à jour une entrée de journal existante.

    - Vérifie que l'entrée appartient à l'utilisateur connecté.
    - Valide les nouvelles données avec JournalForm.
    - Met à jour date_entree, taches, competences et difficultes.
    - Retourne un message JSON de confirmation.
    """
    user_id = int(get_jwt_identity())
    entry = Journal.query.get_or_404(entry_id)
    if entry.user_id != user_id:
        return jsonify({"msg": "Non autorisé"}), 403

    user = Users.query.get(user_id)
    form = JournalForm(data=request.json)
    form.start_date = user.date_debut
    form.end_date = user.date_fin

    if form.validate():
        entry.date_entree = form.date_entree.data
        entry.titre = form.titre.data
        entry.description = form.description.data
        entry.taches = form.taches.data
        entry.competences = form.competences.data
        entry.difficultes = form.difficultes.data
        db.session.commit()
        return jsonify({"msg": "Entrée mise à jour"}), 200
    return jsonify({"errors": form.errors}), 400


# ============================
# DELETE supprimer une entrée
# ============================
@journal_bp.route('/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_entry(entry_id):
    """
    Supprime une entrée de journal existante.

    - Vérifie que l'entrée appartient à l'utilisateur connecté.
    - Supprime l'entrée de la base.
    - Retourne un message JSON de confirmation.
    """
    user_id = int(get_jwt_identity())
    entry = Journal.query.get_or_404(entry_id)
    if entry.user_id != user_id:
        return jsonify({"msg": "Non autorisé"}), 403

    db.session.delete(entry)
    db.session.commit()
    return jsonify({"msg": "Entrée supprimée"}), 200
