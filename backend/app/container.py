"""
Container d'injection de dépendances.

Centralise la création des repositories à partir de la session
SQLAlchemy courante (celle de Flask-SQLAlchemy, liée au contexte
de la requête). Permet d'accéder à n'importe quel repository
depuis les blueprints API sans instancier manuellement à chaque fois.

Usage dans un blueprint :
    from app.container import Container

    container = Container()
    user = container.user_repository.find_by_email("a@b.com")
    container.commit()  # si besoin de committer explicitement
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from flask import current_app

from app.extensions import db
from app.repositories import (
    UserRepository,
    RepositoryRepository,
    AnalysisRepository,
    CommitRepository,
    PendingUpdateRepository,
    ReadmeRepository,
    ReadmeVersionRepository,
    WebhookEventRepository,
)
from app.services.git_service import GitService
from app.services.analyzer_service import AnalyzerService
from app.services.ai_service import AIService
from app.services.readme_generator import ReadmeGeneratorService


class Container:
    """
    Point d'accès unique à tous les repositories.
    Une instance de Container = une "unité de travail" (Unit of Work)
    partageant la même session SQLAlchemy, donc le même contexte
    transactionnel.
    """

    def __init__(self, session: Session | None = None):
        # db.session est un scoped_session lié au contexte Flask ;
        # on peut injecter une session custom (utile pour les tests).
        self.session: Session = session or db.session

        self.user_repository = UserRepository(self.session)
        self.repository_repository = RepositoryRepository(self.session)
        self.analysis_repository = AnalysisRepository(self.session)
        self.commit_repository = CommitRepository(self.session)
        self.pending_update_repository = PendingUpdateRepository(self.session)
        self.readme_repository = ReadmeRepository(self.session)
        self.readme_version_repository = ReadmeVersionRepository(self.session)
        self.webhook_event_repository = WebhookEventRepository(self.session)

        # --- Services (pipeline de génération initiale du README) ---
        self.git_service = GitService(
            clones_base_dir=current_app.config.get("CLONES_BASE_DIR", "/data/repo_clones")
        )
        self.analyzer_service = AnalyzerService()
        self.ai_service = AIService(
            base_url=current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=current_app.config.get("OLLAMA_MODEL", "llama3"),
            timeout=current_app.config.get("OLLAMA_TIMEOUT", 300),
            num_predict=current_app.config.get("OLLAMA_NUM_PREDICT", 2048),
        )
        self.readme_generator_service = ReadmeGeneratorService(
            ai_service=self.ai_service,
            readme_repository=self.readme_repository,
            readme_version_repository=self.readme_version_repository,
        )

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __enter__(self) -> "Container":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Permet d'utiliser le container comme context manager :

            with Container() as c:
                c.user_repository.create(...)
                c.commit()

        En cas d'exception, rollback automatique.
        """
        if exc_type is not None:
            self.rollback()


def get_container() -> Container:
    """Factory pratique à utiliser dans les routes Flask."""
    return Container()