"""
Table de correspondance statique : chemin/type de fichier → sections README impactées.

Utilisée en premier par le Diff Analyzer, avant tout appel IA — la plupart
des changements courants sont catégorisables sans LLM (moins cher, plus fiable).

BUG CORRIGÉ ICI (root-cause) :
Les valeurs "affected_sections" pointaient vers des noms de sections
("features", "installation", "configuration", "license", "usage") qui
n'ont jamais existé dans le schéma réel du README. Le README généré par
ReadmeGeneratorService/AIService ne contient QUE les 10 clés de
AIService.README_SCHEMA (project_goal, general_operation, architecture,
technologies, main_modules, data_flow, entry_points, api_endpoints,
important_dependencies, recommendations) — voir markdown_renderer.py.

Conséquence concrète du bug : ReadmeUpdaterService.generate_patch()
générait bien un contenu pour, par ex., "installation", et
sections_diff montrait un changement réel (has_real_changes() -> True),
donc un commit+push et une nouvelle ReadmeVersion étaient créés — mais
markdown_renderer.render_readme() ignore silencieusement toute clé hors
README_SCHEMA. Le README.md réellement écrit sur le repo ne changeait
JAMAIS pour ces sections. Le pipeline semblait fonctionner (logs,
versions, commits) tout en ne modifiant rien de visible.

Les "affected_sections" ci-dessous utilisent donc désormais exclusivement
les clés réelles de README_SCHEMA. "LICENSE" n'a pas d'équivalent dans ce
schéma (pas de section dédiée) : le changement reste détecté/loggé
(impact_category="license") mais ne déclenche volontairement aucune
réécriture de section plutôt que d'être mappé arbitrairement sur un champ
sans rapport.
"""

import re
import fnmatch

RULES = [
    {"patterns": ["requirements.txt", "package.json", "Pipfile", "pyproject.toml", "go.mod", "Gemfile"],
     "impact_category": "dependency", "affected_sections": ["technologies", "important_dependencies"]},
    {"patterns": ["Dockerfile", "docker-compose.yml", ".env.example", "*.config.js", "config/*"],
     "impact_category": "config", "affected_sections": ["architecture"]},
    {"patterns": ["LICENSE", "LICENSE.md", "LICENSE.txt"],
     "impact_category": "license", "affected_sections": []},
    {"patterns": ["Makefile", "scripts/*", "*.sh", "install.*"],
     "impact_category": "structure", "affected_sections": ["general_operation"]},
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
            return {"impact_category": "feature", "affected_sections": ["main_modules", "api_endpoints"]}

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