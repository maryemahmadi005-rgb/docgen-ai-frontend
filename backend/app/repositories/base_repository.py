from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Repository générique fournissant les opérations CRUD de base.
    Chaque repository spécifique hérite de celui-ci et ajoute
    ses propres méthodes métier (find_by_email, find_by_sha, ...).
    """

    model: Type[ModelType]

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, id_: str) -> Optional[ModelType]:
        return self.session.get(self.model, id_)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        self.session.flush()  # récupère l'id généré sans committer
        return instance

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, instance: ModelType) -> ModelType:
        self.session.refresh(instance)
        return instance
