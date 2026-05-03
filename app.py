"""
app.py - Point d'entrée de l'application
"""

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from extensions import db, mail,jwt
from auth import auth_bp
from users import users_bp
from echeances import echeances_bp
from journal import journal_bp
from entreprise import entreprise_bp

# ============================
# CRÉATION DE L'APPLICATION
# ============================
app = Flask(__name__)
app.config.from_object(Config)

# Initialiser CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://stagebroad.com",
            "https://www.stagebroad.com"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})


# Initialiser extensions
db.init_app(app)
with app.app_context():
    db.create_all()  # Toujours exécuté, Gunicorn inclus

jwt.init_app(app)
mail.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(echeances_bp, url_prefix='/api/echeances')
app.register_blueprint(journal_bp, url_prefix='/api/journal')
app.register_blueprint(entreprise_bp, url_prefix='/api/entreprise')


@app.errorhandler(400)
def bad_request(e): return {"error": "Bad request"}, 400

@app.errorhandler(401)
def unauthorized(e): return {"error": "Unauthorized"}, 401

@app.errorhandler(403)
def forbidden(e): return {"error": "Forbidden"}, 403

@app.errorhandler(404)
def not_found(e): return {"error": "Not found"}, 404

@app.errorhandler(429)
def too_many(e): return {"error": "Too many requests"}, 429

@app.errorhandler(500)
def internal(e):
    app.logger.error(f"Internal error: {e}")  # Log côté serveur
    return {"error": "Internal server error"}, 500  # Message générique client




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
