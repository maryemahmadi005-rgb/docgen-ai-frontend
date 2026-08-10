from __future__ import annotations

import enum
from typing import Optional, List
from datetime import datetime

from sqlalchemy import String, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, TimestampMixin


class SyncMode(str, enum.Enum):
    manual = "manual"
    automatic = "automatic"


class SyncMethod(str, enum.Enum):
    webhook = "webhook"
    polling = "polling"


class Repository(db.Model, UUIDPKMixin, TimestampMixin):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("user_id", "full_name", name="uq_repo_user_fullname"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)  # owner/repo
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    tracked_branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    local_clone_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_synced_commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    sync_mode: Mapped[SyncMode] = mapped_column(
        Enum(SyncMode), default=SyncMode.manual, nullable=False
    )
    sync_mode_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sync_method: Mapped[SyncMethod] = mapped_column(
        Enum(SyncMethod), default=SyncMethod.webhook, nullable=False
    )
    webhook_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # chiffré

    current_readme_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("readme_versions.id", ondelete="SET NULL"), nullable=True
    )

    # --- Relations ---
    user: Mapped["User"] = relationship(back_populates="repositories")
    analyses: Mapped[List["Analysis"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    generated_readme: Mapped[Optional["GeneratedReadme"]] = relationship(
        back_populates="repository", uselist=False, cascade="all, delete-orphan"
    )
    commits: Mapped[List["Commit"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    pending_updates: Mapped[List["PendingUpdate"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    webhook_events: Mapped[List["WebhookEvent"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    current_readme_version: Mapped[Optional["ReadmeVersion"]] = relationship(
        foreign_keys=[current_readme_version_id]
    )

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "github_url": self.github_url,
            "full_name": self.full_name,
            "default_branch": self.default_branch,
            "tracked_branch": self.tracked_branch,
            "sync_mode": self.sync_mode.value if self.sync_mode else None,
            "sync_method": self.sync_method.value if self.sync_method else None,
            "last_synced_commit_sha": self.last_synced_commit_sha,
            "current_readme_version_id": self.current_readme_version_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
