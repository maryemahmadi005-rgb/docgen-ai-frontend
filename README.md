# Project Documentation

Analyser et générer des documents de synthèse pour les projets Open Source

---

## Fonctionnement général

Le flux réel fonctionne comme suit : une requête HTTP est envoyée à l'endpoint API /api/health, qui renvoie un JSON contenant le statut du serveur. Le client frontend (readme-sync-frontend) envoie ensuite une requête POST à l'endpoint API /auth/refresh pour obtenir un token de refresh, qui est utilisé pour authentifier les appels suivants.

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

**Classes principales :** `Flask`, `get_config`, `db`, `migrate`, `jwt`, `cors`
**Fonctions importantes :** `create_app`, `health`
**Dépendances internes :** `flask`, `requests`, `itsdangerous`, `werkzeug`
### backend/app/api/auth.py
**Fichier :** `backend/app/api/auth.py`

**Rôle :** Gère les appels d'authentification et de refresh token

**Classes principales :** `Blueprint`, `URLSafeTimedSerializer`, `generate_password_hash`, `check_password_hash`
**Fonctions importantes :** `register_blueprints`, `_oauth_serializer`, `_create_github_state`
**Dépendances internes :** `flask`, `requests`, `itsdangerous`, `werkzeug`
**Routes exposées :** `{'endpoint': '/api/auth/register', 'methods': ['POST']}`, `{'endpoint': '/api/auth/login', 'methods': ['POST']}`
### readme-sync-frontend/src/api/client.js
**Fichier :** `readme-sync-frontend/src/api/client.js`

**Rôle :** Envoie les requêtes HTTP à l'endpoint API /auth/refresh

**Fonctions importantes :** `POST`, `_oauth_serializer`
**Dépendances internes :** `axios`
**Routes exposées :** `{'endpoint': '${API_URL}/auth/refresh', 'methods': ['POST']}`

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

- {'type': "erreur de gestion d'erreur", 'description': "L'endpoint API /api/health n'a pas de gestion d'erreur pour les erreurs HTTP"}
- {'type': 'dépendance non utilisée', 'description': "La dépendance 'requests' n'est pas utilisée dans le code"}
