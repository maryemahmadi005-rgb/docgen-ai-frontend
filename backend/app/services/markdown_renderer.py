"""
Rendu déterministe sections_json → README.md.
Aucune IA impliquée — garantit un format cohérent indépendamment
du contenu généré par le LLM.
"""

from jinja2 import Environment, FileSystemLoader
import os

_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_readme(sections_json: dict) -> str:
    template = _env.get_template("readme_template.md.j2")
    return template.render(**sections_json)