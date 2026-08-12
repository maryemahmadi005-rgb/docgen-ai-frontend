"""
README Generator — génération initiale complète.

Flow :

AnalyzerService
↓
AIService
↓
Markdown Renderer
↓
Database
↓
README.md local
↓
Git add
↓
Git commit
↓
Git push

Ce service orchestre la génération du README.

La logique Git bas niveau reste dans GitService.

IMPORTANT — cohérence de schéma :
sections_json ne contient JAMAIS que les clés de
AIService.README_SCHEMA (project_goal, general_operation,
architecture, technologies, main_modules, data_flow, entry_points,
api_endpoints, important_dependencies, recommendations,
installation, usage). Les preuves brutes de AnalyzerService
(file_structure, important_files, install_scripts, run_scripts,
configuration_evidence, frontend_api_calls, installation_evidence,
usage_evidence) ne sont transmises qu'à AIService pour construire
le prompt ; elles ne font pas partie du README rendu telles quelles
(voir règle: ne jamais afficher un catalogue de fichiers dans le
README) — seules les versions rédigées/structurées par le LLM
(installation/usage) apparaissent dans sections_json.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from app.services.ai_service import (
    AIService,
    AIServiceError,
)

from app.services.analyzer_service import (
    ProjectAnalysis,
)

from app.models.readme_version import (
    TriggeredBy,
)

from app.services.markdown_renderer import (
    render_readme,
    validate_rendered_readme,
)

from app.services.git_service import (
    GitService,
    GitServiceError,
)


logger = logging.getLogger(__name__)


class ReadmeGeneratorError(Exception):
    """Erreur de génération ou publication du README."""

    pass


# ============================================================
# PROJECT CONTEXT
# ============================================================


def build_project_context(
    project_name: str,
    analysis: ProjectAnalysis,
) -> dict[str, Any]:
    """
    Transforme ProjectAnalysis en contexte AI.

    ProjectAnalysis reste la source de vérité. Ce contexte est
    volontairement plus riche que sections_json : il inclut des
    preuves internes (file_structure, install_scripts, ...) qui
    servent à AIService pour rédiger un texte spécifique au projet,
    mais qui ne se retrouveront jamais telles quelles dans le README
    rendu.
    """

    return {
        "project_name": project_name,
        "languages": analysis.languages,
        "frameworks": analysis.frameworks,
        "dependencies": analysis.dependencies,
        "file_structure": analysis.file_structure,
        "important_files": analysis.important_files,
        "entry_points": analysis.entry_points,
        "install_scripts": analysis.install_scripts,
        "run_scripts": analysis.run_scripts,
        "code_evidence": analysis.code_evidence,
        "api_endpoints": analysis.api_endpoints,
        "frontend_api_calls": analysis.frontend_api_calls,
        "configuration_evidence": analysis.configuration_evidence,
        "architecture": getattr(analysis, "architecture", {}),
        "installation_evidence": getattr(analysis, "installation_evidence", {}),
        "usage_evidence": getattr(analysis, "usage_evidence", {}),
    }


# ============================================================
# DEBUG LOG
# ============================================================


def _log_project_analysis(
    repository_id: str,
    analysis: ProjectAnalysis,
    project_context: dict[str, Any],
) -> None:
    """Trace le contexte transmis à AIService."""

    try:
        context_size = len(
            json.dumps(project_context, ensure_ascii=False, default=str)
        )
    except Exception:
        context_size = 0

    print(f"[README] ProjectAnalysis received — repo_id={repository_id}")
    print(f"[README] Languages: {analysis.languages}")
    print(f"[README] Frameworks: {analysis.frameworks}")
    print(
        f"[README] Important files: {len(analysis.important_files or [])}"
    )
    print(f"[README] Entry points: {len(analysis.entry_points or [])}")
    print(f"[README] API endpoints: {len(analysis.api_endpoints or [])}")
    print(
        "[README] Installation evidence keys: "
        f"{list((getattr(analysis, 'installation_evidence', {}) or {}).keys())}"
    )
    print(
        "[README] Usage evidence keys: "
        f"{list((getattr(analysis, 'usage_evidence', {}) or {}).keys())}"
    )
    print(f"[README] Context size: {context_size}")

    logger.info(
        "[README] ProjectAnalysis received — repo_id=%s — context_size=%d",
        repository_id,
        context_size,
    )


# ============================================================
# SERVICE
# ============================================================


class ReadmeGeneratorService:

    def __init__(
        self,
        ai_service: AIService,
        readme_repository,
        readme_version_repository,
        git_service: GitService,
    ) -> None:

        self.ai_service = ai_service
        self.readme_repository = readme_repository
        self.readme_version_repository = readme_version_repository
        self.git_service = git_service

    # ========================================================
    # LOCAL README PATH
    # ========================================================

    def _get_local_repository_path(self, repository_id: str) -> str:
        """
        Retourne le chemin du clone local.

        GitService clone les repositories sous :
        <clones_base_dir>/<repository_id>
        """

        return os.path.normpath(
            os.path.join(
                self.git_service.clones_base_dir,
                str(repository_id),
            )
        )

    # ========================================================
    # WRITE README
    # ========================================================

    def _write_readme_file(
        self,
        repository_id: str,
        rendered_md: str,
    ) -> str:
        """
        Écrit README.md dans le clone local.

        Retourne le chemin absolu du fichier.
        """

        local_path = self._get_local_repository_path(repository_id)

        if not os.path.isdir(local_path):
            raise ReadmeGeneratorError(
                "Clone local introuvable pour "
                f"le repository {repository_id}: {local_path}"
            )

        readme_path = os.path.join(local_path, "README.md")

        try:
            with open(
                readme_path, "w", encoding="utf-8", newline="\n"
            ) as file:
                file.write(rendered_md.rstrip() + "\n")

        except OSError as exc:
            logger.exception(
                "Impossible d'écrire README.md pour repo %s",
                repository_id,
            )
            raise ReadmeGeneratorError(
                f"Impossible d'écrire README.md: {exc}"
            ) from exc

        print(
            f"📄 [README] FILE WRITTEN — repo_id={repository_id} — "
            f"path={readme_path}"
        )

        return readme_path

    # ========================================================
    # GIT PUBLISH
    # ========================================================

    def _commit_and_push_readme(self, repository_id: str) -> str:
        """
        Commit + push de README.md.

        GitService gère toute la logique Git.
        """

        local_path = self._get_local_repository_path(repository_id)

        try:
            commit_sha = self.git_service.commit_and_push(
                local_path=local_path,
                file_paths=["README.md"],
                commit_message="docs: generate initial README",
            )

        except GitServiceError as exc:
            logger.exception(
                "Échec publication README pour repo %s",
                repository_id,
            )
            raise ReadmeGeneratorError(
                "README généré mais impossible de le pousser vers Git: "
                f"{exc}"
            ) from exc

        print(
            f"🚀 [README] PUSH SUCCESS — repo_id={repository_id} — "
            f"commit={commit_sha}"
        )

        return commit_sha

    # ========================================================
    # VALIDATE SECTIONS
    # ========================================================

    @staticmethod
    def _validate_sections(sections_json: Any) -> None:
        """
        Validation structurelle avant rendu.

        sections_json doit correspondre EXACTEMENT à
        AIService.README_SCHEMA — ni clé manquante, ni clé en trop.
        Cette validation empêche un README mal formé ou un schéma
        divergent de passer jusqu'au commit/push.
        """

        if not isinstance(sections_json, dict):
            raise ReadmeGeneratorError(
                "AIService a retourné un résultat qui n'est pas un "
                "dictionnaire."
            )

        required_fields = set(AIService.README_SCHEMA)
        actual_fields = set(sections_json.keys())

        missing = required_fields - actual_fields
        if missing:
            raise ReadmeGeneratorError(
                "Sections README manquantes: " + ", ".join(sorted(missing))
            )

        unexpected = actual_fields - required_fields
        if unexpected:
            raise ReadmeGeneratorError(
                "Sections README inattendues (hors schéma): "
                + ", ".join(sorted(unexpected))
            )

        list_fields = (
            "technologies",
            "main_modules",
            "entry_points",
            "api_endpoints",
            "recommendations",
        )

        for field in list_fields:
            if not isinstance(sections_json[field], list):
                raise ReadmeGeneratorError(
                    f"La section '{field}' doit être une liste."
                )

        # Architecture and dependencies are factual Analyzer payloads.
        # They may be dictionaries/lists and must not be flattened.
        if not isinstance(sections_json["architecture"], (dict, list, str)):
            raise ReadmeGeneratorError(
                "La section 'architecture' doit être un objet, une "
                "liste ou une chaîne."
            )

        if not isinstance(
            sections_json["important_dependencies"], (dict, list)
        ):
            raise ReadmeGeneratorError(
                "La section 'important_dependencies' doit être un "
                "objet ou une liste."
            )

        text_fields = ("project_goal", "general_operation", "data_flow")

        for field in text_fields:
            if not isinstance(sections_json[field], str):
                raise ReadmeGeneratorError(
                    f"La section '{field}' doit être une chaîne."
                )

        # ----------------------------------------------------
        # MODULE VALIDATION
        # ----------------------------------------------------

        for index, module in enumerate(sections_json["main_modules"]):

            if not isinstance(module, dict):
                raise ReadmeGeneratorError(
                    f"main_modules[{index}] doit être un objet."
                )

            for field in ("name", "path", "role", "blueprint"):
                if not isinstance(module.get(field, ""), str):
                    raise ReadmeGeneratorError(
                        f"main_modules[{index}].{field} doit être "
                        "une chaîne."
                    )

            for field in ("classes", "functions", "dependencies", "routes"):
                if not isinstance(module.get(field, []), list):
                    raise ReadmeGeneratorError(
                        f"main_modules[{index}].{field} doit être "
                        "une liste."
                    )

    # ========================================================
    # ANALYZER FACTS
    # ========================================================

    @staticmethod
    def _apply_analyzer_facts(
        sections_json: dict[str, Any],
        project_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Réinjecte les faits directement depuis AnalyzerService.

        Le LLM ne peut donc jamais remplacer ou modifier les champs
        factuels utilisés par le README final. Le résultat contient
        strictement les clés de AIService.README_SCHEMA (10 champs
        historiques + installation/usage) — aucune preuve brute
        supplémentaire (file_structure, install_scripts, ...) n'est
        ajoutée ici : ces preuves ne servent qu'au prompt envoyé à
        AIService. installation/usage restent des champs rédigés par
        le LLM (voir LLM_WRITTEN_FIELDS) mais strictement bornés aux
        evidences AnalyzerService (installation_evidence/
        usage_evidence) transmises dans le prompt.
        """

        facts = {
            field: sections_json.get(field)
            for field in AIService.LLM_WRITTEN_FIELDS
        }

        facts["architecture"] = project_context.get("architecture", {})
        facts["entry_points"] = project_context.get("entry_points", [])
        facts["api_endpoints"] = project_context.get("api_endpoints", [])
        facts["important_dependencies"] = project_context.get(
            "dependencies", {}
        )

        # ProjectAnalysis n'expose pas un champ "technologies" dédié.
        # Les technologies affichées sont donc la projection
        # déterministe des langages et frameworks analysés.
        technologies: list[str] = []

        languages = project_context.get("languages", {})
        if isinstance(languages, dict):
            technologies.extend(
                key
                for key in languages.keys()
                if isinstance(key, str) and key.strip()
            )
        elif isinstance(languages, list):
            technologies.extend(
                item
                for item in languages
                if isinstance(item, str) and item.strip()
            )

        frameworks = project_context.get("frameworks", [])
        if isinstance(frameworks, list):
            technologies.extend(
                item
                for item in frameworks
                if isinstance(item, str) and item.strip()
            )
        elif isinstance(frameworks, dict):
            technologies.extend(
                key
                for key in frameworks.keys()
                if isinstance(key, str) and key.strip()
            )

        facts["technologies"] = list(dict.fromkeys(technologies))

        assert set(facts.keys()) == set(AIService.README_SCHEMA), (
            "_apply_analyzer_facts a produit un schéma inattendu: "
            f"{sorted(facts.keys())}"
        )

        return facts

    # ========================================================
    # MAIN
    # ========================================================

    def generate_initial_readme(
        self,
        repository_id: str,
        project_name: str,
        analysis: ProjectAnalysis,
    ) -> dict[str, Any]:
        """
        Génère le README initial complet.

        Flow :
        1. Construire le contexte.
        2. Appeler AIService.
        3. Valider sections_json.
        4. Render Markdown.
        5. Valider le Markdown.
        6. Sauvegarder en DB.
        7. Écrire README.md local.
        8. Commit.
        9. Push.
        """

        print(f"🚀 [README] INITIAL GENERATION START — repo_id={repository_id}")

        # ----------------------------------------------------
        # 1. CONTEXT
        # ----------------------------------------------------

        project_context = build_project_context(project_name, analysis)
        _log_project_analysis(repository_id, analysis, project_context)

        # ----------------------------------------------------
        # 2. AI
        # ----------------------------------------------------

        try:
            sections_json = self.ai_service.generate_full_readme(
                project_context,
                repository_id=repository_id,
            )

            # AnalyzerService reste la source de vérité finale pour
            # toutes les informations factuelles.
            sections_json = self._apply_analyzer_facts(
                sections_json,
                project_context,
            )

        except AIServiceError as exc:
            print(f"❌ [README] OLLAMA ERROR — repo_id={repository_id} — {exc}")
            logger.error(
                "Échec génération README initial pour repo %s: %s",
                repository_id,
                exc,
            )
            raise ReadmeGeneratorError(
                f"Impossible de générer le README initial: {exc}"
            ) from exc

        # ----------------------------------------------------
        # 3. STRUCTURAL VALIDATION
        # ----------------------------------------------------

        try:
            self._validate_sections(sections_json)

        except ReadmeGeneratorError:
            logger.exception(
                "[README] Invalid sections_json — repo_id=%s",
                repository_id,
            )
            raise

        print(f"✅ [README] AI SCHEMA VALID — repo_id={repository_id}")

        # ----------------------------------------------------
        # 4. MARKDOWN
        # ----------------------------------------------------

        try:
            rendered_md = render_readme(sections_json)

        except Exception as exc:
            logger.exception("Erreur rendu README repo %s", repository_id)
            raise ReadmeGeneratorError(
                f"Impossible de rendre le README: {exc}"
            ) from exc

        # ----------------------------------------------------
        # 5. RENDER VALIDATION
        # ----------------------------------------------------

        if not validate_rendered_readme(sections_json, rendered_md):
            logger.error(
                "[README] Rendered README invalid — repo_id=%s",
                repository_id,
            )
            raise ReadmeGeneratorError(
                "Le README généré est invalide. Aucun enregistrement "
                "ni push ne sera effectué."
            )

        print(
            f"📝 [README] README GENERATED — repo_id={repository_id} — "
            f"size={len(rendered_md)}"
        )

        # ----------------------------------------------------
        # 6. DATABASE
        # ----------------------------------------------------

        try:
            print(f"💾 [README] DATABASE SAVE — repo_id={repository_id}")

            readme = self.readme_repository.get_or_create_for_repository(
                repository_id=repository_id,
                sections_json=sections_json,
                content_md=rendered_md,
            )

            version = self.readme_version_repository.create_next_version(
                readme_id=readme.id,
                sections_json=sections_json,
                content_md=rendered_md,
                triggered_by=TriggeredBy.initial_generation,
            )

            self.readme_repository.update_content(
                readme,
                sections_json,
                rendered_md,
                current_version_id=version.id,
            )

        except Exception as exc:
            print(f"❌ [README] DATABASE ERROR — repo_id={repository_id} — {exc}")
            logger.exception(
                "Erreur sauvegarde README initial pour repo %s",
                repository_id,
            )
            raise ReadmeGeneratorError(
                f"Erreur sauvegarde README: {exc}"
            ) from exc

        # ----------------------------------------------------
        # 7. WRITE README.md
        # ----------------------------------------------------

        readme_path = self._write_readme_file(repository_id, rendered_md)

        # ----------------------------------------------------
        # 8. COMMIT + PUSH
        # ----------------------------------------------------

        commit_sha = self._commit_and_push_readme(repository_id)

        # ----------------------------------------------------
        # 9. DONE
        # ----------------------------------------------------

        print(
            f"🎉 [README] INITIAL GENERATION COMPLETE — "
            f"repo_id={repository_id} — commit={commit_sha}"
        )

        return {
            "sections_json": sections_json,
            "rendered_md": rendered_md,
            "readme": readme,
            "version": version,
            "readme_path": readme_path,
            "commit_sha": commit_sha,
        }