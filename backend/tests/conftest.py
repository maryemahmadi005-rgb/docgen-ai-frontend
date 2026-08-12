"""
Fixtures partagées pour les tests de la synchronisation README <-> GitHub.

Stratégie :
- DB réelle mais en mémoire (SQLite, via TestingConfig) : on veut valider
  le câblage réel (container, repositories, services), pas seulement des
  mocks isolés.
- GitService et AIService sont monkeypatchés au niveau des méthodes de
  classe (fetch/get_diff/commit_and_push, classify_impact/generate_section)
  car Container() recrée une instance à chaque requête (get_container()) :
  patcher l'instance ne suffirait pas.
- Un vrai serveur Git / Ollama n'est jamais requis pour ces tests.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid

import pytest

from app import create_app
from app.extensions import db as _db
from app.services.git_service import GitService, FileChange
from app.services.ai_service import AIService
from app.models.user import User
from app.models.repository import Repository, SyncMode, SyncMethod
from app.models.generated_readme import GeneratedReadme
from app.models.readme_version import ReadmeVersion, TriggeredBy


# ---------------------------------------------------------------------
# App / DB
# ---------------------------------------------------------------------

@pytest.fixture()
def app():
    flask_app = create_app("testing")
    flask_app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        TESTING=True,
    )

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    return _db.session


# ---------------------------------------------------------------------
# Seed data — utilisateur + repository + README initial déjà généré
# ---------------------------------------------------------------------

INITIAL_SECTIONS = {
    "project_goal": "Un outil de gestion de tâches.",
    "general_operation": "Le serveur expose une API REST.",
    "architecture": {},
    "technologies": ["Python", "Flask"],
    "main_modules": ["app/core"],
    "data_flow": "Client -> API -> DB",
    "entry_points": ["app/__init__.py"],
    "api_endpoints": [],
    "important_dependencies": ["flask"],
    "recommendations": [],
}


@pytest.fixture()
def seed(app, session):
    """
    Crée un user + un repository (sync_mode=manual par défaut) + un
    GeneratedReadme + sa ReadmeVersion #1 (triggered_by=initial_generation),
    exactement comme le laisserait la génération initiale déjà existante
    (que ce test ne réimplémente pas).
    """
    user = User(email=f"{uuid.uuid4()}@example.com", github_token="fake-token")
    session.add(user)
    session.flush()

    repo = Repository(
        user_id=user.id,
        github_url="https://github.com/acme/widgets.git",
        full_name="acme/widgets",
        default_branch="main",
        tracked_branch="main",
        local_clone_path="/data/repo_clones/fake",
        sync_mode=SyncMode.manual,
        sync_method=SyncMethod.webhook,
        webhook_secret="s3cr3t",
    )
    session.add(repo)
    session.flush()

    readme = GeneratedReadme(
        repository_id=repo.id,
        sections_json=dict(INITIAL_SECTIONS),
        content_md="# Project Documentation\n\n(contenu initial)\n",
    )
    session.add(readme)
    session.flush()

    version = ReadmeVersion(
        readme_id=readme.id,
        version_number=1,
        sections_json=dict(INITIAL_SECTIONS),
        content_md=readme.content_md,
        triggered_by=TriggeredBy.initial_generation,
    )
    session.add(version)
    session.flush()

    readme.current_version_id = version.id
    session.flush()
    session.commit()

    return {"user": user, "repository": repo, "readme": readme, "version": version}


@pytest.fixture()
def auth_headers(app, seed):
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(identity=seed["user"].id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------
# Mocks GitService / AIService
# ---------------------------------------------------------------------

@pytest.fixture()
def git_diffs(monkeypatch):
    """
    Contrôle ce que GitService.get_diff() renvoie pour un after_sha donné.
    Usage : git_diffs["<after_sha>"] = [FileChange(...), ...]
    """
    store: dict[str, list[FileChange]] = {}

    def fake_fetch(self, local_path, auth_token=None):
        return None

    def fake_get_diff(self, local_path, before_sha, after_sha, exclude_paths=None):
        return store.get(after_sha, [])

    pushed = []

    def fake_commit_and_push(self, local_path, file_paths, commit_message,
                              author_name="readme-bot", author_email="readme-bot@yourapp.io",
                              branch=None, auth_token=None):
        sha = f"botsha-{len(pushed)}"
        pushed.append({"message": commit_message, "author_email": author_email, "sha": sha})
        return sha

    monkeypatch.setattr(GitService, "fetch", fake_fetch)
    monkeypatch.setattr(GitService, "get_diff", fake_get_diff)
    monkeypatch.setattr(GitService, "commit_and_push", fake_commit_and_push)

    store["_pushed"] = pushed  # expose pour assertions
    return store


@pytest.fixture()
def ai_stub(monkeypatch):
    """
    Empêche tout appel réseau réel vers Ollama.
    generate_section() renvoie un contenu déterministe et distinct de
    old_content, pour que has_real_changes() détecte bien un changement.
    """

    def fake_classify_impact(self, file_changes, repo_context=""):
        return {"impact_category": "none", "affected_sections": [], "confidence_score": 0.3}

    def fake_generate_section(self, section_name, old_content, relevant_files):
        if isinstance(old_content, list):
            return old_content + [f"nouveau-{section_name}"]
        return f"[MAJ AI] {section_name} mis à jour ({len(relevant_files)} fichier(s))."

    monkeypatch.setattr(AIService, "classify_impact", fake_classify_impact)
    monkeypatch.setattr(AIService, "generate_section", fake_generate_section)


# ---------------------------------------------------------------------
# Helper webhook payload signé
# ---------------------------------------------------------------------

def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def make_push_payload(before, after, branch="main", author_email="dev@example.com",
                       author_name="Dev", files=()):
    return {
        "before": before,
        "after": after,
        "ref": f"refs/heads/{branch}",
        "pusher": {"name": author_name},
        "head_commit": {"author": {"name": author_name, "email": author_email}},
        "commits": [{"id": after}],
    }


def post_webhook(client, repo_id, secret, payload, delivery_id=None, event_type="push"):
    body = json.dumps(payload).encode("utf-8")
    delivery_id = delivery_id or str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event_type,
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": sign(secret, body),
    }
    return client.post(f"/api/webhooks/github/{repo_id}", data=body, headers=headers)
