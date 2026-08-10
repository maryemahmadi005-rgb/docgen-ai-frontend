"""
Sync Orchestrator — seul composant connaissant sync_mode.
Coordonne README Updater, Git Service, Pending Update Service.
"""

import logging

from app.services.readme_updater import ReadmeUpdaterService, Patch
from app.services.git_service import GitService, GitServiceError
from app.services.pending_update_service import PendingUpdateService
from app.services.diff_analyzer_service import DetectedChange

logger = logging.getLogger(__name__)

BOT_AUTHOR_NAME = "readme-bot"
BOT_AUTHOR_EMAIL = "readme-bot@yourapp.io"
COMMIT_MESSAGE = "docs: auto-update README [skip-readme-sync]"


class SyncOrchestratorError(Exception):
    pass


class SyncOrchestrator:
    def __init__(
        self,
        readme_updater: ReadmeUpdaterService,
        git_service: GitService,
        pending_update_service: PendingUpdateService,
        repository_repository,
        readme_version_repository,
    ):
        self.readme_updater = readme_updater
        self.git_service = git_service
        self.pending_update_service = pending_update_service
        self.repository_repository = repository_repository
        self.readme_version_repository = readme_version_repository

    # ------------------------------------------------------------------
    # Point d'entrée principal — appelé par Commit Detector
    # ------------------------------------------------------------------
    def process(self, repository_id: str, detected_change: DetectedChange) -> dict:
        repo = self.repository_repository.get(repository_id)

        # Invalide toute proposition pending existante avant d'en créer une nouvelle
        self.pending_update_service.mark_existing_pending_as_stale(repository_id)

        if not detected_change.affected_sections:
            return {"action": "no_update_needed"}

        current_readme = self.repository_repository.get_current_readme(repository_id)

        patch = self.readme_updater.generate_patch(
            repository_id=repository_id,
            detected_change=detected_change,
            current_sections_json=current_readme.sections_json,
        )

        if not patch.has_real_changes():
            return {"action": "no_real_changes", "affected_sections": detected_change.affected_sections}

        if repo.sync_mode == "automatic":
            self._finalize_and_push(repo, patch, triggered_by="sync_auto")
            return {"action": "auto_synced", "sections": patch.affected_sections}

        # mode manuel
        pending_update = self.pending_update_service.create(
            repository_id=repository_id,
            commit_id=detected_change.commit_id,
            detected_change_id=detected_change.commit_id,
            base_readme_version_id=repo.current_readme_version_id,
            sections_diff=patch.sections_diff,
            proposed_content_md=patch.rendered_md,
            proposed_sections_json=patch.sections_json,
        )
        return {"action": "pending_update_created", "pending_update_id": pending_update.id}

    # ------------------------------------------------------------------
    # Après Approve — appelé par l'API pending_updates
    # ------------------------------------------------------------------
    def apply_pending(self, pending_update_id: str, user_id: str) -> dict:
        pending_update = self.pending_update_service.get(pending_update_id)

        if pending_update.status != "pending":
            raise SyncOrchestratorError(f"Proposition {pending_update_id} n'est plus 'pending' (statut: {pending_update.status}).")

        repo = self.repository_repository.get(pending_update.repository_id)

        if pending_update.base_readme_version_id != repo.current_readme_version_id:
            self.pending_update_service.mark_stale(pending_update_id)
            raise SyncOrchestratorError(
                "Le README a changé depuis cette proposition — elle est désormais obsolète."
            )

        patch = Patch(
            repository_id=pending_update.repository_id,
            detected_change_id=pending_update.detected_change_id,
            affected_sections=list(pending_update.sections_diff.keys()),
            sections_diff=pending_update.sections_diff,
            sections_json=pending_update.proposed_sections_json,
            rendered_md=pending_update.proposed_content_md,
        )

        self._finalize_and_push(repo, patch, triggered_by="sync_manual_approved")

        self.pending_update_service.mark_approved(pending_update_id, user_id)

        return {"action": "approved_and_synced", "sections": patch.affected_sections}

    # ------------------------------------------------------------------
    # Après Reject — appelé par l'API pending_updates
    # ------------------------------------------------------------------
    def discard_pending(self, pending_update_id: str, user_id: str, reason: str | None = None) -> dict:
        pending_update = self.pending_update_service.get(pending_update_id)

        if pending_update.status != "pending":
            raise SyncOrchestratorError(f"Proposition {pending_update_id} n'est plus 'pending'.")

        self.pending_update_service.mark_rejected(pending_update_id, user_id, reason)

        return {"action": "rejected"}

    # ------------------------------------------------------------------
    # Étape commune factorisée — apply_patch + commit_and_push + version
    # ------------------------------------------------------------------
    def _finalize_and_push(self, repo, patch: Patch, triggered_by: str) -> None:
        self.readme_updater.apply_patch(patch)

        try:
            self.git_service.commit_and_push(
                local_path=repo.local_clone_path,
                file_paths=["README.md"],
                commit_message=COMMIT_MESSAGE,
                author_name=BOT_AUTHOR_NAME,
                author_email=BOT_AUTHOR_EMAIL,
                branch=repo.tracked_branch,
                auth_token=getattr(repo.owner, "github_token", None),
            )
        except GitServiceError as e:
            logger.error(f"Échec push README pour repo {repo.id}: {e}")
            raise SyncOrchestratorError(f"Le README a été mis à jour localement mais le push a échoué: {e}") from e

        self.readme_version_repository.create(
            repository_id=repo.id,
            sections_json=patch.sections_json,
            content_md=patch.rendered_md,
            triggered_by=triggered_by,
        )