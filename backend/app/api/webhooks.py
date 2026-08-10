from __future__ import annotations

import hashlib
import hmac

from flask import Blueprint, request, jsonify, current_app

from app.container import get_container

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")


def _verify_signature(payload_body: bytes, secret: str, signature_header: str | None) -> bool:
    """Vérifie la signature HMAC-SHA256 envoyée par GitHub (X-Hub-Signature-256)."""
    if not signature_header or not secret:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@webhooks_bp.post("/github/<repo_id>")
def github_webhook(repo_id: str):
    """
    Endpoint public appelé par GitHub à chaque push (ou autre event configuré).
    Pas de @jwt_required ici : l'authentification se fait via la signature HMAC.
    """
    container = get_container()
    repo = container.repository_repository.get_by_id(repo_id)

    if not repo:
        return jsonify({"error": "Repository introuvable"}), 404

    delivery_id = request.headers.get("X-GitHub-Delivery")
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not delivery_id:
        return jsonify({"error": "En-tête X-GitHub-Delivery manquant"}), 400

    # --- Idempotency : ignorer les redéliveries déjà connues ---
    if container.webhook_event_repository.exists(delivery_id):
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
        current_app.logger.warning(
            "Signature webhook invalide pour repo=%s delivery=%s", repo.id, delivery_id
        )
        return jsonify({"error": "Signature invalide"}), 401

    if event_type == "ping":
        container.webhook_event_repository.mark_processed(event)
        container.commit()
        return jsonify({"status": "pong"}), 200

    if event_type == "push":
        # Le traitement réel (fetch commits, diff analysis, génération...)
        # est délégué à un job asynchrone (Celery/RQ) déclenché ici.
        # On se contente d'enregistrer l'event pour l'instant.
        # ex: enqueue_push_processing.delay(repo.id, event.id)
        pass

    return jsonify({"status": "received", "event_id": event.id}), 202


@webhooks_bp.get("/<repo_id>/events")
def list_webhook_events(repo_id: str):
    """Historique des events reçus pour un repo (utile pour debug/audit)."""
    container = get_container()
    events = container.webhook_event_repository.find_by_repository(repo_id)
    return jsonify([e.to_dict() for e in events])
