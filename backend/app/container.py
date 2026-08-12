"""
Container d'injection de dépendances.

Centralise la création des repositories à partir de la session
SQLAlchemy courante (celle de Flask-SQLAlchemy, liée au contexte
de la requête). Permet d'accéder à n'importe quel repository
depuis les blueprints API sans instancier manuellement à chaque fois.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from flask import current_app

from app.extensions import db
from app.services.github_integration_service import GitHubIntegrationService

from app.repositories import (
    UserRepository,
    RepositoryRepository,
    AnalysisRepository,
    CommitRepository,
    PendingUpdateRepository,
    ReadmeRepository,
    ReadmeVersionRepository,
    WebhookEventRepository,
    DetectedChangeRepository,
    FileChangeRepository,
)

from app.services.git_service import GitService
from app.services.analyzer_service import AnalyzerService
from app.services.ai_service import AIService
from app.services.readme_generator import ReadmeGeneratorService
from app.services.diff_analyzer_service import DiffAnalyzerService
from app.services.readme_updater import ReadmeUpdaterService
from app.services.pending_update_service import PendingUpdateService
from app.services.sync_orchestrator import SyncOrchestrator
from app.services.commit_detector import CommitDetector


class Container:
    """
    Point d'accès unique à tous les repositories et services.

    Une instance de Container = une unité de travail partageant
    la même session SQLAlchemy.
    """

    def __init__(self, session: Session | None = None):
        # ============================================================
        # DATABASE SESSION
        # ============================================================

        self.session: Session = session or db.session

        # ============================================================
        # REPOSITORIES
        # ============================================================

        self.user_repository = UserRepository(self.session)

        self.repository_repository = RepositoryRepository(
            self.session
        )

        self.analysis_repository = AnalysisRepository(
            self.session
        )

        self.commit_repository = CommitRepository(
            self.session
        )

        self.pending_update_repository = PendingUpdateRepository(
            self.session
        )

        self.readme_repository = ReadmeRepository(
            self.session
        )

        self.readme_version_repository = ReadmeVersionRepository(
            self.session
        )

        self.webhook_event_repository = WebhookEventRepository(
            self.session
        )

        self.detected_change_repository = DetectedChangeRepository(
            self.session
        )

        self.file_change_repository = FileChangeRepository(
            self.session
        )

        # ============================================================
        # CORE SERVICES
        # ============================================================

        self.git_service = GitService(
            clones_base_dir=current_app.config.get(
                "CLONES_BASE_DIR",
                "/data/repo_clones",
            )
        )
        self.github_integration = GitHubIntegrationService(
            webhook_callback_url=current_app.config.get(
                "GITHUB_WEBHOOK_CALLBACK_URL",
                "",
            )
            )



        self.analyzer_service = AnalyzerService()

        self.ai_service = AIService(
            base_url=current_app.config.get(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            ),
            model=current_app.config.get(
                "OLLAMA_MODEL",
                "llama3",
            ),
            timeout=current_app.config.get(
                "OLLAMA_TIMEOUT",
                300,
            ),
            num_predict=current_app.config.get(
                "OLLAMA_NUM_PREDICT",
                2048,
            ),
        )

        # ============================================================
        # INITIAL README GENERATION PIPELINE
        # ============================================================

        self.readme_generator_service = ReadmeGeneratorService(
            ai_service=self.ai_service,
            readme_repository=self.readme_repository,
            readme_version_repository=self.readme_version_repository,

            # IMPORTANT:
            # ReadmeGeneratorService requires GitService.
            git_service=self.git_service,
        )

        # ============================================================
        # CONTINUOUS GITHUB -> README SYNCHRONIZATION
        # ============================================================

        self.diff_analyzer_service = DiffAnalyzerService(
            ai_service=self.ai_service,
        )

        self.readme_updater_service = ReadmeUpdaterService(
            ai_service=self.ai_service,
            readme_repository=self.readme_repository,
        )

        self.pending_update_service = PendingUpdateService(
            pending_update_repository=self.pending_update_repository,
        )

        self.sync_orchestrator = SyncOrchestrator(
            readme_updater=self.readme_updater_service,
            git_service=self.git_service,
            pending_update_service=self.pending_update_service,
            repository_repository=self.repository_repository,
            readme_version_repository=self.readme_version_repository,
            readme_repository=self.readme_repository,
        )

        self.commit_detector = CommitDetector(
            git_service=self.git_service,
            diff_analyzer=self.diff_analyzer_service,
            sync_orchestrator=self.sync_orchestrator,
            commit_repository=self.commit_repository,
            repository_repository=self.repository_repository,
            detected_change_repository=self.detected_change_repository,
            file_change_repository=self.file_change_repository,
        )

    # ================================================================
    # TRANSACTION MANAGEMENT
    # ================================================================

    def commit(self) -> None:
        """Commit la transaction SQLAlchemy courante."""
        self.session.commit()

    def rollback(self) -> None:
        """Annule la transaction SQLAlchemy courante."""
        self.session.rollback()

    # ================================================================
    # CONTEXT MANAGER
    # ================================================================

    def __enter__(self) -> "Container":
        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:
        """
        Rollback automatique en cas d'exception.
        """

        if exc_type is not None:
            self.rollback()


def get_container() -> Container:
    """
    Factory pratique utilisée dans les routes Flask.
    """
    return Container()

