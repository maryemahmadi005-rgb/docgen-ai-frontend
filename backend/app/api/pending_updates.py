from __future__ import annotations

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.container import get_container
from app.models.pending_update import PendingUpdateStatus
from app.models.readme_version import TriggeredBy
from app.services.sync_orchestrator import SyncOrchestratorError

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
    Approuve une proposition.

    Avant ce fix, cet endpoint mettait seulement à jour generated_readmes/
    readme_versions en DB — il n'appelait jamais git_service.commit_and_push().
    "Approve" ne publiait donc jamais réellement sur GitHub. Il délègue
    maintenant à SyncOrchestrator.apply_pending(), qui fait réellement :
    vérification de fraîcheur (staleness) -> apply_patch -> commit+push
    -> nouvelle ReadmeVersion -> statut approved.
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

    try:
        result = container.sync_orchestrator.apply_pending(update_id, user_id)
        container.commit()
    except SyncOrchestratorError as e:
        container.rollback()
        # Le message distingue explicitement le cas "stale" (conflit avec un
        # nouveau commit distant) des autres échecs, pour que le frontend
        # puisse proposer "Regenerate README" comme demandé.
        return jsonify({"error": str(e)}), 409

    refreshed = container.pending_update_repository.get_by_id(update_id)
    return jsonify({**refreshed.to_dict(), "sync_result": result})


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

    try:
        container.sync_orchestrator.discard_pending(update_id, user_id, reason)
        container.commit()
    except SyncOrchestratorError as e:
        container.rollback()
        return jsonify({"error": str(e)}), 409

    refreshed = container.pending_update_repository.get_by_id(update_id)
    return jsonify(refreshed.to_dict())
