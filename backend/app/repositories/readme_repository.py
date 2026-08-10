from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.models.generated_readme import GeneratedReadme
from app.repositories.base_repository import BaseRepository


class ReadmeRepository(BaseRepository[GeneratedReadme]):
    model = GeneratedReadme

    def find_by_repository(self, repository_id: str) -> Optional[GeneratedReadme]:
        stmt = select(GeneratedReadme).where(GeneratedReadme.repository_id == repository_id)
        return self.session.scalars(stmt).first()

    def create(
        self,
        repository_id: str,
        sections_json: Optional[dict] = None,
        content_md: Optional[str] = None,
    ) -> GeneratedReadme:
        """
        INSERT direct. À utiliser uniquement quand on est certain qu'aucune
        ligne n'existe déjà pour ce repository_id (le champ est UNIQUE) —
        sinon utiliser get_or_create_for_repository().
        """
        readme = GeneratedReadme(
            repository_id=repository_id,
            sections_json=sections_json,
            content_md=content_md,
        )
        return self.add(readme)

    def get_or_create_for_repository(
        self,
        repository_id: str,
        sections_json: Optional[dict] = None,
        content_md: Optional[str] = None,
    ) -> GeneratedReadme:
        """
        Upsert sur repository_id (colonne UNIQUE de generated_readmes).

        generated_readmes est l'état courant du README, 1 ligne par repo.
        Appeler /generate une 2e fois sur le même repository ne doit pas
        tenter un second INSERT (violerait la contrainte unique) : on
        réutilise la ligne existante et on la met à jour à la place.
        """
        existing = self.find_by_repository(repository_id)
        if existing is not None:
            if sections_json is not None:
                existing.sections_json = sections_json
            if content_md is not None:
                existing.content_md = content_md
            self.session.flush()
            return existing

        return self.create(
            repository_id=repository_id,
            sections_json=sections_json,
            content_md=content_md,
        )

    def update_content(
        self,
        readme: GeneratedReadme,
        sections_json: dict,
        content_md: str,
        current_version_id: Optional[str] = None,
    ) -> GeneratedReadme:
        readme.sections_json = sections_json
        readme.content_md = content_md
        if current_version_id:
            readme.current_version_id = current_version_id
        self.session.flush()
        return readme
