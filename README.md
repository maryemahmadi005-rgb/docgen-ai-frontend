# Project Documentation

Analyser et générer des documents automatiquement

---

## Fonctionnement général

Le projet utilise une approche hybride pour analyser les fichiers et générer des documents. Le flux de données se déroule comme suit : le frontend envoie une requête à l'API backend, qui envoie ensuite la requête au service d'analyse. Ce service utilise un modèle Ollama pour analyser le fichier et générer un document. Les résultats sont ensuite envoyés à la base de données, qui les stocke.

---


## Technologies utilisées

- JavaScript
- Python
- Flask
- React

---

## Modules principaux

### Backend
**Fichier :** `backend/app/__init__.py`

**Rôle :** Gère les appels HTTP vers Ollama et la validation du JSON retourné

**Classes principales :** `Flask`, `get_config`, `db`, `migrate`, `jwt`, `cors`
**Dépendances internes :** `Flask`, `Python`
**Routes exposées :** `/api/health`
### Frontend
**Fichier :** `readme-sync-frontend/src/App.jsx`

**Rôle :** Affiche le document généré par le backend

**Classes principales :** `App`, `api/client`
**Dépendances internes :** `React`, `Python`
**Routes exposées :** `/`

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

---

## Dépendances importantes

Aucune dépendance importante détectée.

---

## Installation

**Prérequis**

- Python 3.11+

**Installation backend**

- docker-compose up -d
- python backend/app/__init__.py

**Installation frontend**

- npm install
- npm run build

**Configuration**

- .env.example

**Services externes**

- Ollama
- base de données

**Commandes de démarrage**

- docker-compose up -d


---

## Usage

**Démarrage de l'application**

- docker-compose up -d
- npm install
- npm run build

**API principale**

- /api/health
- /api/auth/register
- /api/auth/login
- /api/auth/refresh

**Exemple d'utilisation**

- curl -X POST https://localhost:5000/api/auth/refresh

**Flux frontend/backend**

- Frontend envoie une requête à l'API backend
- API backend envoie la requête au service d'analyse
- Service d'analyse utilise un modèle Ollama pour analyser le fichier et générer un document
- Résultats sont envoyés à la base de données


---

## Recommandations

Aucune recommandation spécifique détectée.
