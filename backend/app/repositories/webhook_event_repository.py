from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, desc

from app.models.webhook_event import WebhookEvent
from app.repositories.base_repository import BaseRepository


class WebhookEventRepository(BaseRepository[WebhookEvent]):
    model = WebhookEvent

    def find_by_delivery_id(self, delivery_id: str) -> Optional[WebhookEvent]:
        """Idempotency check contre les redéliveries GitHub."""
        stmt = select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id)
        return self.session.scalars(stmt).first()

    def exists(self, delivery_id: str) -> bool:
        return self.find_by_delivery_id(delivery_id) is not None

    def find_by_repository(self, repository_id: str, limit: int = 50) -> List[WebhookEvent]:
        stmt = (
            select(WebhookEvent)
            .where(WebhookEvent.repository_id == repository_id)
            .order_by(desc(WebhookEvent.received_at))
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def create(
        self,
        repository_id: str,
        delivery_id: str,
        event_type: Optional[str] = None,
        signature_valid: Optional[bool] = None,
        payload_summary: Optional[dict] = None,
    ) -> WebhookEvent:
        event = WebhookEvent(
            repository_id=repository_id,
            delivery_id=delivery_id,
            event_type=event_type,
            signature_valid=signature_valid,
            payload_summary=payload_summary,
        )
        return self.add(event)

    def mark_processed(self, event: WebhookEvent) -> WebhookEvent:
        event.processed = True
        self.session.flush()
        return event
