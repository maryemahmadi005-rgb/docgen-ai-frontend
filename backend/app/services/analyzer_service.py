"""
Analyzer Service — scan complet d'un repository (Phase 1).,pahse 2 hajnjdnzejdndejfneejfnekfkvnezkjfnerkjrkjrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr 
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import tomllib  # stdlib depuis Python 3.11
except ModuleNotFoundError:  # pragma: no cover - filet pour <3.11
    tomllib = None


logger = logging.getLogger(__name__)


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


FRAMEWORK_SIGNATURES = {
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
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "streamlit": "Streamlit",
    "gin-gonic": "Gin",
    "rails": "Ruby on Rails",
}


IMPORTANT_FILES = {
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


IGNORED_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
    ".cache",
    ".parcel-cache",
    "out",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    ".env",
    "target",
    "vendor",
    "tmp",
    "temp",
    "README.md",
}


IGNORED_FILE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".lock",
}


DEFAULT_MAX_CONTENT_FILES = 20
DEFAULT_MAX_TOTAL_CONTENT_CHARS = 30000
DEFAULT_MAX_CHARS_PER_FILE = 4000

MAX_CONTENT_READ_CHARS_PER_FILE = DEFAULT_MAX_CHARS_PER_FILE
MAX_FILES_WITH_CONTENT_READ = DEFAULT_MAX_CONTENT_FILES
MAX_TOTAL_CONTENT_READ_CHARS = DEFAULT_MAX_TOTAL_CONTENT_CHARS

LOW_VALUE_CONTENT_DIR_MARKERS = (
    "/node_modules/",
    "/.git/",
    "/venv/",
    "/.venv/",
    "/env/",
    "/dist/",
    "/build/",
    "/coverage/",
    "/__pycache__/",
    "/.pytest_cache/",
    "/.mypy_cache/",
    "/.next/",
    "/.nuxt/",
    "/generated_docs/",
    "/doc-output/",
    "/.tox/",
    "/site-packages/",
    "/migrations/",
    "/vendor/",
    "/static/",
    "/assets/",
    "/public/",
)

LOW_VALUE_CONTENT_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "cargo.lock",
    "gemfile.lock",
}

LOW_VALUE_CONTENT_SUFFIXES = (
    ".min.js",
    ".min.css",
    ".map",
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".exe",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mp3",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
)

HIGH_VALUE_CODE_EXTENSIONS = {
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

# Extensions whose content is EVER worth reading. Used by the single
# global candidate-discovery pass (path/metadata only) so that no
# other method needs to walk the filesystem again for content.
CONTENT_CANDIDATE_EXTENSIONS = HIGH_VALUE_CODE_EXTENSIONS | {
    ".json",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".cfg",
    ".ini",
}

# Manifest / config filenames that have no extension or a generic one
# but must still be considered content candidates (Dockerfile, etc).
CONTENT_CANDIDATE_EXTRA_NAMES = {
    "dockerfile",
    "makefile",
    "pipfile",
    "gemfile",
}


@dataclass
class ProjectAnalysis:
    languages: dict = field(default_factory=dict)
    frameworks: list = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)
    file_structure: dict = field(default_factory=dict)
    important_files: list = field(default_factory=list)
    install_scripts: list = field(default_factory=list)
    run_scripts: list = field(default_factory=list)
    entry_points: list = field(default_factory=list)
    code_evidence: list = field(default_factory=list)
    api_endpoints: list = field(default_factory=list)
    frontend_api_calls: list = field(default_factory=list)
    configuration_evidence: list = field(default_factory=list)
    installation_evidence: dict = field(default_factory=dict)
    usage_evidence: dict = field(default_factory=dict)


def _is_test_file(relative_path: str, filename: str) -> bool:
    name_lower = filename.lower()

    if name_lower.startswith("test_") and name_lower.endswith(".py"):
        return True
    if name_lower.endswith("_test.py"):
        return True
    if name_lower.endswith(".test.js") or name_lower.endswith(".test.ts"):
        return True
    if name_lower.endswith(".spec.js") or name_lower.endswith(".spec.ts"):
        return True

    path_lower = relative_path.replace("\\", "/").lower()
    test_dir_markers = ("/test/", "/tests/", "/__tests__/", "/spec/")

    return any(marker in f"/{path_lower}/" for marker in test_dir_markers)


def _is_likely_app_factory_init(relative_path: str, filename: str) -> bool:
    """
    True for an `__init__.py` that sits directly under a directory
    named `app`/`backend`/`server`/`api` — the conventional location
    of a Flask application-factory entry point
    (`def create_app(): ...`, `app = Flask(__name__)`,
    `register_blueprint(...)`). Metadata-only test (path/filename),
    never opens the file.

    Excluding EVERY `__init__.py` by default (see
    `exclude_init_py`) is right for the common case — most
    `__init__.py` files are empty or trivial — but it silently hides
    the one `__init__.py` that IS the entry point in an app-factory
    layout (`backend/app/__init__.py`), which is why Flask/Blueprint
    detection and entry-point detection could miss real evidence
    entirely on that layout. This carve-out lets that one file back
    into the candidate pool without reintroducing every trivial
    `__init__.py` in the repo.
    """

    if filename.lower() != "__init__.py":
        return False

    path_lower = relative_path.replace("\\", "/").lower()
    parent = path_lower.rsplit("/", 2)[-2] if "/" in path_lower else ""

    return parent in {"app", "backend", "server", "api"}


def _is_low_value_content_path(
    relative_path: str,
    filename: str,
    exclude_tests: bool = True,
    exclude_init_py: bool = True,
) -> bool:
    name_lower = filename.lower()

    if (
        exclude_init_py
        and name_lower == "__init__.py"
        and not _is_likely_app_factory_init(relative_path, filename)
    ):
        return True

    if exclude_tests and _is_test_file(relative_path, filename):
        return True

    if name_lower in LOW_VALUE_CONTENT_FILENAMES:
        return True

    if any(name_lower.endswith(suffix) for suffix in LOW_VALUE_CONTENT_SUFFIXES):
        return True

    normalized = "/" + relative_path.replace("\\", "/").lower() + "/"

    return any(marker in normalized for marker in LOW_VALUE_CONTENT_DIR_MARKERS)


def _is_content_candidate_name(filename: str) -> bool:
    """
    Metadata-only test: could this file's content EVER be worth
    reading. Used at discovery time to decide whether a path even
    enters the candidate pool — never opens the file.
    """

    name_lower = filename.lower()
    ext = os.path.splitext(name_lower)[1]

    if ext in CONTENT_CANDIDATE_EXTENSIONS:
        return True

    if name_lower in CONTENT_CANDIDATE_EXTRA_NAMES:
        return True

    if name_lower in {n.lower() for n in IMPORTANT_FILES}:
        return True

    return False


def _content_read_priority(relative_path: str, filename: str) -> int:
    """
    Priority of content read (lower = read first). Computed ONLY
    from path metadata (filename, extension, directory) — never from
    file content, which has not been read at this stage.

    Tier 0: entry points
    Tier 0.5: dependency manifests (package.json, requirements.txt,
              pyproject.toml, etc.) — kept high priority so they are
              always read before the budget is exhausted by generic
              code files.
    Tier 1: backend API routes/controllers/endpoints
    Tier 2: core services
    Tier 3: architecture/config
    Tier 4: README/Docker/other manifests
    Tier 5: frontend API clients
    Tier 6: models/database, frontend representative files
    Tier 7: everything else
    Tier 8: __init__.py
    Tier 9: test files
    """

    path_lower = relative_path.replace("\\", "/").lower()
    name_lower = filename.lower()

    if _is_test_file(relative_path, filename):
        return 9

    if name_lower == "__init__.py":
        # An app-factory __init__.py (backend/app/__init__.py, etc.)
        # is functionally an entry point — it's where Flask()/
        # create_app()/register_blueprint() commonly live — so it
        # must not be starved by generic source files the way a
        # trivial package __init__.py should be.
        if _is_likely_app_factory_init(relative_path, filename):
            return 0
        return 8

    entry_point_names = {
        "app.py", "main.py", "run.py", "server.py",
        "wsgi.py", "asgi.py", "manage.py",
        "app.js", "app.jsx", "app.tsx",
        "main.js", "main.jsx", "main.tsx",
        "index.js", "index.jsx", "index.tsx",
    }

    if name_lower in entry_point_names:
        return 0

    # Dependency manifests get very high priority — they must never
    # lose the shared budget to generic source files.
    core_manifest_names = {
        "package.json", "requirements.txt", "pyproject.toml",
        "pipfile", "go.mod", "gemfile", "setup.py",
        "pom.xml", "cargo.toml", "composer.json",
    }

    if name_lower in core_manifest_names:
        return 0

    # requirements/*.txt : même priorité que requirements.txt (voir
    # _find_manifest_files) — sinon ces fichiers, souvent lus plus tard
    # dans le classement générique, peuvent être privés du budget de
    # lecture partagé par des fichiers de code sans rapport.
    if name_lower.endswith(".txt") and os.path.basename(
        os.path.dirname(path_lower)
    ) == "requirements":
        return 0

    route_markers = (
        "/routes/", "/route/", "/routers/", "/router/",
        "/api/", "/controllers/", "/controller/", "/endpoints/",
    )

    if any(marker in path_lower for marker in route_markers):
        return 1

    service_markers = (
        "/services/", "/service/", "/usecases/", "/use_cases/",
        "/business/", "/logic/", "/domain/",
    )

    if any(marker in path_lower for marker in service_markers):
        return 2

    architecture_config_names = {
        "config.py", "settings.py", "extensions.py",
        "dependencies.py", "container.py", "di.py",
        "__init__.py",
    }

    architecture_config_markers = (
        "/config/", "/settings/", "/di/", "/middleware/",
    )

    if (
        name_lower in architecture_config_names
        or any(marker in path_lower for marker in architecture_config_markers)
    ):
        return 3

    manifest_names = {
        "dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".env.example", "readme.md", "readme",
    }

    if name_lower in manifest_names:
        return 4

    frontend_api_markers = ("/api/", "/apis/", "/clients/", "/client/")
    frontend_api_names_hints = ("axios", "apiclient", "api-client", "http")

    if (
        any(marker in path_lower for marker in frontend_api_markers)
        or any(hint in name_lower for hint in frontend_api_names_hints)
    ):
        return 5

    model_markers = (
        "/models/", "/model/", "/schemas/", "/schema/",
        "/entities/", "/database/", "/db/",
    )

    if any(marker in path_lower for marker in model_markers):
        return 6

    frontend_representative_markers = (
        "/components/", "/pages/", "/views/", "/hooks/",
    )

    if any(marker in path_lower for marker in frontend_representative_markers):
        return 6

    return 7


class _ContentReadBudget:
    """
    Central UNIQUE and SHARED budget for content reading during one
    analyze() run. Every method that needs file content goes through
    this budget (via `_read_file_with_budget` / `_read_file_safe`):
    no method has its own independent budget, and no physical file
    is ever read twice (shared cache).
    """

    def __init__(
        self,
        max_files: int = DEFAULT_MAX_CONTENT_FILES,
        max_total_chars: int = DEFAULT_MAX_TOTAL_CONTENT_CHARS,
    ) -> None:
        self.max_files = max_files
        self.max_total_chars = max_total_chars

        self.files_read = 0
        self.chars_read = 0
        self.cache_hits = 0
        self.files_skipped_budget = 0

        self.cache: dict = {}

    @property
    def total_chars_read(self) -> int:
        return self.chars_read

    @property
    def _cache(self) -> dict:
        return self.cache

    def exhausted(self) -> bool:
        return (
            self.files_read >= self.max_files
            or self.chars_read >= self.max_total_chars
        )

    def record_read(self, path: str, chars: int) -> None:
        self.files_read += 1
        self.chars_read += chars

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_skip(self) -> None:
        self.files_skipped_budget += 1

    def summary_log_lines(self, files_discovered: int) -> list:
        return [
            f"[ANALYZER] FILES DISCOVERED: {files_discovered}",
            f"[ANALYZER] CONTENT READ BUDGET: "
            f"{self.max_files} files / {self.max_total_chars} chars",
            f"[ANALYZER] CONTENT FILES READ: {self.files_read}",
            f"[ANALYZER] CONTENT CHARS READ: {self.chars_read}",
            f"[ANALYZER] CONTENT CACHE HITS: {self.cache_hits}",
            f"[ANALYZER] CONTENT BUDGET EXHAUSTED: "
            f"{'true' if self.exhausted() else 'false'}",
        ]


class AnalyzerService:
    """
    Deterministic repository analyzer.

    CRITICAL INVARIANT (enforced structurally, not just by
    convention): discovery NEVER reads file content. A single
    metadata-only candidate pool is built once per analyze() run
    (`_discover_content_candidates`), ranked by path/filename
    priority, filtered by exclusions, and only then is the shared
    budget spent reading the top-priority files — through
    `_read_file_safe` / `_read_file_with_budget`, which are the ONLY
    methods in this class allowed to call open() on a repository
    file. Every detection pass (entry points, code evidence,
    endpoints, frameworks, dependencies, configuration, scripts)
    consumes files from that same shared, budgeted, cached pool.
    """

    def __init__(
        self,
        max_content_files: int = DEFAULT_MAX_CONTENT_FILES,
        max_total_content_chars: int = DEFAULT_MAX_TOTAL_CONTENT_CHARS,
        max_chars_per_file: int = DEFAULT_MAX_CHARS_PER_FILE,
        exclude_tests: bool = True,
        exclude_init_py: bool = True,
    ) -> None:
        self.max_content_files = max_content_files
        self.max_total_content_chars = max_total_content_chars
        self.max_chars_per_file = max_chars_per_file
        self.exclude_tests = exclude_tests
        self.exclude_init_py = exclude_init_py

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
            raise FileNotFoundError(f"Repository introuvable: {local_path}")

        analysis_start = time.monotonic()

        budget = _ContentReadBudget(
            max_files=self.max_content_files,
            max_total_chars=self.max_total_content_chars,
        )

        total_files_discovered = 0

        for _root, _dirs, files in self._walk_repository(local_path):
            total_files_discovered += len(files)

        # ==========================================================
        # SINGLE METADATA-ONLY DISCOVERY PASS
        #
        # This is the ONLY place that walks the filesystem to build
        # the set of files eligible for content reading. It reads
        # NO content. It ranks purely by path/filename metadata, then
        # every other method below draws from this same ordered,
        # already-filtered candidate list (or its already-read
        # subset via budget.cache) instead of re-walking the repo
        # and re-filtering to decide what to open.
        # ==========================================================

        ranked_candidates = self._discover_content_candidates(local_path)

        try:
            analysis = ProjectAnalysis()

            analysis.languages = self._detect_languages(local_path)

            analysis.important_files = self._find_important_files(local_path)

            # Seed the shared cache with the fixed, very small set of
            # dependency manifests FIRST, unconditionally, before any
            # broader priority-ranked scan runs. Manifests sit at
            # priority tier 0 in `ranked_candidates`, but entry-point
            # detection and code-evidence collection each iterate
            # hundreds of same-or-lower-tier generic source files and
            # can exhaust the shared budget before ever reaching the
            # dependency/config passes that run later in this method.
            # Reading manifests here guarantees they always land in
            # budget.cache, at negligible cost (fixed filename set,
            # not proportional to repo size) — every later pass then
            # serves them from cache instead of re-reading.
            analysis.code_evidence = self._collect_code_evidence(
                ranked_candidates,
                budget=budget,
            )
            analysis.dependencies = self._extract_dependencies(
                local_path,
                budget=budget,
            )

            analysis.configuration_evidence = self._collect_configuration_evidence(
                local_path,
                budget=budget,
            )

            (
                analysis.install_scripts,
                analysis.run_scripts,
            ) = self._detect_scripts(local_path, budget=budget)

            # Entry points: highest priority among the broad,
            # repo-size-proportional scans — runs only after the
            # small fixed manifest/config passes above have already
            # claimed their (small, bounded) share of the budget.
            analysis.entry_points = self._detect_entry_points(
                ranked_candidates,
                budget=budget,
            )

            # Real code evidence — reuses the shared cache: entry
            # points / manifests already read above are not re-read
            # from disk.

            print("\n========== EVIDENCE FLOW DEBUG ==========")
            print("COLLECTED EVIDENCE TYPE:", type(analysis.code_evidence))
            print("COLLECTED EVIDENCE COUNT:", len(analysis.code_evidence or []))

            for item in (analysis.code_evidence  or [])[:5]:
                print(
                    "PATH:", item.get("path"),
                    "| CONTENT:", len(item.get("content", "")),
                    "| SCORE:", item.get("score"),
                    )
                print("==========================================\n")

            # API endpoints — does not depend on the code_evidence
            # cap. All relevant Python files are scanned to find real
            # routes, via the shared budget, so already-seen files
            # aren't re-read.
            analysis.api_endpoints = self._extract_all_api_endpoints(
                ranked_candidates,
                budget=budget,
            )

            python_evidence_cache = [
                {"path": path, "content": content}
                for path, content in budget.cache.items()
                if path.lower().endswith(".py")
            ]

            analysis.frontend_api_calls = self._extract_frontend_api_calls(
                analysis.code_evidence
            )

            analysis.frameworks = self._detect_frameworks(
                local_path,
                ranked_candidates,
                budget=budget,
                python_evidence=python_evidence_cache,
            )

            logger.info(
                "[ANALYZER] FLASK DETECTED: %s — "
                "ENTRY POINTS: %d — API ENDPOINTS: %d — "
                "CODE EVIDENCE: %d",
                "Flask" in analysis.frameworks,
                len(analysis.entry_points),
                len(analysis.api_endpoints),
                len(analysis.code_evidence),
            )

            analysis.file_structure = self._build_file_structure(local_path)

            # ==========================================================
            # INSTALLATION / USAGE EVIDENCE
            #
            # Construites en dernier : elles agrègent uniquement des
            # champs déjà présents sur `analysis` à ce stade
            # (dependencies, install_scripts, run_scripts,
            # entry_points, api_endpoints, frontend_api_calls,
            # configuration_evidence) — aucune lecture disque
            # supplémentaire, réutilisation totale du budget/cache
            # partagé.
            # ==========================================================

            analysis.installation_evidence = self._build_installation_evidence(
                local_path,
                analysis,
                budget=budget,
            )
            analysis.usage_evidence = self._build_usage_evidence(analysis)

            print("[README] INSTALLATION EVIDENCE:", analysis.installation_evidence)
            print("[README] USAGE EVIDENCE:", analysis.usage_evidence)

            logger.info(
                "[README] INSTALLATION EVIDENCE — repo_id=%s — %s",
                repository_id,
                analysis.installation_evidence,
            )
            logger.info(
                "[README] USAGE EVIDENCE — repo_id=%s — %s",
                repository_id,
                analysis.usage_evidence,
            )

            # NOTE: install_scripts/run_scripts were already computed
            # once above (right after dependencies/configuration_evidence).
            # A second call here used to exist and was removed — it
            # was redundant work: _find_manifest_files() would be
            # re-walked and every manifest re-read (served from the
            # shared cache, so no extra physical I/O, but still
            # wasted CPU re-parsing package.json/requirements.txt and
            # rebuilding identical lists) for a result already held in
            # `analysis.install_scripts` / `analysis.run_scripts`.

        except Exception as e:

            print(
                f"❌ [README] ERREUR — étape=ANALYSE — "
                f"repo_id={repository_id} — {e}"
            )

            logger.exception("AnalyzerService failed for %s", local_path)

            raise

        analysis_duration = time.monotonic() - analysis_start

        files_content_read = budget.files_read
        files_skipped_budget = budget.files_skipped_budget
        total_chars_read = budget.total_chars_read
        files_not_read = max(0, total_files_discovered - files_content_read)

        for line in budget.summary_log_lines(total_files_discovered):
            logger.info(line)
            print(line)

        selected_files = sorted(budget.cache.keys())
        selected_relative_files = [
            os.path.relpath(path, local_path).replace("\\", "/")
            for path in selected_files
        ]

        logger.info(
            "[ANALYZER] SELECTED FILES (%d): %s",
            len(selected_relative_files),
            selected_relative_files,
        )

        logger.info(
            "[ANALYZER] repo_id=%s — total_files_discovered=%d — "
            "files_content_read=%d — files_skipped=%d "
            "(not-candidate/low-value=%d, budget-exhausted=%d) — "
            "total_chars_read=%d — analysis_duration=%.3fs",
            repository_id,
            total_files_discovered,
            files_content_read,
            files_not_read,
            max(0, files_not_read - files_skipped_budget),
            files_skipped_budget,
            total_chars_read,
            analysis_duration,
        )

        print(
            f"✅ [README] ANALYSE TERMINÉE — "
            f"repo_id={repository_id} — "
            f"langages={analysis.languages} — "
            f"frameworks={analysis.frameworks} — "
            f"entry_points={len(analysis.entry_points)} — "
            f"code_evidence={len(analysis.code_evidence)} — "
            f"api_endpoints={len(analysis.api_endpoints)} — "
            f"installation_evidence_keys={list(analysis.installation_evidence.keys())} — "
            f"usage_evidence_keys={list(analysis.usage_evidence.keys())} — "
            f"files_discovered={total_files_discovered} — "
            f"files_content_read={files_content_read} — "
            f"total_chars_read={total_chars_read} — "
            f"duration={analysis_duration:.3f}s"
        )

        # Expose the run's diagnostics on the returned object so
        # callers (and tests) can assert on them without re-parsing
        # log output.
        analysis.diagnostics = {
            "files_discovered": total_files_discovered,
            "files_content_read": files_content_read,
            "content_budget": f"{budget.max_files} files / {budget.max_total_chars} chars",
            "content_used": total_chars_read,
            "selected_files": selected_relative_files,
        }

        return analysis

    # ========================================================
    # IGNORE HELPERS
    # ========================================================

    def _is_ignored_dir(self, dirname: str) -> bool:
        return dirname in IGNORED_DIRS

    def _is_ignored_file(self, filename: str) -> bool:
        lower = filename.lower()
        _, ext = os.path.splitext(lower)
        return ext in IGNORED_FILE_EXTENSIONS

    # ========================================================
    # WALK REPOSITORY (structure discovery — no content reads)
    # ========================================================

    def _walk_repository(self, local_path: str):
        for root, dirs, files in os.walk(local_path):

            dirs[:] = sorted(d for d in dirs if not self._is_ignored_dir(d))

            files = [f for f in files if not self._is_ignored_file(f)]

            yield root, dirs, files

    # ========================================================
    # SINGLE METADATA-ONLY CANDIDATE DISCOVERY
    # ========================================================

    def _discover_content_candidates(self, local_path: str) -> list:
        """
        Metadata-only discovery of every file that could plausibly
        have its content read this run. NO file is opened here.

        Returns a list of (full_path, relative_path, filename) tuples
        already:
          - filtered to content-plausible extensions/names
          - filtered by low-value-path exclusions
          - sorted by `_content_read_priority` (path/filename only)

        This is the single source of truth that `_detect_entry_points`,
        `_collect_code_evidence`, and `_extract_all_api_endpoints`
        draw from — none of them re-walk the filesystem to decide
        what to read.
        """

        candidates = []

        for root, _, files in self._walk_repository(local_path):

            for filename in files:

                if not _is_content_candidate_name(filename):
                    continue

                full_path = os.path.join(root, filename)

                relative_path = os.path.relpath(
                    full_path, local_path
                ).replace("\\", "/")

                if _is_low_value_content_path(
                    relative_path,
                    filename,
                    exclude_tests=self.exclude_tests,
                    exclude_init_py=self.exclude_init_py,
                ):
                    continue

                candidates.append((full_path, relative_path, filename))

        candidates.sort(
            key=lambda c: (_content_read_priority(c[1], c[2]), c[1])
        )

        return candidates

    # ========================================================
    # LANGUAGES (structure only — no content reads)
    # ========================================================

    def _detect_languages(self, local_path: str) -> dict:
        counts = {}

        print(f"🚀 [LANGUAGE] START — path={local_path}")

        try:
            for root, _, files in self._walk_repository(local_path):
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()

                    language = LANGUAGE_EXTENSIONS.get(ext)

                    if not language:
                        continue

                    counts[language] = counts.get(language, 0) + 1

        except Exception as exc:
            print(f"❌ [LANGUAGE] ERROR — {type(exc).__name__}: {exc}")
            raise

        result = dict(
            sorted(counts.items(), key=lambda item: item[1], reverse=True)
        )

        print(f"✅ [LANGUAGE] COMPLETE — {result}")

        return result

    # ========================================================
    # IMPORTANT FILES (structure only — no content reads)
    # ========================================================

    def _find_important_files(self, local_path: str) -> list:
        found = set()

        important_names = {name.lower() for name in IMPORTANT_FILES}

        important_code_names = {
            "app.py", "main.py", "run.py", "server.py", "wsgi.py",
            "asgi.py", "manage.py", "models.py", "config.py",
            "settings.py", "__init__.py",
        }

        important_dir_names = {
            "routes", "route", "routers", "router", "api", "services",
            "service", "controllers", "controller", "models",
            "repositories", "repository", "config",
        }

        for root, _, files in self._walk_repository(local_path):

            relative_root = os.path.relpath(root, local_path).replace("\\", "/")

            for filename in files:

                filename_lower = filename.lower()

                if relative_root != ".":
                    relative_path = f"{relative_root}/{filename}"
                else:
                    relative_path = filename

                relative_path = relative_path.replace("\\", "/")

                path_parts = {part.lower() for part in relative_path.split("/")}

                is_manifest = filename_lower in important_names
                is_important_code = filename_lower in important_code_names
                is_important_directory = bool(
                    path_parts.intersection(important_dir_names)
                )
                is_code_file = filename_lower.endswith(
                    (".py", ".js", ".jsx", ".ts", ".tsx")
                )

                if (
                    is_manifest
                    or is_important_code
                    or (is_important_directory and is_code_file)
                ):
                    found.add(relative_path)

        return sorted(found)

    # ========================================================
    # ENTRY POINTS
    # ========================================================

    def _detect_entry_points(
        self,
        ranked_candidates: list,
        budget: "_ContentReadBudget",
    ) -> list:
        """
        Draws from the shared `ranked_candidates` pool (already
        metadata-filtered and priority-sorted) — no filesystem walk
        here, no content read outside `_read_file_safe`.
        """

        found = set()

        candidate_names = {
            "app.py", "main.py", "run.py", "server.py", "index.py",
            "manage.py", "wsgi.py", "asgi.py",
            "App.jsx", "App.js", "main.jsx", "main.js",
            "index.jsx", "index.js", "App.tsx", "main.tsx", "index.tsx",
        }

        entry_point_extensions = {".py", ".js", ".jsx", ".ts", ".tsx"}

        for full_path, relative_path, filename in ranked_candidates:

            extension = os.path.splitext(filename)[1].lower()

            if extension not in entry_point_extensions:
                continue

            content = self._read_file_safe(full_path, budget=budget)

            if not content:
                continue

            content_lower = content.lower()

            flask_signals = (
                "from flask import", "import flask", "flask(",
                "create_app(", "blueprint(", "register_blueprint(",
                "@app.route", "@bp.route",
            )

            is_flask = extension == ".py" and any(
                signal in content_lower for signal in flask_signals
            )

            if is_flask:
                found.add(relative_path)
                continue

            python_entry = extension == ".py" and (
                filename in candidate_names
                or 'if __name__ == "__main__"' in content
            )

            if python_entry:
                found.add(relative_path)
                continue

            frontend_entry = extension in {".js", ".jsx", ".ts", ".tsx"} and (
                filename in candidate_names
                or "createRoot(" in content
                or "ReactDOM.createRoot" in content
                or "ReactDOM.render" in content
            )

            if frontend_entry:
                found.add(relative_path)

        return sorted(found)

    # ========================================================
    # CODE EVIDENCE
    # ========================================================

    def _collect_code_evidence(
        self,
        ranked_candidates: list,
        max_files: int = 35,
        max_chars_per_file: Optional[int] = None,
        budget: Optional["_ContentReadBudget"] = None,
    ) -> list:
        """
        Draws from the shared `ranked_candidates` pool. Reads content
        only for candidates with a high-value code extension.
        """

        if max_chars_per_file is None:
            max_chars_per_file = self.max_chars_per_file

        candidates = []

        for full_path, relative_path, filename in ranked_candidates:

            extension = os.path.splitext(filename)[1].lower()

            if extension not in HIGH_VALUE_CODE_EXTENSIONS:
                continue

            content = self._read_file_safe(
                full_path,
                budget=budget,
                max_chars=max_chars_per_file,
            )

            if not content:
                continue

            file_info = {
                "path": relative_path,
                "full_path": full_path,
                "size": len(content),
            }

            score = self._advanced_score_file(file_info, content)

            if score <= -900000:
                continue

            candidates.append(
                {
                    "path": relative_path,
                    "full_path": full_path,
                    "score": score,
                    "content": content[:max_chars_per_file],
                }
            )

        backend_candidates = []
        frontend_candidates = []
        other_candidates = []

        for item in candidates:

            normalized = item["path"].lower()
            content_lower = item["content"].lower()

            is_backend = (
                normalized.startswith("backend/")
                or "/backend/" in normalized
                or (
                    normalized.endswith(".py")
                    and any(
                        signal in content_lower
                        for signal in (
                            "from flask import", "import flask",
                            "@app.route", "@bp.route", "blueprint(",
                            "register_blueprint(", "fastapi(",
                            "from fastapi import",
                        )
                    )
                )
            )

            is_frontend = (
                normalized.startswith("frontend/")
                or normalized.startswith("front2/")
                or "/frontend/" in normalized
                or "/front2/" in normalized
                or normalized.endswith((".jsx", ".tsx"))
            )

            if is_backend:
                backend_candidates.append(item)
            elif is_frontend:
                frontend_candidates.append(item)
            else:
                other_candidates.append(item)

        backend_candidates.sort(key=lambda item: item["score"], reverse=True)
        frontend_candidates.sort(key=lambda item: item["score"], reverse=True)
        other_candidates.sort(key=lambda item: item["score"], reverse=True)

        selected = []
        selected_paths = set()

        def add_item(item):
            path = item["path"]
            if path in selected_paths:
                return
            selected.append(item)
            selected_paths.add(path)

        for item in backend_candidates:

            path_lower = item["path"].lower()
            filename = os.path.basename(path_lower)
            content_lower = item["content"].lower()

            is_route_file = any(
                marker in path_lower
                for marker in ("/routes/", "/route/", "/routers/", "/router/", "/api/")
            )

            is_service_file = any(
                marker in path_lower for marker in ("/services/", "/service/")
            )

            is_backend_entry = filename in {
                "run.py", "app.py", "main.py", "server.py",
                "wsgi.py", "asgi.py", "__init__.py",
            }

            has_flask_signal = any(
                marker in content_lower
                for marker in (
                    "from flask import", "import flask", "@app.route",
                    "@bp.route", "blueprint(", "register_blueprint(",
                )
            )

            if is_route_file or is_service_file or is_backend_entry or has_flask_signal:
                add_item(item)

        for item in backend_candidates:
            add_item(item)

        for item in frontend_candidates:
            add_item(item)

        for item in other_candidates:
            add_item(item)

        selected = selected[:max_files]

        print("\n========== README CODE EVIDENCE ==========")

        for item in selected:
            print(f"{item['path']} score={item['score']} chars={len(item['content'])}")

        print("==========================================\n")

        return selected

    # ========================================================
    # STRUCTURAL FILE SCORE
    # ========================================================

    def _score_file(self, file_info):

        path_lower = file_info["path"].replace("\\", "/").lower()
        filename = os.path.basename(path_lower)

        score = 0

        entry_points = {
            "app.py", "main.py", "server.py", "index.py", "index.js",
            "index.ts", "manage.py", "wsgi.py", "asgi.py", "run.py",
            "flasky.py",
        }

        if filename in entry_points:
            score += 9000

        if filename == "__init__.py" and any(
            x in path_lower for x in ("app/", "src/", "backend/", "server/")
        ):
            score += 7000

        business_paths = [
            "app/", "src/", "backend/", "server/", "core/", "services/",
            "service/", "controllers/", "controller/", "routes/",
            "routers/", "models/", "repositories/", "entities/",
            "domain/", "modules/", "api/",
        ]

        if any(p in path_lower for p in business_paths):
            score += 5000

        code_extensions = (
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".php",
            ".rb", ".rs", ".cpp", ".c", ".cs", ".swift", ".kt",
        )

        if path_lower.endswith(code_extensions):
            score += 1500

        dependency_files = {
            "requirements.txt", "package.json", "pyproject.toml",
            "setup.py", "pom.xml", "cargo.toml", "gemfile", "go.mod",
            "composer.json",
        }

        if filename in dependency_files:
            score += 2000

        deploy_configs = {
            "dockerfile", "docker-compose.yml", "docker-compose.yaml",
            "vite.config.js", "vite.config.ts", "tsconfig.json",
        }

        if filename in deploy_configs:
            score += 500

        if filename.startswith("readme"):
            score -= 12000

        if filename.endswith((".md", ".txt")):
            score -= 8000

        low_dirs = [
            "docs/", "documentation/", "static/", "assets/", "images/",
            "public/", "coverage/", "examples/", "example/", "samples/",
            "sample/", "tests/", "test/",
        ]

        if any(x in path_lower for x in low_dirs):
            score -= 15000

        if filename in {"boot.sh", "start.sh", "run.sh", "build.sh"}:
            score -= 40000

        size = file_info.get("size", 0)

        if 1000 < size < 200000:
            score += 500

        return score

    # ========================================================
    # ADVANCED FILE SCORE
    # ========================================================

    def _advanced_score_file(self, file_info, content):

        path = file_info["path"].replace("\\", "/").lower()
        filename = os.path.basename(path)
        content_lower = content.lower()

        score = self._score_file(file_info)

        excluded_dirs = [
            "node_modules/", "vendor/", "__pycache__/", "dist/", "build/",
            "coverage/", ".next/", ".nuxt/", "migrations/", "templates/",
            "static/", "assets/", "public/",
        ]

        if any(x in path for x in excluded_dirs):
            return -999999

        if any(x in path for x in ("test/", "tests/", "__tests__/", "spec/")):
            score -= 30000

        if any(
            x in path
            for x in (
                "services/", "controllers/", "routes/", "routers/",
                "models/", "repositories/", "core/", "api/", "auth/",
            )
        ):
            score += 50000

        if filename == "models.py":
            score += 60000

        if path.startswith("backend/") and filename.endswith(".py"):
            score += 12000

        if "/backend/" in path and filename.endswith(".py"):
            score += 12000

        if filename in {
            "app.py", "main.py", "server.py", "index.py", "index.js",
            "index.ts", "manage.py", "wsgi.py", "asgi.py", "run.py",
        }:
            score += 9000

        signals = {
            "flask": 500, "fastapi": 500, "django": 500, "express": 500,
            "router": 400, "@app.route": 600, "@bp.route": 600,
            ".route(": 500, "blueprint": 500, "register_blueprint": 700,
            "controller": 300, "service": 300, "repository": 300,
            "class ": 150, "def ": 100, "async def": 150,
            "sqlalchemy": 400, "mongoose": 400, "sequelize": 300,
            "axios": 400, "fetch(": 400, "usestate": 150,
            "useeffect": 150, "react": 300,
        }

        for signal, bonus in signals.items():
            if signal in content_lower:
                score += bonus

        if filename.startswith("readme"):
            score -= 5000

        if path.startswith("docs/"):
            score -= 20000

        if filename.endswith((".html", ".css")):
            score -= 15000

        config_files = {
            "docker-compose.yml", "docker-compose.yaml", "dockerfile",
            "vite.config.js", "vite.config.ts", "tsconfig.json",
            "mkdocs.yml", "package.json", "requirements.txt",
            "pyproject.toml",
        }

        if filename in config_files:
            if filename in {"requirements.txt", "package.json", "pyproject.toml"}:
                score += 10000
            else:
                score = min(score, 4000)

        if any(x in filename for x in ("fake", "mock", "dummy", "sample")):
            return -999999

        if filename.endswith((".sh", ".bat", ".cmd")):
            score -= 50000

        priority_files = {
            "app/__init__.py": 50000,
            "app/models.py": 45000,
            "config.py": 30000,
            "flasky.py": 30000,
        }

        normalized_path = path.replace("\\", "/").lower()

        for priority_path, bonus in priority_files.items():
            if normalized_path.endswith(priority_path):
                score += bonus
                break

        if path.startswith("app/auth/") and filename.endswith(".py"):
            score += 40000

        if normalized_path.endswith("app/__init__.py"):
            score += 100000

        print("FINAL SCORE:", file_info["path"], score)

        return score

    # ========================================================
    # API ENDPOINTS
    # ========================================================

    def _extract_api_endpoints(self, code_evidence: list) -> list:

        endpoints = []

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

        method_pattern = re.compile(
            r"""
            @
            (?P<object>[A-Za-z_]\w*)
            \.
            (?P<method>get|post|put|patch|delete|options)
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

        string_pattern = re.compile(r"""['"]([A-Za-z]+)['"]""")

        seen = set()

        for item in code_evidence:

            path = item["path"]
            content = item["content"]

            if not path.lower().endswith(".py"):
                continue

            for match in route_pattern.finditer(content):

                endpoint = match.group("path")
                args = match.group("args")

                methods_match = methods_pattern.search(args)

                if methods_match:
                    methods = [
                        method.upper()
                        for method in string_pattern.findall(methods_match.group("methods"))
                        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
                    ]
                    if not methods:
                        methods = ["GET"]
                else:
                    methods = ["GET"]

                key = (path, endpoint, tuple(methods))

                if key in seen:
                    continue

                seen.add(key)

                endpoints.append(
                    {
                        "file": path,
                        "endpoint": endpoint,
                        "methods": methods,
                        "_decorator_object": match.group("object"),
                    }
                )

            for match in method_pattern.finditer(content):

                method = match.group("method").upper()
                endpoint = match.group("path")

                if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}:
                    continue

                key = (path, endpoint, (method,))

                if key in seen:
                    continue

                seen.add(key)

                endpoints.append(
                    {
                        "file": path,
                        "endpoint": endpoint,
                        "methods": [method],
                        "_decorator_object": match.group("object"),
                    }
                )

        return endpoints

    # ========================================================
    # EXTRACT ALL API ENDPOINTS
    # ========================================================

    def _extract_all_api_endpoints(
        self,
        ranked_candidates: list,
        budget: "_ContentReadBudget",
    ) -> list:
        """
        Draws from the shared `ranked_candidates` pool, restricted to
        .py files. Content already read by other passes is served
        from the shared cache.
        """

        all_python_evidence = []

        for full_path, relative_path, filename in ranked_candidates:

            if not filename.lower().endswith(".py"):
                continue

            content = self._read_file_safe(full_path, budget=budget)

            if not content:
                continue

            all_python_evidence.append(
                {
                    "path": relative_path,
                    "full_path": full_path,
                    "content": content,
                    "score": 0,
                }
            )

        endpoints = self._extract_api_endpoints(all_python_evidence)

        return self._resolve_blueprint_prefixes(all_python_evidence, endpoints)

    # ========================================================
    # BLUEPRINT PREFIX RESOLUTION
    # ========================================================

    def _resolve_blueprint_prefixes(self, python_files: list, endpoints: list) -> list:

        blueprint_prefixes = {}

        # Case 1: prefix declared inline on the Blueprint() constructor.
        #     api_bp = Blueprint("api", __name__, url_prefix="/api")
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

        # Case 2: prefix declared where the blueprint is registered,
        # which is at least as common as case 1 in app-factory layouts:
        #     app.register_blueprint(users_bp, url_prefix="/api")
        register_blueprint_pattern = re.compile(
            r"""
            register_blueprint
            \s*\(
            \s*
            (?P<name>[A-Za-z_]\w*)
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

        def _record_prefix(name: str, prefix: str) -> None:
            if not prefix.startswith("/"):
                prefix = "/" + prefix
            if prefix != "/":
                prefix = prefix.rstrip("/")
            blueprint_prefixes[name] = prefix

        for item in python_files:

            content = item["content"]

            for match in blueprint_pattern.finditer(content):
                _record_prefix(match.group("name"), match.group("prefix"))

            for match in register_blueprint_pattern.finditer(content):
                # Don't let a register_blueprint() call without an
                # explicit prefix override one already found via
                # Blueprint(...) — only record when a prefix is
                # actually present in this call (guaranteed by the
                # pattern itself matching url_prefix=...).
                _record_prefix(match.group("name"), match.group("prefix"))

        result = []

        for endpoint in endpoints:

            file_path = endpoint["file"]
            endpoint_path = endpoint["endpoint"]

            decorator_object = endpoint.get("_decorator_object")

            prefix = (
                blueprint_prefixes.get(decorator_object)
                if decorator_object
                else None
            )

            if not endpoint_path.startswith("/"):
                endpoint_path = "/" + endpoint_path

            if prefix:
                if prefix == "/":
                    resolved_path = endpoint_path
                else:
                    resolved_path = prefix.rstrip("/") + "/" + endpoint_path.lstrip("/")
                    if resolved_path != "/":
                        resolved_path = resolved_path.rstrip("/")
            else:
                resolved_path = endpoint_path

            clean_endpoint = {
                "file": file_path,
                "endpoint": resolved_path,
                "methods": endpoint["methods"],
            }

            result.append(clean_endpoint)

        unique = []
        seen = set()

        for item in result:

            key = (item["file"], item["endpoint"], tuple(item["methods"]))

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
        ranked_candidates: list,
        budget: "_ContentReadBudget",
        python_evidence: Optional[list] = None,
    ) -> bool:
        """
        If `python_evidence` is provided (already built by
        `_extract_all_api_endpoints`), reuse it directly — no extra
        disk reads. Otherwise fall back to a bounded scan over the
        shared `ranked_candidates` pool (with cache).
        """

        flask_signals = (
            r"\bfrom\s+flask\s+import\b",
            r"\bimport\s+flask\b",
            r"\bFlask\s*\(",
            r"\bBlueprint\s*\(",
            r"@[\w_]+\.(?:route|get|post|put|patch|delete|options)\s*\(",
            r"\bregister_blueprint\s*\(",
        )

        patterns = [re.compile(pattern, re.IGNORECASE) for pattern in flask_signals]

        if python_evidence is not None:
            return any(
                pattern.search(item["content"])
                for item in python_evidence
                for pattern in patterns
            )

        for full_path, _relative_path, filename in ranked_candidates:

            if not filename.lower().endswith(".py"):
                continue

            content = self._read_file_safe(full_path, budget=budget)

            if not content:
                continue

            if any(pattern.search(content) for pattern in patterns):
                return True

        return False

    # ========================================================
    # FRAMEWORK DETECTION
    # ========================================================

    def _detect_frameworks(
        self,
        local_path: str,
        ranked_candidates: list,
        budget: "_ContentReadBudget",
        python_evidence: Optional[list] = None,
    ) -> list:

        frameworks = set()

        manifests = self._find_manifest_files(local_path)

        for filename, path, _ in manifests:

            content = self._read_file_safe(path, budget=budget)

            if not content:
                continue

            content_lower = content.lower()

            for signature, framework_name in FRAMEWORK_SIGNATURES.items():
                if signature.lower() in content_lower:
                    frameworks.add(framework_name)

        if self._detect_flask_backend(
            ranked_candidates,
            budget=budget,
            python_evidence=python_evidence,
        ):
            frameworks.add("Flask")

        # React detection: draws from the shared ranked_candidates
        # pool, restricted to JS/TS extensions, stops as soon as a
        # React signal is found.
        for full_path, _relative_path, filename in ranked_candidates:

            extension = os.path.splitext(filename)[1].lower()

            if extension not in {".js", ".jsx", ".ts", ".tsx"}:
                continue

            content = self._read_file_safe(full_path, budget=budget)

            if not content:
                continue

            content_lower = content.lower()

            if (
                "from 'react'" in content_lower
                or 'from "react"' in content_lower
                or "from 'react-dom'" in content_lower
                or 'from "react-dom"' in content_lower
                or "createroot(" in content_lower
            ):
                frameworks.add("React")
                break

        return sorted(frameworks)

    # ========================================================
    # DEPENDENCIES
    # ========================================================

    # Options pip qui ne représentent jamais une dépendance installable
    # (-r other.txt, --index-url ..., -e ., --hash=..., -c constraints.txt).
    _PIP_REQUIREMENT_URL_PREFIXES = ("git+", "http://", "https://", "./", "../", "/")

    def _parse_pip_requirement_line(self, line: str) -> Optional[str]:
        """
        Extrait le nom du package d'UNE ligne au format requirements.txt.

        Réutilisé pour requirements.txt / requirements/*.txt ET pour les
        entrées de `project.dependencies` d'un pyproject.toml (PEP 621),
        qui partagent exactement la même syntaxe ("package==1.2.3").

        Retourne None (ligne ignorée) pour : lignes vides, commentaires,
        options pip (-r, --index-url, -e, ...), dépendances par URL/chemin
        direct (pas de nom de package fiable à en extraire) — jamais une
        dépendance inventée.
        """
        line = line.strip()

        if not line or line.startswith("#"):
            return None

        # Options pip : -r requirements-dev.txt / --index-url ... / -e . ...
        if line.startswith("-"):
            return None

        # Commentaire de fin de ligne ("flask  # framework web").
        line = line.split("#", 1)[0].strip()
        if not line:
            return None

        if line.startswith(self._PIP_REQUIREMENT_URL_PREFIXES):
            return None

        # Marqueur d'environnement ("package>=1.0; python_version < '3.9'").
        line = line.split(";", 1)[0].strip()
        if not line:
            return None

        # Coupe à la première contrainte de version (==, >=, <=, ~=, !=, >, <).
        package = re.split(r"(?:==|>=|<=|~=|!=|>|<)", line, maxsplit=1)[0].strip()

        # Retire les extras : "requests[security]" -> "requests".
        package = re.sub(r"\[.*?\]", "", package).strip()

        return package or None

    def _extract_dependencies(
        self,
        local_path: str,
        budget: Optional["_ContentReadBudget"] = None,
    ) -> dict:

        dependencies = {"npm": [], "pip": [], "other": []}

        manifests = self._find_manifest_files(local_path)

        for filename, path, relative_path in manifests:
            print(f"[DEPENDENCIES] FILE FOUND: {relative_path}")

        for filename, path, relative_path in manifests:

            content = self._read_file_safe(
                path,
                budget=budget,
                max_chars=max(self.max_chars_per_file, 20000),
            )

            if not content:
                logger.warning(
                    "[DEPENDENCIES] Contenu vide/illisible pour %s "
                    "(budget épuisé ou fichier vide) — ignoré.",
                    relative_path,
                )
                continue

            parsed_for_file: list[str] = []

            if filename == "package.json":

                try:
                    data = json.loads(content)

                    npm_dependencies = set()
                    npm_dependencies.update(data.get("dependencies", {}).keys())
                    npm_dependencies.update(data.get("devDependencies", {}).keys())

                    for dependency in sorted(npm_dependencies):
                        dependencies["npm"].append(f"{relative_path}: {dependency}")
                        parsed_for_file.append(dependency)

                except (json.JSONDecodeError, TypeError):
                    logger.warning("Invalid package.json: %s", relative_path)

            elif filename == "requirements.txt":

                for line in content.splitlines():
                    package = self._parse_pip_requirement_line(line)
                    if package:
                        dependencies["pip"].append(f"{relative_path}: {package}")
                        parsed_for_file.append(package)

            elif filename == "pyproject.toml":

                if tomllib is None:
                    logger.warning(
                        "tomllib indisponible (Python < 3.11) — "
                        "pyproject.toml ignoré: %s", relative_path,
                    )
                else:
                    try:
                        data = tomllib.loads(content)
                    except Exception:
                        logger.warning("Invalid pyproject.toml: %s", relative_path)
                        data = None

                    if isinstance(data, dict):
                        # PEP 621 : [project] dependencies = ["flask>=2.0", ...]
                        pep621_deps = (
                            data.get("project", {}).get("dependencies", [])
                        )
                        if isinstance(pep621_deps, list):
                            for raw in pep621_deps:
                                if not isinstance(raw, str):
                                    continue
                                package = self._parse_pip_requirement_line(raw)
                                if package:
                                    dependencies["pip"].append(f"{relative_path}: {package}")
                                    parsed_for_file.append(package)

                        # Poetry : [tool.poetry.dependencies]
                        poetry_deps = (
                            data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                        )
                        if isinstance(poetry_deps, dict):
                            for name in poetry_deps:
                                if not isinstance(name, str) or name.lower() == "python":
                                    continue
                                dependencies["pip"].append(f"{relative_path}: {name}")
                                parsed_for_file.append(name)

            else:
                dependencies["other"].append(relative_path)

            print(f"[DEPENDENCIES] PARSED: {relative_path} -> {parsed_for_file}")

        result = {
            manager: values for manager, values in dependencies.items() if values
        }

        print(f"[DEPENDENCIES] FINAL: {result}")

        return result

    # ========================================================
    # PREREQUISITES (certain-only — parsed from already-read manifests)
    # ========================================================

    def _detect_prerequisites(
        self,
        local_path: str,
        budget: Optional["_ContentReadBudget"] = None,
    ) -> list:
        """
        Prérequis détectables AVEC CERTITUDE uniquement (version
        Python/Node explicitement déclarée dans un manifeste, ou
        simple présence d'un langage détecté). Ne fait aucune
        supposition — pas de version par défaut inventée.

        Réutilise `_find_manifest_files` (déjà appelé plus haut dans
        `analyze()`) et le cache partagé du `budget` : les manifestes
        ont déjà été lus par `_extract_dependencies`/`_detect_scripts`,
        donc aucune nouvelle lecture disque n'est déclenchée ici.
        """

        prerequisites = []

        for filename, path, relative_path in self._find_manifest_files(local_path):

            content = self._read_file_safe(
                path,
                budget=budget,
                max_chars=max(self.max_chars_per_file, 20000),
            )

            if not content:
                continue

            if filename == "pyproject.toml" and tomllib is not None:
                try:
                    data = tomllib.loads(content)
                except Exception:
                    data = None

                if isinstance(data, dict):
                    requires_python = (
                        data.get("project", {}).get("requires-python")
                    )
                    if isinstance(requires_python, str) and requires_python.strip():
                        prerequisites.append(
                            f"Python {requires_python.strip()} "
                            f"(déclaré dans {relative_path})"
                        )

            elif filename == "package.json":
                try:
                    data = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    data = None

                if isinstance(data, dict):
                    engines = data.get("engines")
                    if isinstance(engines, dict):
                        for engine_name, engine_version in engines.items():
                            if isinstance(engine_version, str) and engine_version.strip():
                                prerequisites.append(
                                    f"{engine_name} {engine_version.strip()} "
                                    f"(déclaré dans {relative_path})"
                                )

        return sorted(set(prerequisites))

    # ========================================================
    # INSTALLATION / USAGE EVIDENCE
    #
    # Agrège UNIQUEMENT des preuves déjà collectées ailleurs dans
    # `analyze()` (dependencies, configuration_evidence,
    # install_scripts, run_scripts, entry_points, api_endpoints,
    # frontend_api_calls, important_files). Aucune lecture disque
    # supplémentaire n'est faite ici — tout provient de champs déjà
    # présents sur `analysis` ou du cache partagé `budget`. Rien
    # n'est inventé : un champ reste vide/absent si aucune preuve
    # réelle n'a été trouvée.
    # ========================================================

    def _build_installation_evidence(
        self,
        local_path: str,
        analysis: "ProjectAnalysis",
        budget: Optional["_ContentReadBudget"] = None,
    ) -> dict:

        evidence: dict = {}

        if analysis.dependencies:
            evidence["dependencies"] = analysis.dependencies

        manifest_paths = sorted(
            {
                relative_path
                for _filename, _path, relative_path in self._find_manifest_files(local_path)
            }
        )
        if manifest_paths:
            evidence["manifests"] = manifest_paths

        if analysis.install_scripts:
            evidence["install_scripts"] = list(analysis.install_scripts)

        if analysis.run_scripts:
            evidence["run_scripts"] = list(analysis.run_scripts)

        dockerfile_path = self._find_file(local_path, "Dockerfile")
        docker_compose_path = (
            self._find_file(local_path, "docker-compose.yml")
            or self._find_file(local_path, "docker-compose.yaml")
        )

        docker_evidence = []
        if dockerfile_path:
            docker_evidence.append(
                os.path.relpath(dockerfile_path, local_path).replace("\\", "/")
            )
        if docker_compose_path:
            docker_evidence.append(
                os.path.relpath(docker_compose_path, local_path).replace("\\", "/")
            )
        if docker_evidence:
            evidence["docker"] = sorted(set(docker_evidence))

        env_example_path = self._find_file(local_path, ".env.example")
        if env_example_path:
            relative_env_path = os.path.relpath(
                env_example_path, local_path
            ).replace("\\", "/")

            env_content = self._read_file_safe(
                env_example_path, budget=budget, max_chars=4000
            )

            env_keys = []
            if env_content:
                for line in env_content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key = line.split("=", 1)[0].strip()
                    if key:
                        env_keys.append(key)

            evidence["env_example"] = {
                "path": relative_env_path,
                "variables": sorted(set(env_keys)),
            }

        if analysis.configuration_evidence:
            evidence["configuration_files"] = [
                item.get("path")
                for item in analysis.configuration_evidence
                if isinstance(item, dict) and item.get("path")
            ]

        prerequisites = self._detect_prerequisites(local_path, budget=budget)
        if prerequisites:
            evidence["prerequisites"] = prerequisites

        return evidence

    def _build_usage_evidence(
        self,
        analysis: "ProjectAnalysis",
    ) -> dict:

        evidence: dict = {}

        if analysis.entry_points:
            evidence["entry_points"] = list(analysis.entry_points)

        if analysis.api_endpoints:
            evidence["api_endpoints"] = list(analysis.api_endpoints)

        if analysis.frontend_api_calls:
            evidence["frontend_api_calls"] = list(analysis.frontend_api_calls)

        if analysis.run_scripts:
            evidence["run_scripts"] = list(analysis.run_scripts)

        if analysis.configuration_evidence:
            evidence["configuration_required"] = [
                item.get("path")
                for item in analysis.configuration_evidence
                if isinstance(item, dict) and item.get("path")
            ]

        return evidence

    # ========================================================
    # FILE STRUCTURE (no content reads)
    # ========================================================

    def _build_file_structure(self, local_path: str, max_depth: int = 5) -> dict:

        structure = {}

        base_depth = local_path.rstrip(os.sep).count(os.sep)

        for root, dirs, files in self._walk_repository(local_path):

            depth = root.rstrip(os.sep).count(os.sep) - base_depth

            if depth >= max_depth:
                dirs[:] = []
                continue

            relative_path = os.path.relpath(root, local_path)

            if relative_path == ".":
                relative_path = "."

            structure[relative_path.replace("\\", "/")] = {
                "dirs": sorted(dirs),
                "files": sorted(f for f in files if not f.startswith(".")),
            }

        return structure

    # ========================================================
    # CONFIGURATION EVIDENCE
    # ========================================================

    def _collect_configuration_evidence(
        self,
        local_path: str,
        budget: Optional["_ContentReadBudget"] = None,
    ) -> list:

        config_names = {
            "package.json", "requirements.txt", "pyproject.toml",
            ".env.example", "dockerfile", "docker-compose.yml",
            "docker-compose.yaml", "mkdocs.yml", "vite.config.js",
            "vite.config.ts", "tsconfig.json",
        }

        result = []

        config_names_lower = {name.lower() for name in config_names}

        for root, _, files in self._walk_repository(local_path):

            for filename in files:

                if filename.lower() not in config_names_lower:
                    continue

                full_path = os.path.join(root, filename)

                content = self._read_file_safe(full_path, budget=budget, max_chars=6000)

                if not content:
                    continue

                relative_path = os.path.relpath(full_path, local_path).replace("\\", "/")

                result.append({"path": relative_path, "content": content})

        return result

    # ========================================================
    # MANIFEST DISCOVERY (no content reads)
    # ========================================================

    def _find_manifest_files(self, local_path: str):

        manifests = []

        manifest_names = {
            "package.json", "requirements.txt", "pyproject.toml",
            "Pipfile", "go.mod", "Gemfile", "pom.xml", "Cargo.toml",
            "composer.json", "setup.py",
        }

        for root, _, files in self._walk_repository(local_path):

            for filename in files:

                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, local_path).replace("\\", "/")

                if filename in manifest_names:
                    manifests.append((filename, full_path, relative_path))
                    continue

                # requirements/*.txt (ex: requirements/common.txt,
                # requirements/dev.txt) : beaucoup de projets Python
                # (dont flasky) éclatent leurs dépendances dans un
                # dossier requirements/ au lieu d'un unique
                # requirements.txt à la racine. C'est la même famille
                # de fichier, simplement répartie sur plusieurs fichiers
                # — normalisé ici sous le même label "requirements.txt"
                # pour que tous les consommateurs existants de cette
                # méthode (extraction des dépendances, des scripts
                # d'installation, détection de frameworks) les
                # traitent automatiquement, sans changement ailleurs.
                if (
                    filename.endswith(".txt")
                    and os.path.basename(root).lower() == "requirements"
                ):
                    manifests.append(("requirements.txt", full_path, relative_path))

        return manifests

    # ========================================================
    # FRONTEND API CALLS (no reads — derived from code_evidence)
    # ========================================================

    def _extract_frontend_api_calls(self, code_evidence: list) -> list:

        calls = []

        axios_pattern = re.compile(
            r'axios\.(get|post|put|patch|delete|options)'
            r'\s*\(\s*[`\'"]([^`\'"]+)',
            re.IGNORECASE,
        )

        fetch_pattern = re.compile(
            r'fetch\(' r'\s*[`\'"]([^`\'"]+)',
            re.IGNORECASE,
        )

        for item in code_evidence:

            path = item["path"]
            content = item["content"]

            if not path.lower().endswith((".js", ".jsx", ".ts", ".tsx")):
                continue

            for match in axios_pattern.finditer(content):
                calls.append(
                    {
                        "file": path,
                        "method": match.group(1).upper(),
                        "endpoint": match.group(2),
                    }
                )

            for match in fetch_pattern.finditer(content):
                calls.append(
                    {
                        "file": path,
                        "method": "FETCH",
                        "endpoint": match.group(1),
                    }
                )

        return calls

    # ========================================================
    # SCRIPTS
    # ========================================================

    def _detect_scripts(
        self,
        local_path: str,
        budget: Optional["_ContentReadBudget"] = None,
    ):

        install_scripts = []
        run_scripts = []

        for filename, path, relative_path in self._find_manifest_files(local_path):

            content = self._read_file_safe(
                path,
                budget=budget,
                max_chars=max(self.max_chars_per_file, 20000),
            )

            if not content:
                continue

            if filename == "package.json":

                try:
                    data = json.loads(content)
                    scripts = data.get("scripts", {})

                    prefix = os.path.dirname(relative_path)
                    prefix = prefix if prefix not in ("", ".") else ""

                    npm_prefix = f"cd {prefix} && " if prefix else ""

                    install_scripts.append(f"{npm_prefix}npm install")

                    if "dev" in scripts:
                        run_scripts.append(f"{npm_prefix}npm run dev")
                    if "start" in scripts:
                        run_scripts.append(f"{npm_prefix}npm start")
                    if "build" in scripts:
                        run_scripts.append(f"{npm_prefix}npm run build")

                except (json.JSONDecodeError, TypeError):
                    logger.warning("Invalid package.json: %s", relative_path)

            elif filename == "requirements.txt":
                install_scripts.append(f"pip install -r {relative_path}")

        makefile = self._find_file(local_path, "Makefile")

        if makefile:
            install_scripts.append("make install")

        dockerfile = self._find_file(local_path, "Dockerfile")

        if dockerfile:
            run_scripts.append("docker build . && docker run <image>")

        return (sorted(set(install_scripts)), sorted(set(run_scripts)))

    # ========================================================
    # FIND FILE (no content reads)
    # ========================================================

    def _find_file(self, local_path: str, filename: str):

        for root, _, files in self._walk_repository(local_path):

            if filename in files:
                return os.path.join(root, filename)

        return None

    # ========================================================
    # SAFE READ — the ONLY methods allowed to open() a repo file
    # ========================================================

    def _read_file_with_budget(
        self,
        path: str,
        budget: "_ContentReadBudget",
        max_chars: Optional[int] = None,
    ) -> Optional[str]:
        """
        The SOLE entry point for reading file content anywhere in
        AnalyzerService. Every method that needs content MUST go
        through this method with the SAME shared `budget` — no method
        has an independent budget/cache.
        """

        if max_chars is None:
            max_chars = self.max_chars_per_file

        cached = budget.cache.get(path)

        if cached is not None:
            budget.record_cache_hit()
            return cached

        if budget.exhausted():
            budget.record_skip()
            return None

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read(max_chars)

        except (IOError, OSError):
            return None

        budget.cache[path] = content
        budget.record_read(path, len(content))

        return content

    def _read_file_safe(
        self,
        path: str,
        budget: Optional["_ContentReadBudget"] = None,
        max_chars: Optional[int] = None,
    ) -> str:
        """
        Compatibility wrapper over `_read_file_with_budget`. This,
        together with `_read_file_with_budget`, is the ONLY code in
        this class allowed to call open() on a repository file. Every
        other method must obtain content by calling this method (with
        a shared `budget`) — never directly.

        If `max_chars` is not given explicitly, uses
        `self.max_chars_per_file`.

        If `budget` is provided, the read goes entirely through the
        shared budget (cache + global limits). If `budget` is None
        (isolated call with no shared pass), reads bounded by
        `max_chars` without cache/budget sharing.
        """

        if max_chars is None:
            max_chars = self.max_chars_per_file

        if budget is not None:
            content = self._read_file_with_budget(path, budget=budget, max_chars=max_chars)
            return content if content is not None else ""

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read(max_chars)

        except (IOError, OSError):
            return ""

        return content
