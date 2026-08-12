"""
README Updater Service — generate_patch() / apply_patch()

generate_patch() : pure, ne modifie aucun état persistant. Retourne un objet Patch.
apply_patch()    : seule méthode qui écrit réellement en DB (generated_readmes).

Cette séparation permet au patch d'être stocké dans pending_updates (mode manuel)
et rejoué à l'identique plus tard sans nouvel appel IA.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services.ai_service import AIService, AIServiceError
from app.services.diff_analyzer_service import DetectedChange
from app.services.markdown_renderer import render_readme
from app.services.impact_rules import FEATURE_PATH_HINTS

logger = logging.getLogger(__name__)


class ReadmeUpdaterError(Exception):
    pass


@dataclass
class Patch:
    repository_id: str
    detected_change_id: str
    affected_sections: list[str]
    sections_diff: dict = field(default_factory=dict)   # {section: {before, after}}
    sections_json: dict = field(default_factory=dict)    # état complet post-patch
    rendered_md: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_real_changes(self) -> bool:
        """True si au moins une section a un contenu réellement différent."""
        return any(
            diff["before"] != diff["after"]
            for diff in self.sections_diff.values()
        )


# Sections dont le contenu est une liste vs texte libre — doit rester aligné
# sur les vrais types utilisés par le template (readme_template.md.j2) et
# AIService.README_SCHEMA. N'affecte que la valeur par défaut utilisée quand
# une clé serait absente de sections_json (cas normalement rare : la
# génération initiale peuple toujours les 10 clés).
LIST_SECTIONS = {"technologies", "main_modules", "entry_points", "api_endpoints", "recommendations"}


class ReadmeUpdaterService:
    def __init__(self, ai_service: AIService, readme_repository):
        """
        readme_repository : couche d'accès DB pour generated_readmes
        (injectée pour garder ce service testable sans DB réelle).
        """
        self.ai_service = ai_service
        self.readme_repository = readme_repository

    # ------------------------------------------------------------------
    # generate_patch() — calcule le changement, n'écrit rien
    # ------------------------------------------------------------------
    def generate_patch(
        self,
        repository_id: str,
        detected_change: DetectedChange,
        current_sections_json: dict,
    ) -> Patch:
        if not detected_change.affected_sections:
            return Patch(
                repository_id=repository_id,
                detected_change_id=detected_change.commit_id,
                affected_sections=[],
                sections_json=current_sections_json,
                rendered_md=render_readme(current_sections_json),
            )

        sections_diff = {}
        new_sections_json = dict(current_sections_json)  # copie — ne pas muter l'input

        for section_name in detected_change.affected_sections:
            old_content = current_sections_json.get(section_name, "" if section_name not in LIST_SECTIONS else [])
            relevant_files = self._filter_relevant_files(section_name, detected_change.file_changes)

            try:
                new_content = self.ai_service.generate_section(
                    section_name=section_name,
                    old_content=old_content,
                    relevant_files=[
                        {"path": fc.path, "change_type": fc.change_type, "diff_excerpt": fc.diff_excerpt}
                        for fc in relevant_files
                    ],
                )
            except AIServiceError as e:
                logger.warning(f"Échec génération section '{section_name}': {e} — section conservée inchangée.")
                new_content = old_content

            sections_diff[section_name] = {"before": old_content, "after": new_content}
            new_sections_json[section_name] = new_content

        rendered_md = render_readme(new_sections_json)

        return Patch(
            repository_id=repository_id,
            detected_change_id=detected_change.commit_id,
            affected_sections=detected_change.affected_sections,
            sections_diff=sections_diff,
            sections_json=new_sections_json,
            rendered_md=rendered_md,
        )

    def _filter_relevant_files(self, section_name: str, file_changes: list) -> list:
        """
        Associe les fichiers modifiés à la section qu'ils justifient,
        pour donner un contexte ciblé à l'IA plutôt que tous les fichiers du commit.
        """
        # Clés alignées sur README_SCHEMA (voir impact_rules.py pour le
        # détail du bug corrigé : ces clés doivent correspondre aux vraies
        # sections du README, pas à des noms inventés).
        feature_predicate = lambda fc: any(hint in fc.path.lower() for hint in FEATURE_PATH_HINTS) or fc.change_type == "added"
        dependency_predicate = lambda fc: any(fc.path.endswith(ext) for ext in
                                               ["requirements.txt", "package.json", "Pipfile", "go.mod", "pyproject.toml", "Gemfile"])
        mapping = {
            "main_modules": feature_predicate,
            "api_endpoints": feature_predicate,
            "technologies": dependency_predicate,
            "important_dependencies": dependency_predicate,
            "general_operation": lambda fc: "script" in fc.path.lower() or fc.path in
                                        ("Makefile", "requirements.txt", "package.json"),
            "architecture": lambda fc: "config" in fc.path.lower() or fc.path.startswith("."),
        }

        predicate = mapping.get(section_name)
        if predicate is None:
            return file_changes  # section inconnue → tout le contexte par défaut

        filtered = [fc for fc in file_changes if predicate(fc)]
        return filtered or file_changes  # fallback si rien ne matche explicitement

    # ------------------------------------------------------------------
    # apply_patch() — seule méthode qui persiste réellement
    # ------------------------------------------------------------------
    def apply_patch(self, patch: Patch) -> str:
        """
        Persiste le patch dans generated_readmes.
        Aucun appel IA ici — pure écriture.
        Retourne le contenu markdown final.

        Fix: readme_repository n'expose pas de méthode générique .update() —
        seulement get_or_create_for_repository()/update_content(instance, ...).
        L'appel précédent (self.readme_repository.update(repository_id=...))
        levait AttributeError à chaque tentative de publication.
        """
        if not patch.sections_json:
            raise ReadmeUpdaterError("Patch invalide: sections_json vide.")

        self.readme_repository.get_or_create_for_repository(
            repository_id=patch.repository_id,
            sections_json=patch.sections_json,
            content_md=patch.rendered_md,
        )

        return patch.rendered_md