"""
Analyzer Service — scan complet d'un repository (Phase 1).

Responsabilités :

- détecter les langages
- détecter les frameworks
- extraire les dépendances
- construire la structure du repository
- détecter les fichiers importants
- sélectionner intelligemment les fichiers importants
- détecter les entry points
- extraire les preuves réelles du code
- détecter les endpoints API
- détecter les appels API frontend
- détecter les fichiers de configuration
- détecter les scripts d'installation/exécution

Aucun appel IA.
Aucun accès réseau.
Aucune modification du repository.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional


logger = logging.getLogger(__name__)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rb": "Ruby",
    ".java": "Java",
    ".php": "PHP",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
}


# ============================================================
# FRAMEWORK DETECTION
# ============================================================

FRAMEWORK_SIGNATURES = {
    # JavaScript / npm
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue.js",
    "@angular/core": "Angular",
    "express": "Express",
    "fastify": "Fastify",
    "nestjs": "NestJS",
    "@nestjs/core": "NestJS",
    "vite": "Vite",
    "webpack": "Webpack",

    # Python
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "streamlit": "Streamlit",

    # Other
    "gin-gonic": "Gin",
    "rails": "Ruby on Rails",
}


# ============================================================
# IMPORTANT FILES
# ============================================================

IMPORTANT_FILES = {
    "README.md",
    "LICENSE",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "Makefile",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "go.mod",
    "Gemfile",
    "setup.py",
    "pom.xml",
    "Cargo.toml",
    "composer.json",
}


# ============================================================
# IGNORED DIRECTORIES
# ============================================================

IGNORED_DIRS = {
    ".git",
    ".svn",
    ".hg",

    # JavaScript
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    ".cache",
    ".parcel-cache",
    "out",

    # Python
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    ".env",

    # Other
    "target",
    "vendor",
    "tmp",
    "temp",
}


IGNORED_FILE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".lock",
}


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class ProjectAnalysis:
    # {"Python": 42, "JavaScript": 94}
    languages: dict = field(default_factory=dict)

    # ["Flask", "React", "Vite"]
    frameworks: list = field(default_factory=list)

    # {"npm": [...], "pip": [...]}
    dependencies: dict = field(default_factory=dict)

    # Simplified repository tree
    file_structure: dict = field(default_factory=dict)

    # Important files
    important_files: list = field(default_factory=list)

    # Installation commands
    install_scripts: list = field(default_factory=list)

    # Run commands
    run_scripts: list = field(default_factory=list)

    # Entry points
    entry_points: list = field(default_factory=list)

    # Real code evidence
    code_evidence: list = field(default_factory=list)

    # Backend API endpoints
    api_endpoints: list = field(default_factory=list)

    # Frontend API calls
    frontend_api_calls: list = field(default_factory=list)

    # Configuration evidence
    configuration_evidence: list = field(default_factory=list)


# ============================================================
# ANALYZER SERVICE
# ============================================================

class AnalyzerService:
    """
    Analyseur déterministe d'un repository.

    Important :
    - aucune IA
    - aucun appel réseau
    - aucune modification du repository
    """

    # ========================================================
    # MAIN ANALYSIS
    # ========================================================

    def analyze(
        self,
        local_path: str,
        repository_id: Optional[str] = None,
    ) -> ProjectAnalysis:

        print(
            f"🔍 [README] ANALYSE START — "
            f"repo_id={repository_id} — path={local_path}"
        )

        if not local_path:
            raise ValueError("local_path est obligatoire")

        if not os.path.isdir(local_path):
            raise FileNotFoundError(
                f"Repository introuvable: {local_path}"
            )

        try:
            analysis = ProjectAnalysis()

            # ==================================================
            # LANGUAGES
            # ==================================================

            analysis.languages = self._detect_languages(
                local_path
            )

            # ==================================================
            # IMPORTANT FILES
            # ==================================================

            analysis.important_files = (
                self._find_important_files(
                    local_path
                )
            )

            # ==================================================
            # ENTRY POINTS
            # ==================================================

            analysis.entry_points = (
                self._detect_entry_points(
                    local_path
                )
            )

            # ==================================================
            # REAL CODE EVIDENCE
            # ==================================================

            analysis.code_evidence = (
                self._collect_code_evidence(
                    local_path
                )
            )

            # ==================================================
            # API ENDPOINTS
            #
            # IMPORTANT :
            # Ne dépend PAS de la limite code_evidence=35.
            # Tous les fichiers Python sont scannés pour
            # trouver les routes Flask réelles.
            # ==================================================

            analysis.api_endpoints = (
                self._extract_all_api_endpoints(
                    local_path
                )
            )

            # ==================================================
            # FRONTEND API CALLS
            # ==================================================

            analysis.frontend_api_calls = (
                self._extract_frontend_api_calls(
                    analysis.code_evidence
                )
            )

            # ==================================================
            # CONFIGURATION
            # ==================================================

            analysis.configuration_evidence = (
                self._collect_configuration_evidence(
                    local_path
                )
            )

            # ==================================================
            # FRAMEWORKS
            # ==================================================

            analysis.frameworks = (
                self._detect_frameworks(
                    local_path
                )
            )

            # ==================================================
            # DEPENDENCIES
            # ==================================================

            analysis.dependencies = (
                self._extract_dependencies(
                    local_path
                )
            )

            # ==================================================
            # STRUCTURE
            # ==================================================

            analysis.file_structure = (
                self._build_file_structure(
                    local_path
                )
            )

            # ==================================================
            # INSTALL / RUN SCRIPTS
            # ==================================================

            (
                analysis.install_scripts,
                analysis.run_scripts,
            ) = self._detect_scripts(
                local_path
            )

        except Exception as e:

            print(
                f"❌ [README] ERREUR — étape=ANALYSE — "
                f"repo_id={repository_id} — {e}"
            )

            logger.exception(
                "AnalyzerService failed for %s",
                local_path,
            )

            raise

        print(
            f"✅ [README] ANALYSE TERMINÉE — "
            f"repo_id={repository_id} — "
            f"langages={analysis.languages} — "
            f"frameworks={analysis.frameworks} — "
            f"entry_points={len(analysis.entry_points)} — "
            f"code_evidence={len(analysis.code_evidence)} — "
            f"api_endpoints={len(analysis.api_endpoints)}"
        )

        return analysis

    # ========================================================
    # IGNORE HELPERS
    # ========================================================

    def _is_ignored_dir(
        self,
        dirname: str,
    ) -> bool:

        return dirname in IGNORED_DIRS

    def _is_ignored_file(
        self,
        filename: str,
    ) -> bool:

        lower = filename.lower()

        _, ext = os.path.splitext(lower)

        return ext in IGNORED_FILE_EXTENSIONS

    # ========================================================
    # WALK REPOSITORY
    # ========================================================

    def _walk_repository(
        self,
        local_path: str,
    ):
        """
        Parcourt le repository réel.

        IMPORTANT :
        backend/ n'est PAS ignoré.
        Les fichiers Python dans backend/ sont donc analysés.

        Les dossiers générés/cache sont supprimés de dirs[:]
        afin que os.walk n'entre même pas dedans.
        """

        for root, dirs, files in os.walk(local_path):

            dirs[:] = sorted(
                d
                for d in dirs
                if not self._is_ignored_dir(d)
            )

            files = [
                f
                for f in files
                if not self._is_ignored_file(f)
            ]

            yield root, dirs, files

    # ========================================================
    # LANGUAGES
    # ========================================================

    def _detect_languages(
        self,
        local_path: str,
    ) -> dict:

        counts = {}

        for root, _, files in self._walk_repository(
            local_path
        ):

            print(
                f"🔎 [LANGUAGE] root={root} "
                f"— files={len(files)}"
            )

            for filename in files:

                ext = os.path.splitext(
                    filename
                )[1].lower()

                language = LANGUAGE_EXTENSIONS.get(
                    ext
                )

                if not language:
                    continue

                counts[language] = (
                    counts.get(language, 0) + 1
                )

        return dict(
            sorted(
                counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

    # ========================================================
    # IMPORTANT FILES
    # ========================================================

    def _find_important_files(
        self,
        local_path: str,
    ) -> list:
        """
        Détecte les fichiers importants à partir :
        - du nom
        - du chemin
        - du rôle potentiel

        Important :
        backend/ n'est jamais considéré automatiquement comme
        un backend. Le contenu est vérifié ailleurs.
        """

        found = set()

        important_names = {
            name.lower()
            for name in IMPORTANT_FILES
        }

        important_code_names = {
            "app.py",
            "main.py",
            "run.py",
            "server.py",
            "wsgi.py",
            "asgi.py",
            "manage.py",
            "models.py",
            "config.py",
            "settings.py",
            "__init__.py",
        }

        important_dir_names = {
            "routes",
            "route",
            "routers",
            "router",
            "api",
            "services",
            "service",
            "controllers",
            "controller",
            "models",
            "repositories",
            "repository",
            "config",
        }

        for root, _, files in self._walk_repository(
            local_path
        ):

            relative_root = os.path.relpath(
                root,
                local_path,
            ).replace("\\", "/")

            for filename in files:

                filename_lower = filename.lower()

                if relative_root != ".":
                    relative_path = (
                        f"{relative_root}/{filename}"
                    )
                else:
                    relative_path = filename

                relative_path = relative_path.replace(
                    "\\",
                    "/",
                )

                path_parts = {
                    part.lower()
                    for part in relative_path.split("/")
                }

                is_manifest = (
                    filename_lower in important_names
                )

                is_important_code = (
                    filename_lower in important_code_names
                )

                is_important_directory = bool(
                    path_parts.intersection(
                        important_dir_names
                    )
                )

                is_code_file = filename_lower.endswith(
                    (
                        ".py",
                        ".js",
                        ".jsx",
                        ".ts",
                        ".tsx",
                    )
                )

                if (
                    is_manifest
                    or is_important_code
                    or (
                        is_important_directory
                        and is_code_file
                    )
                ):
                    found.add(relative_path)

        return sorted(found)

    # ========================================================
    # ENTRY POINTS
    # ========================================================

    def _detect_entry_points(
        self,
        local_path: str,
    ) -> list:
        """
        Détecte les vrais points d'entrée à partir :
        - du nom
        - du contenu réel.
        """

        found = set()

        candidate_names = {
            "app.py",
            "main.py",
            "run.py",
            "server.py",
            "index.py",
            "manage.py",
            "wsgi.py",
            "asgi.py",
            "App.jsx",
            "App.js",
            "main.jsx",
            "main.js",
            "index.jsx",
            "index.js",
            "App.tsx",
            "main.tsx",
            "index.tsx",
        }

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                full_path = os.path.join(
                    root,
                    filename,
                )

                relative_path = os.path.relpath(
                    full_path,
                    local_path,
                ).replace("\\", "/")

                extension = os.path.splitext(
                    filename
                )[1].lower()

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                content_lower = content.lower()

                # --------------------------------------------
                # Flask entry point
                # --------------------------------------------

                flask_signals = (
                    "from flask import",
                    "import flask",
                    "flask(",
                    "create_app(",
                    "blueprint(",
                    "register_blueprint(",
                    "@app.route",
                    "@bp.route",
                )

                is_flask = (
                    extension == ".py"
                    and any(
                        signal in content_lower
                        for signal in flask_signals
                    )
                )

                if is_flask:
                    found.add(relative_path)
                    continue

                # --------------------------------------------
                # Python executable entry point
                # --------------------------------------------

                python_entry = (
                    extension == ".py"
                    and (
                        filename in candidate_names
                        or 'if __name__ == "__main__"'
                        in content
                    )
                )

                if python_entry:
                    found.add(relative_path)
                    continue

                # --------------------------------------------
                # React / Vite entry point
                # --------------------------------------------

                frontend_entry = (
                    extension in {
                        ".js",
                        ".jsx",
                        ".ts",
                        ".tsx",
                    }
                    and (
                        filename in candidate_names
                        or "createRoot(" in content
                        or "ReactDOM.createRoot"
                        in content
                        or "ReactDOM.render"
                        in content
                    )
                )

                if frontend_entry:
                    found.add(relative_path)

        return sorted(found)

    # ========================================================
    # CODE EVIDENCE
    # ========================================================

    def _collect_code_evidence(
        self,
        local_path: str,
        max_files: int = 35,
        max_chars_per_file: int = 8000,
    ) -> list:
        """
        Sélectionne les preuves de code.

        IMPORTANT :
        le top global ne doit pas faire disparaître le backend.

        On garantit donc :
        - backend evidence
        - frontend evidence
        - routes
        - services
        - entry points
        """

        code_extensions = {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rb",
            ".php",
            ".rs",
            ".cpp",
            ".c",
            ".cs",
            ".swift",
            ".kt",
        }

        candidates = []

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension not in code_extensions:
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                relative_path = os.path.relpath(
                    full_path,
                    local_path,
                ).replace("\\", "/")

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                file_info = {
                    "path": relative_path,
                    "full_path": full_path,
                    "size": len(content),
                }

                score = self._advanced_score_file(
                    file_info,
                    content,
                )

                if score <= -900000:
                    continue

                candidates.append(
                    {
                        "path": relative_path,
                        "full_path": full_path,
                        "score": score,
                        "content": content[
                            :max_chars_per_file
                        ],
                    }
                )

        backend_candidates = []
        frontend_candidates = []
        other_candidates = []

        for item in candidates:

            normalized = item["path"].lower()
            content_lower = item["content"].lower()

            # ------------------------------------------------
            # Backend detection
            # ------------------------------------------------

            is_backend = (
                normalized.startswith("backend/")
                or "/backend/" in normalized
                or (
                    normalized.endswith(".py")
                    and any(
                        signal in content_lower
                        for signal in (
                            "from flask import",
                            "import flask",
                            "@app.route",
                            "@bp.route",
                            "blueprint(",
                            "register_blueprint(",
                            "fastapi(",
                            "from fastapi import",
                        )
                    )
                )
            )

            # ------------------------------------------------
            # Frontend detection
            # ------------------------------------------------

            is_frontend = (
                normalized.startswith("frontend/")
                or normalized.startswith("front2/")
                or "/frontend/" in normalized
                or "/front2/" in normalized
                or normalized.endswith(
                    (
                        ".jsx",
                        ".tsx",
                    )
                )
            )

            if is_backend:
                backend_candidates.append(item)

            elif is_frontend:
                frontend_candidates.append(item)

            else:
                other_candidates.append(item)

        backend_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        frontend_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        other_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # ----------------------------------------------------
        # Selected evidence
        # ----------------------------------------------------

        selected = []
        selected_paths = set()

        def add_item(item):
            path = item["path"]

            if path in selected_paths:
                return

            selected.append(item)
            selected_paths.add(path)

        # ----------------------------------------------------
        # Backend first
        # ----------------------------------------------------

        for item in backend_candidates:

            path_lower = item["path"].lower()
            filename = os.path.basename(
                path_lower
            )

            content_lower = item["content"].lower()

            is_route_file = any(
                marker in path_lower
                for marker in (
                    "/routes/",
                    "/route/",
                    "/routers/",
                    "/router/",
                    "/api/",
                )
            )

            is_service_file = any(
                marker in path_lower
                for marker in (
                    "/services/",
                    "/service/",
                )
            )

            is_backend_entry = filename in {
                "run.py",
                "app.py",
                "main.py",
                "server.py",
                "wsgi.py",
                "asgi.py",
                "__init__.py",
            }

            has_flask_signal = any(
                marker in content_lower
                for marker in (
                    "from flask import",
                    "import flask",
                    "@app.route",
                    "@bp.route",
                    "blueprint(",
                    "register_blueprint(",
                )
            )

            if (
                is_route_file
                or is_service_file
                or is_backend_entry
                or has_flask_signal
            ):
                add_item(item)

        # ----------------------------------------------------
        # Remaining backend
        # ----------------------------------------------------

        for item in backend_candidates:
            add_item(item)

        # ----------------------------------------------------
        # Frontend
        # ----------------------------------------------------

        for item in frontend_candidates:
            add_item(item)

        # ----------------------------------------------------
        # Other code
        # ----------------------------------------------------

        for item in other_candidates:
            add_item(item)

        # ----------------------------------------------------
        # Limit
        # ----------------------------------------------------

        selected = selected[:max_files]

        print(
            "\n========== README CODE EVIDENCE =========="
        )

        for item in selected:

            print(
                f"{item['path']} "
                f"score={item['score']} "
                f"chars={len(item['content'])}"
            )

        print(
            "==========================================\n"
        )

        return selected

    # ========================================================
    # IMPORTANT FILE SELECTION
    # ========================================================

    def _select_important_files(
        self,
        text_files,
        max_files=None,
    ):
        """
        Sélection intelligente des fichiers importants.
        """

        ranked = []

        for file_info in text_files:

            try:

                full_path = file_info["full_path"]

                content = (
                    self._read_file_safe(
                        full_path
                    )
                    or ""
                )

                score = self._advanced_score_file(
                    file_info,
                    content,
                )

                file_info["importance_score"] = score

                print(
                    "SELECT SCORE:",
                    file_info["path"],
                    "=>",
                    score,
                )

                ranked.append(file_info)

            except Exception as e:

                logger.warning(
                    "Impossible de scorer %s: %s",
                    file_info.get("path"),
                    e,
                )

                continue

        ranked.sort(
            key=lambda x: x.get(
                "importance_score",
                -999999,
            ),
            reverse=True,
        )

        if max_files is None:

            max_files = int(
                os.environ.get(
                    "DOC_IMPORTANT_FILES_LIMIT",
                    "35",
                )
            )

        ranked = [
            f
            for f in ranked
            if f.get(
                "importance_score",
                -999999,
            ) > -5000
        ]

        print(
            "\n========== TOP IMPORTANT FILES =========="
        )

        for file_info in ranked[:max_files]:

            print(
                f"{file_info.get('path')} "
                f"score={file_info.get('importance_score')}"
            )

        print(
            "=========================================\n"
        )

        return ranked[:max_files]

    # ========================================================
    # STRUCTURAL FILE SCORE
    # ========================================================

    def _score_file(
        self,
        file_info,
    ):
        """
        Score structurel de base.
        """

        path_lower = (
            file_info["path"]
            .replace("\\", "/")
            .lower()
        )

        filename = os.path.basename(
            path_lower
        )

        score = 0

        # ==================================================
        # ENTRY POINTS
        # ==================================================

        entry_points = {
            "app.py",
            "main.py",
            "server.py",
            "index.py",
            "index.js",
            "index.ts",
            "manage.py",
            "wsgi.py",
            "asgi.py",
            "run.py",
            "flasky.py",
        }

        if filename in entry_points:
            score += 9000

        # ==================================================
        # INIT FILES
        # ==================================================

        if (
            filename == "__init__.py"
            and any(
                x in path_lower
                for x in (
                    "app/",
                    "src/",
                    "backend/",
                    "server/",
                )
            )
        ):
            score += 7000

        # ==================================================
        # BUSINESS DIRECTORIES
        # ==================================================

        business_paths = [
            "app/",
            "src/",
            "backend/",
            "server/",
            "core/",
            "services/",
            "service/",
            "controllers/",
            "controller/",
            "routes/",
            "routers/",
            "models/",
            "repositories/",
            "entities/",
            "domain/",
            "modules/",
            "api/",
        ]

        if any(
            p in path_lower
            for p in business_paths
        ):
            score += 5000

        # ==================================================
        # CODE FILES
        # ==================================================

        code_extensions = (
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".php",
            ".rb",
            ".rs",
            ".cpp",
            ".c",
            ".cs",
            ".swift",
            ".kt",
        )

        if path_lower.endswith(
            code_extensions
        ):
            score += 1500

        # ==================================================
        # DEPENDENCY FILES
        # ==================================================

        dependency_files = {
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "pom.xml",
            "cargo.toml",
            "gemfile",
            "go.mod",
            "composer.json",
        }

        if filename in dependency_files:
            score += 2000

        # ==================================================
        # DEPLOYMENT CONFIG
        # ==================================================

        deploy_configs = {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "vite.config.js",
            "vite.config.ts",
            "tsconfig.json",
        }

        if filename in deploy_configs:
            score += 500

        # ==================================================
        # LOW VALUE
        # ==================================================

        if filename.startswith("readme"):
            score -= 12000

        if filename.endswith(
            (
                ".md",
                ".txt",
            )
        ):
            score -= 8000

        low_dirs = [
            "docs/",
            "documentation/",
            "static/",
            "assets/",
            "images/",
            "public/",
            "coverage/",
            "examples/",
            "example/",
            "samples/",
            "sample/",
            "tests/",
            "test/",
        ]

        if any(
            x in path_lower
            for x in low_dirs
        ):
            score -= 15000

        # ==================================================
        # SHELL SCRIPTS
        # ==================================================

        if filename in {
            "boot.sh",
            "start.sh",
            "run.sh",
            "build.sh",
        }:
            score -= 40000

        # ==================================================
        # FILE SIZE
        # ==================================================

        size = file_info.get("size", 0)

        if 1000 < size < 200000:
            score += 500

        return score

    # ========================================================
    # ADVANCED FILE SCORE
    # ========================================================

    def _advanced_score_file(
        self,
        file_info,
        content,
    ):
        """
        Score final d'un fichier.
        """

        path = (
            file_info["path"]
            .replace("\\", "/")
            .lower()
        )

        filename = os.path.basename(path)

        content_lower = content.lower()

        score = self._score_file(
            file_info
        )

        # ==================================================
        # GENERATED / DEPENDENCIES
        # ==================================================

        excluded_dirs = [
            "node_modules/",
            "vendor/",
            "__pycache__/",
            "dist/",
            "build/",
            "coverage/",
            ".next/",
            ".nuxt/",
            "migrations/",
            "templates/",
            "static/",
            "assets/",
            "public/",
        ]

        if any(
            x in path
            for x in excluded_dirs
        ):
            return -999999

        # ==================================================
        # TESTS
        # ==================================================

        if any(
            x in path
            for x in (
                "test/",
                "tests/",
                "__tests__/",
                "spec/",
            )
        ):
            score -= 30000

        # ==================================================
        # BUSINESS CODE
        # ==================================================

        if any(
            x in path
            for x in (
                "services/",
                "controllers/",
                "routes/",
                "routers/",
                "models/",
                "repositories/",
                "core/",
                "api/",
                "auth/",
            )
        ):
            score += 50000

        if filename == "models.py":
            score += 60000

        # ==================================================
        # BACKEND PRIORITY
        # ==================================================

        if (
            path.startswith("backend/")
            and filename.endswith(".py")
        ):
            score += 12000

        if (
            "/backend/" in path
            and filename.endswith(".py")
        ):
            score += 12000

        # ==================================================
        # ENTRY POINTS
        # ==================================================

        if filename in {
            "app.py",
            "main.py",
            "server.py",
            "index.py",
            "index.js",
            "index.ts",
            "manage.py",
            "wsgi.py",
            "asgi.py",
            "run.py",
        }:
            score += 9000

        # ==================================================
        # FRAMEWORK / API SIGNALS
        # ==================================================

        signals = {
            "flask": 500,
            "fastapi": 500,
            "django": 500,
            "express": 500,
            "router": 400,
            "@app.route": 600,
            "@bp.route": 600,
            ".route(": 500,
            "blueprint": 500,
            "register_blueprint": 700,
            "controller": 300,
            "service": 300,
            "repository": 300,
            "class ": 150,
            "def ": 100,
            "async def": 150,
            "sqlalchemy": 400,
            "mongoose": 400,
            "sequelize": 300,
            "axios": 400,
            "fetch(": 400,
            "usestate": 150,
            "useeffect": 150,
            "react": 300,
        }

        for signal, bonus in signals.items():

            if signal in content_lower:
                score += bonus

        # ==================================================
        # LOW VALUE
        # ==================================================

        if filename.startswith("readme"):
            score -= 5000

        if path.startswith("docs/"):
            score -= 20000

        if filename.endswith(
            (
                ".html",
                ".css",
            )
        ):
            score -= 15000

        # ==================================================
        # CONFIGURATION
        # ==================================================

        config_files = {
            "docker-compose.yml",
            "docker-compose.yaml",
            "dockerfile",
            "vite.config.js",
            "vite.config.ts",
            "tsconfig.json",
            "mkdocs.yml",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
        }

        if filename in config_files:

            if filename in {
                "requirements.txt",
                "package.json",
                "pyproject.toml",
            }:
                score += 10000

            else:
                score = min(
                    score,
                    4000,
                )

        # ==================================================
        # FAKE / MOCK
        # ==================================================

        if any(
            x in filename
            for x in (
                "fake",
                "mock",
                "dummy",
                "sample",
            )
        ):
            return -999999

        # ==================================================
        # SHELL SCRIPTS
        # ==================================================

        if filename.endswith(
            (
                ".sh",
                ".bat",
                ".cmd",
            )
        ):
            score -= 50000

        # ==================================================
        # PROJECT SPECIFIC PRIORITY
        # ==================================================

        priority_files = {
            "app/__init__.py": 50000,
            "app/models.py": 45000,
            "config.py": 30000,
            "flasky.py": 30000,
        }

        normalized_path = (
            path
            .replace("\\", "/")
            .lower()
        )

        for priority_path, bonus in (
            priority_files.items()
        ):

            if normalized_path.endswith(
                priority_path
            ):
                score += bonus
                break

        # ==================================================
        # FLASK AUTH
        # ==================================================

        if (
            path.startswith("app/auth/")
            and filename.endswith(".py")
        ):
            score += 40000

        # ==================================================
        # VERY IMPORTANT FLASK INIT
        # ==================================================

        if normalized_path.endswith(
            "app/__init__.py"
        ):
            score += 100000

        print(
            "FINAL SCORE:",
            file_info["path"],
            score,
        )

        return score

    # ========================================================
    # API ENDPOINTS
    # ========================================================

    def _extract_api_endpoints(
        self,
        code_evidence: list,
    ) -> list:
        """
        Extrait les endpoints Flask réels.

        Support :
        - @app.route(...)
        - @bp.route(...)
        - @api.route(...)
        - @app.get(...)
        - @app.post(...)
        - @app.put(...)
        - @app.patch(...)
        - @app.delete(...)
        - @app.options(...)

        Aucun endpoint n'est inventé.
        """

        endpoints = []

        # ----------------------------------------------------
        # @app.route("/path", methods=[...])
        # ----------------------------------------------------

        route_pattern = re.compile(
            r"""
            @
            (?P<object>[A-Za-z_]\w*)
            \.
            route
            \(
            \s*
            (?P<quote>['"])
            (?P<path>.*?)
            (?P=quote)
            (?P<args>.*?)
            \)
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        # ----------------------------------------------------
        # @app.get("/path")
        # ----------------------------------------------------

        method_pattern = re.compile(
            r"""
            @
            (?P<object>[A-Za-z_]\w*)
            \.
            (?P<method>
                get|
                post|
                put|
                patch|
                delete|
                options
            )
            \(
            \s*
            (?P<quote>['"])
            (?P<path>.*?)
            (?P=quote)
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        methods_pattern = re.compile(
            r"""
            methods
            \s*=\s*
            \[
            (?P<methods>[^\]]*)
            \]
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        string_pattern = re.compile(
            r"""['"]([A-Za-z]+)['"]"""
        )

        seen = set()

        for item in code_evidence:

            path = item["path"]
            content = item["content"]

            if not path.lower().endswith(".py"):
                continue

            # ------------------------------------------------
            # @something.route()
            # ------------------------------------------------

            for match in route_pattern.finditer(
                content
            ):

                endpoint = match.group("path")
                args = match.group("args")

                methods_match = (
                    methods_pattern.search(args)
                )

                if methods_match:

                    methods = [
                        method.upper()
                        for method in string_pattern.findall(
                            methods_match.group("methods")
                        )
                        if method.upper()
                        in {
                            "GET",
                            "POST",
                            "PUT",
                            "PATCH",
                            "DELETE",
                            "OPTIONS",
                        }
                    ]

                    if not methods:
                        methods = ["GET"]

                else:
                    methods = ["GET"]

                key = (
                    path,
                    endpoint,
                    tuple(methods),
                )

                if key in seen:
                    continue

                seen.add(key)

                endpoints.append(
                    {
                        "file": path,
                        "endpoint": endpoint,
                        "methods": methods,
                        "_decorator_object": match.group(
                            "object"
                        ),
                    }
                )

            # ------------------------------------------------
            # @something.get/post/put/...
            # ------------------------------------------------

            for match in method_pattern.finditer(
                content
            ):

                method = match.group(
                    "method"
                ).upper()

                endpoint = match.group(
                    "path"
                )

                if method not in {
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                }:
                    continue

                key = (
                    path,
                    endpoint,
                    (method,),
                )

                if key in seen:
                    continue

                seen.add(key)

                endpoints.append(
                    {
                        "file": path,
                        "endpoint": endpoint,
                        "methods": [method],
                        "_decorator_object": match.group(
                            "object"
                        ),
                    }
                )

        return endpoints

    # ========================================================
    # EXTRACT ALL API ENDPOINTS
    # ========================================================

    def _extract_all_api_endpoints(
        self,
        local_path: str,
    ) -> list:
        """
        Scanne directement TOUS les fichiers Python.

        Très important :
        cette méthode ne dépend pas de code_evidence=35.

        Donc même si le frontend possède énormément de fichiers,
        les routes backend restent détectables.
        """

        all_python_evidence = []

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                if not filename.lower().endswith(".py"):
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                relative_path = os.path.relpath(
                    full_path,
                    local_path,
                ).replace("\\", "/")

                all_python_evidence.append(
                    {
                        "path": relative_path,
                        "full_path": full_path,
                        "content": content,
                        "score": 0,
                    }
                )

        endpoints = self._extract_api_endpoints(
            all_python_evidence
        )

        return self._resolve_blueprint_prefixes(
            all_python_evidence,
            endpoints,
        )

    # ========================================================
    # BLUEPRINT PREFIX RESOLUTION
    # ========================================================

    def _resolve_blueprint_prefixes(
        self,
        python_files: list,
        endpoints: list,
    ) -> list:
        """
        Résout les prefixes Blueprint uniquement lorsqu'ils
        sont explicitement présents dans le code.

        Exemple :

            api_bp = Blueprint(
                "api",
                __name__,
                url_prefix="/api"
            )

            @api_bp.route("/users")

        devient :

            /api/users
        """

        blueprint_prefixes = {}

        blueprint_pattern = re.compile(
            r"""
            (?P<name>[A-Za-z_]\w*)
            \s*=
            \s*Blueprint
            \s*\(
            .*?
            url_prefix
            \s*=
            \s*
            (?P<quote>['"])
            (?P<prefix>.*?)
            (?P=quote)
            """,
            re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        # ----------------------------------------------------
        # Find Blueprint variable -> prefix
        # ----------------------------------------------------

        for item in python_files:

            content = item["content"]

            for match in blueprint_pattern.finditer(
                content
            ):

                name = match.group("name")
                prefix = match.group("prefix")

                if not prefix.startswith("/"):
                    prefix = "/" + prefix

                if prefix != "/":
                    prefix = prefix.rstrip("/")

                blueprint_prefixes[name] = prefix

        # ----------------------------------------------------
        # Apply prefix
        # ----------------------------------------------------

        result = []

        for endpoint in endpoints:

            file_path = endpoint["file"]
            endpoint_path = endpoint["endpoint"]

            content = ""

            for item in python_files:

                if item["path"] == file_path:
                    content = item["content"]
                    break

            decorator_object = endpoint.get(
                "_decorator_object"
            )

            prefix = (
                blueprint_prefixes.get(
                    decorator_object
                )
                if decorator_object
                else None
            )

            if not endpoint_path.startswith("/"):
                endpoint_path = "/" + endpoint_path

            if prefix:
                if prefix == "/":
                    resolved_path = endpoint_path
                else:
                    resolved_path = (
                        prefix.rstrip("/")
                        + "/"
                        + endpoint_path.lstrip("/")
                    )

                    if resolved_path != "/":
                        resolved_path = (
                            resolved_path.rstrip("/")
                        )
            else:
                resolved_path = endpoint_path

            clean_endpoint = {
                "file": file_path,
                "endpoint": resolved_path,
                "methods": endpoint["methods"],
            }

            result.append(
                clean_endpoint
            )

        # ----------------------------------------------------
        # Remove exact duplicates
        # ----------------------------------------------------

        unique = []
        seen = set()

        for item in result:

            key = (
                item["file"],
                item["endpoint"],
                tuple(item["methods"]),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        return unique

    # ========================================================
    # FLASK BACKEND DETECTION
    # ========================================================

    def _detect_flask_backend(
        self,
        local_path: str,
    ) -> bool:
        """
        Détecte Flask depuis le contenu réel.

        Le nom backend/ seul ne suffit PAS.
        """

        flask_signals = (
            r"\bfrom\s+flask\s+import\b",
            r"\bimport\s+flask\b",
            r"\bFlask\s*\(",
            r"\bBlueprint\s*\(",
            r"@[\w_]+\.(?:route|get|post|put|patch|delete|options)\s*\(",
            r"\bregister_blueprint\s*\(",
        )

        patterns = [
            re.compile(
                pattern,
                re.IGNORECASE,
            )
            for pattern in flask_signals
        ]

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                if not filename.lower().endswith(".py"):
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                if any(
                    pattern.search(content)
                    for pattern in patterns
                ):
                    return True

        return False

    # ========================================================
    # FRAMEWORK DETECTION
    # ========================================================

    def _detect_frameworks(
        self,
        local_path: str,
    ) -> list:

        frameworks = set()

        # ----------------------------------------------------
        # Manifest detection
        # ----------------------------------------------------

        manifests = self._find_manifest_files(
            local_path
        )

        for filename, path, _ in manifests:

            content = self._read_file_safe(
                path
            )

            if not content:
                continue

            content_lower = content.lower()

            for (
                signature,
                framework_name,
            ) in FRAMEWORK_SIGNATURES.items():

                if signature.lower() in content_lower:
                    frameworks.add(
                        framework_name
                    )

        # ----------------------------------------------------
        # Real Flask source detection
        # ----------------------------------------------------

        if self._detect_flask_backend(
            local_path
        ):
            frameworks.add("Flask")

        # ----------------------------------------------------
        # React source detection
        # ----------------------------------------------------

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension not in {
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                }:
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                content_lower = content.lower()

                if (
                    "from 'react'" in content_lower
                    or 'from "react"' in content_lower
                    or "from 'react-dom'"
                    in content_lower
                    or 'from "react-dom"'
                    in content_lower
                    or "createroot("
                    in content_lower
                ):
                    frameworks.add("React")

        return sorted(frameworks)

    # ========================================================
    # DEPENDENCIES
    # ========================================================

    def _extract_dependencies(
        self,
        local_path: str,
    ) -> dict:

        dependencies = {
            "npm": [],
            "pip": [],
            "other": [],
        }

        for (
            filename,
            path,
            relative_path,
        ) in self._find_manifest_files(
            local_path
        ):

            content = self._read_file_safe(
                path
            )

            if not content:
                continue

            # ------------------------------------------------
            # package.json
            # ------------------------------------------------

            if filename == "package.json":

                try:

                    data = json.loads(
                        content
                    )

                    npm_dependencies = set()

                    npm_dependencies.update(
                        data.get(
                            "dependencies",
                            {},
                        ).keys()
                    )

                    npm_dependencies.update(
                        data.get(
                            "devDependencies",
                            {},
                        ).keys()
                    )

                    for dependency in sorted(
                        npm_dependencies
                    ):

                        dependencies["npm"].append(
                            f"{relative_path}: "
                            f"{dependency}"
                        )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    logger.warning(
                        "Invalid package.json: %s",
                        relative_path,
                    )

            # ------------------------------------------------
            # requirements.txt
            # ------------------------------------------------

            elif filename == "requirements.txt":

                for line in content.splitlines():

                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("#"):
                        continue

                    package = re.split(
                        r"(?:==|>=|<=|>|<|~=|!=)",
                        line,
                        maxsplit=1,
                    )[0].strip()

                    if package:
                        dependencies["pip"].append(
                            f"{relative_path}: "
                            f"{package}"
                        )

            # ------------------------------------------------
            # Other manifests
            # ------------------------------------------------

            else:

                dependencies["other"].append(
                    relative_path
                )

        return {
            manager: values
            for manager, values
            in dependencies.items()
            if values
        }

    # ========================================================
    # FILE STRUCTURE
    # ========================================================

    def _build_file_structure(
        self,
        local_path: str,
        max_depth: int = 5,
    ) -> dict:
        """
        Construit la structure réelle du repository.

        backend/, frontend/, front2/ restent visibles.
        node_modules, .git, venv, etc. sont exclus.
        """

        structure = {}

        base_depth = local_path.rstrip(
            os.sep
        ).count(os.sep)

        for root, dirs, files in self._walk_repository(
            local_path
        ):

            depth = (
                root.rstrip(os.sep).count(os.sep)
                - base_depth
            )

            if depth >= max_depth:

                dirs[:] = []

                continue

            relative_path = os.path.relpath(
                root,
                local_path,
            )

            if relative_path == ".":
                relative_path = "."

            structure[
                relative_path.replace(
                    "\\",
                    "/",
                )
            ] = {
                "dirs": sorted(dirs),
                "files": sorted(
                    f
                    for f in files
                    if not f.startswith(".")
                ),
            }

        return structure

    # ========================================================
    # CONFIGURATION EVIDENCE
    # ========================================================

    def _collect_configuration_evidence(
        self,
        local_path: str,
    ) -> list:

        config_names = {
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            ".env.example",
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "mkdocs.yml",
            "vite.config.js",
            "vite.config.ts",
            "tsconfig.json",
        }

        result = []

        config_names_lower = {
            name.lower()
            for name in config_names
        }

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                if (
                    filename.lower()
                    not in config_names_lower
                ):
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                content = self._read_file_safe(
                    full_path
                )

                if not content:
                    continue

                relative_path = os.path.relpath(
                    full_path,
                    local_path,
                ).replace("\\", "/")

                result.append(
                    {
                        "path": relative_path,
                        "content": content[:6000],
                    }
                )

        return result

    # ========================================================
    # MANIFEST DISCOVERY
    # ========================================================

    def _find_manifest_files(
        self,
        local_path: str,
    ):

        manifests = []

        manifest_names = {
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
            "go.mod",
            "Gemfile",
            "pom.xml",
            "Cargo.toml",
            "composer.json",
            "setup.py",
        }

        for root, _, files in self._walk_repository(
            local_path
        ):

            for filename in files:

                if filename not in manifest_names:
                    continue

                full_path = os.path.join(
                    root,
                    filename,
                )

                relative_path = os.path.relpath(
                    full_path,
                    local_path,
                ).replace("\\", "/")

                manifests.append(
                    (
                        filename,
                        full_path,
                        relative_path,
                    )
                )

        return manifests

    # ========================================================
    # FRONTEND API CALLS
    # ========================================================

    def _extract_frontend_api_calls(
        self,
        code_evidence: list,
    ) -> list:

        calls = []

        axios_pattern = re.compile(
            r'axios\.(get|post|put|patch|delete|options)'
            r'\s*\(\s*[`\'"]([^`\'"]+)',
            re.IGNORECASE,
        )

        fetch_pattern = re.compile(
            r'fetch\('
            r'\s*[`\'"]([^`\'"]+)',
            re.IGNORECASE,
        )

        for item in code_evidence:

            path = item["path"]
            content = item["content"]

            if not path.lower().endswith(
                (
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                )
            ):
                continue

            for match in axios_pattern.finditer(
                content
            ):

                calls.append(
                    {
                        "file": path,
                        "method": match.group(
                            1
                        ).upper(),
                        "endpoint": match.group(
                            2
                        ),
                    }
                )

            for match in fetch_pattern.finditer(
                content
            ):

                calls.append(
                    {
                        "file": path,
                        "method": "FETCH",
                        "endpoint": match.group(
                            1
                        ),
                    }
                )

        return calls

    # ========================================================
    # SCRIPTS
    # ========================================================

    def _detect_scripts(
        self,
        local_path: str,
    ):

        install_scripts = []
        run_scripts = []

        for (
            filename,
            path,
            relative_path,
        ) in self._find_manifest_files(
            local_path
        ):

            content = self._read_file_safe(
                path
            )

            if not content:
                continue

            # ------------------------------------------------
            # package.json
            # ------------------------------------------------

            if filename == "package.json":

                try:

                    data = json.loads(
                        content
                    )

                    scripts = data.get(
                        "scripts",
                        {},
                    )

                    prefix = os.path.dirname(
                        relative_path
                    )

                    prefix = (
                        prefix
                        if prefix not in (
                            "",
                            ".",
                        )
                        else ""
                    )

                    npm_prefix = (
                        f"cd {prefix} && "
                        if prefix
                        else ""
                    )

                    install_scripts.append(
                        f"{npm_prefix}npm install"
                    )

                    if "dev" in scripts:

                        run_scripts.append(
                            f"{npm_prefix}npm run dev"
                        )

                    if "start" in scripts:

                        run_scripts.append(
                            f"{npm_prefix}npm start"
                        )

                    if "build" in scripts:

                        run_scripts.append(
                            f"{npm_prefix}npm run build"
                        )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):

                    logger.warning(
                        "Invalid package.json: %s",
                        relative_path,
                    )

            # ------------------------------------------------
            # requirements.txt
            # ------------------------------------------------

            elif filename == "requirements.txt":

                install_scripts.append(
                    f"pip install -r {relative_path}"
                )

        # ----------------------------------------------------
        # Makefile
        # ----------------------------------------------------

        makefile = self._find_file(
            local_path,
            "Makefile",
        )

        if makefile:

            install_scripts.append(
                "make install"
            )

        # ----------------------------------------------------
        # Dockerfile
        # ----------------------------------------------------

        dockerfile = self._find_file(
            local_path,
            "Dockerfile",
        )

        if dockerfile:

            run_scripts.append(
                "docker build . && "
                "docker run <image>"
            )

        return (
            sorted(
                set(install_scripts)
            ),
            sorted(
                set(run_scripts)
            ),
        )

    # ========================================================
    # FIND FILE
    # ========================================================

    def _find_file(
        self,
        local_path: str,
        filename: str,
    ):

        for root, _, files in self._walk_repository(
            local_path
        ):

            if filename in files:

                return os.path.join(
                    root,
                    filename,
                )

        return None

    # ========================================================
    # SAFE READ
    # ========================================================

    def _read_file_safe(
        self,
        path: str,
    ) -> str:

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:

                return file.read()

        except (
            IOError,
            OSError,
        ):

            return ""