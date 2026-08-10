from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class GeneratedReadme(db.Model, UUIDPKMixin):
    """État courant du README — un seul enregistrement actif par repo (1-1)."""

    __tablename__ = "generated_readmes"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    sections_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_md: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    current_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("readme_versions.id", ondelete="SET NULL"), nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="generated_readme")
    versions: Mapped[List["ReadmeVersion"]] = relationship(
        back_populates="readme",
        cascade="all, delete-orphan",
        foreign_keys="ReadmeVersion.readme_id",
    )
    current_version: Mapped[Optional["ReadmeVersion"]] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )

    def __repr__(self) -> str:
        return f"<GeneratedReadme repo={self.repository_id}>"

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "repository_id": self.repository_id,
            "current_version_id": self.current_version_id,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data["sections_json"] = self.sections_json
            data["content_md"] = self.content_md
        return data
