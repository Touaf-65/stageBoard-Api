"""
app.py - Point d'entrée de l'application
"""

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
from app.extensions import db, mail,jwt
from app.auth import auth_bp
from app.users import users_bp
from app.echeances import echeances_bp
from app.journal import journal_bp
from app.entreprise import entreprise_bp

# ============================
# CRÉATION DE L'APPLICATION
# ============================
app = Flask(__name__)
app.config.from_object(Config)

# Initialiser CORS
CORS(app)

# Initialiser extensions
db.init_app(app)
jwt.init_app(app)
mail.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(echeances_bp, url_prefix='/api/echeances')
app.register_blueprint(journal_bp, url_prefix='/api/journal')
app.register_blueprint(entreprise_bp, url_prefix='/api/entreprise')

# ============================
# ROUTE DE TEST
# ============================
@app.route('/')
def home():
    return {"message": "StageBoard API is running"}

# ============================
# LANCEMENT DU SERVEUR
# ============================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
