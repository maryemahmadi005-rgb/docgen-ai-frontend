"""
Markdown Renderer — rendu déterministe des sections_json vers README.md.

Aucune IA impliquée ici.
Le renderer transforme les données structurées en Markdown via Jinja2.
Les données factuelles reçues du pipeline sont rendues sans interprétation.

IMPORTANT — cohérence de schéma :
sections_json ne contient QUE les clés de AIService.README_SCHEMA
(y compris installation/usage). Ce module (et le template qu'il
charge) ne doit donc jamais s'attendre à d'autres clés
(file_structure, important_files, install_scripts, run_scripts,
configuration_evidence, frontend_api_calls, installation_evidence,
usage_evidence...) : ces preuves brutes restent internes au pipeline
de génération et ne sont jamais rendues telles quelles dans le
README — seules les versions structurées par le LLM
(installation/usage) le sont.
"""

from __future__ import annotations

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader


# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "templates",
)

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
)


# ---------------------------------------------------------------------------
# README rendering
# ---------------------------------------------------------------------------

# Doit rester identique à AIService.README_SCHEMA. Dupliqué ici en
# constante simple (plutôt qu'importé) pour ne pas introduire de
# dépendance circulaire entre markdown_renderer et ai_service ; les
# deux listes sont vérifiées comme identiques par les tests /
# validate_rendered_readme.
README_SCHEMA = (
    "project_goal",
    "general_operation",
    "architecture",
    "technologies",
    "main_modules",
    "data_flow",
    "entry_points",
    "api_endpoints",
    "important_dependencies",
    "recommendations",
    "installation",
    "usage",
)


def render_readme(sections_json: dict[str, Any]) -> str:
    """
    Transforme sections_json en README.md.

    Le rendu est déterministe : aucune IA n'est utilisée ici.
    Le template reçoit exactement les 10 clés du schéma, ni plus ni
    moins, afin qu'aucun champ ne soit perdu ou ajouté silencieusement
    entre AIService, ReadmeGeneratorService et le template Jinja.
    """
    if not isinstance(sections_json, dict):
        raise TypeError("sections_json doit être un dictionnaire.")

    context = {key: sections_json.get(key) for key in README_SCHEMA}

    template = _env.get_template("readme_template.md.j2")

    rendered = template.render(**context)

    if not isinstance(rendered, str):
        raise TypeError("Le template README doit retourner une chaîne.")

    return rendered.strip() + "\n"


# ---------------------------------------------------------------------------
# README validation
# ---------------------------------------------------------------------------

_REQUIRED_SECTIONS = README_SCHEMA

# "## Architecture", "## Installation" et "## Usage" sont
# volontairement absents de cette liste : ces sections sont
# entièrement omises du template (aucun heading, aucun texte de
# repli) quand aucune preuve fiable n'a été détectée par
# AnalyzerService (architecture non détectée, ou
# installation_evidence/usage_evidence vides — voir
# `_is_architecture_reliably_detected` dans ai_service.py et le
# même principe appliqué à installation/usage). Forcer ces headings
# ici ferait échouer la validation à chaque fois que ces sections
# sont légitimement absentes.
_REQUIRED_HEADINGS = (
    "## Technologies utilisées",
    "## Modules principaux",
    "## Points d'entrée",
    "## Endpoints API",
    "## Dépendances importantes",
)


def _has_usable_value(value: Any) -> bool:
    """Retourne True si une valeur contient réellement des données."""
    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set)):
        return bool(value)

    if isinstance(value, dict):
        return bool(value)

    return value is not None


def validate_rendered_readme(
    sections_json: dict[str, Any],
    rendered_md: str,
) -> bool:
    """
    Valide la structure du rendu sans réinterpréter les données.

    La validation vérifie :
      - la présence EXACTE des sections attendues (schéma fermé) ;
      - le type global du rendu ;
      - la présence des sections Markdown importantes ;
      - qu'une section non vide n'est pas remplacée par un README vide.

    Elle ne modifie jamais sections_json.
    """
    if not isinstance(sections_json, dict):
        return False

    if not isinstance(rendered_md, str):
        return False

    if not rendered_md.strip():
        return False

    actual_keys = set(sections_json.keys())
    expected_keys = set(_REQUIRED_SECTIONS)

    if actual_keys != expected_keys:
        return False

    if any(heading not in rendered_md for heading in _REQUIRED_HEADINGS):
        return False

    if not any(
        _has_usable_value(value) for value in sections_json.values()
    ):
        return False

    # Les champs factuels critiques doivent exister dans le contexte.
    # Leur contenu est rendu directement par le template ; la validation
    # ne les filtre donc jamais et ne tente pas de les normaliser.
    factual_fields = (
        "architecture",
        "technologies",
        "entry_points",
        "api_endpoints",
        "important_dependencies",
        "installation",
        "usage",
    )

    if any(field not in sections_json for field in factual_fields):
        return False

    return True