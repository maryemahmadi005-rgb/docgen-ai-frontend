"""
Tests du flow : GitHub push -> Webhook -> DiffAnalyzer -> ReadmeUpdater
(generate_patch/apply_patch) -> ReadmeVersion -> (pending_update | commit+push).

Voir tests/conftest.py pour les fixtures (app, seed, git_diffs, ai_stub,
auth_headers, post_webhook/make_push_payload).
"""
from __future__ import annotations

from app.services.git_service import FileChange
from app.models.repository import SyncMode
from app.models.pending_update import PendingUpdateStatus
from app.models.readme_version import TriggeredBy
from app.extensions import db as _db

from tests.conftest import make_push_payload, post_webhook, INITIAL_SECTIONS


BEFORE = "a" * 40
AFTER = "b" * 40


# ---------------------------------------------------------------------
# Mode manual : crée un pending_update, ne push jamais
# ---------------------------------------------------------------------

def test_manual_mode_creates_pending_update_single_section(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="FROM python:3.12")]

    payload = make_push_payload(BEFORE, AFTER)
    resp = post_webhook(client, repo.id, repo.webhook_secret, payload)

    assert resp.status_code == 202
    body = resp.get_json()
    assert body["result"]["status"] == "processed"
    assert body["result"]["orchestrator_result"]["action"] == "pending_update_created"

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        updates = _db.session.query(PendingUpdate).filter_by(repository_id=repo.id).all()
        assert len(updates) == 1
        pu = updates[0]
        assert pu.status == PendingUpdateStatus.pending
        assert set(pu.sections_diff.keys()) == {"architecture"}
        # Aucun push ne doit avoir eu lieu en mode manuel.
        assert git_diffs["_pushed"] == []
        # Le README courant n'a pas bougé.
        readme = _db.session.get(type(seed["readme"]), seed["readme"].id)
        assert readme.current_version_id == seed["version"].id


# ---------------------------------------------------------------------
# Mode automatic : applique le patch, commit+push, crée une version
# ---------------------------------------------------------------------

def test_automatic_mode_applies_patch_and_pushes(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    with app.app_context():
        repo_db = _db.session.get(type(repo), repo.id)
        repo_db.sync_mode = SyncMode.automatic
        _db.session.commit()

    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="FROM python:3.12")]

    payload = make_push_payload(BEFORE, AFTER)
    resp = post_webhook(client, repo.id, repo.webhook_secret, payload)

    assert resp.status_code == 202
    result = resp.get_json()["result"]["orchestrator_result"]
    assert result["action"] == "auto_synced"
    assert result["sections"] == ["architecture"]

    assert len(git_diffs["_pushed"]) == 1
    assert "[skip-readme-sync]" in git_diffs["_pushed"][0]["message"]

    with app.app_context():
        from app.models.readme_version import ReadmeVersion
        readme = _db.session.get(type(seed["readme"]), seed["readme"].id)
        versions = _db.session.query(ReadmeVersion).filter_by(readme_id=readme.id).order_by(
            ReadmeVersion.version_number
        ).all()
        assert len(versions) == 2
        v2 = versions[-1]
        assert v2.triggered_by == TriggeredBy.sync_auto
        assert readme.current_version_id == v2.id

        # Seule "architecture" a changé, tout le reste est intact.
        for key, value in INITIAL_SECTIONS.items():
            if key == "architecture":
                assert v2.sections_json[key] != value
            else:
                assert v2.sections_json[key] == value

        # Le markdown rendu reflète bien le nouveau contenu.
        assert v2.content_md == readme.content_md


def test_automatic_mode_multiple_sections_affected(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    with app.app_context():
        repo_db = _db.session.get(type(repo), repo.id)
        repo_db.sync_mode = SyncMode.automatic
        _db.session.commit()

    git_diffs[AFTER] = [
        FileChange(path="requirements.txt", change_type="modified", diff_excerpt="+flask==3.0"),
        FileChange(path="Dockerfile", change_type="modified", diff_excerpt="FROM python:3.12"),
    ]

    payload = make_push_payload(BEFORE, AFTER)
    resp = post_webhook(client, repo.id, repo.webhook_secret, payload)

    result = resp.get_json()["result"]["orchestrator_result"]
    assert result["action"] == "auto_synced"
    assert set(result["sections"]) == {"technologies", "important_dependencies", "architecture"}

    with app.app_context():
        readme = _db.session.get(type(seed["readme"]), seed["readme"].id)
        for key in ("technologies", "important_dependencies", "architecture"):
            assert readme.sections_json[key] != INITIAL_SECTIONS[key]
        for key in ("project_goal", "general_operation", "main_modules", "data_flow",
                    "entry_points", "api_endpoints", "recommendations"):
            assert readme.sections_json[key] == INITIAL_SECTIONS[key]


# ---------------------------------------------------------------------
# Commit sans impact réel sur le README
# ---------------------------------------------------------------------

def test_commit_without_readme_impact_creates_no_version(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="CHANGELOG.md", change_type="modified", diff_excerpt="- fix typo")]

    payload = make_push_payload(BEFORE, AFTER)
    resp = post_webhook(client, repo.id, repo.webhook_secret, payload)

    result = resp.get_json()["result"]["orchestrator_result"]
    assert result["action"] == "no_update_needed"
    assert git_diffs["_pushed"] == []

    with app.app_context():
        from app.models.readme_version import ReadmeVersion
        from app.models.pending_update import PendingUpdate
        versions = _db.session.query(ReadmeVersion).filter_by(readme_id=seed["readme"].id).all()
        assert len(versions) == 1  # seulement la version initiale
        assert _db.session.query(PendingUpdate).count() == 0


