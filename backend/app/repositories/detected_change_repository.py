from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select

from app.models.detected_change import DetectedChange, ImpactCategory
from app.repositories.base_repository import BaseRepository

# merge_impacts() (impact_rules.py) peut retourner "mixed" quand plusieurs
# catégories d'impact statiques sont fusionnées — cette valeur n'existe pas
# dans l'enum DB ImpactCategory (feature/dependency/structure/config/license/none).
# On ne modifie pas le schéma DB ni impact_rules.py : on stocke None dans ce
# cas précis et on garde affected_sections (la donnée réellement actionnable).
_VALID_DB_CATEGORIES = {c.value for c in ImpactCategory}


class DetectedChangeRepository(BaseRepository[DetectedChange]):
    model = DetectedChange

    def find_by_commit(self, commit_id: str) -> List[DetectedChange]:
        stmt = select(DetectedChange).where(DetectedChange.commit_id == commit_id)
        return list(self.session.scalars(stmt).all())

    def create(
        self,
        commit_id: str,
        impact_category: Optional[str],
        affected_sections: Optional[list],
        confidence_score: Optional[float] = None,
    ) -> DetectedChange:
        safe_category = impact_category if impact_category in _VALID_DB_CATEGORIES else None
        detected_change = DetectedChange(
            commit_id=commit_id,
            impact_category=safe_category,
            affected_sections=affected_sections or [],
            confidence_score=confidence_score,
        )
        return self.add(detected_change)
