"""
forms.py - Définition des formulaires Flask-WTF pour StageBoard
"""

from flask import request
from flask_wtf import FlaskForm
from flask_wtf.form import _Auto
from werkzeug.datastructures import ImmutableMultiDict
from wtforms import DateField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import AnyOf, DataRequired, Email, Length, Optional, ValidationError
from datetime import date

# Bornes des mots de passe : le maximum évite qu'un mot de passe géant
# (plusieurs centaines de Ko) monopolise le CPU au hachage
PASSWORD_MIN = 6
PASSWORD_MAX = 128


def normalize_email(email):
    """Email comparé et stocké sans espaces et en minuscules (évite les doublons A@x / a@x)."""
    return (email or '').strip().lower()


# ============================
# FORMULAIRE DE BASE
# ============================
def json_body():
    """Corps JSON de la requête, ou {} s'il est absent ou n'est pas un objet."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


class BaseForm(FlaskForm):
    """
    Base commune :
    - messages de validation WTForms en français (nécessite WTF_I18N_ENABLED = False
      dans la config, sinon Flask-WTF passe par Flask-Babel qui n'est pas installé) ;
    - lecture robuste du JSON : un corps qui n'est pas un objet, ou des valeurs qui ne
      sont pas du texte ({"title": 123}, listes…), donnent une erreur de validation 400
      au lieu d'une erreur 500.
    """
    class Meta:
        locales = ['fr_FR', 'fr']

        def wrap_formdata(self, form, formdata):
            if formdata is _Auto and request.is_json:
                return ImmutableMultiDict({
                    key: str(value) for key, value in json_body().items()
                    if isinstance(value, (str, int, float)) and not isinstance(value, bool)
                })
            return super().wrap_formdata(form, formdata)


# ============================
# FORMULAIRE D'INSCRIPTION
# ============================
class RegisterForm(BaseForm):
    """
    Formulaire d'inscription utilisateur.

    Champs :
    - email : obligatoire, format email valide
    - password : obligatoire, entre PASSWORD_MIN et PASSWORD_MAX caractères
    - submit : bouton d'inscription
    """
    email = StringField('Email', filters=[normalize_email], validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=PASSWORD_MIN, max=PASSWORD_MAX)])
    submit = SubmitField('S’inscrire')


# ============================
# FORMULAIRE DE CONNEXION
# ============================
class LoginForm(BaseForm):
    """
    Formulaire de connexion utilisateur.

    Champs :
    - email : obligatoire, format email valide
    - password : obligatoire
    - submit : bouton de connexion
    """
    email = StringField('Email', filters=[normalize_email], validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(max=PASSWORD_MAX)])
    submit = SubmitField('Se connecter')


# ============================
# FORMULAIRE D'AJOUT D'ECHEANCE
# ============================
class DeadlineForm(BaseForm):
    """
    Formulaire pour créer ou modifier une échéance.

    Champs :
    - title : obligatoire, minimum 3 caractères
    - description : optionnel
    - statut : obligatoire, parmi STATUTS
    - due_date : obligatoire, format date (AAAA-MM-JJ)
    - submit : bouton d'ajout

    Validation personnalisée :
    - La date ne peut pas être dans le passé, sauf si elle est inchangée lors d'une
      modification (current_date) : une échéance dépassée peut ainsi passer en "Fait".
    - Si dates de stage définies → doit être comprise entre date_debut et date_fin.
    """
    STATUTS = ['A venir', 'Fait', 'En retard']

    title = StringField('Titre', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description')
    statut = StringField('Statut', validators=[DataRequired(), AnyOf(STATUTS, message="Statut invalide (A venir, Fait ou En retard).")])
    due_date = DateField('Date limite', validators=[DataRequired()])
    submit = SubmitField('Ajouter échéance')

    def validate_due_date(self, field):
        """Vérifie que la date limite est valide (pas passée et dans les bornes du stage)."""
        unchanged = field.data == getattr(self, "current_date", None)
        if field.data < date.today() and not unchanged:
            raise ValidationError("La date limite ne peut pas être dans le passé.")
        if hasattr(self, "start_date") and hasattr(self, "end_date"):
            if self.start_date and self.end_date:
                if not (self.start_date <= field.data <= self.end_date):
                    raise ValidationError("La date doit être comprise entre le début et la fin du stage.")


# ============================
# FORMULAIRE D'AJOUT DE JOURNAL
# ============================
class JournalForm(BaseForm):
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
    titre = StringField('Titre', validators=[DataRequired(), Length(min=3)])
    description = TextAreaField('Description', validators=[Length(max=500)])
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
class ProfileForm(BaseForm):
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
    # Longueurs maximales = colonnes du modèle Users (MySQL refuserait une valeur trop longue)
    nom = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', filters=[normalize_email], validators=[Optional(), Email(), Length(max=120)])
    filiere = StringField('Filière', validators=[Length(max=100)])
    annee = StringField('Année', validators=[Length(max=50)])
    type_stage = StringField('Type de stage', validators=[Length(max=50)])
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
class EntrepriseForm(BaseForm):
    """
    Formulaire pour créer ou modifier une fiche entreprise.

    Champs :
    - nom : obligatoire, minimum 2 caractères
    - secteur, adresse, telephone : optionnels
    - email_tuteur : optionnel, format email valide si renseigné
    - nom_tuteur : optionnel
    - submit : bouton d'enregistrement

    Les longueurs maximales correspondent aux colonnes du modèle Entreprise.
    """
    nom = StringField('Nom de l’entreprise', validators=[DataRequired(), Length(min=2, max=100)])
    secteur = StringField('Secteur', validators=[Length(max=100)])
    adresse = StringField('Adresse', validators=[Length(max=200)])
    telephone = StringField('Téléphone', validators=[Length(max=20)])
    email_tuteur = StringField('Email du tuteur', filters=[normalize_email], validators=[Optional(), Email(), Length(max=120)])
    nom_tuteur = StringField('Nom du tuteur', validators=[Length(max=100)])
    submit = SubmitField('Enregistrer')
