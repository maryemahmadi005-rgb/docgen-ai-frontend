# Project Documentation

Gérer les données de code et fournir des recommandations pour améliorer la qualité du code

---

## Fonctionnement général

Le flux réel fonctionne comme suit : une requête HTTP est envoyée à l'endpoint API, qui envoie ensuite la requête vers le service de base de données/LLM. Le résultat est ensuite renvoyé à l'endpoint API, qui le traite et le retourne au frontend. Les interactions entre les composants sont observées dans les preuves.

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

**Rôle :** Création de l'application Flask et configuration des extensions

**Classes principales :** `Flask`, `get_config`, `db`, `migrate`, `jwt`, `cors`
**Fonctions importantes :** `create_app`, `health`
**Dépendances internes :** `app.config`, `app.extensions`
### backend/app/api/auth.py
**Fichier :** `backend/app/api/auth.py`

**Rôle :** Gestion des utilisateurs et authentification

**Classes principales :** `auth_bp`, `_oauth_serializer`
**Fonctions importantes :** `register_blueprints`, `_create_github_state`
**Dépendances internes :** `app.container`, `app.utils.encryption`
**Routes exposées :** `{'endpoint': '/api/auth/register', 'method': 'POST'}`, `{'endpoint': '/api/auth/login', 'method': 'POST'}`
### backend/app/api/pending_updates.py
**Fichier :** `backend/app/api/pending_updates.py`

**Rôle :** Gestion des mises à jour pendantes et validation du JSON

**Classes principales :** `pending_updates_bp`, `_oauth_serializer`
**Fonctions importantes :** `register_blueprints`, `get_pending_updates`
**Dépendances internes :** `app.container`, `app.utils.encryption`
**Routes exposées :** `{'endpoint': '/api/repositories/<repo_id>/pending-updates', 'method': 'GET'}`, `{'endpoint': '/api/repositories/<repo_id>/pending-updates/<update_id>', 'method': 'GET'}`

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

Aucune recommandation spécifique détectée.
