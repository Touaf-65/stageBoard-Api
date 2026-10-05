"""
tests/test_securite.py - Tests de sécurité de l'API StageBoard.

Lancement, depuis la racine du dépôt :
    python tests/test_securite.py

Le script crée sa propre base SQLite temporaire : il ne touche JAMAIS à la base
configurée dans .env ou en production (il vide entièrement la base qu'il utilise).
Chaque test affiche OK (protégé), VULN (faille constatée) ou ACCEPTÉ (risque connu
et assumé). Code de sortie 1 si au moins une faille est constatée.
"""
import datetime
import os
import subprocess
import sys
import tempfile
from unittest import mock

# Base temporaire imposée AVANT d'importer l'application (load_dotenv ne remplace pas
# une variable déjà définie) : la base réelle ne peut pas être utilisée par erreur
_TMP_DIR = tempfile.mkdtemp(prefix='stageboard-tests-')
TEST_DB_URL = 'sqlite:///' + os.path.join(_TMP_DIR, 'securite.db').replace(os.sep, '/')
os.environ['DATABASE_URL'] = TEST_DB_URL
os.environ['FLASK_ENV'] = 'test'
os.environ.setdefault('SECRET_KEY', 'tests-secret-key')
os.environ.setdefault('JWT_SECRET_KEY', 'tests-jwt-secret-key-au-moins-32-caracteres')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402
from extensions import db  # noqa: E402

app = app_module.app
assert app.config['SQLALCHEMY_DATABASE_URI'] == TEST_DB_URL, 'Refus : la base de test n est pas la base temporaire'
c = app.test_client()
results = []

# Risques connus et assumés : affichés, mais ne font pas échouer le script
ACCEPTES = {
    "Inscription : révèle si un email est inscrit":
        "message utile à l'utilisateur ; freiné par nginx (3 inscriptions/min par IP)",
}


def check(name, vulnerable, detail=""):
    accepte = vulnerable and name in ACCEPTES
    results.append((name, vulnerable and not accepte))
    label = 'ACCEPTÉ' if accepte else ('VULN' if vulnerable else 'OK')
    suffix = f"  -> {detail}" if detail else ""
    if accepte:
        suffix += f"  ({ACCEPTES[name]})"
    print(f"{label:<8} {name}{suffix}")


def register_login(email, password="secret123"):
    c.post('/api/auth/register', json={'email': email, 'password': password})
    r = c.post('/api/auth/login', json={'email': email, 'password': password}).get_json()
    return {'Authorization': f"Bearer {r['token']}"}, r['userId']


today = datetime.date.today()
with app.app_context():
    db.drop_all()
    db.create_all()

victime, vid = register_login('victime@test.io')
attaquant, aid = register_login('attaquant@test.io')
c.put('/api/users/profile', headers=victime, json={
    'nom': 'Victime', 'prenom': 'Vic', 'email': 'victime@test.io', 'filiere': 'Info', 'annee': '3',
    'type_stage': 'PFE', 'date_debut': str(today - datetime.timedelta(days=10)),
    'date_fin': str(today + datetime.timedelta(days=60))})
eid = c.post('/api/echeances/', headers=victime, json={'title': 'Rapport', 'due_date': str(today), 'statut': 'A venir'}).get_json()['id']
jid = c.post('/api/journal/', headers=victime, json={'titre': 'Jour 1', 'date_entree': str(today), 'taches': 'aaaaa',
                                                  'competences': 'aaaaa', 'difficultes': 'aaaaa'}).get_json()['id']
entid = c.post('/api/entreprise/', headers=victime, json={'nom': 'Acme'}).get_json()['id']

print("\n=== Contrôle d'accès (IDOR) ===")
r = c.get('/api/users/', headers=attaquant)
check("GET /users/ : liste de tous les comptes", r.status_code == 200, f"{r.status_code}, {len(r.get_json() or [])} comptes visibles" if r.status_code == 200 else str(r.status_code))
r = c.get(f'/api/users/{vid}', headers=attaquant)
check("GET /users/<id> d'un autre compte", r.status_code == 200, f"{r.status_code} {r.get_json()}" if r.status_code == 200 else str(r.status_code))
r = c.put(f'/api/users/{vid}', headers=attaquant, json={'nom': 'Pirate', 'prenom': 'Pi'})
check("PUT /users/<id> d'un autre compte", r.status_code < 400, str(r.status_code))
r = c.delete(f'/api/users/{vid}', headers=attaquant)
check("DELETE /users/<id> d'un autre compte", r.status_code < 400, str(r.status_code))
for label, url, payload in [
    ("échéance", f'/api/echeances/{eid}', {'title': 'Pirate', 'due_date': str(today), 'statut': 'Fait'}),
    ("journal", f'/api/journal/{jid}', {'titre': 'Pirate', 'date_entree': str(today), 'taches': 'aaaaa', 'competences': 'aaaaa', 'difficultes': 'aaaaa'}),
    ("entreprise", f'/api/entreprise/{entid}', {'nom': 'Pirate'}),
]:
    r = c.put(url, headers=attaquant, json=payload)
    check(f"PUT {label} d'un autre compte", r.status_code < 400, str(r.status_code))
    r = c.delete(url, headers=attaquant)
    check(f"DELETE {label} d'un autre compte", r.status_code < 400, str(r.status_code))
r = c.get('/api/echeances/', headers=attaquant)
check("GET échéances : fuite des données d'un autre compte", len(r.get_json()) > 0, str(r.get_json()))

