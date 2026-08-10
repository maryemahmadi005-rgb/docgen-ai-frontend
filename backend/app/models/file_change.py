from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import String, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin


class ChangeType(str, enum.Enum):
    added = "added"
    modified = "modified"
    deleted = "deleted"
    renamed = "renamed"


class FileChange(db.Model, UUIDPKMixin):
    """Résultat brut du git diff, par commit."""

    __tablename__ = "file_changes"

    commit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    change_type: Mapped[ChangeType] = mapped_column(Enum(ChangeType), nullable=False)
    diff_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relations ---
    commit: Mapped["Commit"] = relationship(back_populates="file_changes")

    def __repr__(self) -> str:
        return f"<FileChange {self.file_path} ({self.change_type})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "commit_id": self.commit_id,
            "file_path": self.file_path,
            "change_type": self.change_type.value if self.change_type else None,
            "diff_summary": self.diff_summary,
        }
