from __future__ import annotations

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.container import get_container
from app.models.pending_update import PendingUpdateStatus
from app.models.readme_version import TriggeredBy

pending_updates_bp = Blueprint(
    "pending_updates", __name__, url_prefix="/api/repositories/<repo_id>/pending-updates"
)


def _ensure_repo_owned(container, repo_id: str, user_id: str):
    repo = container.repository_repository.get_by_id(repo_id)
    if not repo or repo.user_id != user_id:
        return None
    return repo


@pending_updates_bp.get("")
@jwt_required()
def list_pending_updates(repo_id: str):
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    status_param = request.args.get("status")
    status = PendingUpdateStatus(status_param) if status_param else None

    updates = container.pending_update_repository.find_by_repository(repo_id, status=status)
    return jsonify([u.to_dict(include_content=False) for u in updates])


@pending_updates_bp.get("/<update_id>")
@jwt_required()
def get_pending_update(repo_id: str, update_id: str):
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    update = container.pending_update_repository.get_by_id(update_id)
    if not update or update.repository_id != repo_id:
        return jsonify({"error": "Proposition introuvable"}), 404

    return jsonify(update.to_dict())


@pending_updates_bp.post("/<update_id>/approve")
@jwt_required()
def approve_pending_update(repo_id: str, update_id: str):
    """
    Approuve une proposition -> crée une nouvelle readme_version (sync_manual_approved)
    et met à jour l'état courant du README.
    """
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    update = container.pending_update_repository.get_by_id(update_id)
    if not update or update.repository_id != repo_id:
        return jsonify({"error": "Proposition introuvable"}), 404

    if update.status != PendingUpdateStatus.pending:
        return jsonify({"error": f"Cette proposition est déjà '{update.status.value}'"}), 409

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    version = container.readme_version_repository.create_next_version(
        readme_id=readme.id,
        sections_json=update.proposed_sections_json,
        content_md=update.proposed_content_md,
        triggered_by=TriggeredBy.sync_manual_approved,
    )
    container.readme_repository.update_content(
        readme,
        update.proposed_sections_json,
        update.proposed_content_md,
        current_version_id=version.id,
    )
    update = container.pending_update_repository.approve(update, resolved_by=user_id)
    container.commit()

    return jsonify(update.to_dict())


@pending_updates_bp.post("/<update_id>/reject")
@jwt_required()
def reject_pending_update(repo_id: str, update_id: str):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")

    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    update = container.pending_update_repository.get_by_id(update_id)
    if not update or update.repository_id != repo_id:
        return jsonify({"error": "Proposition introuvable"}), 404

    if update.status != PendingUpdateStatus.pending:
        return jsonify({"error": f"Cette proposition est déjà '{update.status.value}'"}), 409

    update = container.pending_update_repository.reject(update, resolved_by=user_id, reason=reason)
    container.commit()

    return jsonify(update.to_dict())
