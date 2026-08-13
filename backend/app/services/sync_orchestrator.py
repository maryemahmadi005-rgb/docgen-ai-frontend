"""
Sync Orchestrator — seul composant connaissant sync_mode.
Coordonne README Updater, Git Service, Pending Update Service.

Root-cause fixes appliqués ici (jamais exécuté avec succès jusqu'ici) :
- repository_repository.get(...) n'existe pas -> get_by_id(...)
- repository_repository.get_current_readme(...) n'existe pas du tout ;
  l'état courant du README vit dans generated_readmes (ReadmeRepository),
  pas sur Repository. readme_repository est maintenant injecté.
- readme_version_repository.create(triggered_by="sync_auto") (string) ->
  create_next_version(readme_id=..., triggered_by=TriggeredBy.sync_auto)
  (l'ancien appel utilisait une méthode/signature qui n'existe pas).
- Après avoir créé une ReadmeVersion, l'état courant (generated_readmes)
  n'était JAMAIS mis à jour : readme_repository.update_content(...) est
  maintenant appelé, exactement comme le fait déjà api/readmes.py pour
  les mêmes opérations (édition manuelle, rollback).
- repo.owner n'existe pas -> repo.user.
- La détection de conflit comparait pending_update.base_readme_version_id
  à repo.current_readme_version_id, un champ qui n'est en réalité jamais
  maintenu à jour ailleurs dans le code (seul generated_readmes.current_
  version_id l'est, par readme_generator.py et api/readmes.py). Comparer
  contre un champ toujours None aurait rendu CHAQUE approbation "stale"
  à tort. Le check utilise maintenant readme.current_version_id, le seul
  pointeur réellement tenu à jour.
"""

import logging

