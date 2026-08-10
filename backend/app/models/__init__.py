"""
Regroupe tous les modèles pour que Flask-Migrate / Alembic
détecte bien toutes les tables via db.metadata.

IMPORTANT : l'ordre des imports n'a pas d'importance pour SQLAlchemy
(les relations utilisent des strings résolues en fin de mapping),
mais il faut que TOUS les modèles soient importés ici.
"""

from app.models.user import User
from app.models.repository import Repository, SyncMode, SyncMethod
from app.models.analysis import Analysis
from app.models.generated_readme import GeneratedReadme
from app.models.readme_version import ReadmeVersion, TriggeredBy
from app.models.commit import Commit
from app.models.file_change import FileChange, ChangeType
from app.models.detected_change import DetectedChange, ImpactCategory
from app.models.pending_update import PendingUpdate, PendingUpdateStatus
from app.models.webhook_event import WebhookEvent

__all__ = [
    "User",
    "Repository",
    "SyncMode",
    "SyncMethod",
    "Analysis",
    "GeneratedReadme",
    "ReadmeVersion",
    "TriggeredBy",
    "Commit",
    "FileChange",
    "ChangeType",
    "DetectedChange",
    "ImpactCategory",
    "PendingUpdate",
    "PendingUpdateStatus",
    "WebhookEvent",
]
