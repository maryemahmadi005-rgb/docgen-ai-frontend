from __future__ import annotations

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.container import get_container
from app.models.readme_version import TriggeredBy

readmes_bp = Blueprint("readmes", __name__, url_prefix="/api/repositories/<repo_id>/readme")


def _ensure_repo_owned(container, repo_id: str, user_id: str):
    repo = container.repository_repository.get_by_id(repo_id)
    if not repo or repo.user_id != user_id:
        return None
    return repo


@readmes_bp.get("")
@jwt_required()
def get_current_readme(repo_id: str):
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    return jsonify(readme.to_dict())


@readmes_bp.put("")
@jwt_required()
def update_readme_manually(repo_id: str):
    """Édition manuelle du README -> crée une nouvelle version (manual_edit)."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    content_md = data.get("content_md")
    sections_json = data.get("sections_json")

    if content_md is None or sections_json is None:
        return jsonify({"error": "content_md et sections_json sont requis"}), 400

    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    version = container.readme_version_repository.create_next_version(
        readme_id=readme.id,
        sections_json=sections_json,
        content_md=content_md,
        triggered_by=TriggeredBy.manual_edit,
    )
    readme = container.readme_repository.update_content(
        readme, sections_json, content_md, current_version_id=version.id
    )
    container.commit()

    return jsonify(readme.to_dict())


@readmes_bp.get("/versions")
@jwt_required()
def list_versions(repo_id: str):
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    versions = container.readme_version_repository.find_by_readme(readme.id)
    return jsonify([v.to_dict(include_content=False) for v in versions])


@readmes_bp.get("/versions/<int:version_number>")
@jwt_required()
def get_version(repo_id: str, version_number: int):
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    version = container.readme_version_repository.find_by_version_number(readme.id, version_number)
    if not version:
        return jsonify({"error": "Version introuvable"}), 404

    return jsonify(version.to_dict())


@readmes_bp.post("/versions/<int:version_number>/rollback")
@jwt_required()
def rollback_to_version(repo_id: str, version_number: int):
    """Restaure une ancienne version comme état courant (sans la supprimer de l'historique)."""
    user_id = get_jwt_identity()
    container = get_container()

    if not _ensure_repo_owned(container, repo_id, user_id):
        return jsonify({"error": "Repository introuvable"}), 404

    readme = container.readme_repository.find_by_repository(repo_id)
    if not readme:
        return jsonify({"error": "Aucun README généré pour ce repository"}), 404

    target_version = container.readme_version_repository.find_by_version_number(
        readme.id, version_number
    )
    if not target_version:
        return jsonify({"error": "Version introuvable"}), 404

    # Le rollback crée une NOUVELLE version (traçabilité), pointant sur le contenu restauré
    new_version = container.readme_version_repository.create_next_version(
        readme_id=readme.id,
        sections_json=target_version.sections_json,
        content_md=target_version.content_md,
        triggered_by=TriggeredBy.manual_edit,
    )
    readme = container.readme_repository.update_content(
        readme,
        target_version.sections_json,
        target_version.content_md,
        current_version_id=new_version.id,
    )
    container.commit()

    return jsonify(readme.to_dict())
