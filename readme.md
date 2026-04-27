# StageBoard API – Documentation des routes

## Authentification

### Inscription
- **Méthode** : POST  
- **URL** : `/api/auth/register`  
- **Body JSON Exemple** :
```json
{
  "email": "user@example.com",
  "password": "motdepasse123"
}
```

---

### Connexion
- **Méthode** : POST  
- **URL** : `/api/auth/login`  
- **Body JSON Exemple** :
```json
{
  "email": "user@example.com",
  "password": "motdepasse123"
}
```

---

### Déconnexion
- **Méthode** : POST  
- **URL** : `/api/auth/logout`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```

---

### Mot de passe oublié – Demande
- **Méthode** : POST  
- **URL** : `/api/auth/reset-password-request`  
- **Body JSON Exemple** :
```json
{
  "email": "user@example.com"
}
```

---

### Mot de passe oublié – Réinitialisation
- **Méthode** : POST  
- **URL** : `/api/auth/reset-password`  
- **Body JSON Exemple** :
```json
{
  "token": "<RESET_TOKEN>",
  "new_password": "nouveauMotDePasse123"
}
```

---

## Utilisateurs

### Liste des utilisateurs
- **Méthode** : GET  
- **URL** : `/api/users/`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```

---

## Échéances

### Créer une échéance
- **Méthode** : POST  
- **URL** : `/api/echeances/`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "titre": "Projet StageBoard",
  "date": "2026-05-01",
  "description": "Livrable final"
}
```

---

### Modifier une échéance
- **Méthode** : PUT  
- **URL** : `/api/echeances/<id>`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "titre": "Projet StageBoard (modifié)",
  "date": "2026-05-02",
  "description": "Livrable corrigé"
}
```

---

## Journal

### Ajouter une entrée
- **Méthode** : POST  
- **URL** : `/api/journal/`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "titre": "Réunion avec encadrant",
  "contenu": "Discussion sur l’avancement du projet"
}
```

---

### Modifier une entrée
- **Méthode** : PUT  
- **URL** : `/api/journal/<id>`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "titre": "Réunion avec encadrant (mise à jour)",
  "contenu": "Ajout des points discutés"
}
```

---

## Entreprise

### Créer une entreprise
- **Méthode** : POST  
- **URL** : `/api/entreprise/`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "nom": "Microsoft",
  "secteur": "Technologie",
  "adresse": "Redmond, WA"
}
```

---

### Modifier une entreprise
- **Méthode** : PUT  
- **URL** : `/api/entreprise/<id>`  
- **Headers** :
```
Authorization: Bearer <TOKEN>
```
- **Body JSON Exemple** :
```json
{
  "nom": "Microsoft Corp",
  "secteur": "Technologie",
  "adresse": "Redmond, Washington"
}
```

---
