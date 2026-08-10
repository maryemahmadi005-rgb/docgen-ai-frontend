from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, TimestampMixin, utcnow


class User(db.Model, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_token: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)  # chiffré applicativement

    # --- Relations ---
    repositories: Mapped[List["Repository"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    resolved_pending_updates: Mapped[List["PendingUpdate"]] = relationship(
        back_populates="resolved_by_user"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def to_dict(self, include_token: bool = False) -> dict:
        data = {
            "id": self.id,
            "email": self.email,
            "github_username": self.github_username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_token:
            data["github_token"] = self.github_token
        return data
