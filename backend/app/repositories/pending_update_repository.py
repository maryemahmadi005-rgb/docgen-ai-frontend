from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, desc

from app.models.pending_update import PendingUpdate, PendingUpdateStatus
from app.repositories.base_repository import BaseRepository


class PendingUpdateRepository(BaseRepository[PendingUpdate]):
    model = PendingUpdate

    def find_by_repository(
        self, repository_id: str, status: Optional[PendingUpdateStatus] = None
    ) -> List[PendingUpdate]:
        stmt = select(PendingUpdate).where(PendingUpdate.repository_id == repository_id)
        if status is not None:
            stmt = stmt.where(PendingUpdate.status == status)
        stmt = stmt.order_by(desc(PendingUpdate.created_at))
        return list(self.session.scalars(stmt).all())

    def find_pending_for_repository(self, repository_id: str) -> List[PendingUpdate]:
        return self.find_by_repository(repository_id, status=PendingUpdateStatus.pending)

    def create(
        self,
        repository_id: str,
        commit_id: str,
        detected_change_id: str,
        base_readme_version_id: str,
        **fields,
    ) -> PendingUpdate:
        pu = PendingUpdate(
            repository_id=repository_id,
            commit_id=commit_id,
            detected_change_id=detected_change_id,
            base_readme_version_id=base_readme_version_id,
            **fields,
        )
        return self.add(pu)

    def approve(self, pending_update: PendingUpdate, resolved_by: str) -> PendingUpdate:
        from app.models.base import utcnow

        pending_update.status = PendingUpdateStatus.approved
        pending_update.resolved_by = resolved_by
        pending_update.resolved_at = utcnow()
        self.session.flush()
        return pending_update

    def reject(
        self, pending_update: PendingUpdate, resolved_by: str, reason: Optional[str] = None
    ) -> PendingUpdate:
        from app.models.base import utcnow

        pending_update.status = PendingUpdateStatus.rejected
        pending_update.resolved_by = resolved_by
        pending_update.rejection_reason = reason
        pending_update.resolved_at = utcnow()
        self.session.flush()
        return pending_update

    def mark_stale(self, pending_update: PendingUpdate) -> PendingUpdate:
        pending_update.status = PendingUpdateStatus.stale
        self.session.flush()
        return pending_update
