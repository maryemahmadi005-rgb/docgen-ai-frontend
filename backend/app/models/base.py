import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPKMixin:
    """Ajoute une PK UUID (stockée en CHAR(36)) à un modèle."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=gen_uuid
    )


class TimestampMixin:
    """Ajoute created_at / updated_at automatiques."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


Base = db.Model
