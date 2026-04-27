"""
forms.py - Définition des formulaires Flask-WTF pour StageBoard
"""

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from datetime import date

# ============================
# FORMULAIRE D'INSCRIPTION
# ============================
class RegisterForm(FlaskForm):
    """
    Formulaire d'inscription utilisateur.

    Champs :
    - email : obligatoire, format email valide
    - password : obligatoire, minimum 6 caractères
    - submit : bouton d'inscription
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('S’inscrire')


# ============================
# FORMULAIRE DE CONNEXION
# ============================
class LoginForm(FlaskForm):
    """
    Formulaire de connexion utilisateur.

    Champs :
    - email : obligatoire, format email valide
    - password : obligatoire
    - submit : bouton de connexion
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')


# ============================
# FORMULAIRE D'AJOUT D'ECHEANCE
# ============================
class DeadlineForm(FlaskForm):
    """
    Formulaire pour créer ou modifier une échéance.

    Champs :
    - title : obligatoire, minimum 3 caractères
    - description : optionnel
    - statut : obligatoire (ex: 'a_venir', 'termine', 'retard')
    - due_date : obligatoire, format date
    - submit : bouton d'ajout

    Validation personnalisée :
    - La date ne peut pas être dans le passé.
    - Si dates de stage définies → doit être comprise entre date_debut et date_fin.
    """
    title = StringField('Titre', validators=[DataRequired(), Length(min=3)])
    description = TextAreaField('Description')
    statut = StringField('Statut', validators=[DataRequired()])
    due_date = DateField('Date limite', validators=[DataRequired()])
    submit = SubmitField('Ajouter échéance')

    def validate_due_date(self, field):
        """Vérifie que la date limite est valide (pas passée et dans les bornes du stage)."""
        if field.data < date.today():
            raise ValidationError("La date limite ne peut pas être dans le passé.")
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            if self.start_date and self.end_date:
                if not (self.start_date <= field.data <= self.end_date):
                    raise ValidationError("La date doit être comprise entre le début et la fin du stage.")


# ============================
# FORMULAIRE D'AJOUT DE JOURNAL
# ============================
class JournalForm(FlaskForm):
    """
    Formulaire pour ajouter une entrée de journal.

    Champs :
    - date_entree : obligatoire, format date
    - taches : obligatoire, minimum 5 caractères
    - competences : obligatoire, minimum 5 caractères
    - difficultes : obligatoire, minimum 5 caractères
    - submit : bouton d'ajout

    Validation personnalisée :
    - La date ne peut pas être dans le futur.
    - Si dates de stage définies → doit être comprise entre date_debut et date_fin.
    """
    date_entree = DateField('Date du journal', validators=[DataRequired()])
    taches = TextAreaField('Tâches', validators=[DataRequired(), Length(min=5)])
    competences = TextAreaField('Compétences', validators=[DataRequired(), Length(min=5)])
    difficultes = TextAreaField('Difficultés', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Ajouter journal')

    def validate_date_entree(self, field):
        """Vérifie que la date du journal est valide (pas future et dans les bornes du stage)."""
        if field.data > date.today():
            raise ValidationError("La date du journal ne peut pas être dans le futur.")
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            if self.start_date and self.end_date:
                if not (self.start_date <= field.data <= self.end_date):
                    raise ValidationError("La date doit être comprise entre le début et la fin du stage.")


# ============================
# FORMULAIRE DE MISE À JOUR DU PROFIL
# ============================
class ProfileForm(FlaskForm):
    """
    Formulaire pour mettre à jour le profil utilisateur.

    Champs :
    - nom : obligatoire, minimum 2 caractères
    - prenom : obligatoire, minimum 2 caractères
    - filiere, annee, type_stage : optionnels
    - date_debut, date_fin : dates du stage
    - submit : bouton de mise à jour

    Validation personnalisée :
    - date_fin doit être après date_debut.
    """
    nom = StringField('Nom', validators=[DataRequired(), Length(min=2)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(min=2)])
    filiere = StringField('Filière')
    annee = StringField('Année')
    type_stage = StringField('Type de stage')
    date_debut = DateField('Date de début')
    date_fin = DateField('Date de fin')
    submit = SubmitField('Mettre à jour profil')

    def validate_date_fin(self, field):
        """Vérifie que la date de fin est postérieure à la date de début."""
        if self.date_debut.data and field.data:
            if field.data < self.date_debut.data:
                raise ValidationError("La date de fin doit être après la date de début.")


# ============================
# FORMULAIRE ENTREPRISE
# ============================
class EntrepriseForm(FlaskForm):
    """
    Formulaire pour créer ou modifier une fiche entreprise.

    Champs :
    - nom : obligatoire, minimum 2 caractères
    - secteur, adresse, telephone : optionnels
    - email_tuteur : format email valide
    - nom_tuteur : optionnel
    - submit : bouton d'enregistrement
    """
    nom = StringField('Nom de l’entreprise', validators=[DataRequired(), Length(min=2)])
    secteur = StringField('Secteur')
    adresse = StringField('Adresse')
    telephone = StringField('Téléphone')
    email_tuteur = StringField('Email du tuteur', validators=[Email()])
    nom_tuteur = StringField('Nom du tuteur')
    submit = SubmitField('Enregistrer')
