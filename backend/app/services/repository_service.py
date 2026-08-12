"""
Repository Service — ajout, clone, gestion des repositories.

Point d'entrée orchestrant, à l'ajout d'un repo :
clone → analyse → génération README initiale → push README → création webhook GitHub.
"""

import logging
import os

from app.services.git_service import GitService, GitServiceError
from app.services.analyzer_service import AnalyzerService
from app.services.readme_generator import (
    ReadmeGeneratorService,
    ReadmeGeneratorError,
)
from app.services.github_integration_service import (
    GitHubIntegrationService,
    GitHubIntegrationError,
)

logger = logging.getLogger(__name__)


class RepositoryServiceError(Exception):
    """Erreur métier du Repository Service."""

    pass


class RepositoryService:

    def __init__(
        self,
        git_service: GitService,
        analyzer_service: AnalyzerService,
        readme_generator: ReadmeGeneratorService,
        github_integration: GitHubIntegrationService,
        repository_repository,
        analysis_repository,
    ):
        self.git_service = git_service
        self.analyzer_service = analyzer_service
        self.readme_generator = readme_generator
        self.github_integration = github_integration
        self.repository_repository = repository_repository
        self.analysis_repository = analysis_repository

    # ============================================================
    # ADD REPOSITORY
    # ============================================================

    def add_repository(
        self,
        user_id: str,
        github_url: str,
        auth_token: str | None = None,
    ) -> dict:
        """
        Pipeline complet d'ajout d'un repository :

        1. Création du repository en DB
        2. Clone GitHub
        3. Analyse du projet
        4. Génération du README initial
        5. Écriture du README.md dans le clone
        6. Commit + push du README vers GitHub
        7. Création du webhook GitHub

        Le repository reste enregistré même si la génération
        du README ou la création du webhook échoue.
        """

        full_name = self._extract_full_name(github_url)

        print(
            f"🚀 [REPOSITORY] AJOUT START — "
            f"full_name={full_name}"
        )

        # ========================================================
        # 1. CREATE REPOSITORY
        # ========================================================

        repository = self.repository_repository.create(
            user_id=user_id,
            github_url=github_url,
            full_name=full_name,
            sync_mode="manual",
        )

        print(
            f"✅ [REPOSITORY] DB CREATED — "
            f"repo_id={repository.id}"
        )

        # ========================================================
        # 2. CLONE
        # ========================================================

        try:
            print(
                f"📥 [REPOSITORY] CLONE START — "
                f"repo_id={repository.id}"
            )

            local_path = self.git_service.clone_repository(
                github_url=github_url,
                repository_id=repository.id,
                auth_token=auth_token,
            )

            self.repository_repository.update(
                repository.id,
                local_clone_path=local_path,
            )

            print(
                f"✅ [REPOSITORY] CLONE TERMINÉ — "
                f"repo_id={repository.id} — "
                f"path={local_path}"
            )

        except GitServiceError as e:
            logger.error(
                "Échec clone pour repo %s: %s",
                repository.id,
                e,
            )

            self.repository_repository.mark_failed(
                repository.id,
                reason=str(e),
            )

            raise RepositoryServiceError(
                f"Impossible de cloner le repository: {e}"
            ) from e

        # ========================================================
        # 3. ANALYSE
        # ========================================================

        try:
            print(
                f"🔎 [REPOSITORY] ANALYSE START — "
                f"repo_id={repository.id}"
            )

            analysis = self.analyzer_service.analyze(
                local_path
            )

            self.analysis_repository.create(
                repository_id=repository.id,
                languages=analysis.languages,
                frameworks=analysis.frameworks,
                dependencies=analysis.dependencies,
                file_structure=analysis.file_structure,
                important_files=analysis.important_files,
                install_scripts=analysis.install_scripts,
                run_scripts=analysis.run_scripts,
            )

            print(
                f"✅ [REPOSITORY] ANALYSE TERMINÉE — "
                f"repo_id={repository.id}"
            )

        except Exception as e:
            logger.exception(
                "Échec analyse pour repo %s",
                repository.id,
            )

            raise RepositoryServiceError(
                f"Impossible d'analyser le repository: {e}"
            ) from e

        # ========================================================
        # 4. GENERATE + WRITE + PUSH README
        # ========================================================

        try:
            print(
                f"🤖 [README] GÉNÉRATION START — "
                f"repo_id={repository.id}"
            )

            readme_result = (
                self.readme_generator.generate_initial_readme(
                    repository_id=repository.id,
                    project_name=full_name.split("/")[-1],
                    analysis=analysis,
                )
            )

            # IMPORTANT :
            # sections_json = structure JSON du README
            # rendered_md = vrai contenu Markdown
            rendered_md = readme_result["rendered_md"]

            if not rendered_md or not rendered_md.strip():
                raise ReadmeGeneratorError(
                    "Le README généré est vide."
                )

            print(
                f"📝 [README] GÉNÉRATION TERMINÉE — "
                f"repo_id={repository.id} — "
                f"chars={len(rendered_md)}"
            )

            # ----------------------------------------------------
            # 4.1 WRITE README.md
            # ----------------------------------------------------

            readme_path = os.path.join(
                local_path,
                "README.md",
            )

            with open(
                readme_path,
                "w",
                encoding="utf-8",
            ) as f:
                f.write(rendered_md)

            print(
                f"📄 [README] FICHIER ÉCRIT — "
                f"repo_id={repository.id} — "
                f"path={readme_path}"
            )

            # ----------------------------------------------------
            # 4.2 COMMIT + PUSH
            # ----------------------------------------------------

            print(
                f"🚀 [README] PUSH START — "
                f"repo_id={repository.id}"
            )

            pushed_sha = self.git_service.commit_and_push(
                local_path=local_path,
                file_paths=["README.md"],
                commit_message="docs: generate initial README",
                branch=None,
                auth_token=auth_token,
            )

            print(
                f"✅ [README] PUSH TERMINÉ — "
                f"repo_id={repository.id} — "
                f"commit={pushed_sha}"
            )

        except ReadmeGeneratorError as e:
            logger.error(
                "Échec génération README pour repo %s: %s",
                repository.id,
                e,
            )

            print(
                f"❌ [README] GENERATION ERROR — "
                f"repo_id={repository.id} — "
                f"{e}"
            )

            self.repository_repository.mark_readme_generation_failed(
                repository.id,
                reason=str(e),
            )

        except GitServiceError as e:
            logger.error(
                "Échec push README pour repo %s: %s",
                repository.id,
                e,
            )

            print(
                f"❌ [README] PUSH ERROR — "
                f"repo_id={repository.id} — "
                f"{e}"
            )

            self.repository_repository.mark_readme_generation_failed(
                repository.id,
                reason=f"README généré mais push échoué: {e}",
            )

        except Exception as e:
            logger.exception(
                "Erreur inattendue génération/push README "
                "pour repo %s",
                repository.id,
            )

            print(
                f"❌ [README] ERROR — "
                f"repo_id={repository.id} — "
                f"{e}"
            )

            self.repository_repository.mark_readme_generation_failed(
                repository.id,
                reason=str(e),
            )

        # ========================================================
        # 5. CREATE GITHUB WEBHOOK
        # ========================================================

        try:
            print(
                f"🔗 [WEBHOOK] CREATION START — "
                f"repo_id={repository.id}"
            )

            webhook_info = (
                self.github_integration.create_webhook(
                    repository_id=repository.id,
                    full_name=full_name,
                    auth_token=auth_token,
                )
            )

            self.repository_repository.update(
                repository.id,
                webhook_id=webhook_info["id"],
                webhook_secret=webhook_info["secret"],
                sync_method="webhook",
            )

            print(
                f"✅ [WEBHOOK] CRÉÉ — "
                f"repo_id={repository.id}"
            )

        except GitHubIntegrationError as e:
            logger.warning(
                "Échec création webhook pour repo %s: %s "
                "— fallback polling.",
                repository.id,
                e,
            )

            print(
                f"⚠️ [WEBHOOK] ÉCHEC — "
                f"repo_id={repository.id} — "
                f"fallback=polling"
            )

            self.repository_repository.update(
                repository.id,
                sync_method="polling",
            )

        # ========================================================
        # 6. FIN
        # ========================================================

        print(
            f"🎉 [REPOSITORY] AJOUT TERMINÉ — "
            f"repo_id={repository.id}"
        )

        return {
            "repository_id": repository.id,
            "status": "added",
        }

    # ============================================================
    # DELETE REPOSITORY
    # ============================================================

    def delete_repository(
        self,
        repository_id: str,
    ) -> None:

        repository = self.repository_repository.get(
            repository_id
        )

        if repository is None:
            raise RepositoryServiceError(
                f"Repository {repository_id} introuvable."
            )

        if repository.webhook_id:
            try:
                self.github_integration.delete_webhook(
                    full_name=repository.full_name,
                    webhook_id=repository.webhook_id,
                    auth_token=getattr(
                        repository.owner,
                        "github_token",
                        None,
                    ),
                )

            except GitHubIntegrationError as e:
                logger.warning(
                    "Échec suppression webhook "
                    "pour repo %s: %s",
                    repository_id,
                    e,
                )

        self.repository_repository.delete(
            repository_id
        )

        print(
            f"🗑️ [REPOSITORY] SUPPRIMÉ — "
            f"repo_id={repository_id}"
        )

    # ============================================================
    # FULL NAME
    # ============================================================

    def _extract_full_name(
        self,
        github_url: str,
    ) -> str:

        cleaned = (
            github_url
            .rstrip("/")
            .removesuffix(".git")
        )

        parts = cleaned.split("/")

        if len(parts) < 2:
            raise RepositoryServiceError(
                f"URL GitHub invalide: {github_url}"
            )

        return f"{parts[-2]}/{parts[-1]}"