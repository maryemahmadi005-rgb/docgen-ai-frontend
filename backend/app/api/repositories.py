
from __future__ import annotations
import requests

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.container import get_container
from app.models.repository import SyncMode, SyncMethod
from app.services.git_service import GitServiceError
from app.services.readme_generator import ReadmeGeneratorError
from app.utils.encryption import EncryptionService, EncryptionError


repositories_bp = Blueprint(
    "repositories",
    __name__,
    url_prefix="/api/repositories",
)


# ============================================================
# LIST REPOSITORIES
# ============================================================

@repositories_bp.get("")
@jwt_required()
def list_repositories():
    user_id = get_jwt_identity()

    container = get_container()

    repos = container.repository_repository.find_by_user(user_id)

    return jsonify([r.to_dict() for r in repos])


# ============================================================
# CREATE REPOSITORY
# ============================================================

@repositories_bp.post("")
@jwt_required()
def create_repository():
    user_id = get_jwt_identity()

    data = request.get_json(silent=True) or {}

    github_url = data.get("github_url")
    full_name = data.get("full_name")
    default_branch = data.get("default_branch", "main")

    if not github_url or not full_name:
        return jsonify({
            "error": "github_url et full_name sont requis"
        }), 400

    container = get_container()

    existing = (
        container.repository_repository
        .find_by_user_and_fullname(user_id, full_name)
    )

    if existing:
        return jsonify({
            "error": "Ce repository est déjà tracké"
        }), 409

    try:
        sync_mode = SyncMode(
            data.get("sync_mode", SyncMode.manual.value)
        )

        sync_method = SyncMethod(
            data.get("sync_method", SyncMethod.webhook.value)
        )

    except ValueError:
        return jsonify({
            "error": "sync_mode ou sync_method invalide"
        }), 400

    repo = container.repository_repository.create(
        user_id=user_id,
        github_url=github_url,
        full_name=full_name,
        default_branch=default_branch,
        sync_mode=sync_mode,
        sync_method=sync_method,
    )

    container.commit()

    return jsonify(repo.to_dict()), 201


# ============================================================
# GET REPOSITORY
# ============================================================

@repositories_bp.get("/<repo_id>")
@jwt_required()
def get_repository(repo_id: str):
    user_id = get_jwt_identity()

    container = get_container()

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        return jsonify({
            "error": "Repository introuvable"
        }), 404

    return jsonify(repo.to_dict())


# ============================================================
# UPDATE SYNC MODE
# ============================================================

@repositories_bp.patch("/<repo_id>/sync-mode")
@jwt_required()
def update_sync_mode(repo_id: str):
    user_id = get_jwt_identity()

    data = request.get_json(silent=True) or {}

    new_mode = data.get("sync_mode")

    if new_mode not in (
        SyncMode.manual.value,
        SyncMode.automatic.value,
    ):
        return jsonify({
            "error": "sync_mode doit être 'manual' ou 'automatic'"
        }), 400

    container = get_container()

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        return jsonify({
            "error": "Repository introuvable"
        }), 404

    repo = container.repository_repository.update_sync_mode(
        repo,
        SyncMode(new_mode),
    )

    container.commit()

    return jsonify(repo.to_dict())


# ============================================================
# DELETE REPOSITORY
# ============================================================

@repositories_bp.delete("/<repo_id>")
@jwt_required()
def delete_repository(repo_id: str):
    user_id = get_jwt_identity()

    container = get_container()

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        return jsonify({
            "error": "Repository introuvable"
        }), 404

    container.repository_repository.delete(repo)

    container.commit()

    return "", 204


# ============================================================
# LIST COMMITS
# ============================================================

@repositories_bp.get("/<repo_id>/commits")
@jwt_required()
def list_commits(repo_id: str):
    user_id = get_jwt_identity()

    container = get_container()

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        return jsonify({
            "error": "Repository introuvable"
        }), 404

    limit = request.args.get(
        "limit",
        default=50,
        type=int,
    )

    offset = request.args.get(
        "offset",
        default=0,
        type=int,
    )

    commits = (
        container.commit_repository.find_by_repository(
            repo_id,
            limit=limit,
            offset=offset,
        )
    )

    return jsonify([
        c.to_dict()
        for c in commits
    ])


# ============================================================
# GET LATEST ANALYSIS
# ============================================================

@repositories_bp.get("/<repo_id>/analyses/latest")
@jwt_required()
def get_latest_analysis(repo_id: str):
    user_id = get_jwt_identity()

    container = get_container()

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        return jsonify({
            "error": "Repository introuvable"
        }), 404

    analysis = (
        container.analysis_repository
        .find_latest_for_repository(repo_id)
    )

    if not analysis:
        return jsonify({
            "error": "Aucune analyse trouvée"
        }), 404

    return jsonify(analysis.to_dict())


