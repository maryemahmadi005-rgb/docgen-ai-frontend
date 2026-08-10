from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select

from app.models.repository import Repository, SyncMode
from app.repositories.base_repository import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    model = Repository

    def find_by_user(self, user_id: str) -> List[Repository]:
        stmt = select(Repository).where(Repository.user_id == user_id)
        return list(self.session.scalars(stmt).all())

    def find_by_user_and_fullname(self, user_id: str, full_name: str) -> Optional[Repository]:
        stmt = select(Repository).where(
            Repository.user_id == user_id, Repository.full_name == full_name
        )
        return self.session.scalars(stmt).first()

    def find_by_webhook_id(self, webhook_id: str) -> Optional[Repository]:
        stmt = select(Repository).where(Repository.webhook_id == webhook_id)
        return self.session.scalars(stmt).first()

    def list_automatic_sync(self) -> List[Repository]:
        """Repos en mode sync automatique (pour le job de polling par ex.)."""
        stmt = select(Repository).where(Repository.sync_mode == SyncMode.automatic)
        return list(self.session.scalars(stmt).all())

    def create(
        self,
        user_id: str,
        github_url: str,
        full_name: str,
        default_branch: str = "main",
        **kwargs,
    ) -> Repository:
        repo = Repository(
            user_id=user_id,
            github_url=github_url,
            full_name=full_name,
            default_branch=default_branch,
            # tracked_branch reste NULL sauf si explicitement fourni par
            # l'appelant : ne jamais retomber sur default_branch, sinon
            # GitService croit qu'une branche a été choisie par
            # l'utilisateur et force --branch=main même quand la vraie
            # branche distante est "master" (ou autre).
            tracked_branch=kwargs.get("tracked_branch"),
            **{k: v for k, v in kwargs.items() if k != "tracked_branch"},
        )
        return self.add(repo)

    def update_sync_mode(self, repo: Repository, sync_mode: SyncMode) -> Repository:
        from app.models.base import utcnow

        repo.sync_mode = sync_mode
        repo.sync_mode_updated_at = utcnow()
        self.session.flush()
        return repo

    def update_last_synced_commit(self, repo: Repository, sha: str) -> Repository:
        repo.last_synced_commit_sha = sha
        self.session.flush()
        return repo