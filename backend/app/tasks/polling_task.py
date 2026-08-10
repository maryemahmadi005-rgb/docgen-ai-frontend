"""
Polling Task — fallback pour les repositories dont sync_method='polling'
(webhook non créable, ex: permissions insuffisantes).

Interroge périodiquement l'API GitHub pour détecter de nouveaux commits,
puis converge vers le même point d'entrée que le webhook: CommitDetector.

Exécuté via Celery beat (ou APScheduler en alternative plus légère).
"""

import logging
import requests

from app.services.commit_detector import CommitDetector, PushEvent, CommitDetectorError

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class PollingTaskError(Exception):
    pass


class PollingTask:
    def __init__(
        self,
        commit_detector: CommitDetector,
        repository_repository,
        timeout: int = 15,
    ):
        self.commit_detector = commit_detector
        self.repository_repository = repository_repository
        self.timeout = timeout

    def run(self) -> dict:
        """
        Point d'entrée appelé périodiquement (ex: toutes les 5 minutes)
        par Celery beat. Traite tous les repositories en sync_method='polling'.
        """
        repositories = self.repository_repository.list_by_sync_method("polling")

        summary = {"checked": 0, "processed": 0, "errors": 0}

        for repo in repositories:
            summary["checked"] += 1
            try:
                processed = self._check_repository(repo)
                if processed:
                    summary["processed"] += 1
            except PollingTaskError as e:
                logger.error(f"Erreur polling pour repo {repo.id}: {e}")
                summary["errors"] += 1

        return summary

    def _check_repository(self, repo) -> bool:
        latest_commit = self._fetch_latest_commit(repo)

        if latest_commit is None:
            return False

        latest_sha = latest_commit["sha"]

        if latest_sha == repo.last_synced_commit_sha:
            return False  # rien de nouveau

        event = PushEvent(
            repository_id=repo.id,
            before_sha=repo.last_synced_commit_sha or latest_commit.get("parents", [{}])[0].get("sha", ""),
            after_sha=latest_sha,
            author_email=latest_commit.get("commit", {}).get("author", {}).get("email", ""),
            author_name=latest_commit.get("commit", {}).get("author", {}).get("name", ""),
            branch=repo.tracked_branch,
        )

        try:
            self.commit_detector.handle_push_event(event)
        except CommitDetectorError as e:
            raise PollingTaskError(f"Échec traitement commit {latest_sha}: {e}") from e

        self.repository_repository.update(repo.id, last_synced_commit_sha=latest_sha)
        return True

    def _fetch_latest_commit(self, repo) -> dict | None:
        auth_token = getattr(repo.owner, "github_token", None)
        headers = {"Accept": "application/vnd.github+json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo.full_name}/commits/{repo.tracked_branch}",
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise PollingTaskError(f"Erreur réseau: {e}") from e

        if response.status_code != 200:
            logger.warning(f"Échec récupération dernier commit pour {repo.full_name}: {response.status_code}")
            return None

        return response.json()