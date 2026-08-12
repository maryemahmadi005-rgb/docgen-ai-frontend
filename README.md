# Project Documentation

Analyser et générer des documents de synthèse pour les projets Open Source

---

## Fonctionnement général

Le flux réel fonctionne comme suit : une requête HTTP est envoyée à l'endpoint API /api/auth/register, qui crée un token d'authentification. Ce token est ensuite utilisé pour appeler l'endpoint API /api/repositories/<repo_id>/readme, qui récupère les informations du projet et génère un document de synthèse.

---


## Technologies utilisées

- JavaScript
- Python
- Flask
- React

---

## Modules principaux

### backend/app/__init__.py
**Fichier :** `backend/app/__init__.py`

**Rôle :** Crée l'application Flask et configure les extensions

**Classes principales :** `Flask`, `db`, `migrate`, `jwt`, `cors`
**Fonctions importantes :** `create_app`, `get_config`, `register_blueprints`
**Dépendances internes :** `app.config`, `app.extensions`
### backend/app/api/auth.py
**Fichier :** `backend/app/api/auth.py`

**Rôle :** Gère les appels d'authentification et la gestion des tokens

**Classes principales :** `Blueprint`, `requests`, `URLSafeTimedSerializer`
**Fonctions importantes :** `_oauth_serializer`, `_create_github_state`, `register_blueprint`
**Dépendances internes :** `app.config`, `app.container`, `flask_jwt_extended`
**Routes exposées :** `{'endpoint': '/api/auth/register', 'method': 'POST'}`, `{'endpoint': '/api/auth/login', 'method': 'POST'}`
### readme-sync-frontend/src/api/client.js
**Fichier :** `readme-sync-frontend/src/api/client.js`

**Rôle :** Appelle l'endpoint API /api/auth/refresh pour obtenir un nouveau token d'authentification

**Fonctions importantes :** `POST`, `API_URL`
**Routes exposées :** `{'endpoint': '${API_URL}/auth/refresh', 'method': 'POST'}`

---

## Flux de données

Flux non détecté.

---

## Points d'entrée

- `backend/app/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/api/auth.py`
- `backend/app/api/pending_updates.py`
- `backend/app/api/readmes.py`
- `backend/app/api/repositories.py`
- `backend/app/api/webhooks.py`
- `backend/run.py`
- `readme-sync-frontend/src/App.jsx`
- `readme-sync-frontend/src/main.jsx`

---

## Endpoints API

| Méthode(s) | Endpoint | Fichier |
|---|---|---|
| GET | `/api/health` | `backend/app/__init__.py` |
| POST | `/api/auth/register` | `backend/app/api/auth.py` |
| POST | `/api/auth/login` | `backend/app/api/auth.py` |
| POST | `/api/auth/refresh` | `backend/app/api/auth.py` |
| GET | `/api/repositories/<repo_id>/pending-updates` | `backend/app/api/pending_updates.py` |
| GET | `/api/repositories/<repo_id>/pending-updates/<update_id>` | `backend/app/api/pending_updates.py` |
| POST | `/api/repositories/<repo_id>/pending-updates/<update_id>/approve` | `backend/app/api/pending_updates.py` |
| POST | `/api/repositories/<repo_id>/pending-updates/<update_id>/reject` | `backend/app/api/pending_updates.py` |
| GET | `/api/repositories/<repo_id>/readme` | `backend/app/api/readmes.py` |
| PUT | `/api/repositories/<repo_id>/readme` | `backend/app/api/readmes.py` |
| GET | `/api/repositories/<repo_id>/readme/versions` | `backend/app/api/readmes.py` |
| GET | `/api/repositories/<repo_id>/readme/versions/<int:version_number>` | `backend/app/api/readmes.py` |
| POST | `/api/repositories/<repo_id>/readme/versions/<int:version_number>/rollback` | `backend/app/api/readmes.py` |
| GET | `/api/repositories` | `backend/app/api/repositories.py` |
| POST | `/api/repositories` | `backend/app/api/repositories.py` |
| GET | `/api/repositories/<repo_id>` | `backend/app/api/repositories.py` |
| PATCH | `/api/repositories/<repo_id>/sync-mode` | `backend/app/api/repositories.py` |
| POST | `/api/webhooks/github/<repo_id>` | `backend/app/api/webhooks.py` |
| GET | `/api/webhooks/<repo_id>/events` | `backend/app/api/webhooks.py` |

---

## Dépendances importantes

Aucune dépendance importante détectée.

---

## Recommandations

- {'type': "absence de gestion d'erreur visible", 'description': "L'endpoint API /api/auth/register ne gère pas les erreurs de validation des données"}
- {'type': 'dépendance non utilisée', 'description': "La dépendance 'requests' n'est pas utilisée dans le code"}
