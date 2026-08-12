from __future__ import annotations

from typing import List

from sqlalchemy import select

from app.models.file_change import FileChange
from app.repositories.base_repository import BaseRepository


class FileChangeRepository(BaseRepository[FileChange]):
    model = FileChange

    def find_by_commit(self, commit_id: str) -> List[FileChange]:
        stmt = select(FileChange).where(FileChange.commit_id == commit_id)
        return list(self.session.scalars(stmt).all())

    def create_bulk(self, commit_id: str, file_changes: list) -> List[FileChange]:
        """
        file_changes: liste d'objets FileChange (dataclass de git_service.py),
        chacun avec .path / .change_type / .diff_excerpt.
        """
        created = []
        for fc in file_changes:
            row = FileChange(
                commit_id=commit_id,
                file_path=fc.path,
                change_type=fc.change_type,
                diff_summary=fc.diff_excerpt,
            )
            self.session.add(row)
            created.append(row)
        self.session.flush()
        return created
