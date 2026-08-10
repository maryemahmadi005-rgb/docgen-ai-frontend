from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class Commit(db.Model, UUIDPKMixin):
    __tablename__ = "commits"
    __table_args__ = (
        UniqueConstraint("repository_id", "sha", name="uq_commit_repo_sha"),
    )

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    sha: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_bot_commit: Mapped[bool] = mapped_column(Boolean, default=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="commits")
    file_changes: Mapped[List["FileChange"]] = relationship(
        back_populates="commit", cascade="all, delete-orphan"
    )
    detected_changes: Mapped[List["DetectedChange"]] = relationship(
        back_populates="commit", cascade="all, delete-orphan"
    )
    pending_updates: Mapped[List["PendingUpdate"]] = relationship(
        back_populates="commit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Commit {self.sha[:7]}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "sha": self.sha,
            "parent_sha": self.parent_sha,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "message": self.message,
            "is_bot_commit": self.is_bot_commit,
            "processed": self.processed,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