from app.services.readme_updater import ReadmeUpdaterService, Patch
from app.services.git_service import GitService, GitServiceError
from app.services.pending_update_service import PendingUpdateService
from app.services.diff_analyzer_service import DetectedChange
from app.models.readme_version import TriggeredBy

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
        readme_repository,
    ):
        self.readme_updater = readme_updater
        self.git_service = git_service
        self.pending_update_service = pending_update_service
        self.repository_repository = repository_repository
        self.readme_version_repository = readme_version_repository
        self.readme_repository = readme_repository

    # ------------------------------------------------------------------
    # Point d'entrée principal — appelé par Commit Detector
    # ------------------------------------------------------------------
    def process(self, repository_id: str, detected_change: DetectedChange, detected_change_db_id: str) -> dict:
        repo = self.repository_repository.get_by_id(repository_id)
        if repo is None:
            raise SyncOrchestratorError(f"Repository {repository_id} introuvable.")

        # Invalide toute proposition pending existante avant d'en créer une nouvelle
        self.pending_update_service.mark_existing_pending_as_stale(repository_id)

        if not detected_change.affected_sections:
            print(f"[README PATCH] repo={repository_id} aucune section affectée — no_update_needed")
            return {"action": "no_update_needed"}

        readme = self.readme_repository.find_by_repository(repository_id)
        if readme is None:
            print(f"[README PATCH] repo={repository_id} aucun README généré — impossible de patcher")
            return {"action": "no_readme_yet"}

        if readme.current_version_id is None:
            # État anormal (ne devrait pas arriver via le flux normal de
            # generate_initial_readme, qui crée toujours readme + version
            # ensemble) mais base_readme_version_id est NOT NULL en DB :
            # sans cette garde, la création du PendingUpdate plantait avec
            # une IntegrityError brute au lieu d'un message clair.
            print(f"[README PATCH] repo={repository_id} README sans version associée — état incohérent, sync ignorée")
            return {"action": "readme_missing_version"}

        print(f"[README SYNC] Affected sections: {detected_change.affected_sections}")

        patch = self.readme_updater.generate_patch(
            repository_id=repository_id,
            detected_change=detected_change,
            current_sections_json=readme.sections_json or {},
        )

        if not patch.has_real_changes():
            print(f"[README PATCH] repo={repository_id} patch généré mais sans différence réelle")
            return {"action": "no_real_changes", "affected_sections": detected_change.affected_sections}

        print(f"[README SYNC] Patch generated: true")

        if repo.sync_mode.value == "automatic":
            version = self._finalize_and_push(repo, readme, patch, triggered_by=TriggeredBy.sync_auto)
            return {
                "action": "auto_synced",
                "sections": patch.affected_sections,
                "version_number": version.version_number,
            }

        # mode manuel : on crée une proposition et on s'arrête — AUCUN commit/push ici.
        pending_update = self.pending_update_service.create(
            repository_id=repository_id,
            commit_id=detected_change.commit_id,
            detected_change_id=detected_change_db_id,
            base_readme_version_id=readme.current_version_id,
            sections_diff=patch.sections_diff,
            proposed_content_md=patch.rendered_md,
            proposed_sections_json=patch.sections_json,
        )
        print(f"[PENDING UPDATE CREATED] ID: {pending_update.id} Repository: {repository_id} Status: pending")
        return {"action": "pending_update_created", "pending_update_id": pending_update.id}

    # ------------------------------------------------------------------
    # Après Approve — appelé par l'API pending_updates
    # ------------------------------------------------------------------
    def apply_pending(self, pending_update_id: str, user_id: str) -> dict:
        pending_update = self.pending_update_service.get(pending_update_id)

        if pending_update.status != "pending":
            raise SyncOrchestratorError(
                f"Proposition {pending_update_id} n'est plus 'pending' (statut: {pending_update.status})."
            )

        repo = self.repository_repository.get_by_id(pending_update.repository_id)
        if repo is None:
            raise SyncOrchestratorError(f"Repository {pending_update.repository_id} introuvable.")

        readme = self.readme_repository.find_by_repository(repo.id)
        if readme is None:
            raise SyncOrchestratorError(f"Aucun README pour repository {repo.id}.")

        if pending_update.base_readme_version_id != readme.current_version_id:
            self.pending_update_service.mark_stale(pending_update_id)
            raise SyncOrchestratorError(
                "Le README a changé depuis cette proposition — elle est désormais obsolète."
            )

        patch = Patch(
            repository_id=pending_update.repository_id,
            detected_change_id=pending_update.detected_change_id,
            affected_sections=list((pending_update.sections_diff or {}).keys()),
            sections_diff=pending_update.sections_diff or {},
            sections_json=pending_update.proposed_sections_json or {},
            rendered_md=pending_update.proposed_content_md or "",
        )

        version = self._finalize_and_push(
            repo, readme, patch, triggered_by=TriggeredBy.sync_manual_approved
        )

        self.pending_update_service.mark_approved(pending_update_id, user_id)

        return {
            "action": "approved_and_synced",
            "sections": patch.affected_sections,
            "version_number": version.version_number,
        }

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
    def _finalize_and_push(self, repo, readme, patch: Patch, triggered_by: TriggeredBy):
        self.readme_updater.apply_patch(patch)

        try:
            commit_sha = self.git_service.commit_and_push(
                local_path=repo.local_clone_path,
                file_paths=["README.md"],
                commit_message=COMMIT_MESSAGE,
                author_name=BOT_AUTHOR_NAME,
                author_email=BOT_AUTHOR_EMAIL,
                branch=repo.tracked_branch or repo.default_branch,
                auth_token=getattr(repo.user, "github_token", None),
            )
        except GitServiceError as e:
            logger.error(f"Échec push README pour repo {repo.id}: {e}")
            raise SyncOrchestratorError(
                f"Le README a été mis à jour localement mais le push a échoué: {e}"
            ) from e

        version = self.readme_version_repository.create_next_version(
            readme_id=readme.id,
            sections_json=patch.sections_json,
            content_md=patch.rendered_md,
            triggered_by=triggered_by,
        )

        # Sans cet appel, generated_readmes (l'état "courant") restait
        # désynchronisé de readme_versions après chaque sync — bug présent
        # avant ce fix.
        self.readme_repository.update_content(
            readme,
            patch.sections_json,
            patch.rendered_md,
            current_version_id=version.id,
        )

        print(f"[README SYNC] Publié — repo={repo.id} commit={commit_sha} version={version.version_number}")

        return version
