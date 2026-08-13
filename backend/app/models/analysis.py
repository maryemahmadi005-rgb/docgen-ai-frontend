from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class Analysis(db.Model, UUIDPKMixin):
    __tablename__ = "analyses"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    languages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    frameworks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    file_structure: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    important_files: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    install_scripts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    run_scripts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis repo={self.repository_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "file_structure": self.file_structure,
            "important_files": self.important_files,
            "install_scripts": self.install_scripts,
            "run_scripts": self.run_scripts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class Analysis(db.Model, UUIDPKMixin):
    __tablename__ = "analyses"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    languages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    frameworks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    file_structure: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    important_files: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    install_scripts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    run_scripts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis repo={self.repository_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "file_structure": self.file_structure,
            "important_files": self.important_files,
            "install_scripts": self.install_scripts,
            "run_scripts": self.run_scripts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    # Test automatic README synchronization
