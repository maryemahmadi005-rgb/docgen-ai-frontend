from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, desc

from app.models.commit import Commit
from app.repositories.base_repository import BaseRepository


class CommitRepository(BaseRepository[Commit]):
    model = Commit

    def find_by_sha(self, repository_id: str, sha: str) -> Optional[Commit]:
        stmt = select(Commit).where(
            Commit.repository_id == repository_id, Commit.sha == sha
        )
        return self.session.scalars(stmt).first()

    def exists(self, repository_id: str, sha: str) -> bool:
        """Idempotency check avant insertion (unique index repo+sha)."""
        return self.find_by_sha(repository_id, sha) is not None

    def find_by_repository(
        self, repository_id: str, limit: int = 50, offset: int = 0
    ) -> List[Commit]:
        stmt = (
            select(Commit)
            .where(Commit.repository_id == repository_id)
            .order_by(desc(Commit.timestamp))
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def find_unprocessed(self, repository_id: str) -> List[Commit]:
        stmt = select(Commit).where(
            Commit.repository_id == repository_id,
            Commit.processed.is_(False),
            Commit.is_bot_commit.is_(False),
        )
        return list(self.session.scalars(stmt).all())

    def mark_processed(self, commit: Commit) -> Commit:
        commit.processed = True
        self.session.flush()
        return commit

    def create(
        self,
        repository_id: str,
        sha: str,
        message: Optional[str] = None,
        **kwargs,
    ) -> Commit:
        commit = Commit(
            repository_id=repository_id, sha=sha, message=message, **kwargs
        )
        return self.add(commit)