print("\n=== Énumération de comptes ===")
r1 = c.post('/api/auth/register', json={'email': 'victime@test.io', 'password': 'secret123'})
check("Inscription : révèle si un email est inscrit", 'déjà' in (r1.get_json() or {}).get('msg', ''), r1.get_json().get('msg'))
with mock.patch('auth.mail.send'):
    a = c.post('/api/auth/reset-password-request', json={'email': 'victime@test.io'}).get_json()
    b = c.post('/api/auth/reset-password-request', json={'email': 'inconnu@test.io'}).get_json()
check("Mot de passe oublié : réponse différente selon l'existence du compte", a != b, f"{a} / {b}")
r = c.post('/api/auth/login', json={'email': 'VICTIME@test.io', 'password': 'secret123'})
r2 = c.post('/api/auth/register', json={'email': 'VICTIME@test.io', 'password': 'secret123'})
check("Email sensible à la casse : doublon de compte possible", r2.status_code == 201, f"inscription VICTIME@… -> {r2.status_code}")

print("\n=== Robustesse des entrées ===")
for url in ['/api/auth/reset-password-request', '/api/auth/reset-password']:
    r = c.post(url, data='pas du json', content_type='text/plain')
    check(f"POST {url} sans JSON -> erreur 500", r.status_code >= 500, str(r.status_code))
r = c.post('/api/auth/reset-password-request', json=['liste'])
check("POST reset-password-request avec un JSON non-objet -> 500", r.status_code >= 500, str(r.status_code))
big = 'x' * (12 * 1024 * 1024)
r = c.post('/api/auth/login', json={'email': 'a@b.io', 'password': big})
check("Corps de 12 Mo accepté par l'API (pas de MAX_CONTENT_LENGTH)", r.status_code != 413, str(r.status_code))
r = c.post('/api/auth/register', json={'email': 'long@test.io', 'password': 'p' * 100_000})
check("Mot de passe de 100 000 caractères accepté (coût de hachage)", r.status_code == 201, str(r.status_code))

print("\n=== Sessions ===")
old = dict(victime)
with mock.patch('auth.mail.send') as send:
    c.post('/api/auth/reset-password-request', json={'email': 'victime@test.io'})
    token = send.call_args[0][0].body.split('token=')[1].split()[0]
c.post('/api/auth/reset-password', json={'token': token, 'new_password': 'nouveau123', 'confirm_password': 'nouveau123'})
r = c.get('/api/users/profile', headers=old)
check("Ancienne session encore valide après changement de mot de passe", r.status_code == 200, str(r.status_code))
fantome, fid = register_login('fantome@test.io')
c.delete(f'/api/users/{fid}', headers=fantome)
r = c.post('/api/echeances/', headers=fantome, json={'title': 'Test', 'due_date': str(today), 'statut': 'A venir'})
check("Token d'un compte supprimé -> erreur 500", r.status_code >= 500, str(r.status_code))
r = c.get('/api/users/profile', headers=fantome)
check("Token d'un compte supprimé encore accepté (404 au lieu de 401)", r.status_code != 401, str(r.status_code))

r = c.post('/api/echeances/', headers=attaquant, json={'title': 123, 'due_date': ['x'], 'statut': None})
check("Valeurs JSON non textuelles -> erreur 500", r.status_code >= 500, str(r.status_code))
r = c.post('/api/journal/', headers=attaquant, json=['liste'])
check("Corps JSON en liste sur /journal -> erreur 500", r.status_code >= 500, str(r.status_code))
data_user, _ = register_login('donnees@test.io')
c.put('/api/users/profile', headers=data_user, json={'nom': 'Data', 'prenom': 'Da', 'date_debut': str(today - datetime.timedelta(days=1)), 'date_fin': str(today + datetime.timedelta(days=30))})
c.post('/api/echeances/', headers=data_user, json={'title': 'Doc', 'due_date': str(today), 'statut': 'A venir'})
c.post('/api/entreprise/', headers=data_user, json={'nom': 'Corp'})
did = c.get('/api/users/profile', headers=data_user).get_json()['id']
r = c.delete(f'/api/users/{did}', headers=data_user)
check("Suppression d'un compte qui a des données -> erreur", r.status_code >= 400, str(r.status_code))
with app.app_context():
    from models import Echeances, Entreprise
    orphelins = Echeances.query.filter_by(user_id=did).count() + Entreprise.query.filter_by(user_id=did).count()
check("Données orphelines après suppression du compte", orphelins > 0, f"{orphelins} ligne(s)")

print("\n=== CORS ===")
r = c.options('/api/users/profile', headers={'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'GET'})
check("CORS : origine tierce autorisée", r.headers.get('Access-Control-Allow-Origin') not in (None, ''), str(r.headers.get('Access-Control-Allow-Origin')))

print("\n=== Configuration ===")
API_DIR = os.path.dirname(os.path.abspath(app_module.__file__))
with open(os.path.join(API_DIR, 'config.py'), encoding='utf-8') as f:
    config_source = f.read()
check("JWT_SECRET_KEY avec valeur par défaut publique dans le code", 'cle-jwt-ultra-secrete' in config_source)
check("Mot de passe MySQL en clair dans config.py", 'stageboard_user:' in config_source)

# Variables vides (et non absentes) : load_dotenv ne les remplace pas par celles du .env
env = dict(os.environ, FLASK_ENV='production', JWT_SECRET_KEY='', SECRET_KEY='', DATABASE_URL='')
p = subprocess.run([sys.executable, '-c', 'import config'], env=env, capture_output=True, text=True, cwd=API_DIR)
check("Démarrage en production sans secrets accepté", p.returncode == 0,
      (p.stderr.strip().splitlines() or ['démarrage accepté'])[-1])

failles = sum(v for _, v in results)
print(f"\n{failles} faille(s) sur {len(results)} tests")
sys.exit(1 if failles else 0)
