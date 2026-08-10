from __future__ import annotations

import enum
from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, Enum, JSON, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class PendingUpdateStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    stale = "stale"


class PendingUpdate(db.Model, UUIDPKMixin):
    """Propositions en attente — mode manuel uniquement."""

    __tablename__ = "pending_updates"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    commit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    detected_change_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("detected_changes.id", ondelete="CASCADE"), nullable=False
    )
    base_readme_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("readme_versions.id", ondelete="RESTRICT"), nullable=False
    )

    sections_diff: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    proposed_content_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_sections_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[PendingUpdateStatus] = mapped_column(
        Enum(PendingUpdateStatus), default=PendingUpdateStatus.pending, nullable=False
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="pending_updates")
    commit: Mapped["Commit"] = relationship(back_populates="pending_updates")
    detected_change: Mapped["DetectedChange"] = relationship(back_populates="pending_update")
    base_readme_version: Mapped["ReadmeVersion"] = relationship(foreign_keys=[base_readme_version_id])
    resolved_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="resolved_pending_updates", foreign_keys=[resolved_by]
    )

    def __repr__(self) -> str:
        return f"<PendingUpdate {self.id} status={self.status}>"

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "repository_id": self.repository_id,
            "commit_id": self.commit_id,
            "detected_change_id": self.detected_change_id,
            "base_readme_version_id": self.base_readme_version_id,
            "status": self.status.value if self.status else None,
            "resolved_by": self.resolved_by,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
        if include_content:
            data["sections_diff"] = self.sections_diff
            data["proposed_content_md"] = self.proposed_content_md
            data["proposed_sections_json"] = self.proposed_sections_json
        return data
