from __future__ import annotations

import enum
from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON, Integer, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class TriggeredBy(str, enum.Enum):
    initial_generation = "initial_generation"
    manual_edit = "manual_edit"
    sync_auto = "sync_auto"
    sync_manual_approved = "sync_manual_approved"


class ReadmeVersion(db.Model, UUIDPKMixin):
    """Historique complet — chaque version, manuelle ou synchronisée."""

    __tablename__ = "readme_versions"

    readme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generated_readmes.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sections_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    content_md: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    triggered_by: Mapped[TriggeredBy] = mapped_column(Enum(TriggeredBy), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    readme: Mapped["GeneratedReadme"] = relationship(
        back_populates="versions", foreign_keys=[readme_id]
    )

    def __repr__(self) -> str:
        return f"<ReadmeVersion #{self.version_number} readme={self.readme_id}>"

    def to_dict(self, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "readme_id": self.readme_id,
            "version_number": self.version_number,
            "triggered_by": self.triggered_by.value if self.triggered_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_content:
            data["sections_json"] = self.sections_json
            data["content_md"] = self.content_md
        return data
