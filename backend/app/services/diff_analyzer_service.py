"""
Diff Analyzer Service — détermine l'impact d'un ensemble de changements
de fichiers sur les sections du README.

Stratégie: règles statiques d'abord (impact_rules.py), IA seulement
pour les fichiers non catégorisables. Ne modifie jamais le README lui-même.
"""

import logging
from dataclasses import dataclass, field

from app.services.ai_service import AIService, AIServiceError
from app.services.git_service import FileChange
from app.utils.impact_rules import match_static_rules, merge_impacts

logger = logging.getLogger(__name__)


@dataclass
class DetectedChange:
    commit_id: str
    impact_category: str
    affected_sections: list[str]
    confidence_score: float
    file_changes: list[FileChange] = field(default_factory=list)


class DiffAnalyzerService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def analyze(self, commit_id: str, file_changes: list[FileChange], repo_context: str = "") -> DetectedChange:
        if not file_changes:
            return DetectedChange(commit_id=commit_id, impact_category="none",
                                   affected_sections=[], confidence_score=1.0, file_changes=[])

        static_impacts = []
        ambiguous_files = []

        for fc in file_changes:
            result = match_static_rules(fc.path, fc.change_type)
            if result is not None:
                static_impacts.append(result)
            else:
                ambiguous_files.append(fc)

        confidence = 1.0

        if ambiguous_files:
            try:
                ai_result = self.ai_service.classify_impact(
                    file_changes=[
                        {"path": fc.path, "change_type": fc.change_type, "diff_excerpt": fc.diff_excerpt}
                        for fc in ambiguous_files
                    ],
                    repo_context=repo_context,
                )
                static_impacts.append(ai_result)
                confidence = min(confidence, ai_result.get("confidence_score", 0.7))
            except AIServiceError as e:
                logger.warning(f"Classification IA échouée pour commit {commit_id}: {e}")
                confidence = 0.5  # on continue avec ce qu'on a des règles statiques

        merged = merge_impacts(static_impacts)

        return DetectedChange(
            commit_id=commit_id,
            impact_category=merged["impact_category"],
            affected_sections=merged["affected_sections"],
            confidence_score=confidence,
            file_changes=file_changes,
        )