# ============================================================
# GENERATE INITIAL README
# ============================================================

@repositories_bp.post("/<repo_id>/generate")
@jwt_required()
def generate_readme(repo_id: str):
    """
    Génération initiale complète du README.

    Workflow:
        1. Récupérer repository
        2. Récupérer GitHub token
        3. Clone repository
        4. Vérifier remote
        5. Analyse statique
        6. Génération README avec Ollama
        7. Écrire README.md dans le clone
        8. Sauvegarder README + version en DB
        9. Commit + push vers GitHub
        10. Mettre à jour last_synced_commit_sha
    """

    user_id = get_jwt_identity()
    container = get_container()

    print(
        f"🚀 [README] DÉBUT GÉNÉRATION — "
        f"repo_id={repo_id}"
    )

    # ============================================================
    # 1. GET REPOSITORY
    # ============================================================

    repo = container.repository_repository.get_by_id(repo_id)

    if not repo or repo.user_id != user_id:
        print(
            f"❌ [README] ERREUR — repository introuvable — "
            f"repo_id={repo_id}"
        )

        return jsonify({
            "error": "Repository introuvable"
        }), 404

    # ============================================================
    # 2. GITHUB TOKEN
    # ============================================================

    auth_token = None

    if repo.user and repo.user.github_token:
        try:
            auth_token = EncryptionService().decrypt(
                repo.user.github_token
            )
            # TEST GITHUB TOKEN
            response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Accept": "application/vnd.github+json",
                },
            timeout=10,
            )

            print(
                f"🔐 [GITHUB TEST] status={response.status_code}"
)

            if response.status_code == 200:
                github_user = response.json().get("login")
                print(
                    f"✅ [GITHUB TEST] TOKEN VALIDE — "
                    f"user={github_user}"
                    )
            else:
                print(
                    f"❌ [GITHUB TEST] TOKEN INVALIDE — "
                    f"status={response.status_code}"
                    )
                return jsonify({
                    "error": "GitHub token invalide ou expiré",
                    "github_status": response.status_code,
                    }), 401

            print(
                f"🔐 [GITHUB] TOKEN RÉCUPÉRÉ — "
                f"repo_id={repo.id}"
            )

        except EncryptionError as exc:
            current_app.logger.warning(
                "Impossible de déchiffrer le token GitHub "
                "pour user=%s: %s",
                user_id,
                exc,
            )

            return jsonify({
                "error": (
                    "Impossible d'utiliser la connexion GitHub. "
                    "Veuillez reconnecter votre compte GitHub."
                )
            }), 401

    if not auth_token:
        return jsonify({
            "error": (
                "Compte GitHub non connecté ou token GitHub absent."
            )
        }), 401

    # ============================================================
    # 3. CLONE
    # ============================================================

    try:

        local_path = container.git_service.clone_repository(
            github_url=repo.github_url,
            repository_id=repo.id,
            auth_token=auth_token,
            branch=repo.tracked_branch,
        )

        repo.local_clone_path = local_path

        container.session.flush()

        print(
            f"✅ [README] CLONE OK — "
            f"repo_id={repo.id} — "
            f"path={local_path}"
        )

    except GitServiceError as exc:

        print(
            f"❌ [README] ERREUR — CLONE — "
            f"repo_id={repo.id} — {exc}"
        )

        return jsonify({
            "error": f"Échec du clone du repository: {exc}"
        }), 502

    # ============================================================
    # 4. VERIFY CLONE
    # ============================================================

    try:

        remote_ok = container.git_service.verify_remote_url(
            local_path=local_path,
            expected_url=repo.github_url,
        )

    except GitServiceError as exc:

        print(
            f"❌ [README] ERREUR — VÉRIFICATION CLONE — "
            f"repo_id={repo.id} — {exc}"
        )

        return jsonify({
            "error": (
                "Impossible de vérifier le repository cloné: "
                f"{exc}"
            )
        }), 502

    if not remote_ok:

        print(
            f"❌ [README] ERREUR — REMOTE MISMATCH — "
            f"repo_id={repo.id}"
        )

        return jsonify({
            "error": (
                "Le clone local ne correspond pas "
                "au repository demandé."
            )
        }), 502

    print(
        f"✅ [README] VÉRIF CLONE OK — "
        f"repo_id={repo.id}"
    )

    # ============================================================
    # 5. STATIC ANALYSIS
    # ============================================================

    try:

        analysis = container.analyzer_service.analyze(
            local_path,
            repository_id=repo.id,
        )

        print(
            f"🔎 [README] ANALYSE TERMINÉE — "
            f"repo_id={repo.id}"
        )

    except Exception as exc:

        container.rollback()

        current_app.logger.exception(
            "Erreur pendant l'analyse du repository"
        )

        return jsonify({
            "error": (
                f"Échec de l'analyse du repository: {exc}"
            )
        }), 502

    # ============================================================
    # 6. SAVE ANALYSIS
    # ============================================================

    try:

        container.analysis_repository.create(
            repository_id=repo.id,
            languages=analysis.languages,
            frameworks=analysis.frameworks,
            dependencies=analysis.dependencies,
            file_structure=analysis.file_structure,
            important_files=analysis.important_files,
            install_scripts=analysis.install_scripts,
            run_scripts=analysis.run_scripts,
        )

        container.session.flush()

    except Exception as exc:

        container.rollback()

        current_app.logger.exception(
            "Erreur pendant la sauvegarde de l'analyse"
        )

        return jsonify({
            "error": (
                f"Échec de la sauvegarde de l'analyse: {exc}"
            )
        }), 500

    # ============================================================
    # 7. GENERATE README WITH OLLAMA
    # ============================================================

    try:

        print(
            f"🤖 [README] DÉBUT OLLAMA — "
            f"repo_id={repo.id}"
        )

        result = (
            container.readme_generator_service
            .generate_initial_readme(
                repository_id=repo.id,
                project_name=repo.full_name.split("/")[-1],
                analysis=analysis,
                local_path=local_path,
            )
        )

        print(
            f"✅ [README] OLLAMA TERMINÉ — "
            f"repo_id={repo.id}"
        )

    except ReadmeGeneratorError as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — OLLAMA — "
            f"repo_id={repo.id} — {exc}"
        )

        return jsonify({
            "error": (
                f"Échec de la génération du README: {exc}"
            )
        }), 502

    except Exception as exc:

        container.rollback()

        current_app.logger.exception(
            "Erreur inattendue pendant la génération du README"
        )

        return jsonify({
            "error": (
                "Erreur inattendue pendant "
                f"la génération du README: {exc}"
            )
        }), 502

    # ============================================================
    # 8. UPDATE DATABASE STATE
    # ============================================================

    try:

        readme_version = result["version"]

        repo.current_readme_version_id = (
            readme_version.id
        )

        container.session.flush()

        # IMPORTANT :
        # Ici on ne prend PAS encore le SHA final,
        # car le README vient d'être modifié localement
        # et n'est pas encore pushé.

    except Exception as exc:

        container.rollback()

        current_app.logger.exception(
            "Erreur pendant la préparation de la persistence"
        )

        return jsonify({
            "error": (
                "Échec de la préparation du README: "
                f"{exc}"
            )
        }), 500

    # ============================================================
    # 9. COMMIT + PUSH GITHUB
    # ============================================================

    try:

        print(
            f"🚀 [GITHUB] PUSH README — "
            f"repo_id={repo.id}"
        )

        pushed_sha = container.git_service.commit_and_push(
            local_path=local_path,
            file_paths=["README.md"],
            commit_message="docs: generate README",
            author_name="README Sync Bot",
            author_email="readme-bot@yourapp.io",
            branch=repo.tracked_branch,
            auth_token=auth_token,
        )

        print(
            f"✅ [GITHUB] PUSH TERMINÉ — "
            f"repo_id={repo.id} — "
            f"commit={pushed_sha}"
        )

    except GitServiceError as exc:

        container.rollback()

        print(
            f"❌ [GITHUB] ERREUR PUSH — "
            f"repo_id={repo.id} — {exc}"
        )

        return jsonify({
            "error": (
                "README généré mais impossible "
                f"de le pousser vers GitHub: {exc}"
            ),
            "status": "generated_not_pushed",
        }), 502

    # ============================================================
    # 10. UPDATE SYNC SHA
    # ============================================================

    try:

        repo.last_synced_commit_sha = pushed_sha

        container.commit()

    except Exception as exc:

        container.rollback()

        current_app.logger.exception(
            "Erreur pendant la sauvegarde finale"
        )

        return jsonify({
            "error": (
                "README poussé sur GitHub mais "
                f"erreur de sauvegarde DB: {exc}"
            ),
            "status": "pushed_db_error",
            "commit_sha": pushed_sha,
        }), 500

    # ============================================================
    # 11. SUCCESS
    # ============================================================

    print(
        f"🎉 [README] GÉNÉRATION + PUSH TERMINÉS — "
        f"repo_id={repo.id} — "
        f"commit={pushed_sha}"
    )

    return (
        jsonify({
            "status": "generated_and_pushed",
            "commit_sha": pushed_sha,
            "readme": result["readme"].to_dict(),
            "version": readme_version.to_dict(),
            "repository": repo.to_dict(),
        }),
        201,
    )