"""
models.py - Définition des modèles SQLAlchemy pour StageBoard
"""

from datetime import datetime
from extensions import db   # importer l'instance partagée

# ============================
# Table "users"
# ============================
class Users(db.Model):
    """
    Modèle représentant un utilisateur.

    Champs :
    - id : identifiant unique (auto-incrément)
    - nom : nom de l'utilisateur
    - prenom : prénom de l'utilisateur
    - email : adresse email unique
    - mot_de_passe : mot de passe hashé
    - filiere : filière de l'étudiant
    - annee : année d'étude
    - type_stage : type de stage
    - date_debut : date de début du stage
    - date_fin : date de fin du stage

    Relations :
    - echeances : liste des échéances liées à l'utilisateur
    - journal_entries : liste des entrées de journal liées à l'utilisateur
    - entreprise : fiche entreprise liée (relation 1-1)
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    filiere = db.Column(db.String(100))
    annee = db.Column(db.String(50))
    type_stage = db.Column(db.String(50))
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)

    echeances = db.relationship('Echeances', backref='user', lazy=True)
    journal_entries = db.relationship('Journal', backref='user', lazy=True)


# ============================
# Table "échéances"
# ============================
class Echeances(db.Model):
    """
    Modèle représentant une échéance.

    Champs :
    - id : identifiant unique
    - titre : titre de l'échéance
    - description : description optionnelle
    - date_limite : date limite de l'échéance
    - statut : statut de l'échéance ('a_venir', 'termine', 'retard')
    - user_id : clé étrangère vers l'utilisateur
    """
    __tablename__ = 'echeances'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_limite = db.Column(db.Date, nullable=False)
    statut = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# ============================
# Table "journal"
# ============================
class Journal(db.Model):
    """
    Modèle représentant une entrée de journal.

    Champs :
    - id : identifiant unique
    - date_entree : date de l'entrée
    - taches : tâches réalisées
    - competences : compétences acquises
    - difficultes : difficultés rencontrées
    - user_id : clé étrangère vers l'utilisateur
    """
    __tablename__ = 'journal'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.Text)
    description = db.Column(db.Text)
    date_entree = db.Column(db.Date, nullable=False)
    taches = db.Column(db.Text)
    competences = db.Column(db.Text)
    difficultes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# ============================
# Table "entreprise"
# ============================
class Entreprise(db.Model):
    """
    Modèle représentant une fiche entreprise.

    Champs :
    - id : identifiant unique
    - nom : nom de l'entreprise
    - secteur : secteur d'activité
    - adresse : adresse de l'entreprise
    - telephone : numéro de téléphone
    - email_tuteur : email du tuteur
    - nom_tuteur : nom du tuteur
    - user_id : clé étrangère vers l'utilisateur

    Relation :
    - user : relation 1-1 avec Users (un utilisateur a une entreprise)
    """
    __tablename__ = 'entreprise'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    secteur = db.Column(db.String(100))
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    email_tuteur = db.Column(db.String(120))
    nom_tuteur = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("Users", backref="entreprise", uselist=False)
