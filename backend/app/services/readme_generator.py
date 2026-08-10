"""
README Generator — Phase 1, génération initiale complète.

Distinct de readme_updater.py : ce service ne fait PAS de patch partiel,
il produit le README complet à partir de zéro, une seule fois,
au moment où le repository est ajouté.
"""

import logging
from pathlib import Path

from app.services.ai_service import AIService, AIServiceError
from app.services.analyzer_service import ProjectAnalysis
from app.models.readme_version import TriggeredBy
from app.services.markdown_renderer import render_readme

logger = logging.getLogger(__name__)


class ReadmeGeneratorError(Exception):
    pass


class ReadmeGeneratorService:

    def __init__(
        self,
        ai_service: AIService,
        readme_repository,
        readme_version_repository,
    ):
        self.ai_service = ai_service
        self.readme_repository = readme_repository
        self.readme_version_repository = readme_version_repository

    def generate_initial_readme(
        self,
        repository_id: str,
        project_name: str,
        analysis: ProjectAnalysis,
        local_path: str,
    ) -> dict:
        """
        Génère et persiste le premier README d'un repository.

        Workflow :
        1. Prépare le contexte du projet.
        2. Génère le README avec Ollama.
        3. Rend le contenu en Markdown.
        4. Écrit README.md dans le clone local.
        5. Sauvegarde le README et sa version en DB.

        Le commit/push GitHub est effectué séparément par GitService.
        """

        # ============================================================
        # 1. CONTEXTE PROJET
        # ============================================================

        project_context = {
            "project_name": project_name,
            "languages": analysis.languages,
            "frameworks": analysis.frameworks,
            "dependencies": analysis.dependencies,
            "file_structure": analysis.file_structure,
            "install_scripts": analysis.install_scripts,
            "run_scripts": analysis.run_scripts,
        }

        # ============================================================
        # 2. GÉNÉRATION IA — OLLAMA
        # ============================================================

        try:
            print(
                f"🤖 [README] GÉNÉRATION OLLAMA — "
                f"repo_id={repository_id}"
            )

            sections_json = self.ai_service.generate_full_readme(
                project_context,
                repository_id=repository_id,
            )

        except AIServiceError as e:
            print(
                f"❌ [README] ERREUR — étape=OLLAMA — "
                f"repo_id={repository_id} — {e}"
            )

            logger.error(
                "Échec génération README initial pour repo %s: %s",
                repository_id,
                e,
            )

            raise ReadmeGeneratorError(
                f"Impossible de générer le README initial: {e}"
            ) from e

        # ============================================================
        # 3. RENDU MARKDOWN
        # ============================================================

        try:
            rendered_md = render_readme(sections_json)

        except Exception as e:
            print(
                f"❌ [README] ERREUR — étape=MARKDOWN — "
                f"repo_id={repository_id} — {e}"
            )

            logger.exception(
                "Erreur lors du rendu Markdown pour repo %s",
                repository_id,
            )

            raise ReadmeGeneratorError(
                f"Impossible de rendre le README en Markdown: {e}"
            ) from e

        print(
            f"📝 [README] README GÉNÉRÉ — "
            f"repo_id={repository_id}"
        )

        # ============================================================
        # 4. ÉCRITURE README.md DANS LE CLONE LOCAL
        # ============================================================

        try:
            if not local_path:
                raise ReadmeGeneratorError(
                    "Le chemin local du clone est vide."
                )

            repo_path = Path(local_path)

            if not repo_path.exists():
                raise ReadmeGeneratorError(
                    f"Le clone local est introuvable: {local_path}"
                )

            readme_path = repo_path / "README.md"

            readme_path.write_text(
                rendered_md,
                encoding="utf-8",
            )

            print(
                f"📄 [README] README.md ÉCRIT DANS LE CLONE — "
                f"repo_id={repository_id} — "
                f"path={readme_path}"
            )

        except ReadmeGeneratorError:
            raise

        except Exception as e:
            print(
                f"❌ [README] ERREUR — étape=ÉCRITURE FICHIER — "
                f"repo_id={repository_id} — {e}"
            )

            logger.exception(
                "Impossible d'écrire README.md pour repo %s",
                repository_id,
            )

            raise ReadmeGeneratorError(
                f"Impossible d'écrire README.md dans le clone: {e}"
            ) from e

        # ============================================================
        # 5. SAUVEGARDE DATABASE
        # ============================================================

        try:
            print(
                f"💾 [README] SAUVEGARDE DB — "
                f"repo_id={repository_id}"
            )

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

        except Exception as e:
            print(
                f"❌ [README] ERREUR — étape=SAUVEGARDE DB — "
                f"repo_id={repository_id} — {e}"
            )

            logger.exception(
                "Erreur sauvegarde README en DB pour repo %s",
                repository_id,
            )

            raise

        # ============================================================
        # 6. TERMINÉ
        # ============================================================

        print(
            f"✅ [README] GÉNÉRATION + ÉCRITURE TERMINÉES — "
            f"repo_id={repository_id}"
        )

        return {
            "sections_json": sections_json,
            "readme": readme,
            "version": version,
            "content_md": rendered_md,
            "local_path": str(local_path),
            "readme_path": str(readme_path),
        }