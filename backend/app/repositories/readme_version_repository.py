from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select, desc, func

from app.models.readme_version import ReadmeVersion, TriggeredBy
from app.repositories.base_repository import BaseRepository


class ReadmeVersionRepository(BaseRepository[ReadmeVersion]):
    model = ReadmeVersion

    def find_by_readme(self, readme_id: str) -> List[ReadmeVersion]:
        stmt = (
            select(ReadmeVersion)
            .where(ReadmeVersion.readme_id == readme_id)
            .order_by(desc(ReadmeVersion.version_number))
        )
        return list(self.session.scalars(stmt).all())

    def find_latest_version_number(self, readme_id: str) -> int:
        stmt = select(func.max(ReadmeVersion.version_number)).where(
            ReadmeVersion.readme_id == readme_id
        )
        result = self.session.scalars(stmt).first()
        return result or 0

    def find_by_version_number(self, readme_id: str, version_number: int) -> Optional[ReadmeVersion]:
        stmt = select(ReadmeVersion).where(
            ReadmeVersion.readme_id == readme_id,
            ReadmeVersion.version_number == version_number,
        )
        return self.session.scalars(stmt).first()

    def create_next_version(
        self,
        readme_id: str,
        sections_json: dict,
        content_md: str,
        triggered_by: TriggeredBy,
    ) -> ReadmeVersion:
        """Auto-incrémente version_number en se basant sur la dernière version connue."""
        next_number = self.find_latest_version_number(readme_id) + 1
        version = ReadmeVersion(
            readme_id=readme_id,
            version_number=next_number,
            sections_json=sections_json,
            content_md=content_md,
            triggered_by=triggered_by,
        )
        return self.add(version)
