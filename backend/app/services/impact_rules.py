"""
Table de correspondance statique : chemin/type de fichier → sections README impactées.

Utilisée en premier par le Diff Analyzer, avant tout appel IA — la plupart
des changements courants sont catégorisables sans LLM (moins cher, plus fiable).
"""

import re
import fnmatch

RULES = [
    {"patterns": ["requirements.txt", "package.json", "Pipfile", "pyproject.toml", "go.mod", "Gemfile"],
     "impact_category": "dependency", "affected_sections": ["technologies", "installation"]},
    {"patterns": ["Dockerfile", "docker-compose.yml", ".env.example", "*.config.js", "config/*"],
     "impact_category": "config", "affected_sections": ["configuration"]},
    {"patterns": ["LICENSE", "LICENSE.md", "LICENSE.txt"],
     "impact_category": "license", "affected_sections": ["license"]},
    {"patterns": ["Makefile", "scripts/*", "*.sh", "install.*"],
     "impact_category": "structure", "affected_sections": ["installation", "usage"]},
]

FEATURE_PATH_HINTS = ["auth", "login", "oauth", "payment", "api/", "routes/", "controllers/", "views/"]

EXCLUDED_FILES = {"README.md", "readme.md", ".gitignore", "CHANGELOG.md"}


def match_static_rules(file_path: str, change_type: str) -> dict | None:
    if file_path in EXCLUDED_FILES:
        return {"impact_category": "none", "affected_sections": []}

    for rule in RULES:
        for pattern in rule["patterns"]:
            if fnmatch.fnmatch(file_path, pattern) or file_path == pattern:
                return {"impact_category": rule["impact_category"],
                        "affected_sections": rule["affected_sections"]}

    if change_type == "added":
        lower_path = file_path.lower()
        if any(hint in lower_path for hint in FEATURE_PATH_HINTS):
            return {"impact_category": "feature", "affected_sections": ["features"]}

    return None  # ambigu → nécessite classification IA


def merge_impacts(impacts: list[dict]) -> dict:
    all_sections = set()
    categories = set()
    for impact in impacts:
        if impact and impact.get("impact_category") != "none":
            all_sections.update(impact.get("affected_sections", []))
            categories.add(impact.get("impact_category"))

    return {
        "impact_category": next(iter(categories), "none") if len(categories) == 1 else "mixed",
        "affected_sections": sorted(all_sections),
    }