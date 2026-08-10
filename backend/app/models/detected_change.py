from __future__ import annotations

import enum
from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, Enum, JSON, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class ImpactCategory(str, enum.Enum):
    feature = "feature"
    dependency = "dependency"
    structure = "structure"
    config = "config"
    license = "license"
    none = "none"


class DetectedChange(db.Model, UUIDPKMixin):
    """Résultat du Diff Analyzer — analyse d'impact."""

    __tablename__ = "detected_changes"

    commit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    impact_category: Mapped[Optional[ImpactCategory]] = mapped_column(
        Enum(ImpactCategory), nullable=True
    )
    affected_sections: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    commit: Mapped["Commit"] = relationship(back_populates="detected_changes")
    pending_update: Mapped[Optional["PendingUpdate"]] = relationship(
        back_populates="detected_change", uselist=False
    )

    def __repr__(self) -> str:
        return f"<DetectedChange {self.impact_category} commit={self.commit_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "commit_id": self.commit_id,
            "impact_category": self.impact_category.value if self.impact_category else None,
            "affected_sections": self.affected_sections,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
