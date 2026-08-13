# Project Documentation

Analyser et générer des documents de synthèse automatiquement à partir d'un code source

---

## Fonctionnement général

Le projet utilise une approche de génération de document de synthèse basée sur l'analyse du code source. Lorsqu'une requête est envoyée au serveur, le système analyse le code source et génère un document de synthèse en fonction des informations contenues dans le code.

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

**Rôle :** Affiche le document de synthèse généré par le backend

**Classes principales :** `App`, `useEffect`
**Dépendances internes :** `React`
**Routes exposées :** `/api/refresh`

---

## Flux de données

Le flux de données se compose des appels HTTP entre le frontend et le backend, ainsi que les requêtes à l'API Ollama. Le backend analyse le code source et génère un document de synthèse qui est ensuite envoyé au frontend pour être affiché.

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
- Docker

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

- curl -X POST https://localhost:5173/api/auth/refresh


---

## Recommandations

Aucune recommandation spécifique détectée.

## Test automatique webhook
jbhjbdchbdc,nndc
## Webhook Test 2 
vgvhgvgh
jn,,vb,nbv cfvgbhn
,nbjhb vghjnbvghbhjn

## General Operation

This application analyzes the repository structure.

It detects the technologies used by the project.

It identifies important files and directories.

It generates technical documentation automatically.

The documentation can be synchronized when the repository changes.

## Test Automatic Sync

This section was added to test automatic README synchronization.
nbvghjnsdcbshdccdbshchhb
