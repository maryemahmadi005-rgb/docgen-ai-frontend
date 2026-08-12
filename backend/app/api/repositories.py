from __future__ import annotations
import os

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
    Génération initiale du README pour un repository déjà tracké.

    Pipeline :

        1. Récupération du repository
        2. Récupération du token GitHub
        3. Clone du repository
        4. Vérification du remote
        5. Analyse statique
        6. Génération README via IA
        7. Sauvegarde README + version
        8. Mise à jour du SHA synchronisé
    """

    user_id = get_jwt_identity()

    container = get_container()

    print(
        f"🚀 [README] DÉBUT GÉNÉRATION — "
        f"repo_id={repo_id}"
    )

    # ========================================================
    # 1. GET REPOSITORY
    # ========================================================

    repo = (
        container.repository_repository
        .get_by_id(repo_id)
    )

    if not repo or repo.user_id != user_id:

        print(
            f"❌ [README] ERREUR — "
            f"étape=INIT — "
            f"repo_id={repo_id} — "
            f"repository introuvable"
        )

        return jsonify({
            "error": "Repository introuvable"
        }), 404

    # ========================================================
    # 2. GITHUB TOKEN
    # ========================================================

    auth_token = None

    if repo.user and repo.user.github_token:

        try:

            auth_token = (
                EncryptionService()
                .decrypt(repo.user.github_token)
            )

        except EncryptionError as exc:

            current_app.logger.warning(
                "Impossible de déchiffrer le token GitHub "
                "pour user=%s: %s",
                user_id,
                exc,
            )

            auth_token = None

    # ========================================================
    # 3. CLONE
    # ========================================================

    try:

        local_path = (
            container.git_service
            .clone_repository(
                github_url=repo.github_url,
                repository_id=repo.id,
                auth_token=auth_token,

                # Si tracked_branch existe, on l'utilise.
                # Sinon GitService détecte automatiquement
                # la branche par défaut du repository.
                branch=repo.tracked_branch,
            )
        )

        repo.local_clone_path = local_path

        container.session.flush()

    except GitServiceError as exc:

        print(
            f"❌ [README] ERREUR — "
            f"étape=CLONE — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        return jsonify({
            "error": f"Échec du clone du repository: {exc}"
        }), 502

    # ========================================================
    # 4. VERIFY CLONE
    # ========================================================
    #
    # IMPORTANT :
    #
    # NE PAS comparer directement :
    #
    #     origin_url == repo.github_url
    #
    # car origin peut contenir :
    #
    # https://x-access-token:TOKEN@github.com/...
    #
    # GitService.verify_remote_url() normalise les deux URLs
    # et supprime les credentials avant comparaison.
    # ========================================================

    try:

        remote_ok = (
            container.git_service
            .verify_remote_url(
                local_path=local_path,
                expected_url=repo.github_url,
            )
        )

    except GitServiceError as exc:

        print(
            f"❌ [README] ERREUR — "
            f"étape=VÉRIF CLONE — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        return jsonify({
            "error": (
                "Impossible de vérifier le repository cloné: "
                f"{exc}"
            )
        }), 502

    if not remote_ok:

        normalized_expected = (
            container.git_service
            .normalize_git_url(repo.github_url)
        )

        try:
            actual_origin = (
                container.git_service
                ._open_repo(local_path)
                .remotes.origin.url
            )

            normalized_origin = (
                container.git_service
                .normalize_git_url(actual_origin)
            )

        except Exception:
            normalized_origin = "<indisponible>"

        print(
            f"❌ [README] ERREUR — "
            f"étape=VÉRIF CLONE — "
            f"repo_id={repo.id} — "
            f"MISMATCH"
        )

        print(
            f"   attendu={normalized_expected}"
        )

        print(
            f"   trouvé={normalized_origin}"
        )

        return jsonify({
            "error": (
                "Le clone local ne correspond pas "
                "au repository demandé. "
                "Génération annulée pour éviter "
                "un README incorrect."
            )
        }), 502

    print(
        f"✅ [README] VÉRIF CLONE OK — "
        f"repo_id={repo.id} — "
        f"repository="
        f"{container.git_service.normalize_git_url(repo.github_url)}"
    )

    # ========================================================
    # 5. STATIC ANALYSIS
    # ========================================================

    try:

        analysis = (
            container.analyzer_service
            .analyze(
                local_path,
                repository_id=repo.id,
            )
        )

    except Exception as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — "
            f"étape=ANALYSE — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        current_app.logger.exception(
            "Erreur pendant l'analyse du repository"
        )

        return jsonify({
            "error": (
                f"Échec de l'analyse du repository: {exc}"
            )
        }), 502

    print(
        f"🔎 [README] PREUVE ANALYSE — "
        f"repo_id={repo.id} — "
        f"important_files="
        f"{analysis.important_files}"
    )

    if isinstance(
        analysis.file_structure,
        dict,
    ):

        root_structure = (
            analysis.file_structure.get(
                ".",
                {},
            )
        )

        if isinstance(
            root_structure,
            dict,
        ):

            top_level = list(
                root_structure.get(
                    "dirs",
                    [],
                )
            )

        else:
            top_level = analysis.file_structure

    else:

        top_level = analysis.file_structure

    print(
        f"🔎 [README] STRUCTURE — "
        f"repo_id={repo.id} — "
        f"top_level={top_level}"
    )

    # ========================================================
    # 6. SAVE ANALYSIS
    # ========================================================

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

        print(
            f"❌ [README] ERREUR — "
            f"étape=SAUVEGARDE ANALYSE — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        current_app.logger.exception(
            "Erreur pendant la sauvegarde de l'analyse"
        )

        return jsonify({
            "error": (
                f"Échec de la sauvegarde de l'analyse: {exc}"
            )
        }), 500

    # ========================================================
    # 7. GENERATE README WITH AI
    # ========================================================

    try:

        result = (
            container.readme_generator_service
            .generate_initial_readme(
                repository_id=repo.id,
                project_name=(
                    repo.full_name
                    .split("/")[-1]
                ),
                analysis=analysis,
            )
        )

    except ReadmeGeneratorError as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — "
            f"étape=GÉNÉRATION IA — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        return jsonify({
            "error": (
                "Échec de la génération du README: "
                f"{exc}"
            )
        }), 502

    except Exception as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — "
            f"étape=GÉNÉRATION IA — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        current_app.logger.exception(
            "Erreur inattendue pendant la génération du README"
        )

        return jsonify({
            "error": (
                "Erreur inattendue pendant "
                f"la génération du README: {exc}"
            )
        }), 502

    # ========================================================
    # 8. UPDATE REPOSITORY STATE
    # ========================================================
       # ========================================================
    # 8. WRITE README.md + COMMIT + PUSH
    # ========================================================

    try:
        readme_version = result["version"]
        rendered_md = result["rendered_md"]

        # ----------------------------------------------------
        # 8.1 WRITE README.md INTO LOCAL CLONE
        # ----------------------------------------------------

        readme_path = os.path.join(
            local_path,
            "README.md",
        )

        print(
            f"📝 [README] ÉCRITURE FICHIER — "
            f"path={readme_path}"
        )

        with open(
            readme_path,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as f:
            f.write(rendered_md)

        print(
            f"✅ [README] README.md ÉCRIT — "
            f"repo_id={repo.id}"
        )

        # ----------------------------------------------------
        # 8.2 DETECT TARGET BRANCH
        # ----------------------------------------------------

        target_branch = (
            repo.tracked_branch
            or repo.default_branch
            or "main"
        )

        print(
            f"🌿 [README] PUSH BRANCH — "
            f"repo_id={repo.id} — "
            f"branch={target_branch}"
        )

        # ----------------------------------------------------
        # 8.3 COMMIT + PUSH
        # ----------------------------------------------------

        push_sha = (
            container.git_service
            .commit_and_push(
                local_path=local_path,
                file_paths=["README.md"],
                commit_message="docs: generate initial README",
                author_name="readme-bot",
                author_email="readme-bot@yourapp.io",
                branch=target_branch,
                auth_token=auth_token,
            )
        )

        print(
            f"🎉 [README] PUSH TERMINÉ — "
            f"repo_id={repo.id} — "
            f"sha={push_sha}"
        )

        # ----------------------------------------------------
        # 8.4 UPDATE README VERSION
        # ----------------------------------------------------

        repo.current_readme_version_id = (
            readme_version.id
        )

        repo.last_synced_commit_sha = push_sha

        container.commit()

    except GitServiceError as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — "
            f"étape=COMMIT/PUSH — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        current_app.logger.exception(
            "Erreur pendant le commit/push du README initial"
        )

        return jsonify({
            "error": (
                "README généré mais impossible de "
                f"le pousser vers GitHub: {exc}"
            )
        }), 502

    except Exception as exc:

        container.rollback()

        print(
            f"❌ [README] ERREUR — "
            f"étape=PERSISTENCE/PUSH — "
            f"repo_id={repo.id} — "
            f"{exc}"
        )

        current_app.logger.exception(
            "Erreur pendant la persistance/push du README"
        )

        return jsonify({
            "error": (
                "Erreur pendant la sauvegarde ou "
                f"le push du README: {exc}"
            )
        }), 500

    # ========================================================
    # 9. SUCCESS
    # ========================================================

    print(
        f"🎉 [README] GÉNÉRATION INITIALE + PUSH TERMINÉS — "
        f"repo_id={repo.id}"
    )

    return (
        jsonify({
            "status": "generated_and_pushed",
            "readme": result["readme"].to_dict(),
            "version": readme_version.to_dict(),
            "repository": repo.to_dict(),
            "commit_sha": push_sha,
        }),
        201,
    )