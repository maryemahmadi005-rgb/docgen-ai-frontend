from __future__ import annotations

import hashlib
import hmac

from flask import Blueprint, request, jsonify, current_app

from app.container import get_container
from app.services.commit_detector import PushEvent, CommitDetectorError
from app.services.sync_orchestrator import SyncOrchestratorError
from app.services.git_service import GitServiceError

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")


def _verify_signature(payload_body: bytes, secret: str, signature_header: str | None) -> bool:
    """Vérifie la signature HMAC-SHA256 envoyée par GitHub (X-Hub-Signature-256)."""
    if not signature_header or not secret:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _branch_from_ref(ref: str | None) -> str | None:
    """'refs/heads/main' -> 'main'. None si ce n'est pas une branche (ex: tag)."""
    if not ref or not ref.startswith("refs/heads/"):
        return None
    return ref[len("refs/heads/"):]


@webhooks_bp.post("/github/<repo_id>")
def github_webhook(repo_id: str):
    """
    Endpoint public appelé par GitHub à chaque push (ou autre event configuré).
    Pas de @jwt_required ici : l'authentification se fait via la signature HMAC.
    """
    print(f"[WEBHOOK RECEIVED] repo_id={repo_id} event={request.headers.get('X-GitHub-Event')} "
          f"delivery={request.headers.get('X-GitHub-Delivery')}")

    container = get_container()
    repo = container.repository_repository.get_by_id(repo_id)

    if not repo:
        print(f"[REPOSITORY] introuvable pour repo_id={repo_id} — webhook ignoré")
        return jsonify({"error": "Repository introuvable"}), 404

    print(f"[REPOSITORY FOUND] id={repo.id} full_name={repo.full_name} "
          f"tracked_branch={repo.tracked_branch or repo.default_branch} sync_mode={repo.sync_mode.value}")

    delivery_id = request.headers.get("X-GitHub-Delivery")
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not delivery_id:
        return jsonify({"error": "En-tête X-GitHub-Delivery manquant"}), 400

    # --- Idempotency : ignorer les redéliveries déjà connues ---
    if container.webhook_event_repository.exists(delivery_id):
        print(f"[WEBHOOK] delivery={delivery_id} déjà traité (redélivrance GitHub) — ignoré")
        return jsonify({"status": "already_processed"}), 200

    signature_valid = _verify_signature(
        request.get_data(), repo.webhook_secret or "", signature_header
    )

    payload = request.get_json(silent=True) or {}
    payload_summary = {
        "before": payload.get("before"),
        "after": payload.get("after"),
        "ref": payload.get("ref"),
        "pusher": (payload.get("pusher") or {}).get("name"),
    }

    event = container.webhook_event_repository.create(
        repository_id=repo.id,
        delivery_id=delivery_id,
        event_type=event_type,
        signature_valid=signature_valid,
        payload_summary=payload_summary,
    )
    container.commit()

    if not signature_valid:
        print(f"[WEBHOOK] signature HMAC invalide pour repo={repo.id} delivery={delivery_id}")
        current_app.logger.warning(
            "Signature webhook invalide pour repo=%s delivery=%s", repo.id, delivery_id
        )
        return jsonify({"error": "Signature invalide"}), 401

    if event_type == "ping":
        container.webhook_event_repository.mark_processed(event)
        container.commit()
        print(f"[WEBHOOK] event=ping repo={repo.id} — pong")
        return jsonify({"status": "pong"}), 200

    if event_type != "push":
        print(f"[WEBHOOK] event={event_type} non géré (seul 'push' déclenche la sync) — enregistré, non traité")
        return jsonify({"status": "received", "event_id": event.id}), 202

    # ------------------------------------------------------------------
    # event_type == "push" : c'était un simple `pass` avant ce fix — la
    # cause exacte pour laquelle un vrai push GitHub ne produisait jamais
    # de PendingUpdate. On câble maintenant réellement le pipeline.
    # ------------------------------------------------------------------
    before_sha = payload.get("before")
    after_sha = payload.get("after")
    branch = _branch_from_ref(payload.get("ref"))
    commits_payload = payload.get("commits", [])

    print(f"[BEFORE SHA] {before_sha}")
    print(f"[AFTER SHA] {after_sha}")
    print(f"[COMMITS FOUND] {len(commits_payload)} commit(s) dans le payload push")

    if not before_sha or not after_sha or not branch:
        print(f"[WEBHOOK] payload push incomplet (before/after/ref manquant) — ignoré")
        container.webhook_event_repository.mark_processed(event)
        container.commit()
        return jsonify({"status": "ignored", "reason": "incomplete_payload"}), 200

    # Auteur : on prend head_commit si disponible, sinon pusher.
    head_commit = payload.get("head_commit") or {}
    author = head_commit.get("author") or {}
    author_name = author.get("name") or (payload.get("pusher") or {}).get("name") or "unknown"
    author_email = author.get("email") or "unknown@unknown"

    push_event = PushEvent(
        repository_id=repo.id,
        before_sha=before_sha,
        after_sha=after_sha,
        author_email=author_email,
        author_name=author_name,
        branch=branch,
    )

    try:
        result = container.commit_detector.handle_push_event(push_event)
        container.commit()
        print(f"[CHANGES DETECTED] résultat={result}")
    except CommitDetectorError as e:
        container.rollback()
        print(f"[WEBHOOK] ERREUR CommitDetector repo={repo.id}: {e}")
        current_app.logger.error("CommitDetector error repo=%s: %s", repo.id, e)
        return jsonify({"error": str(e)}), 500
    except GitServiceError as e:
        container.rollback()
        print(f"[WEBHOOK] ERREUR Git repo={repo.id}: {e}")
        current_app.logger.error("GitService error repo=%s: %s", repo.id, e)
        return jsonify({"error": str(e)}), 502
    except SyncOrchestratorError as e:
        container.rollback()
        print(f"[WEBHOOK] ERREUR SyncOrchestrator repo={repo.id}: {e}")
        current_app.logger.error("SyncOrchestrator error repo=%s: %s", repo.id, e)
        return jsonify({"error": str(e)}), 500

    container2 = get_container()
    fresh_event = container2.webhook_event_repository.get_by_id(event.id)
    if fresh_event is not None:
        container2.webhook_event_repository.mark_processed(fresh_event)
        container2.commit()

    return jsonify({"status": "processed", "event_id": event.id, "result": result}), 202


@webhooks_bp.get("/<repo_id>/events")
def list_webhook_events(repo_id: str):
    """Historique des events reçus pour un repo (utile pour debug/audit)."""
    container = get_container()
    events = container.webhook_event_repository.find_by_repository(repo_id)
    return jsonify([e.to_dict() for e in events])
