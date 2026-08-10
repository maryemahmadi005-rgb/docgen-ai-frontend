"""
AI Service — client unique pour Ollama.

Ce service est le seul point de contact avec le LLM dans toute l'application.
Il ne connaît ni git, ni la base de données, ni le README — il reçoit du texte
en entrée et retourne du texte ou du JSON structuré en sortie.

Utilisé par :

- diff_analyzer_service.py → classify_impact()
- readme_updater.py → generate_section() / generate_full_readme()

Principes :

- Ollama est le seul point de contact avec le LLM.
- Les informations fournies par AnalyzerService sont la source de vérité.
- Le modèle ne doit jamais inventer une fonctionnalité, commande, endpoint,
  technologie ou configuration absente des preuves.
- Les appels Ollama sont configurables via les variables d'environnement.
- Le parsing JSON est défensif et possède une seule tentative de réparation.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Optional

import requests


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Levée quand l'appel au modèle échoue ou renvoie une réponse invalide."""


class AIService:
    """
    Client unique pour Ollama.

    Aucune logique Git, DB ou filesystem n'est implémentée ici.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        num_predict: Optional[int] = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        ).rstrip("/")

        self.model = (
            model
            or os.getenv("OLLAMA_MODEL")
            or os.getenv("DEFAULT_MODEL")
            or "llama3.2:3b"
        )

        self.timeout = self._env_int(
            "OLLAMA_TIMEOUT",
            timeout,
            800,
        )

        self.num_predict = self._env_int(
            "OLLAMA_NUM_PREDICT",
            num_predict,
            800,
        )

        self.temperature = self._env_float(
            "OLLAMA_TEMPERATURE",
            0.3,
            minimum=0.0,
            maximum=2.0,
        )

        self.json_temperature = self._env_float(
            "OLLAMA_JSON_TEMPERATURE",
            0.1,
            minimum=0.0,
            maximum=2.0,
        )

    # ============================================================
    # ENV HELPERS
    # ============================================================

    @staticmethod
    def _env_int(
        name: str,
        explicit: Optional[int],
        default: int,
    ) -> int:
        """
        Lit un entier depuis une variable d'environnement.

        Une valeur explicitement fournie au constructeur est prioritaire.
        """

        if explicit is not None:
            return max(1, int(explicit))

        value = os.getenv(name)

        if not value:
            return default

        try:
            return max(1, int(value))
        except ValueError:
            logger.warning(
                "Valeur invalide pour %s=%r. Utilisation de %s.",
                name,
                value,
                default,
            )
            return default

    @staticmethod
    def _env_float(
        name: str,
        default: float,
        minimum: float = 0.0,
        maximum: float = 2.0,
    ) -> float:
        """Lit un float depuis une variable d'environnement."""

        value = os.getenv(name)

        if not value:
            return default

        try:
            parsed = float(value)
            return max(minimum, min(maximum, parsed))
        except ValueError:
            logger.warning(
                "Valeur invalide pour %s=%r. Utilisation de %s.",
                name,
                value,
                default,
            )
            return default

    # ============================================================
    # LOW LEVEL OLLAMA CALL
    # ============================================================

    def _call(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Appelle Ollama /api/generate et retourne le texte brut.

        Cette méthode est l'unique point réseau vers le LLM.
        """

        if not isinstance(prompt, str) or not prompt.strip():
            raise AIServiceError("Le prompt Ollama est vide.")

        selected_temperature = (
            self.temperature
            if temperature is None
            else temperature
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": selected_temperature,
                "num_predict": self.num_predict,
            },
        }

        if system and system.strip():
            payload["system"] = system

        prompt_chars = len(prompt) + len(system or "")
        started_at = time.monotonic()

        logger.info(
            "Appel Ollama — model=%s — url=%s — "
            "prompt_size=%d — timeout=%ss",
            self.model,
            self.base_url,
            prompt_chars,
            self.timeout,
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:
            elapsed = time.monotonic() - started_at

            logger.error(
                "Ollama injoignable après %.1fs sur %s",
                elapsed,
                self.base_url,
            )

            raise AIServiceError(
                f"Ollama n'est pas joignable sur {self.base_url}. "
                "Vérifie qu'Ollama est lancé et accessible."
            ) from exc

        except requests.exceptions.Timeout as exc:
            elapsed = time.monotonic() - started_at

            logger.error(
                "Timeout Ollama après %.1fs — timeout=%ss — model=%s",
                elapsed,
                self.timeout,
                self.model,
            )

            raise AIServiceError(
                f"Ollama n'a pas répondu dans le délai imparti "
                f"({self.timeout}s) avec le modèle '{self.model}'."
            ) from exc

        except requests.RequestException as exc:
            elapsed = time.monotonic() - started_at

            logger.error(
                "Échec appel Ollama après %.1fs: %s",
                elapsed,
                exc,
            )

            raise AIServiceError(
                f"Impossible de contacter Ollama: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise AIServiceError(
                "Ollama a retourné une réponse HTTP "
                "qui n'est pas un JSON valide."
            ) from exc

        if not isinstance(data, dict):
            raise AIServiceError(
                "Ollama a retourné une structure JSON inattendue."
            )

        text = data.get("response")

        if not isinstance(text, str):
            raise AIServiceError(
                "Ollama n'a pas retourné le champ texte 'response'."
            )

        text = text.strip()

        elapsed = time.monotonic() - started_at

        if not text:
            raise AIServiceError(
                f"Le modèle '{self.model}' a retourné une réponse vide."
            )

        logger.info(
            "Réponse Ollama reçue en %.1fs — "
            "model=%s — response_size=%d",
            elapsed,
            self.model,
            len(text),
        )

        return text

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _extract_json(self, raw: str) -> dict[str, Any]:
        """
        Extrait un objet JSON de façon robuste.

        Supporte :
        1. JSON pur.
        2. JSON dans ```json ... ```.
        3. Objet JSON entouré de texte.
        """

        if not isinstance(raw, str):
            raise json.JSONDecodeError(
                "La réponse n'est pas une chaîne JSON.",
                str(raw),
                0,
            )

        stripped = raw.strip()

        if not stripped:
            raise json.JSONDecodeError(
                "Réponse JSON vide.",
                raw,
                0,
            )

        errors: list[json.JSONDecodeError] = []

        # --------------------------------------------------------
        # 1. JSON pur
        # --------------------------------------------------------

        try:
            parsed = json.loads(stripped)

            if not isinstance(parsed, dict):
                raise json.JSONDecodeError(
                    "La réponse JSON n'est pas un objet.",
                    stripped,
                    0,
                )

            return parsed

        except json.JSONDecodeError as exc:
            errors.append(exc)

        # --------------------------------------------------------
        # 2. Markdown fence
        # --------------------------------------------------------

        fence_matches = re.findall(
            r"```(?:json)?\s*(.*?)\s*```",
            raw,
            flags=re.IGNORECASE | re.DOTALL,
        )

        for candidate in fence_matches:
            candidate = candidate.strip()

            try:
                parsed = json.loads(candidate)

                if not isinstance(parsed, dict):
                    raise json.JSONDecodeError(
                        "La réponse JSON n'est pas un objet.",
                        candidate,
                        0,
                    )

                return parsed

            except json.JSONDecodeError as exc:
                errors.append(exc)

        # --------------------------------------------------------
        # 3. Recherche d'objets JSON dans le texte
        # --------------------------------------------------------

        decoder = json.JSONDecoder()

        for match in re.finditer(r"\{", raw):
            try:
                parsed, _ = decoder.raw_decode(
                    raw,
                    match.start(),
                )

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError as exc:
                errors.append(exc)

        if errors:
            raise errors[-1]

        raise json.JSONDecodeError(
            "Impossible de trouver un objet JSON.",
            raw,
            0,
        )

    # ============================================================
    # JSON CALL
    # ============================================================

    def _call_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Appelle Ollama et garantit un objet JSON.

        Une seule tentative de réparation est effectuée.
        """

        json_instruction = """
IMPORTANT — FORMAT DE SORTIE :

Réponds UNIQUEMENT avec un objet JSON valide.
Aucun texte avant ou après.
Aucune balise Markdown.
Aucun ```json.
Respecte exactement les clés demandées.
"""

        raw = self._call(
            prompt + json_instruction,
            system=system,
            temperature=self.json_temperature,
        )

        try:
            return self._extract_json(raw)

        except json.JSONDecodeError as first_error:
            logger.warning(
                "JSON Ollama invalide, tentative de réparation: %s",
                first_error,
            )

            retry_prompt = f"""
La réponse suivante devait être un objet JSON valide
mais elle est invalide.

Erreur JSON :
{first_error.msg}

ligne={first_error.lineno}
colonne={first_error.colno}

Réponse invalide :
{raw}

Corrige uniquement la syntaxe JSON.

Ne change aucune clé.
Ne change aucune valeur.
Ne supprime aucune information.
Ne rajoute aucune information.

Réponds uniquement avec l'objet JSON corrigé.
"""

            retry_raw = self._call(
                retry_prompt,
                system=system,
                temperature=self.json_temperature,
            )

            try:
                return self._extract_json(retry_raw)

            except json.JSONDecodeError as second_error:
                position = max(
                    0,
                    min(
                        second_error.pos,
                        len(retry_raw),
                    ),
                )

                start = max(0, position - 100)
                end = min(
                    len(retry_raw),
                    position + 100,
                )

                context = retry_raw[start:end]

                raise AIServiceError(
                    "Le modèle a retourné un JSON invalide même "
                    "après une tentative de correction. "
                    f"Erreur: {second_error.msg} "
                    f"(ligne {second_error.lineno}, "
                    f"colonne {second_error.colno}). "
                    f"Contexte: ...{context}..."
                ) from second_error

    # ============================================================
    # NORMALIZATION HELPERS
    # ============================================================

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        """Convertit une valeur quelconque en liste."""

        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        return [value]

    @staticmethod
    def _safe_text(value: Any) -> str:
        """Convertit proprement une valeur quelconque en texte."""

        if value is None:
            return ""

        if isinstance(value, str):
            return value

        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
            )
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _format_context_value(value: Any) -> str:
        """
        Sérialise les données AnalyzerService sans perdre les preuves.
        """

        if value is None:
            return "[]"

        if isinstance(value, str):
            return value

        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
            )
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _normalize_change(change: Any) -> dict[str, Any]:
        """
        Rend classify_impact() tolérant aux objets/dicts provenant
        de différentes versions de DiffAnalyzer.
        """

        if isinstance(change, dict):
            return change

        result: dict[str, Any] = {}

        for name in (
            "path",
            "change_type",
            "diff_excerpt",
            "old_content",
            "new_content",
        ):
            try:
                value = getattr(change, name)
            except AttributeError:
                continue

            result[name] = value

        return result

    # ============================================================
    # DIFF ANALYZER
    # ============================================================

    def classify_impact(
        self,
        file_changes: list[dict],
        repo_context: str = "",
    ) -> dict[str, Any]:
        """
        Détermine quelles sections du README sont réellement affectées.

        Compatible avec DiffAnalyzerService :
        - file_changes : liste de dicts
        - repo_context : contexte optionnel

        Le modèle doit rester conservateur.
        """

        normalized_changes = [
            self._normalize_change(change)
            for change in (file_changes or [])
        ]

        if not normalized_changes:
            return {
                "impact_category": "none",
                "affected_sections": [],
                "confidence_score": 0.0,
            }

        files_description_parts: list[str] = []

        for change in normalized_changes:
            path = str(
                change.get(
                    "path",
                    "unknown",
                )
            )

            change_type = str(
                change.get(
                    "change_type",
                    "modified",
                )
            )

            diff_excerpt = str(
                change.get(
                    "diff_excerpt",
                    "",
                )
            )[:3000]

            files_description_parts.append(
                f"FILE: {path}\n"
                f"CHANGE TYPE: {change_type}\n"
                f"DIFF EVIDENCE:\n{diff_excerpt}"
            )

        files_description = "\n\n".join(
            files_description_parts
        )

        system = """
Tu es un analyseur conservateur de changements de code.

Ta mission est uniquement de déterminer si les changements fournis
peuvent nécessiter une mise à jour du README.

Tu dois utiliser UNIQUEMENT les preuves fournies.

Interdictions absolues :

- ne pas inventer de fonctionnalité ;
- ne pas inventer de technologie ;
- ne pas inventer d'endpoint ;
- ne pas déduire une information absente des changements ;
- ne pas considérer un simple changement interne comme une feature
  visible par l'utilisateur sans preuve ;
- ne pas ajouter une section simplement parce qu'elle semble plausible.

Sections README autorisées :

features
installation
usage
technologies
project_structure
configuration
license

Si les preuves sont insuffisantes, retourne "none" et une liste vide.

Le score de confiance doit représenter uniquement la force des preuves
présentes dans les données fournies.
"""

        prompt = f"""
CHANGEMENTS DU COMMIT :

{files_description}

CONTEXTE DU REPOSITORY :

{repo_context or "Aucun contexte supplémentaire fourni."}

RÈGLES :

- features :
  uniquement si une fonctionnalité utilisateur est explicitement
  visible dans les changements.

- installation :
  uniquement si une dépendance, un outil ou une étape d'installation
  change réellement.

- usage :
  uniquement si une commande, un endpoint ou un comportement
  d'utilisation change réellement.

- technologies :
  uniquement si une technologie réellement utilisée est ajoutée,
  supprimée ou remplacée.

- project_structure :
  uniquement si la structure importante du projet change.

- configuration :
  uniquement si une configuration réelle est modifiée.

- license :
  uniquement si un changement de licence est explicitement visible.

Retourne exactement :

{{
    "impact_category": "feature | dependency | structure | config | license | none",
    "affected_sections": [],
    "confidence_score": 0.0
}}

Ne retourne aucune autre clé.
"""

        result = self._call_json(
            prompt,
            system=system,
        )

        allowed_categories = {
            "feature",
            "dependency",
            "structure",
            "config",
            "license",
            "none",
        }

        allowed_sections = {
            "features",
            "installation",
            "usage",
            "technologies",
            "project_structure",
            "configuration",
            "license",
        }

        category = result.get(
            "impact_category",
            "none",
        )

        if category not in allowed_categories:
            category = "none"

        sections = result.get(
            "affected_sections",
            [],
        )

        if not isinstance(sections, list):
            sections = []

        sections = [
            section
            for section in sections
            if isinstance(section, str)
            and section in allowed_sections
        ]

        # Suppression des doublons en conservant l'ordre.
        sections = list(dict.fromkeys(sections))

        if category == "none":
            sections = []

        confidence = result.get(
            "confidence_score",
            0.0,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        return {
            "impact_category": category,
            "affected_sections": sections,
            "confidence_score": confidence,
        }

    # ============================================================
    # README SECTION UPDATE
    # ============================================================

    def generate_section(
        self,
        section_name: str,
        old_content: Any,
        relevant_files: list[dict],
    ) -> Any:
        """
        Régénère une seule section du README.

        La méthode conserve le type de contenu historique :
        - list → list
        - autre → string
        """

        if not section_name or not str(section_name).strip():
            raise ValueError(
                "section_name est obligatoire."
            )

        is_list = isinstance(
            old_content,
            list,
        )

        old_repr = (
            "\n".join(
                f"- {item}"
                for item in old_content
            )
            if is_list
            else str(old_content or "")
        )

        normalized_files = [
            self._normalize_change(change)
            for change in (relevant_files or [])
        ]

        files_description = "\n\n".join(
            (
                f"FILE: {change.get('path', 'unknown')}\n"
                f"CHANGE TYPE: {change.get('change_type', 'modified')}\n"
                f"DIFF EVIDENCE:\n"
                f"{str(change.get('diff_excerpt', ''))[:4000]}"
            )
            for change in normalized_files
        )

        system = f"""
Tu es responsable de mettre à jour uniquement la section
'{section_name}' d'un README.

SOURCE DE VÉRITÉ :

- le contenu actuel de la section ;
- les preuves des changements fournies.

RÈGLES ABSOLUES :

1. Ne jamais inventer une information.
2. Ne jamais ajouter une commande non présente dans les preuves.
3. Ne jamais ajouter un endpoint non présent dans les preuves.
4. Ne jamais ajouter une technologie non présente dans les preuves.
5. Ne jamais transformer une supposition en fait.
6. Si les changements ne nécessitent aucune modification,
   retourne exactement le contenu actuel.
7. Ne modifie jamais les autres sections du README.
8. Retourne uniquement le nouveau contenu de la section.
"""

        prompt = f"""
SECTION :
{section_name}

CONTENU ACTUEL :
{old_repr}

CHANGEMENTS RÉELS :
{files_description or "Aucun changement pertinent fourni."}

TÂCHE :

Réécris uniquement la section '{section_name}'.

Intègre uniquement les informations directement démontrées
par les preuves ci-dessus.

Si aucune modification n'est justifiée, retourne exactement
le contenu actuel.
"""

        raw = self._call(
            prompt,
            system=system,
            temperature=self.temperature,
        ).strip()

        if not raw:
            return old_content

        # Nettoyage prudent d'une éventuelle réponse markdown
        # quand la section est supposée être une liste.
        if is_list:
            lines: list[str] = []

            for line in raw.splitlines():
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith(
                    (
                        "- ",
                        "* ",
                        "• ",
                    )
                ):
                    stripped = stripped[2:].strip()

                lines.append(stripped)

            return lines or old_content

        return raw

    # ============================================================
    # FULL README GENERATION
    # ============================================================

    def generate_full_readme(
        self,
        project_context: dict,
        repository_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Génère le contenu structuré complet d'un README.

        project_context doit provenir de AnalyzerService et peut contenir :

        - languages
        - frameworks
        - dependencies
        - file_structure
        - important_files
        - entry_points
        - code_evidence
        - api_endpoints
        - frontend_api_calls
        - configuration_evidence
        - install_scripts
        - run_scripts
        """

        if not isinstance(project_context, dict):
            raise TypeError(
                "project_context doit être un dictionnaire."
            )

        logger.info(
            "README generation START — repo_id=%s — model=%s",
            repository_id,
            self.model,
        )

        # --------------------------------------------------------
        # Extraction explicite des champs AnalyzerService.
        # --------------------------------------------------------

        languages = project_context.get(
            "languages",
            {},
        )

        frameworks = project_context.get(
            "frameworks",
            [],
        )

        dependencies = project_context.get(
            "dependencies",
            {},
        )

        file_structure = project_context.get(
            "file_structure",
            {},
        )

        important_files = project_context.get(
            "important_files",
            [],
        )

        entry_points = project_context.get(
            "entry_points",
            [],
        )

        code_evidence = project_context.get(
            "code_evidence",
            [],
        )

        api_endpoints = project_context.get(
            "api_endpoints",
            [],
        )

        frontend_api_calls = project_context.get(
            "frontend_api_calls",
            [],
        )

        configuration_evidence = project_context.get(
            "configuration_evidence",
            [],
        )

        install_scripts = project_context.get(
            "install_scripts",
            [],
        )

        run_scripts = project_context.get(
            "run_scripts",
            [],
        )

        # --------------------------------------------------------
        # Prompt système anti-hallucination.
        # --------------------------------------------------------

        system = """
Tu es un générateur professionnel de README GitHub.

Tu dois produire une documentation fidèle au repository analysé.

SOURCE DE VÉRITÉ :

Les données fournies par AnalyzerService sont la seule source de vérité.

PRIORITÉ DES PREUVES :

1. code_evidence
2. api_endpoints
3. frontend_api_calls
4. entry_points
5. configuration_evidence
6. install_scripts / run_scripts
7. dependencies
8. frameworks / languages
9. file_structure / important_files

RÈGLES ANTI-HALLUCINATION ABSOLUES :

- N'invente aucune fonctionnalité.
- N'invente aucun endpoint.
- N'invente aucune commande.
- N'invente aucune variable d'environnement.
- N'invente aucune technologie.
- N'invente aucune architecture.
- N'invente aucune configuration.
- N'invente aucune étape d'installation.
- N'invente aucun comportement utilisateur.

Un nom de fichier seul ne constitue PAS une preuve suffisante
d'une fonctionnalité.

Une technologie doit être basée sur les données fournies.
Une commande d'installation/exécution doit venir des scripts détectés.
Un endpoint doit venir de api_endpoints.
Un appel frontend doit venir de frontend_api_calls.
Une configuration doit venir de configuration_evidence.

Si une information n'est pas suffisamment démontrée :

- ne la mentionne pas ;
- ou reste volontairement général.

Ne transforme jamais une supposition en fait.

Le README doit rester simple, professionnel et exploitable.
"""

        prompt = f"""
# ANALYSE DÉTERMINISTE DU PROJET

LANGUAGES:
{self._format_context_value(languages)}

FRAMEWORKS:
{self._format_context_value(frameworks)}

DEPENDENCIES:
{self._format_context_value(dependencies)}

FILE STRUCTURE:
{self._format_context_value(file_structure)}

IMPORTANT FILES:
{self._format_context_value(important_files)}

ENTRY POINTS:
{self._format_context_value(entry_points)}

REAL CODE EVIDENCE:
{self._format_context_value(code_evidence)}

BACKEND API ENDPOINTS:
{self._format_context_value(api_endpoints)}

FRONTEND API CALLS:
{self._format_context_value(frontend_api_calls)}

CONFIGURATION EVIDENCE:
{self._format_context_value(configuration_evidence)}

INSTALLATION SCRIPTS:
{self._format_context_value(install_scripts)}

RUN SCRIPTS:
{self._format_context_value(run_scripts)}

# INSTRUCTIONS

1. TITLE

Choisis un titre basé uniquement sur les informations disponibles.

Si le nom du projet n'est pas fourni, utilise un titre générique
et factuel plutôt que d'inventer un nom.

2. DESCRIPTION

Décris uniquement le rôle réellement démontré par les preuves.

3. FEATURES

Liste uniquement les fonctionnalités réellement démontrées
par le code evidence ou les endpoints/API détectés.

Ne transforme pas :

- une classe en fonctionnalité ;
- un dossier en fonctionnalité ;
- une dépendance en fonctionnalité.

4. INSTALLATION

Utilise uniquement install_scripts.

Ne crée aucune commande supplémentaire.

Si aucun script d'installation n'est détecté,
retourne une chaîne vide.

5. USAGE

Utilise uniquement :

- run_scripts ;
- api_endpoints ;
- frontend_api_calls ;
- entry_points.

Ne crée aucune commande.

6. TECHNOLOGIES

Utilise uniquement languages, frameworks et dependencies.

7. PROJECT STRUCTURE

Décris uniquement la structure fournie par file_structure
et les rôles directement démontrés.

8. CONFIGURATION

Utilise uniquement configuration_evidence.

Ne fabrique aucune variable d'environnement.

9. LICENSE

Ne prétends pas qu'une licence existe si elle n'est pas démontrée
par les données fournies.

Si aucune information fiable sur la licence n'est disponible,
retourne une chaîne vide.

# FORMAT DE SORTIE OBLIGATOIRE

Retourne exactement un objet JSON avec ces clés :

{{
    "title": "",
    "description": "",
    "features": [],
    "installation": "",
    "usage": "",
    "technologies": [],
    "project_structure": "",
    "configuration": "",
    "license": ""
}}
"""

        try:
            result = self._call_json(
                prompt,
                system=system,
            )

        except AIServiceError:
            logger.exception(
                "README generation failed — repo_id=%s",
                repository_id,
            )
            raise

        result = self._normalize_full_readme(
            result
        )

        logger.info(
            "README generation DONE — repo_id=%s",
            repository_id,
        )

        return result

    # ============================================================
    # README RESULT NORMALIZATION
    # ============================================================

    def _normalize_full_readme(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Garantit une structure stable pour readme_updater.py.
        """

        required_list_keys = {
            "features",
            "technologies",
        }

        required_string_keys = {
            "title",
            "description",
            "installation",
            "usage",
            "project_structure",
            "configuration",
            "license",
        }

        normalized: dict[str, Any] = {}

        # --------------------------------------------------------
        # Lists
        # --------------------------------------------------------

        for key in required_list_keys:
            value = result.get(
                key,
                [],
            )

            if isinstance(value, list):
                normalized[key] = [
                    str(item).strip()
                    for item in value
                    if item is not None
                    and str(item).strip()
                ]

            elif value:
                normalized[key] = [
                    str(value).strip()
                ]

            else:
                normalized[key] = []

        # --------------------------------------------------------
        # Strings
        # --------------------------------------------------------

        for key in required_string_keys:
            value = result.get(
                key,
                "",
            )

            if isinstance(value, str):
                normalized[key] = value.strip()

            elif value is None:
                normalized[key] = ""

            else:
                normalized[key] = self._safe_text(
                    value
                ).strip()

        return normalized
