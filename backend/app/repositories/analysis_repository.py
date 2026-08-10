from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, desc

from app.models.analysis import Analysis
from app.repositories.base_repository import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    model = Analysis

    def find_by_repository(self, repository_id: str) -> List[Analysis]:
        stmt = (
            select(Analysis)
            .where(Analysis.repository_id == repository_id)
            .order_by(desc(Analysis.created_at))
        )
        return list(self.session.scalars(stmt).all())

    def find_latest_for_repository(self, repository_id: str) -> Optional[Analysis]:
        stmt = (
            select(Analysis)
            .where(Analysis.repository_id == repository_id)
            .order_by(desc(Analysis.created_at))
            .limit(1)
        )
        return self.session.scalars(stmt).first()

    def create(self, repository_id: str, **fields) -> Analysis:
        analysis = Analysis(repository_id=repository_id, **fields)
        return self.add(analysis)
