"""
Commit Detector — point d'entrée unique, agnostique de la source
(webhook ou polling). Responsable de :
- idempotency (ne pas retraiter un commit déjà traité)
- anti-loop (ignorer les commits du bot lui-même)
- déclenchement du pipeline Git Service → Diff Analyzer → Sync Orchestrator
"""

import logging
from dataclasses import dataclass

from app.services.git_service import GitService, GitServiceError
from app.services.diff_analyzer_service import DiffAnalyzerService
from app.services.sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

BOT_AUTHOR_EMAIL = "readme-bot@yourapp.io"
EXCLUDED_DIFF_PATHS = ["README.md", "readme.md"]


@dataclass
class PushEvent:
    repository_id: str
    before_sha: str
    after_sha: str
    author_email: str
    author_name: str
    branch: str


class CommitDetectorError(Exception):
    pass


class CommitDetector:
    def __init__(
        self,
        git_service: GitService,
        diff_analyzer: DiffAnalyzerService,
        sync_orchestrator: SyncOrchestrator,
        commit_repository,
        repository_repository,
    ):
        self.git_service = git_service
        self.diff_analyzer = diff_analyzer
        self.sync_orchestrator = sync_orchestrator
        self.commit_repository = commit_repository
        self.repository_repository = repository_repository

    def handle_push_event(self, event: PushEvent) -> dict:
        """
        Point d'entrée unique — appelé par webhooks.py OU polling_task.py.
        Retourne un résumé de ce qui a été fait (utile pour logs/debug).
        """
        repo = self.repository_repository.get(event.repository_id)
        if repo is None:
            raise CommitDetectorError(f"Repository {event.repository_id} introuvable.")

        # 1. Filtre de branche
        if event.branch != repo.tracked_branch:
            logger.info(f"Push sur branche non suivie ({event.branch}), ignoré.")
            return {"status": "ignored", "reason": "branch_not_tracked"}

        # 2. Anti-loop : commit du bot lui-même
        if self._is_bot_author(event.author_email):
            logger.info(f"Commit du bot détecté ({event.author_email}), ignoré.")
            return {"status": "ignored", "reason": "bot_commit"}

        # 3. Idempotency : commit déjà traité ?
        if self.commit_repository.exists(repo.id, event.after_sha):
            logger.info(f"Commit {event.after_sha} déjà traité, ignoré.")
            return {"status": "ignored", "reason": "already_processed"}

        # 4. Enregistrement du commit
        commit = self.commit_repository.create(
            repository_id=repo.id,
            sha=event.after_sha,
            parent_sha=event.before_sha,
            author_name=event.author_name,
            author_email=event.author_email,
            is_bot_commit=False,
        )

        # 5. Fetch + diff via Git Service
        try:
            self.git_service.fetch(repo.local_clone_path, auth_token=self._get_auth_token(repo))
            file_changes = self.git_service.get_diff(
                repo.local_clone_path,
                before_sha=event.before_sha,
                after_sha=event.after_sha,
                exclude_paths=EXCLUDED_DIFF_PATHS,
            )
        except GitServiceError as e:
            logger.error(f"Échec git fetch/diff pour commit {event.after_sha}: {e}")
            self.commit_repository.mark_failed(commit.id, reason=str(e))
            return {"status": "error", "reason": "git_failure"}

        if not file_changes:
            logger.info(f"Aucun fichier pertinent modifié dans {event.after_sha}.")
            self.commit_repository.mark_processed(commit.id)
            return {"status": "no_relevant_changes"}

        # 6. Persist file_changes
        self.commit_repository.save_file_changes(commit.id, file_changes)

        # 7. Diff Analyzer
        detected_change = self.diff_analyzer.analyze(
            commit_id=commit.id,
            file_changes=file_changes,
            repo_context=repo.full_name,
        )
        self.commit_repository.save_detected_change(detected_change)

        # 8. Sync Orchestrator prend le relais
        result = self.sync_orchestrator.process(repo.id, detected_change)

        self.commit_repository.mark_processed(commit.id)

        return {"status": "processed", "orchestrator_result": result}

    def _is_bot_author(self, author_email: str) -> bool:
        return author_email.lower() == BOT_AUTHOR_EMAIL.lower()

    def _get_auth_token(self, repo) -> str | None:
        return getattr(repo.owner, "github_token", None)