# ---------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------

def test_duplicate_webhook_same_delivery_id_is_ignored(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]
    payload = make_push_payload(BEFORE, AFTER)

    resp1 = post_webhook(client, repo.id, repo.webhook_secret, payload, delivery_id="delivery-1")
    assert resp1.status_code == 202

    resp2 = post_webhook(client, repo.id, repo.webhook_secret, payload, delivery_id="delivery-1")
    assert resp2.status_code == 200
    assert resp2.get_json()["status"] == "already_processed"

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        assert _db.session.query(PendingUpdate).count() == 1


def test_duplicate_after_sha_different_delivery_is_ignored(app, client, seed, git_diffs, ai_stub):
    """Deux deliveries GitHub distinctes pour le même push (même after_sha)."""
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]
    payload = make_push_payload(BEFORE, AFTER)

    resp1 = post_webhook(client, repo.id, repo.webhook_secret, payload, delivery_id="delivery-A")
    assert resp1.get_json()["result"]["status"] == "processed"

    resp2 = post_webhook(client, repo.id, repo.webhook_secret, payload, delivery_id="delivery-B")
    assert resp2.status_code == 202
    assert resp2.get_json()["result"] == {"status": "ignored", "reason": "already_processed"}

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        assert _db.session.query(PendingUpdate).count() == 1


# ---------------------------------------------------------------------
# Anti-loop : commit généré par le bot lui-même
# ---------------------------------------------------------------------

def test_bot_generated_commit_does_not_retrigger_sync(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]

    payload = make_push_payload(BEFORE, AFTER, author_email="readme-bot@yourapp.io", author_name="readme-bot")
    resp = post_webhook(client, repo.id, repo.webhook_secret, payload)

    assert resp.status_code == 202
    assert resp.get_json()["result"] == {"status": "ignored", "reason": "bot_commit"}

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        from app.models.readme_version import ReadmeVersion
        assert _db.session.query(PendingUpdate).count() == 0
        assert _db.session.query(ReadmeVersion).count() == 1


# ---------------------------------------------------------------------
# Approve / Reject d'un pending_update
# ---------------------------------------------------------------------

def test_approve_pending_update_applies_patch_and_pushes(app, client, seed, git_diffs, ai_stub, auth_headers):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]
    post_webhook(client, repo.id, repo.webhook_secret, make_push_payload(BEFORE, AFTER))

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        pu = _db.session.query(PendingUpdate).filter_by(repository_id=repo.id).one()
        pu_id = pu.id

    resp = client.post(f"/api/repositories/{repo.id}/pending-updates/{pu_id}/approve", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "approved"
    assert body["sync_result"]["action"] == "approved_and_synced"

    assert len(git_diffs["_pushed"]) == 1

    with app.app_context():
        from app.models.readme_version import ReadmeVersion
        versions = _db.session.query(ReadmeVersion).filter_by(readme_id=seed["readme"].id).all()
        assert len(versions) == 2
        assert any(v.triggered_by == TriggeredBy.sync_manual_approved for v in versions)


def test_reject_pending_update_never_pushes(app, client, seed, git_diffs, ai_stub, auth_headers):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]
    post_webhook(client, repo.id, repo.webhook_secret, make_push_payload(BEFORE, AFTER))

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        pu = _db.session.query(PendingUpdate).filter_by(repository_id=repo.id).one()
        pu_id = pu.id

    resp = client.post(
        f"/api/repositories/{repo.id}/pending-updates/{pu_id}/reject",
        json={"reason": "pas pertinent"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "rejected"
    assert git_diffs["_pushed"] == []


def test_new_commit_marks_previous_pending_update_stale(app, client, seed, git_diffs, ai_stub):
    repo = seed["repository"]
    git_diffs[AFTER] = [FileChange(path="Dockerfile", change_type="modified", diff_excerpt="x")]
    post_webhook(client, repo.id, repo.webhook_secret, make_push_payload(BEFORE, AFTER))

    after2 = "c" * 40
    git_diffs[after2] = [FileChange(path="requirements.txt", change_type="modified", diff_excerpt="+flask")]
    post_webhook(client, repo.id, repo.webhook_secret, make_push_payload(AFTER, after2))

    with app.app_context():
        from app.models.pending_update import PendingUpdate
        updates = _db.session.query(PendingUpdate).filter_by(repository_id=repo.id).order_by(
            PendingUpdate.created_at
        ).all()
        assert len(updates) == 2
        assert updates[0].status == PendingUpdateStatus.stale
        assert updates[1].status == PendingUpdateStatus.pending
