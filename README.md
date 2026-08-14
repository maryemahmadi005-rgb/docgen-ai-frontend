# Project Documentation

Analyser et générer des documents automatiquement

---

## Fonctionnement général

Le projet utilise une approche de génération de document basée sur l'apprentissage automatique, en utilisant les technologies Ollama et React. Le flux de travail consiste à collecter des données de base, à les analyser avec Ollama pour extraire des informations pertinentes, puis à générer un document synthétique en fonction de ces informations.

---


## Technologies utilisées

- JavaScript
- Python
- Flask
- React

---

## Modules principaux

### Ollama
**Fichier :** `backend/app/models/analysis.py`

**Rôle :** Analyse de données et extraction d'informations

**Classes principales :** `AnalysisModel`, `DetectedChange`
**Dépendances internes :** `Flask`, `db`, `migrate`, `jwt`
### React
**Fichier :** `readme-sync-frontend/src/App.jsx`

**Rôle :** Interface utilisateur et génération de document

**Classes principales :** `App`, `DocumentGenerator`
**Dépendances internes :** `Flask`, `api/client.js`

---

## Flux de données

Les données collectées sont analysées par Ollama pour extraire des informations pertinentes, puis ces informations sont transmises à React pour être utilisées dans la génération du document.

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

**Services externes**

- Ollama
- Docker

**Commandes de démarrage**

- docker-compose up -d
- python backend/app/__init__.py


---

## Usage

**Démarrage de l'application**

- docker-compose up -d
- python backend/app/__init__.py


---

## Recommandations

- {'type': "erreur de gestion d'erreur", 'description': "L'application n'a pas de mécanisme de gestion d'erreurs robuste."}
- 
## Usage

**Démarrage de l'application**

- docker-compose up -d
- python backend/app/__init__.py

- 
