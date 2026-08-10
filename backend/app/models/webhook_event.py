from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import UUIDPKMixin, utcnow


class WebhookEvent(db.Model, UUIDPKMixin):
    """Log brut des réceptions webhook — audit + idempotency."""

    __tablename__ = "webhook_events"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 'push', 'ping', ...
    delivery_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # X-GitHub-Delivery
    signature_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    payload_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # --- Relations ---
    repository: Mapped["Repository"] = relationship(back_populates="webhook_events")

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.event_type} delivery={self.delivery_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "event_type": self.event_type,
            "delivery_id": self.delivery_id,
            "signature_valid": self.signature_valid,
            "payload_summary": self.payload_summary,
            "processed": self.processed,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }
