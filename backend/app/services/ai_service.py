"""
AI Service — client unique pour Ollama.dzdzdddddssdcccccccccccccccccdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

Responsable uniquement des interactions avec le LLM.

Le LLM reçoit les preuves produites par AnalyzerService et génère
une documentation technique structurée.
bvcxdfgvbh cdgc vgvbn,,,,,,,,,,,,,,,,,,,

IMPORTANT :
nana nanan ananananananana nqjdnzjdnkdncejfvnesvsjefvvvvvvvvvvvvvvdfvsqsdc
- aucune information ne doit être inventée ;
- les technologies détectées sont la seule source autorisée ;
- les chemins de fichiers doivent provenir de l'analyse ;
- les flux doivent être justifiés par le code ;
- l'architecture détectée est prioritaire ;
- le résultat final respecte strictement le schéma README (README_SCHEMA) ;
- le résultat final NE CONTIENT QUE ces 10 clés — aucune autre clé
  (file_structure, important_files, install_scripts, ...) ne doit
  fuiter dans la sortie : ces données restent des preuves internes
  utilisées uniquement pour construire le prompt.
  fvsbfr gngnnf nndd fnfnrfr,jrnrne,ejejeneej

NOTE CONTEXTE OLLAMA :
Le nombre de preuves envoyées (fichiers de code, structure, endpoints...)
peut être important. Si `num_ctx` n'est pas explicitement fourni à
Ollama, le modèle utilise sa fenêtre de contexte par défaut (souvent
2048-4096 tokens), ce qui tronque silencieusement le prompt et produit
une documentation générique alors même que l'analyse était correcte.
`num_ctx` est donc calculé/forcé ici en fonction de la taille réelle
du prompt envoyé.
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
    """Levée quand l'appel au modèle échoue ou retourne une réponse invalide."""

    pass


class AIService:
    """
    Client unique pour Ollama.

    Aucune logique Git, DB ou filesystem n'est implémentée ici.
    """

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

    # ============================================================
    # CODE EVIDENCE — sélection stricte envoyée à Ollama
    # ============================================================
    DEFAULT_MAX_CODE_EVIDENCE_FILES = 20
    DEFAULT_MAX_CODE_EVIDENCE_CHARS_PER_FILE = 3000
    # Test automatic synchronization

    CONFIG_FILE_BASENAMES = (
        "package.json",
        "package-lock.json",
        "requirements.txt",
        "pyproject.toml",
        "pipfile",
        "poetry.lock",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "vite.config.js",
        "vite.config.ts",
        "webpack.config.js",
        "tsconfig.json",
        "babel.config.js",
        "setup.py",
        "setup.cfg",
        "gemfile",
        "composer.json",
        ".env.example",
    )

    ARCHITECTURE_KEYWORDS = (
        "route",
        "controller",
        "service",
        "api",
        "model",
        "database",
        "db",
        "config",
        "core",
        "schema",
        "middleware",
        "handler",
        "init",
    )

    # Champs rédigés par le LLM. Tout le reste du schéma provient
    # exclusivement de AnalyzerService.
    LLM_WRITTEN_FIELDS = (
        "project_goal",
        "general_operation",
        "main_modules",
        "data_flow",
        "recommendations",
        "installation",
        "usage",
    )

    # Champs factuels : Analyzer uniquement, jamais générés/modifiés
    # par le modèle.
    ANALYZER_ONLY_FIELDS = (
        "architecture",
        "technologies",
        "entry_points",
        "api_endpoints",
        "important_dependencies",
    )

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        num_predict: Optional[int] = None,
        num_ctx: Optional[int] = None,
        max_code_evidence_files: Optional[int] = None,
        max_code_evidence_chars_per_file: Optional[int] = None,
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
            1200,
        )

        self.num_ctx = self._env_int(
            "OLLAMA_NUM_CTX",
            num_ctx,
            8192,
        )

        self.temperature = self._env_float(
            "OLLAMA_TEMPERATURE",
            0.2,
            0.0,
            2.0,
        )

        self.json_temperature = self._env_float(
            "OLLAMA_JSON_TEMPERATURE",
            0.1,
            0.0,
            2.0,
        )

        self.max_code_evidence_files = self._env_int(
            "MAX_CODE_EVIDENCE_FILES",
            max_code_evidence_files,
            self.DEFAULT_MAX_CODE_EVIDENCE_FILES,
        )

        self.max_code_evidence_chars_per_file = self._env_int(
            "MAX_CODE_EVIDENCE_CHARS_PER_FILE",
            max_code_evidence_chars_per_file,
            self.DEFAULT_MAX_CODE_EVIDENCE_CHARS_PER_FILE,
        )

    # ============================================================
    # ENV
    # ============================================================

    @staticmethod
    def _env_int(
        name: str,
        explicit: Optional[int],
        default: int,
    ) -> int:

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

        value = os.getenv(name)

        if not value:
            return default

        try:
            parsed = float(value)
            return max(
                minimum,
                min(maximum, parsed),
            )
        except ValueError:
            logger.warning(
                "Valeur invalide pour %s=%r. Utilisation de %s.",
                name,
                value,
                default,
            )
            return default

    # ============================================================
    # OLLAMA
    # ============================================================

    def _resolve_num_ctx(
        self,
        prompt: str,
        system: Optional[str],
    ) -> int:

        char_count = len(prompt) + len(system or "")
        estimated_input_tokens = (char_count // 4) + 256

        required = estimated_input_tokens + self.num_predict

        ctx = max(self.num_ctx, 2048)

        while ctx < required:
            ctx *= 2

        return ctx

    def _call(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:

        if not isinstance(prompt, str) or not prompt.strip():
            raise AIServiceError("Le prompt Ollama est vide.")

        selected_temperature = (
            self.temperature
            if temperature is None
            else temperature
        )

        resolved_num_ctx = self._resolve_num_ctx(
            prompt,
            system,
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": selected_temperature,
                "num_predict": self.num_predict,
                "num_ctx": resolved_num_ctx,
            },
        }

        if system and system.strip():
            payload["system"] = system

        started_at = time.monotonic()

        logger.info(
            "Appel Ollama — model=%s — prompt_size=%d — num_ctx=%d",
            self.model,
            len(prompt) + len(system or ""),
            resolved_num_ctx,
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:
            raise AIServiceError(
                f"Ollama n'est pas joignable sur {self.base_url}."
            ) from exc

        except requests.exceptions.Timeout as exc:
            raise AIServiceError(
                f"Ollama n'a pas répondu dans le délai "
                f"imparti ({self.timeout}s)."
            ) from exc

        except requests.RequestException as exc:
            raise AIServiceError(
                f"Impossible de contacter Ollama: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise AIServiceError(
                "Ollama a retourné une réponse non JSON."
            ) from exc

        if not isinstance(data, dict):
            raise AIServiceError(
                "Structure JSON Ollama inattendue."
            )

        text = data.get("response")

        if not isinstance(text, str):
            raise AIServiceError(
                "Le champ 'response' est absent de la réponse Ollama."
            )

        text = text.strip()

        if not text:
            raise AIServiceError(
                f"Le modèle '{self.model}' a retourné une réponse vide."
            )

        logger.info(
            "Réponse Ollama reçue en %.1fs — size=%d",
            time.monotonic() - started_at,
            len(text),
        )

        return text

    # ============================================================
    # JSON
    # ============================================================

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any]:

        if not isinstance(raw, str):
            raise json.JSONDecodeError(
                "Réponse non textuelle",
                str(raw),
                0,
            )

        raw = raw.strip()

        if not raw:
            raise json.JSONDecodeError(
                "Réponse vide",
                raw,
                0,
            )

        # Chaque stratégie est essayée sur le texte brut D'ABORD (rapide,
        # ne modifie rien), puis sur la version assainie localement
        # (AIService._sanitize_json_text) si le texte brut échoue. Cette
        # passe de nettoyage déterministe est gratuite (aucun appel
        # Ollama) et corrige la très grande majorité des cas réels vus en
        # production avec les petits modèles locaux : retours à la ligne
        # bruts non échappés à l'intérieur d'une chaîne, virgules
        # traînantes, guillemets typographiques, littéraux Python
        # (True/False/None) — des erreurs de SYNTAXE uniquement, jamais
        # de contenu réécrit ou inventé.
        candidates = [raw]
        sanitized = AIService._sanitize_json_text(raw)
        if sanitized != raw:
            candidates.append(sanitized)

        # --- 1) JSON direct (objet entier, éventuellement déjà propre) ---
        for candidate in candidates:
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                continue

        # --- 2) Bloc(s) ```json ... ``` / ``` ... ``` ---
        for candidate in candidates:
            matches = re.findall(
                r"```(?:json)?\s*(.*?)\s*```",
                candidate,
                flags=re.IGNORECASE | re.DOTALL,
            )
            for block in matches:
                for block_variant in (block, AIService._sanitize_json_text(block)):
                    try:
                        result = json.loads(block_variant)
                        if isinstance(result, dict):
                            return result
                    except json.JSONDecodeError:
                        continue

        # --- 3) Texte avant/après un objet JSON — on scanne chaque '{' ---
        decoder = json.JSONDecoder()
        for candidate in candidates:
            for match in re.finditer(r"\{", candidate):
                try:
                    result, _ = decoder.raw_decode(
                        candidate,
                        match.start(),
                    )
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    continue

        raise json.JSONDecodeError(
            "Impossible de trouver un objet JSON valide.",
            raw,
            0,
        )

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        """
        Nettoyage déterministe et purement SYNTAXIQUE d'une réponse censée
        être du JSON — ne réécrit, ne supprime ni n'invente jamais de
        contenu sémantique, uniquement des artefacts de formatage
        typiques des petits modèles locaux (Ollama) :

        - guillemets typographiques (" " ' ') -> guillemets ASCII
        - littéraux Python True/False/None -> true/false/null
        - virgule traînante avant '}' ou ']'
        - retours à la ligne / tabulations / autres caractères de
          contrôle BRUTS à l'intérieur d'une chaîne JSON -> échappés
          (\\n, \\t) ou supprimés s'ils n'ont pas d'équivalent JSON —
          c'est la cause la plus fréquente de "Invalid control
          character" quand le modèle écrit du texte multi-lignes sans
          échapper les sauts de ligne.
        """
        if not text:
            return text

        cleaned = (
            text.replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )

        cleaned = re.sub(r"\bTrue\b", "true", cleaned)
        cleaned = re.sub(r"\bFalse\b", "false", cleaned)
        cleaned = re.sub(r"\bNone\b", "null", cleaned)

        cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

        cleaned = AIService._escape_raw_control_chars_in_strings(cleaned)

        return cleaned

    @staticmethod
    def _escape_raw_control_chars_in_strings(text: str) -> str:
        """
        Parcourt `text` caractère par caractère et échappe les retours à
        la ligne/tabulations bruts rencontrés À L'INTÉRIEUR d'une chaîne
        JSON (entre guillemets non échappés). En dehors des chaînes, le
        texte n'est pas modifié — la structure JSON (indentation, sauts
        de ligne entre les clés) reste intacte.
        """
        out: list[str] = []
        in_string = False
        escape = False

        for ch in text:
            if in_string:
                if escape:
                    out.append(ch)
                    escape = False
                elif ch == "\\":
                    out.append(ch)
                    escape = True
                elif ch == '"':
                    out.append(ch)
                    in_string = False
                elif ch == "\n":
                    out.append("\\n")
                elif ch == "\r":
                    continue  # normalisé via le \\n du \\n qui suit (CRLF)
                elif ch == "\t":
                    out.append("\\t")
                elif ord(ch) < 0x20:
                    continue  # autre caractère de contrôle sans échappement JSON standard — supprimé
                else:
                    out.append(ch)
            else:
                if ch == '"':
                    in_string = True
                out.append(ch)

        return "".join(out)

    def _call_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> dict[str, Any]:

        instruction = """

IMPORTANT — FORMAT DE RÉPONSE STRICT :

Réponds UNIQUEMENT avec un objet JSON valide, respectant EXACTEMENT
le schéma demandé ci-dessus (mêmes clés, aucune clé en plus, aucune
clé en moins).

Interdictions absolues :
- Aucun texte avant l'objet JSON.
- Aucun texte après l'objet JSON.
- Aucune balise Markdown, aucun ```json, aucun ```.
- Aucune explication, aucun commentaire, aucune excuse.
- N'invente aucune information absente des preuves fournies.

Règles de syntaxe JSON strictes :
- Guillemets doubles (") uniquement — jamais de guillemets simples.
- Aucune virgule après le dernier élément d'une liste ou d'un objet.
- Si une valeur texte contient un retour à la ligne, échappe-le en
  \\n : n'insère jamais un vrai saut de ligne brut à l'intérieur
  d'une chaîne JSON.
"""

        raw = self._call(
            prompt + instruction,
            system=system,
            temperature=self.json_temperature,
        )

        try:
            return self._extract_json(raw)

        except json.JSONDecodeError as first_error:

            logger.warning(
                "JSON invalide, tentative de réparation: %s",
                first_error,
            )

            repair_prompt = f"""
La réponse suivante devait être un objet JSON valide mais ne l'est pas.

Erreur de parsing :
{first_error.msg}

Réponse à corriger :

{raw}

Corrige UNIQUEMENT la syntaxe JSON (guillemets doubles, pas de
virgule traînante, pas de saut de ligne brut à l'intérieur d'une
chaîne — échappe-le en \\n, pas de texte hors de l'objet JSON).

Ne change, n'ajoute ni ne supprime aucune information de contenu.

Retourne uniquement le JSON corrigé, rien d'autre.
"""

            repaired = self._call(
                repair_prompt,
                system=system,
                temperature=self.json_temperature,
            )

            try:
                return self._extract_json(repaired)

            except json.JSONDecodeError as second_error:

                raise AIServiceError(
                    "Le modèle a retourné un JSON invalide "
                    "même après réparation."
                ) from second_error

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _format(value: Any) -> str:

        if value is None:
            return "[]"

        if isinstance(value, str):
            return value

        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except Exception:
            return str(value)

    @staticmethod
    def _clean_structured_section(value: Any) -> dict[str, list[str]]:
        """
        Nettoie une section structurée (installation/usage) rédigée
        par le LLM en données JSON propres, prêtes pour le rendu
        Markdown : {str: [str, ...]}. Ne retourne jamais un dict
        Python brut destiné à être affiché tel quel — toute clé dont
        la valeur n'est ni une chaîne ni une liste de chaînes est
        écartée plutôt que rendue en repr() Python.
        """

        if not isinstance(value, dict):
            return {}

        cleaned: dict[str, list[str]] = {}

        for key, raw in value.items():

            if not isinstance(key, str) or not key.strip():
                continue

            items: list[str] = []

            if isinstance(raw, str):
                if raw.strip():
                    items = [raw.strip()]
            elif isinstance(raw, (list, tuple)):
                for entry in raw:
                    if isinstance(entry, str) and entry.strip():
                        items.append(entry.strip())
                    elif isinstance(entry, (int, float)):
                        items.append(str(entry))
                    # dicts/lists imbriqués ignorés : jamais de
                    # structure brute affichée dans le README.
            # autres types (dict, int, bool, None...) ignorés.

            if items:
                cleaned[key.strip()] = items

        return cleaned

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any]:

        if not isinstance(result, dict):
            result = {}

        defaults = {
            "project_goal": "",
            "general_operation": "",
            "main_modules": [],
            "data_flow": "",
            "recommendations": [],
            "installation": {},
            "usage": {},
        }

        normalized = {}

        for key, default in defaults.items():

            value = result.get(
                key,
                default,
            )

            if isinstance(default, list):
                normalized[key] = (
                    value
                    if isinstance(value, list)
                    else []
                )
            elif isinstance(default, dict):
                normalized[key] = (
                    value
                    if isinstance(value, dict)
                    else {}
                )
            else:
                normalized[key] = (
                    value
                    if isinstance(value, str)
                    else ""
                )

        return normalized

    # ============================================================
    # FULL README
    # ============================================================

    @staticmethod
    def _source_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return []

    @staticmethod
    def _item_identity(item: Any) -> str:
        if isinstance(item, str):
            return item.strip().lower()

        if isinstance(item, dict):
            for key in (
                "path",
                "file",
                "filepath",
                "file_path",
                "name",
                "route",
                "endpoint",
                "url",
                "method",
                "id",
            ):
                value = item.get(key)

                if value is not None:
                    return str(value).strip().lower()

        return str(item).strip().lower()
    @classmethod
    def _build_main_modules(
        cls,
        important_files: Any,
        code_evidence: Any,
        generated: Any,
    ) -> list[Any]:

        allowed = {}

        for item in cls._source_list(important_files):
            identity = cls._item_identity(item)

            if identity:
                allowed[identity] = item

        for item in cls._source_list(code_evidence):
            identity = cls._item_identity(item)

            if identity:
                allowed.setdefault(identity, item)

        result = []

        for item in cls._source_list(generated):

            if not isinstance(item, dict):
                continue

            identity = cls._item_identity(item)

            if identity not in allowed:
                continue

            validated = dict(item)

            # ----------------------------------------------------
            # PATH — source Analyzer uniquement
            # ----------------------------------------------------

            validated["path"] = cls._item_identity_display(
                allowed[identity]
            )

            # ----------------------------------------------------
            # LIST FIELDS — normalize LLM output
            # ----------------------------------------------------

            for field in (
                "classes",
                "functions",
                "dependencies",
                "routes",
            ):
                value = validated.get(field, [])

                if isinstance(value, list):
                    validated[field] = value

                elif value is None:
                    validated[field] = []

                else:
                    validated[field] = [value]

            # ----------------------------------------------------
            # STRING FIELDS
            # ----------------------------------------------------

            for field in (
                "name",
                "role",
                "blueprint",
                "interactions",
            ):
                value = validated.get(field, "")

                if value is None:
                    validated[field] = ""
                elif not isinstance(value, str):
                    validated[field] = str(value)

            result.append(validated)

        return result

    @staticmethod
    def _item_identity_display(source_item: Any) -> str:
        if isinstance(source_item, str):
            return source_item

        if isinstance(source_item, dict):
            for key in ("path", "file", "filepath", "file_path"):
                value = source_item.get(key)
                if value is not None:
                    return str(value)

        return str(source_item)

    # ============================================================
    # CODE EVIDENCE SELECTION (prompt only — Analyzer data untouched)
    # ============================================================

    @classmethod
    def _code_evidence_priority(
        cls,
        normalized_path: str,
        entry_point_identities: set[str],
        important_file_identities: set[str],
    ) -> int:

        basename = normalized_path.rsplit("/", 1)[-1]

        if (
            normalized_path in entry_point_identities
            or basename in entry_point_identities
        ):
            return 1

        if (
            normalized_path in important_file_identities
            or basename in important_file_identities
        ):
            return 2

        if any(
            keyword in normalized_path
            for keyword in cls.ARCHITECTURE_KEYWORDS
        ):
            return 3

        if basename in cls.CONFIG_FILE_BASENAMES:
            return 4

        return 5

    @classmethod
    def _select_code_evidence_for_ollama(
        cls,
        code_evidence: Any,
        important_files: Any,
        entry_points: Any,
        max_files: int,
        max_chars_per_file: int,
    ) -> tuple[list[dict[str, str]], int]:

        if not isinstance(code_evidence, list):
            return [], 0

        entry_point_identities = {
            identity
            for identity in (
                cls._item_identity(item)
                for item in cls._source_list(entry_points)
            )
            if identity
        }

        important_file_identities = {
            identity
            for identity in (
                cls._item_identity(item)
                for item in cls._source_list(important_files)
            )
            if identity
        }

        candidates: list[dict[str, str]] = []
        seen_paths: set[str] = set()

        for item in code_evidence:

            if not isinstance(item, dict):
                continue

            path = item.get("path")
            content = item.get("content", "")

            if not path or not isinstance(content, str):
                continue

            normalized_path = str(path).replace("\\", "/").lower()

            if (
                "generated_docs/" in normalized_path
                or "doc-output/" in normalized_path
            ):
                continue

            if normalized_path in seen_paths:
                continue

            seen_paths.add(normalized_path)

            candidates.append(
                {
                    "path": str(path),
                    "normalized_path": normalized_path,
                    "content": content,
                }
            )

        total_available = len(candidates)

        ranked = sorted(
            enumerate(candidates),
            key=lambda pair: (
                cls._code_evidence_priority(
                    pair[1]["normalized_path"],
                    entry_point_identities,
                    important_file_identities,
                ),
                pair[0],
            ),
        )

        selected: list[dict[str, str]] = []

        for _, candidate in ranked[:max_files]:

            truncated_content = candidate["content"][:max_chars_per_file]

            selected.append(
                {
                    "path": candidate["path"],
                    "truncated_content": truncated_content,
                }
            )

        return selected, total_available

    # ============================================================
    # CLASSIFY IMPACT — utilisé par DiffAnalyzerService
    # ============================================================

    # BUG CORRIGÉ : cette liste doit être un sous-ensemble strict des clés
    # réelles du README (README_SCHEMA, voir markdown_renderer.py) — sinon
    # une section "détectée" par le LLM (ex: "installation", "features")
    # n'existe dans aucun README réel et est silencieusement ignorée par
    # render_readme(), qui ne lit que les clés de README_SCHEMA. Voir
    # impact_rules.py pour le détail de ce bug côté règles statiques.
    SECTION_CHOICES = (
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
    )

    def classify_impact(
        self,
        file_changes: list[dict[str, Any]],
        repo_context: str = "",
    ) -> dict[str, Any]:

        safe_result = {
            "impact_category": "none",
            "affected_sections": [],
            "confidence_score": 0.3,
        }

        if not isinstance(file_changes, list) or not file_changes:
            return safe_result

        valid_changes = [
            fc for fc in file_changes
            if isinstance(fc, dict) and fc.get("path")
        ]

        if not valid_changes:
            return safe_result

        known_paths = {
            str(fc["path"]) for fc in valid_changes
        }

        system = f"""
Tu es un classificateur d'impact de changements de code sur une
documentation README.

Tu reçois une liste de fichiers modifiés (chemin, type de
changement, extrait de diff) et le contexte du dépôt.

Tu dois déterminer quelles sections du README sont réellement
affectées par CES changements précis, parmi UNIQUEMENT cette liste
fermée de sections valides :
{json.dumps(self.SECTION_CHOICES)}

Interdiction absolue :
- inventer une section hors de cette liste ;
- inventer un fichier qui n'est pas dans la liste fournie ;
- déduire un impact non justifié par le contenu des extraits fournis.

Si les preuves sont insuffisantes ou peu claires, retourne une liste
de sections vide plutôt que de deviner.

Retourne uniquement un objet JSON valide avec exactement ces clés :
{{"impact_category": "", "affected_sections": [], "confidence_score": 0.0}}

impact_category doit être un court mot-clé résumant la nature du
changement (ex: "feature", "config", "dependency", "structure",
"mixed", "none").
confidence_score est un nombre entre 0.0 et 1.0.
"""

        prompt = f"""
CONTEXTE DU DÉPÔT :
{self._format(repo_context)}

FICHIERS MODIFIÉS (chemins réels — n'en utilise aucun autre) :
{self._format(valid_changes)}

Analyse ces changements et détermine l'impact sur le README.
"""

        try:
            result = self._call_json(prompt, system=system)
        except AIServiceError as exc:
            logger.warning(
                "classify_impact: échec Ollama, résultat safe retourné: %s",
                exc,
            )
            return safe_result

        if not isinstance(result, dict):
            return safe_result

        impact_category = result.get("impact_category")
        if not isinstance(impact_category, str) or not impact_category.strip():
            impact_category = "none"

        raw_sections = result.get("affected_sections")
        affected_sections = []

        if isinstance(raw_sections, list):
            for section in raw_sections:
                if (
                    isinstance(section, str)
                    and section in self.SECTION_CHOICES
                    and section not in affected_sections
                ):
                    affected_sections.append(section)

        raw_confidence = result.get("confidence_score")
        try:
            confidence_score = float(raw_confidence)
        except (TypeError, ValueError):
            confidence_score = 0.5

        confidence_score = max(0.0, min(1.0, confidence_score))

        if not affected_sections:
            impact_category = "none"

        return {
            "impact_category": impact_category,
            "affected_sections": affected_sections,
            "confidence_score": confidence_score,
        }

    # ============================================================
    # GENERATE SECTION — utilisé par ReadmeUpdaterService
    # ============================================================

    def generate_section(
        self,
        section_name: str,
        old_content: Any,
        relevant_files: list[dict[str, Any]],
    ) -> Any:

        is_list_section = isinstance(old_content, list)

        if not isinstance(relevant_files, list) or not relevant_files:
            return old_content

        valid_files = [
            rf for rf in relevant_files
            if isinstance(rf, dict) and rf.get("path")
        ]

        if not valid_files:
            return old_content

        system = f"""
Tu es un rédacteur technique. Tu dois mettre à jour UNIQUEMENT la
section README "{section_name}", à partir de son contenu actuel et
des fichiers modifiés fournis.

Règles strictes :
- Base-toi UNIQUEMENT sur old_content et les fichiers fournis
  ci-dessous (chemin, type de changement, extrait de diff).
- N'invente jamais un fichier, une technologie, un endpoint API ou
  un élément d'architecture qui n'apparaît pas dans les preuves.
- Si old_content contient déjà une information toujours valide et
  qu'aucune preuve fournie ne la contredit ou ne l'enrichit,
  CONSERVE-la telle quelle : ne supprime rien sans preuve.
- N'ajoute une information que si elle est directement justifiée par
  un des fichiers/extraits fournis.
- Si les preuves fournies sont insuffisantes pour justifier un
  changement, retourne old_content sans modification.

{"Cette section est une LISTE d'éléments courts (pas de phrases)." if is_list_section else "Cette section est un texte libre pouvant contenir du Markdown (listes, gras, etc.)."}

Format de réponse strict :
- Réponds UNIQUEMENT avec un objet JSON valide, exactement cette clé :
  {{"content": {"[]" if is_list_section else '""'}}}
- Aucun texte avant ou après l'objet JSON. Aucune balise ```json.
- La valeur de "content" doit être {"une liste de chaînes courtes" if is_list_section else "une seule chaîne de texte"}, jamais un autre type.
{"" if is_list_section else '- Si le contenu tient sur plusieurs lignes ou paragraphes, échappe chaque retour à la ligne en \\n à l\'intérieur de la chaîne JSON — n\'insère jamais un vrai saut de ligne brut dans la valeur.'}
"""

        prompt = f"""
SECTION : {section_name}

CONTENU ACTUEL DE LA SECTION :
{self._format(old_content)}

FICHIERS MODIFIÉS PERTINENTS (chemins réels — n'en utilise aucun
autre, n'en invente aucun) :
{self._format(valid_files)}

Rédige le nouveau contenu de la section "{section_name}" en
respectant strictement les règles ci-dessus.
"""

        try:
            result = self._call_json(prompt, system=system)
        except AIServiceError as exc:
            logger.warning(
                "generate_section('%s'): échec Ollama, contenu "
                "inchangé conservé: %s",
                section_name,
                exc,
            )
            return old_content

        if not isinstance(result, dict):
            return old_content

        new_content = result.get("content")

        if is_list_section:
            if isinstance(new_content, list):
                cleaned = [
                    item.strip()
                    for item in new_content
                    if isinstance(item, str) and item.strip()
                ]
                return cleaned if cleaned else old_content
            return old_content

        if isinstance(new_content, str) and new_content.strip():
            return new_content.strip()

        return old_content

    # ============================================================
    # COMPACT CONTEXT BUILDER — hard cap on everything sent to Ollama
    # ============================================================

    MAX_TOTAL_PROMPT_CHARS = 15000

    MAX_IMPORTANT_FILES = 25
    MAX_ENTRY_POINTS = 15
    MAX_API_ENDPOINTS = 30
    MAX_FRONTEND_API_CALLS = 15
    MAX_CONFIGURATION_ITEMS = 8
    MAX_CONFIGURATION_CHARS_PER_ITEM = 400
    MAX_INSTALL_SCRIPTS = 5
    MAX_RUN_SCRIPTS = 5
    MAX_SCRIPT_CHARS_PER_ITEM = 300
    MAX_EVIDENCE_BLOCK_CHARS = 3000

    @classmethod
    def _cap_list(cls, value: Any, max_items: int) -> list[Any]:
        items = cls._source_list(value)
        return items[:max_items]

    @classmethod
    def _cap_evidence_items(
        cls,
        value: Any,
        max_items: int,
        max_chars_per_item: int,
    ) -> list[Any]:
        capped = []

        for item in cls._source_list(value)[:max_items]:

            if isinstance(item, dict) and isinstance(
                item.get("content"), str
            ):
                item = dict(item)
                item["content"] = item["content"][:max_chars_per_item]

            capped.append(item)

        return capped

    @classmethod
    def _cap_evidence_dict(
        cls,
        value: Any,
        max_chars: int,
    ) -> dict[str, Any]:
        """
        Borne un dict de preuves (installation_evidence/usage_evidence)
        à `max_chars` une fois sérialisé, en tronquant la
        représentation JSON — jamais en réécrivant/inventant son
        contenu. Retourne {} si la valeur n'est pas un dict.
        """

        if not isinstance(value, dict):
            return {}

        formatted = cls._format(value)

        if len(formatted) <= max_chars:
            return value

        # Repli déterministe : garde les clés telles quelles mais
        # tronque la représentation texte envoyée au prompt (le
        # rendu final passe toujours par _format côté prompt, donc
        # une troncature de la chaîne JSON est sûre ici — aucune
        # donnée n'est inventée, seule la longueur est réduite).
        truncated = formatted[:max_chars]
        return {"_truncated_evidence": truncated}

    def _build_compact_context(
        self,
        important_files: Any,
        entry_points: Any,
        api_endpoints: Any,
        frontend_api_calls: Any,
        configuration_evidence: Any,
        install_scripts: Any,
        run_scripts: Any,
        installation_evidence: Any = None,
        usage_evidence: Any = None,
    ) -> dict[str, Any]:

        return {
            "installation_evidence": self._cap_evidence_dict(
                installation_evidence, self.MAX_EVIDENCE_BLOCK_CHARS
            ),
            "usage_evidence": self._cap_evidence_dict(
                usage_evidence, self.MAX_EVIDENCE_BLOCK_CHARS
            ),
            "important_files": self._cap_list(
                important_files, self.MAX_IMPORTANT_FILES
            ),
            "entry_points": self._cap_list(
                entry_points, self.MAX_ENTRY_POINTS
            ),
            "api_endpoints": self._cap_list(
                api_endpoints, self.MAX_API_ENDPOINTS
            ),
            "frontend_api_calls": self._cap_list(
                frontend_api_calls, self.MAX_FRONTEND_API_CALLS
            ),
            "configuration_evidence": self._cap_evidence_items(
                configuration_evidence,
                self.MAX_CONFIGURATION_ITEMS,
                self.MAX_CONFIGURATION_CHARS_PER_ITEM,
            ),
            "install_scripts": self._cap_evidence_items(
                install_scripts,
                self.MAX_INSTALL_SCRIPTS,
                self.MAX_SCRIPT_CHARS_PER_ITEM,
            ),
            "run_scripts": self._cap_evidence_items(
                run_scripts,
                self.MAX_RUN_SCRIPTS,
                self.MAX_SCRIPT_CHARS_PER_ITEM,
            ),
        }

    # ============================================================
    # HARD PROMPT BUDGET ENFORCEMENT
    # ============================================================

    PROMPT_BUDGET_SAFETY_MARGIN = 300

    EVIDENCE_BUDGET_WEIGHTS = (
        ("important_files", 0.10),
        ("entry_points", 0.07),
        ("api_endpoints", 0.13),
        ("code_evidence", 0.30),
        ("frontend_api_calls", 0.07),
        ("configuration_evidence", 0.08),
        ("install_scripts", 0.05),
        ("run_scripts", 0.05),
        ("installation_evidence", 0.08),
        ("usage_evidence", 0.07),
    )

    def _render_readme_prompt(
        self,
        project_name: Any,
        languages: Any,
        frameworks: Any,
        dependencies: Any,
        architecture: Any,
        architecture_known: bool,
        important_files_f: Any,
        entry_points_f: Any,
        api_endpoints_f: Any,
        frontend_api_calls_f: Any,
        configuration_evidence_f: Any,
        install_scripts_f: Any,
        run_scripts_f: Any,
        code_evidence_text: str,
        installation_evidence_f: Any = None,
        usage_evidence_f: Any = None,
    ) -> str:
        """
        Construit le prompt README à partir de champs déjà bornés.

        `architecture_known` contrôle si le bloc ARCHITECTURE DÉTECTÉE
        est inclus : quand l'architecture n'est pas fiablement
        détectée par AnalyzerService, on ne l'injecte pas dans le
        prompt plutôt que d'envoyer un dict vide qui pousserait le
        LLM à deviner ou à écrire un texte de repli.
        """

        architecture_block = (
            f"""
ARCHITECTURE DÉTECTÉE :
{self._format(architecture)}
"""
            if architecture_known
            else ""
        )

        return f"""
Analyse le projet suivant et rédige une documentation technique
claire et explicative, destinée à un développeur qui découvre ce
projet pour la première fois. Ce projet est un projet réel, pas un
exemple générique : base-toi exclusivement sur les preuves
ci-dessous.

Nom du projet :
{self._format(project_name)}

LANGUAGES DÉTECTÉS :
{self._format(languages)}

FRAMEWORKS DÉTECTÉS :
{self._format(frameworks)}

DEPENDENCIES DÉTECTÉES :
{self._format(dependencies)}
{architecture_block}
IMPORTANT : ces informations proviennent directement de
AnalyzerService. Tu ne dois pas les remplacer, les corriger ou les
inventer.

FICHIERS IMPORTANTS (chemins réels — le champ "path" de chaque
module que tu écris DOIT correspondre exactement à l'un de ces
chemins ou à un chemin des preuves de code ci-dessous) :
{self._format(important_files_f)}

POINTS D'ENTRÉE DÉTECTÉS :
{self._format(entry_points_f)}

ENDPOINTS API DÉTECTÉS :
{self._format(api_endpoints_f)}

APPELS API FRONTEND (preuve indicative uniquement — ne crée jamais
un endpoint backend à partir de ceci) :
{self._format(frontend_api_calls_f)}

CONFIGURATION DÉTECTÉE :
{self._format(configuration_evidence_f)}

SCRIPTS D'INSTALLATION DÉTECTÉS :
{self._format(install_scripts_f)}

SCRIPTS D'EXÉCUTION DÉTECTÉS :
{self._format(run_scripts_f)}

INSTALLATION EVIDENCE (EVIDENCE AUTORITATIVE — provient directement
d'AnalyzerService : dépendances réelles, manifestes, scripts
d'installation, Dockerfile/docker-compose, .env.example et ses
variables, prérequis détectés avec certitude). Ceci est la SEULE
source autorisée pour rédiger la section installation. N'invente
jamais une commande, une variable .env, une version, une base de
données ou un service non présent ici :
{self._format(installation_evidence_f)}

USAGE EVIDENCE (EVIDENCE AUTORITATIVE — provient directement
d'AnalyzerService : points d'entrée, endpoints API, appels API
frontend, scripts d'exécution, configuration nécessaire). Ceci est
la SEULE source autorisée pour rédiger la section usage. N'invente
jamais un endpoint, une commande ou un exemple non prouvé ici :
{self._format(usage_evidence_f)}

PREUVES DE CODE (extraits réels du repository) :
{code_evidence_text or "Aucune preuve de code fournie."}

Rédige :

1. project_goal — l'objectif réel de CE projet, déduit des points
   d'entrée, endpoints, modules et extraits de code ci-dessus. Ne
   devine pas au-delà de ce que les preuves montrent.

2. general_operation — comment CE projet fonctionne concrètement.
   Explique le flux réel : comment une requête / une commande / une
   entrée utilisateur traverse les composants détectés (ex: quel
   fichier la reçoit, quel service ou module la traite, où va le
   résultat), UNIQUEMENT si ce flux est observable dans les preuves
   (endpoints, imports, appels de fonctions visibles dans les
   extraits de code, scripts). Si le flux exact n'est pas visible,
   décris seulement les interactions qui sont réellement montrées
   par les preuves, sans combler les trous.

3. main_modules — uniquement les modules réellement importants
   parmi les fichiers listés ci-dessus. Pour chaque module, fournis :
   - name
   - path (doit être un chemin EXACT parmi ceux fournis)
   - role : à quoi sert ce fichier concrètement et pourquoi il existe
     dans le projet (pas juste "fichier Python" ou "composant React" —
     explique sa responsabilité réelle telle qu'observable dans le
     code : ex. "gère les appels HTTP vers Ollama et la validation
     du JSON retourné")
   - classes, functions : uniquement celles visibles dans les preuves
     de code fournies pour ce fichier
   - dependencies : uniquement celles visibles dans les imports/usages
     réels du fichier
   - routes, blueprint : uniquement si visibles dans les preuves
   - interactions : décris brièvement, si observable dans le code,
     comment ce module appelle ou est appelé par d'autres modules
     listés ici (ex. imports, appels de fonctions, endpoints
     consommés) — laisse vide si non observable.
   N'invente jamais un fichier, une classe, une fonction ou une
   interaction non visible dans les preuves.

4. data_flow — décris le/les flux de données réellement observables
   entre les composants détectés (ex: frontend -> endpoint API ->
   service -> base de données/LLM), en te basant uniquement sur les
   preuves (endpoints, appels API frontend, imports, scripts). Sois
   concret et nomme les fichiers/endpoints impliqués. Si aucun flux
   n'est observable dans les preuves, écris exactement :
   "Flux non détecté."

5. recommendations — uniquement des problèmes réellement visibles
   dans les preuves (ex: absence de gestion d'erreur visible,
   dépendance non utilisée, duplication observable). Sinon : [].

6. installation — structure JSON PROPRE construite UNIQUEMENT à
   partir de INSTALLATION EVIDENCE ci-dessus. N'invente JAMAIS une
   commande d'installation, une variable .env, une base de données,
   un modèle Ollama, une version ou un prérequis absent des preuves.
   Ne retourne JAMAIS un dictionnaire Python brut : toutes les
   valeurs doivent être des chaînes ou des listes de chaînes déjà
   normalisées, prêtes à être affichées telles quelles dans un
   README Markdown. Champs possibles (omets un champ si aucune
   preuve ne le supporte — ne le remplis jamais par défaut) :
   - prerequisites : liste de chaînes (ex: "Python 3.11+")
   - backend_setup : liste de chaînes (étapes/commandes réelles)
   - frontend_setup : liste de chaînes (étapes/commandes réelles,
     uniquement si des preuves frontend existent)
   - configuration : liste de chaînes décrivant les variables .env
     ou fichiers de config réellement détectés
   - external_services : liste de chaînes (Ollama, base de données,
     Docker...) UNIQUEMENT si détectés dans les preuves
   - start_commands : liste de chaînes (commandes de démarrage
     réelles issues de install_scripts/run_scripts)
   Si INSTALLATION EVIDENCE est vide, retourne installation: {{}}.

7. usage — structure JSON PROPRE construite UNIQUEMENT à partir de
   USAGE EVIDENCE ci-dessus. Mêmes règles strictes que pour
   installation : jamais de dictionnaire Python brut, jamais
   d'endpoint ou de commande inventés. Champs possibles (omets un
   champ si aucune preuve ne le supporte) :
   - startup : liste de chaînes décrivant comment démarrer
     l'application (à partir des run_scripts/entry_points réels)
   - main_api : liste de chaînes décrivant les endpoints principaux
     réellement détectés (méthode + chemin)
   - example : liste de chaînes, UNIQUEMENT si une commande ou un
     appel est suffisamment prouvé pour constituer un exemple
     concret (sinon omets ce champ entièrement)
   - frontend_backend_flow : liste de chaînes décrivant le flux
     frontend/backend UNIQUEMENT s'il est observable dans
     frontend_api_calls
   Si USAGE EVIDENCE est vide, retourne usage: {{}}.

Retourne exactement :
{{
    "project_goal": "",
    "general_operation": "",
    "main_modules": [],
    "data_flow": "",
    "recommendations": [],
    "installation": {{}},
    "usage": {{}}
}}

Ne retourne aucune autre clé.
"""

    @classmethod
    def _truncate_list_field_to_budget(
        cls,
        items: Any,
        budget_chars: int,
    ) -> list[Any]:

        truncated = list(cls._source_list(items))

        if budget_chars <= 0:
            return []

        while truncated and len(cls._format(truncated)) > budget_chars:
            truncated.pop()

        if truncated and len(cls._format(truncated)) > budget_chars:
            return []

        return truncated

    @classmethod
    def _truncate_evidence_dict_to_budget(
        cls,
        evidence: Any,
        budget_chars: int,
    ) -> dict[str, Any]:
        """
        Variante de `_truncate_list_field_to_budget` pour les dicts
        de preuves (installation_evidence/usage_evidence) : réduit le
        dict clé par clé (jamais son contenu) jusqu'à tenir dans
        `budget_chars` une fois sérialisé. Ne réécrit ni n'invente
        aucune valeur — supprime uniquement des clés entières, en
        partant des moins prioritaires (dernières du dict).
        """

        if not isinstance(evidence, dict) or budget_chars <= 0:
            return {}

        truncated = dict(evidence)

        while truncated and len(cls._format(truncated)) > budget_chars:
            truncated.pop(next(reversed(truncated)))

        if truncated and len(cls._format(truncated)) > budget_chars:
            return {}

        return truncated

    @classmethod
    def _truncate_code_evidence_to_budget(
        cls,
        selected_code_files: list[dict[str, str]],
        budget_chars: int,
    ) -> tuple[list[dict[str, str]], str]:

        if budget_chars <= 0 or not selected_code_files:
            return [], ""

        kept: list[dict[str, str]] = []
        parts: list[str] = []
        remaining = budget_chars

        for selected in selected_code_files:

            header = f"--- {selected['path']} ---\n"
            content = selected["truncated_content"]
            separator_len = 2 if parts else 0

            block = header + content
            needed = len(block) + separator_len

            if needed <= remaining:
                parts.append(block)
                kept.append(selected)
                remaining -= needed
                continue

            available_for_content = remaining - separator_len - len(header)

            if available_for_content > 100:
                partial_content = content[:available_for_content]
                parts.append(header + partial_content)
                kept.append(
                    {
                        "path": selected["path"],
                        "truncated_content": partial_content,
                    }
                )

            break

        return kept, "\n\n".join(parts)

    def _allocate_evidence_budget(
        self,
        available_chars: int,
    ) -> dict[str, int]:

        available_chars = max(0, available_chars)

        return {
            name: int(available_chars * weight)
            for name, weight in self.EVIDENCE_BUDGET_WEIGHTS
        }

    def _enforce_final_prompt_budget(
        self,
        system: str,
        project_name: Any,
        languages: Any,
        frameworks: Any,
        dependencies: Any,
        architecture: Any,
        architecture_known: bool,
        important_files_f: list[Any],
        entry_points_f: list[Any],
        api_endpoints_f: list[Any],
        frontend_api_calls_f: list[Any],
        configuration_evidence_f: list[Any],
        install_scripts_f: list[Any],
        run_scripts_f: list[Any],
        code_evidence_text: str,
        installation_evidence_f: Optional[dict[str, Any]] = None,
        usage_evidence_f: Optional[dict[str, Any]] = None,
    ) -> tuple[str, int]:

        state: dict[str, Any] = {
            "important_files": important_files_f,
            "entry_points": entry_points_f,
            "api_endpoints": api_endpoints_f,
            "frontend_api_calls": frontend_api_calls_f,
            "configuration_evidence": configuration_evidence_f,
            "install_scripts": install_scripts_f,
            "run_scripts": run_scripts_f,
            "code_evidence_text": code_evidence_text,
            "installation_evidence": installation_evidence_f or {},
            "usage_evidence": usage_evidence_f or {},
        }

        shrink_order = (
            "code_evidence_text",
            "run_scripts",
            "install_scripts",
            "configuration_evidence",
            "frontend_api_calls",
            "api_endpoints",
            "entry_points",
            "important_files",
            "usage_evidence",
            "installation_evidence",
        )

        def render() -> tuple[str, int]:
            prompt = self._render_readme_prompt(
                project_name,
                languages,
                frameworks,
                dependencies,
                architecture,
                architecture_known,
                state["important_files"],
                state["entry_points"],
                state["api_endpoints"],
                state["frontend_api_calls"],
                state["configuration_evidence"],
                state["install_scripts"],
                state["run_scripts"],
                state["code_evidence_text"],
                state["installation_evidence"],
                state["usage_evidence"],
            )
            return prompt, len(system) + len(prompt)

        prompt, size = render()

        if size <= self.MAX_TOTAL_PROMPT_CHARS:
            return prompt, size

        logger.warning(
            "[README AI] Budget encore dépassé après allocation "
            "(%d > %d chars) — repli déterministe sur les sections "
            "de plus basse priorité.",
            size,
            self.MAX_TOTAL_PROMPT_CHARS,
        )

        for key in shrink_order:

            while size > self.MAX_TOTAL_PROMPT_CHARS and state[key]:

                if key == "code_evidence_text":
                    overflow = size - self.MAX_TOTAL_PROMPT_CHARS
                    current_text = state[key]
                    new_len = max(0, len(current_text) - overflow - 50)
                    state[key] = current_text[:new_len]
                elif key in ("installation_evidence", "usage_evidence"):
                    current_dict = dict(state[key])
                    if current_dict:
                        current_dict.pop(next(reversed(current_dict)))
                    state[key] = current_dict
                else:
                    current_list = list(state[key])
                    current_list.pop()
                    state[key] = current_list

                prompt, size = render()

            if size <= self.MAX_TOTAL_PROMPT_CHARS:
                break

        return prompt, size

    # ============================================================
    # ARCHITECTURE RELIABILITY CHECK
    # ============================================================
    #
    # AnalyzerService peut retourner un `architecture` vide ({}),
    # None, ou un dict "faible" (ex: {"type": "unknown"} ou sans
    # signal réel). Dans ces cas, le prompt ne doit ni recevoir de
    # bloc ARCHITECTURE DÉTECTÉE ni pousser le LLM à écrire une
    # section "Architecture" — et le résultat final ne doit pas non
    # plus contenir de placeholder du type "Architecture non
    # détectée.". On omet purement et simplement l'information
    # plutôt que d'inventer ou d'afficher un texte de repli.

    _WEAK_ARCHITECTURE_VALUES = {
        "",
        "unknown",
        "inconnue",
        "inconnu",
        "non détecté",
        "non détectée",
        "not detected",
        "undetected",
        "n/a",
        "none",
    }

    @classmethod
    def _is_architecture_reliably_detected(cls, architecture: Any) -> bool:
        """
        True uniquement si `architecture` transporte un signal réel
        provenant d'AnalyzerService (type non vide/non "unknown", ou
        au moins un champ non trivial dans un dict).
        """

        if architecture is None:
            return False

        if isinstance(architecture, str):
            return architecture.strip().lower() not in cls._WEAK_ARCHITECTURE_VALUES

        if isinstance(architecture, dict):
            if not architecture:
                return False

            arch_type = architecture.get("type") or architecture.get("name")

            if isinstance(arch_type, str) and (
                arch_type.strip().lower() in cls._WEAK_ARCHITECTURE_VALUES
            ):
                # type explicitement vide/inconnu : on regarde s'il
                # reste au moins un autre champ porteur de signal.
                other_signal = any(
                    value not in (None, "", [], {})
                    for key, value in architecture.items()
                    if key not in ("type", "name")
                )
                return other_signal

            return any(value not in (None, "", [], {}) for value in architecture.values())

        if isinstance(architecture, list):
            return len(architecture) > 0

        return bool(architecture)
     # ========================================================
    # RAW SIZE LOG — avant toute réduction
    # ========================================================
    
            

    def generate_full_readme(
        self,
        project_context: dict[str, Any],
        repository_id: Optional[str] = None,
    ) -> dict[str, Any]:
        print("🔥 NEW AI_SERVICE IS RUNNING")
        """
        Retourne STRICTEMENT les 10 clés de README_SCHEMA.

        Aucune autre clé (file_structure, important_files,
        install_scripts, run_scripts, configuration_evidence,
        frontend_api_calls, ...) n'est incluse dans la valeur de
        retour : ces données ne servent qu'à construire le prompt et
        restent des preuves internes, jamais du contenu README.

        Si l'architecture n'est pas fiablement détectée par
        AnalyzerService, `architecture` est retourné comme {} (dict
        vide) — jamais comme un texte de repli type "Architecture
        non détectée." — et le champ n'est pas non plus injecté dans
        le prompt envoyé au LLM. C'est au consommateur du README
        (ex: doc_builder / template Markdown) de ne pas afficher la
        section "Architecture" quand ce champ est vide.
        """

        if not isinstance(project_context, dict):
            raise TypeError(
                "project_context doit être un dictionnaire."
            )

        # ========================================================
        # RAW SIZE LOG — avant toute réduction
        # ========================================================

        try:
            raw_context_size = len(
                json.dumps(project_context, ensure_ascii=False, default=str)
            )
        except Exception:
            raw_context_size = -1

        logger.info(
            "[README AI] RAW PROJECT_CONTEXT SIZE: %d chars",
            raw_context_size,
        )

        project_name = project_context.get("project_name", "")
        languages = project_context.get("languages", {})
        frameworks = project_context.get("frameworks", [])
        dependencies = project_context.get("dependencies", {})
        file_structure = project_context.get("file_structure", {})
        important_files = project_context.get("important_files", [])
        entry_points = project_context.get("entry_points", [])
        code_evidence = project_context.get("code_evidence", [])
        api_endpoints = project_context.get("api_endpoints", [])
        frontend_api_calls = project_context.get("frontend_api_calls", [])
        configuration_evidence = project_context.get(
            "configuration_evidence", []
        )
        install_scripts = project_context.get("install_scripts", [])
        run_scripts = project_context.get("run_scripts", [])
        architecture = project_context.get("architecture", {})
        installation_evidence = project_context.get("installation_evidence", {})
        usage_evidence = project_context.get("usage_evidence", {})

        print("[README] INSTALLATION EVIDENCE (AI CONTEXT):", installation_evidence)
        print("[README] USAGE EVIDENCE (AI CONTEXT):", usage_evidence)
        print(
            "[README] DEPENDENCIES SENT TO AI:",
            installation_evidence.get("dependencies")
            if isinstance(installation_evidence, dict)
            else None,
        )

        logger.info(
            "[README] INSTALLATION EVIDENCE — repo_id=%s — %s",
            repository_id,
            installation_evidence,
        )
        logger.info(
            "[README] USAGE EVIDENCE — repo_id=%s — %s",
            repository_id,
            usage_evidence,
        )
        logger.info(
            "[README] DEPENDENCIES SENT TO AI — repo_id=%s — %s",
            repository_id,
            installation_evidence.get("dependencies")
            if isinstance(installation_evidence, dict)
            else None,
        )

        architecture_known = self._is_architecture_reliably_detected(
            architecture
        )

        logger.info(
            "[README AI] ARCHITECTURE RELIABLY DETECTED: %s",
            architecture_known,
        )

        # ========================================================
        # COMPACT CONTEXT — bornage de TOUS les champs de preuve
        # ========================================================

        compact = self._build_compact_context(
            important_files,
            entry_points,
            api_endpoints,
            frontend_api_calls,
            configuration_evidence,
            install_scripts,
            run_scripts,
            installation_evidence,
            usage_evidence,
        )

        important_files_compact = compact["important_files"]
        entry_points_compact = compact["entry_points"]
        api_endpoints_compact = compact["api_endpoints"]
        frontend_api_calls_compact = compact["frontend_api_calls"]
        configuration_evidence_compact = compact["configuration_evidence"]
        install_scripts_compact = compact["install_scripts"]
        run_scripts_compact = compact["run_scripts"]
        installation_evidence_compact = compact["installation_evidence"]
        usage_evidence_compact = compact["usage_evidence"]

        logger.info(
            "[README AI] FIELD SIZES (chars, after _build_compact_context) "
            "— project_name=%d languages=%d frameworks=%d "
            "dependencies=%d architecture=%d file_structure=%d",
            len(self._format(project_name)),
            len(self._format(languages)),
            len(self._format(frameworks)),
            len(self._format(dependencies)),
            len(self._format(architecture)),
            len(self._format(file_structure)),
        )

        logger.info(
            "[README AI] FIELD SIZES (chars, compact/bounded) — "
            "important_files_compact=%d entry_points_compact=%d "
            "api_endpoints_compact=%d frontend_api_calls_compact=%d "
            "configuration_evidence_compact=%d install_scripts_compact=%d "
            "run_scripts_compact=%d",
            len(self._format(important_files_compact)),
            len(self._format(entry_points_compact)),
            len(self._format(api_endpoints_compact)),
            len(self._format(frontend_api_calls_compact)),
            len(self._format(configuration_evidence_compact)),
            len(self._format(install_scripts_compact)),
            len(self._format(run_scripts_compact)),
        )

        # ========================================================
        # CODE EVIDENCE (uniquement pour construire le prompt)
        # ========================================================

        selected_code_files, total_code_evidence_files = (
            self._select_code_evidence_for_ollama(
                code_evidence,
                important_files,
                entry_points,
                self.max_code_evidence_files,
                self.max_code_evidence_chars_per_file,
            )
        )

        code_text_parts = [
            f"--- {selected['path']} ---\n{selected['truncated_content']}"
            for selected in selected_code_files
        ]

        code_evidence_text = "\n\n".join(code_text_parts)

        selected_code_evidence_size = len(code_evidence_text)

        logger.info(
            "[README AI] TOTAL CODE EVIDENCE FILES: %d",
            total_code_evidence_files,
        )
        logger.info(
            "[README AI] SELECTED FOR OLLAMA: %d",
            len(selected_code_files),
        )
        logger.info(
            "[README AI] MAX CHARS PER FILE: %d",
            self.max_code_evidence_chars_per_file,
        )
        logger.info(
            "[README AI] SELECTED CODE EVIDENCE SIZE: %d chars",
            selected_code_evidence_size,
        )

        if selected_code_files:
            selected_files_log = "\n".join(
                f"{index}. {selected['path']}"
                for index, selected in enumerate(selected_code_files, start=1)
            )
            logger.info(
                "[README AI] SELECTED CODE FILES:\n%s",
                selected_files_log,
            )

        # ========================================================
        # SYSTEM
        # ========================================================

        system = f"""
Tu es un expert en documentation technique. Ton objectif est
d'aider un développeur à comprendre RAPIDEMENT ce que fait ce
projet, comment il est organisé, et comment ses composants
interagissent — pas seulement lister des fichiers.

Tu dois rédiger une documentation claire, factuelle et SPÉCIFIQUE
au projet fourni, à partir UNIQUEMENT des preuves ci-dessous.

Interdiction absolue d'utiliser tes connaissances générales pour
décrire un projet "type" : chaque phrase doit pouvoir être justifiée
par une preuve fournie (nom de fichier, endpoint, dépendance,
extrait de code). Si tu ne peux pas justifier une affirmation par
une preuve, ne l'écris pas.

Pour chaque module important, explique CONCRÈTEMENT :
- ce qu'il fait (comportement observable dans le code) ;
- pourquoi il existe (son rôle dans le projet) ;
- sa responsabilité précise (pas une description générique du
  langage/framework) ;
- comment il interagit avec les autres composants détectés, si
  cette interaction est visible dans les preuves (imports, appels de
  fonctions, endpoints consommés/exposés).

Ne te contente jamais de répéter une liste de chemins de fichiers :
explique-les.

L'AnalyzerService est la source de vérité.

Tu ne dois PAS inventer :
- technologie ; framework ; dépendance ; fichier ; classe ; fonction ;
  route ; endpoint ; architecture ; point d'entrée ; flux.

Les champs suivants sont fournis directement par AnalyzerService
et NE DOIVENT PAS être générés ou modifiés par le modèle :
- technologies ; architecture ; entry_points ; api_endpoints ;
  important_dependencies.

Le modèle est responsable uniquement de :
- {", ".join(self.LLM_WRITTEN_FIELDS)}.

Pour les flux non observables, écrire exactement :
"Flux non détecté."

Les recommandations doivent uniquement signaler des problèmes
réellement visibles dans les preuves. Ne propose aucune migration,
nouvelle technologie, nouvelle architecture, nouvel outil ou
optimisation hypothétique.

Retourne uniquement un objet JSON valide, avec exactement ces clés :
{json.dumps(self.LLM_WRITTEN_FIELDS)}
"""

        # ========================================================
        # PROMPT — BEFORE BUDGET (diagnostic only)
        # ========================================================

        prompt_before_budget = self._render_readme_prompt(
            project_name,
            languages,
            frameworks,
            dependencies,
            architecture,
            architecture_known,
            important_files_compact,
            entry_points_compact,
            api_endpoints_compact,
            frontend_api_calls_compact,
            configuration_evidence_compact,
            install_scripts_compact,
            run_scripts_compact,
            code_evidence_text,
        )

        compact_context_before_budget = len(prompt_before_budget) + len(system)

        logger.info(
            "[README AI] COMPACT CONTEXT BEFORE BUDGET: %d chars "
            "(prompt=%d + system=%d)",
            compact_context_before_budget,
            len(prompt_before_budget),
            len(system),
        )

        # ========================================================
        # PROMPT — HARD BUDGET ENFORCEMENT
        # ========================================================

        skeleton_prompt = self._render_readme_prompt(
            project_name,
            languages,
            frameworks,
            dependencies,
            architecture,
            architecture_known,
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            "",
        )

        base_size = len(system) + len(skeleton_prompt)

        available_for_evidence = max(
            0,
            self.MAX_TOTAL_PROMPT_CHARS
            - base_size
            - self.PROMPT_BUDGET_SAFETY_MARGIN,
        )

        evidence_budgets = self._allocate_evidence_budget(
            available_for_evidence
        )

        logger.info(
            "[README AI] PROMPT BUDGET — base_size=%d (skeleton+identity) "
            "available_for_evidence=%d — allocation=%s",
            base_size,
            available_for_evidence,
            evidence_budgets,
        )

        important_files_final = self._truncate_list_field_to_budget(
            important_files_compact, evidence_budgets["important_files"]
        )
        entry_points_final = self._truncate_list_field_to_budget(
            entry_points_compact, evidence_budgets["entry_points"]
        )
        api_endpoints_final = self._truncate_list_field_to_budget(
            api_endpoints_compact, evidence_budgets["api_endpoints"]
        )
        frontend_api_calls_final = self._truncate_list_field_to_budget(
            frontend_api_calls_compact, evidence_budgets["frontend_api_calls"]
        )
        configuration_evidence_final = self._truncate_list_field_to_budget(
            configuration_evidence_compact,
            evidence_budgets["configuration_evidence"],
        )
        install_scripts_final = self._truncate_list_field_to_budget(
            install_scripts_compact, evidence_budgets["install_scripts"]
        )
        run_scripts_final = self._truncate_list_field_to_budget(
            run_scripts_compact, evidence_budgets["run_scripts"]
        )
        installation_evidence_final = self._truncate_evidence_dict_to_budget(
            installation_evidence_compact, evidence_budgets["installation_evidence"]
        )
        usage_evidence_final = self._truncate_evidence_dict_to_budget(
            usage_evidence_compact, evidence_budgets["usage_evidence"]
        )

        _kept_code_files, code_evidence_text_final = (
            self._truncate_code_evidence_to_budget(
                selected_code_files, evidence_budgets["code_evidence"]
            )
        )

        logger.info(
            "[README AI] FIELD SIZES (chars, AFTER budget) — "
            "important_files=%d entry_points=%d api_endpoints=%d "
            "frontend_api_calls=%d configuration_evidence=%d "
            "install_scripts=%d run_scripts=%d code_evidence=%d "
            "installation_evidence=%d usage_evidence=%d",
            len(self._format(important_files_final)),
            len(self._format(entry_points_final)),
            len(self._format(api_endpoints_final)),
            len(self._format(frontend_api_calls_final)),
            len(self._format(configuration_evidence_final)),
            len(self._format(install_scripts_final)),
            len(self._format(run_scripts_final)),
            len(code_evidence_text_final),
            len(self._format(installation_evidence_final)),
            len(self._format(usage_evidence_final)),
        )

        prompt = self._render_readme_prompt(
            project_name,
            languages,
            frameworks,
            dependencies,
            architecture,
            architecture_known,
            important_files_final,
            entry_points_final,
            api_endpoints_final,
            frontend_api_calls_final,
            configuration_evidence_final,
            install_scripts_final,
            run_scripts_final,
            code_evidence_text_final,
            installation_evidence_final,
            usage_evidence_final,
        )

        final_prompt_size = len(prompt) + len(system)

        if final_prompt_size > self.MAX_TOTAL_PROMPT_CHARS:
            prompt, final_prompt_size = self._enforce_final_prompt_budget(
                system,
                project_name,
                languages,
                frameworks,
                dependencies,
                architecture,
                architecture_known,
                important_files_final,
                entry_points_final,
                api_endpoints_final,
                frontend_api_calls_final,
                configuration_evidence_final,
                install_scripts_final,
                run_scripts_final,
                code_evidence_text_final,
                installation_evidence_final,
                usage_evidence_final,
            )

        # ========================================================
        # FINAL CONTEXT SIZE LOG — ce qui part réellement vers Ollama
        # ========================================================

        logger.info(
            "[README AI] FINAL OLLAMA CONTEXT SIZE: %d chars "
            "(prompt=%d + system=%d) — target=%d",
            final_prompt_size,
            len(prompt),
            len(system),
            self.MAX_TOTAL_PROMPT_CHARS,
        )

        print(
            f"[README] AI CONTEXT SIZE: {final_prompt_size} chars "
            f"(prompt={len(prompt)} + system={len(system)}) — "
            f"target={self.MAX_TOTAL_PROMPT_CHARS}"
        )
        logger.info(
            "[README] AI CONTEXT SIZE — repo_id=%s — %d chars",
            repository_id,
            final_prompt_size,
        )

        if final_prompt_size > self.MAX_TOTAL_PROMPT_CHARS:
            logger.error(
                "[README AI] FINAL CONTEXT (%d chars) DÉPASSE ENCORE LA "
                "CIBLE de %d chars malgré l'enforcement de budget — "
                "ceci ne devrait pas arriver, à investiguer.",
                final_prompt_size,
                self.MAX_TOTAL_PROMPT_CHARS,
            )

        logger.info(
            "README generation START — repo_id=%s — model=%s",
            repository_id,
            self.model,
        )

        # ========================================================
        # AI GENERATION (champs descriptifs uniquement)
        # ========================================================

        result = self._call_json(prompt, system=system)
        result = self._normalize_result(result)

        # ========================================================
        # TECHNOLOGIES — Analyzer ONLY (languages + frameworks)
        # ========================================================

        technologies: list[str] = []

        if isinstance(languages, dict):
            technologies.extend(
                key.strip()
                for key in languages.keys()
                if isinstance(key, str) and key.strip()
            )
        elif isinstance(languages, list):
            technologies.extend(
                item.strip()
                for item in languages
                if isinstance(item, str) and item.strip()
            )

        if isinstance(frameworks, list):
            technologies.extend(
                item.strip()
                for item in frameworks
                if isinstance(item, str) and item.strip()
            )
        elif isinstance(frameworks, dict):
            technologies.extend(
                key.strip()
                for key in frameworks.keys()
                if isinstance(key, str) and key.strip()
            )

        technologies = list(dict.fromkeys(technologies))

        # ========================================================
        # MAIN MODULES — validated against Analyzer evidence
        # ========================================================

        main_modules = self._build_main_modules(
            important_files,
            code_evidence,
            result.get("main_modules"),
        )

        if not important_files and not code_evidence:
            main_modules = []

        # ========================================================
        # Analyzer-only factual fields (verbatim, never touched)
        # ========================================================

        final_entry_points = list(
            entry_points if isinstance(entry_points, list) else []
        )

        final_api_endpoints = list(
            api_endpoints if isinstance(api_endpoints, list) else []
        )

        final_dependencies = (
            dependencies if isinstance(dependencies, (dict, list)) else {}
        )

        # Architecture : {} si non fiablement détectée. Jamais de
        # texte de repli type "Architecture non détectée." — c'est
        # au rendu (doc_builder / template) de simplement omettre la
        # section quand ce champ est vide.
        final_architecture = (
            architecture
            if architecture_known and isinstance(architecture, (dict, list, str))
            else {}
        )

        # ========================================================
        # INSTALLATION / USAGE — rédigés par le LLM à partir des
        # evidences autoritatives, puis nettoyés en données JSON
        # propres (jamais de dict Python brut affiché tel quel).
        # ========================================================

        final_installation = self._clean_structured_section(
            result.get("installation")
        )
        final_usage = self._clean_structured_section(
            result.get("usage")
        )

        # ========================================================
        # FINAL RESULT — strictly README_SCHEMA, nothing else
        # ========================================================

        final_result = {
            "project_goal": result.get("project_goal", ""),
            "general_operation": result.get("general_operation", ""),
            "architecture": final_architecture,
            "technologies": technologies,
            "main_modules": main_modules,
            "data_flow": result.get("data_flow", ""),
            "entry_points": final_entry_points,
            "api_endpoints": final_api_endpoints,
            "important_dependencies": final_dependencies,
            "recommendations": result.get("recommendations", []),
            "installation": final_installation,
            "usage": final_usage,
        }

        assert set(final_result.keys()) == set(self.README_SCHEMA), (
            "generate_full_readme a produit un schéma inattendu: "
            f"{sorted(final_result.keys())}"
        )

        logger.info(
            "[README] FINAL FACTS — repo_id=%s — technologies=%d — "
            "entry_points=%d — api_endpoints=%d — dependencies=%d — "
            "main_modules=%d — architecture_known=%s — "
            "installation_keys=%d — usage_keys=%d",
            repository_id,
            len(final_result["technologies"]),
            len(final_result["entry_points"]),
            len(final_result["api_endpoints"]),
            len(final_result["important_dependencies"]),
            len(final_result["main_modules"]),
            architecture_known,
            len(final_result["installation"]),
            len(final_result["usage"]),
        )

        print(
            f"[README] INSTALLATION (FINAL): {final_result['installation']}"
        )
        print(f"[README] USAGE (FINAL): {final_result['usage']}")

        logger.info(
            "README generation COMPLETE — repo_id=%s",
            repository_id,
        )

        return final_result
