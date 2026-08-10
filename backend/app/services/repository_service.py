"""
Repository Service — ajout, clone, gestion des repositories.

Point d'entrée orchestrant, à l'ajout d'un repo :
clone → analyse → génération README initiale → création webhook GitHub.
"""

import logging

from app.services.git_service import GitService, GitServiceError
from app.services.analyzer_service import AnalyzerService
from app.services.readme_generator import ReadmeGeneratorService, ReadmeGeneratorError
from app.services.github_integration_service import GitHubIntegrationService, GitHubIntegrationError

logger = logging.getLogger(__name__)


class RepositoryServiceError(Exception):
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

    def add_repository(self, user_id: str, github_url: str, auth_token: str | None = None) -> dict:
        """
        Pipeline complet d'ajout d'un repository.
        Chaque étape échoue proprement sans laisser d'état incohérent.
        """
        full_name = self._extract_full_name(github_url)

        repository = self.repository_repository.create(
            user_id=user_id,
            github_url=github_url,
            full_name=full_name,
            sync_mode="manual",  # défaut sécurisé, cf. conception précédente
        )

        try:
            local_path = self.git_service.clone_repository(
                github_url=github_url,
                repository_id=repository.id,
                auth_token=auth_token,
            )
            self.repository_repository.update(repository.id, local_clone_path=local_path)
        except GitServiceError as e:
            logger.error(f"Échec clone pour repo {repository.id}: {e}")
            self.repository_repository.mark_failed(repository.id, reason=str(e))
            raise RepositoryServiceError(f"Impossible de cloner le repository: {e}") from e

        analysis = self.analyzer_service.analyze(local_path)
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

        try:
            self.readme_generator.generate_initial_readme(
                repository_id=repository.id,
                project_name=full_name.split("/")[-1],
                analysis=analysis,
            )
        except ReadmeGeneratorError as e:
            logger.error(f"Échec génération README pour repo {repository.id}: {e}")
            # on continue quand même — le repo existe, l'utilisateur pourra régénérer manuellement
            self.repository_repository.mark_readme_generation_failed(repository.id, reason=str(e))

        try:
            webhook_info = self.github_integration.create_webhook(
                repository_id=repository.id,
                full_name=full_name,
                auth_token=auth_token,
            )
            self.repository_repository.update(
                repository.id,
                webhook_id=webhook_info["id"],
                webhook_secret=webhook_info["secret"],
                sync_method="webhook",
            )
        except GitHubIntegrationError as e:
            logger.warning(f"Échec création webhook pour repo {repository.id}: {e} — fallback polling.")
            self.repository_repository.update(repository.id, sync_method="polling")

        return {"repository_id": repository.id, "status": "added"}

    def delete_repository(self, repository_id: str) -> None:
        repository = self.repository_repository.get(repository_id)
        if repository is None:
            raise RepositoryServiceError(f"Repository {repository_id} introuvable.")

        if repository.webhook_id:
            try:
                self.github_integration.delete_webhook(
                    full_name=repository.full_name,
                    webhook_id=repository.webhook_id,
                    auth_token=getattr(repository.owner, "github_token", None),
                )
            except GitHubIntegrationError as e:
                logger.warning(f"Échec suppression webhook pour repo {repository_id}: {e}")

        self.repository_repository.delete(repository_id)

    def _extract_full_name(self, github_url: str) -> str:
        cleaned = github_url.rstrip("/").removesuffix(".git")
        parts = cleaned.split("/")
        return f"{parts[-2]}/{parts[-1]}"