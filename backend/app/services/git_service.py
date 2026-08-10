"""
Git Service — wrapper autour de GitPython.

Responsable de toutes les opérations git bas niveau :
clone, fetch, diff, commit, push.

Ce service ne connaît AUCUNE logique métier (pas d'IA, pas de notion
de "section README", pas de sync_mode). Il expose des primitives
réutilisables par Repository Service (clone initial) et par
Commit Detector / Sync Orchestrator (fetch, diff, commit, push).
"""

from __future__ import annotations

import logging
import os
import shutil
import stat
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse

from git import Repo, GitCommandError, Actor
from git.exc import InvalidGitRepositoryError, NoSuchPathError


logger = logging.getLogger(__name__)


class GitServiceError(Exception):
    """Levée pour toute erreur d'opération git."""
    pass


@dataclass
class FileChange:
    path: str
    change_type: str  # 'added' | 'modified' | 'deleted' | 'renamed'
    diff_excerpt: str  # extrait du patch, tronqué


class GitService:
    def __init__(self, clones_base_dir: str = "/data/repo_clones"):
        """
        Initialise le service Git.

        Le chemin est normalisé en chemin absolu afin d'éviter les
        problèmes de chemins relatifs, notamment sous Windows.
        """
        self.clones_base_dir = os.path.normpath(
            os.path.abspath(clones_base_dir)
        )

        os.makedirs(
            self.clones_base_dir,
            exist_ok=True,
        )

    # ============================================================
    # URL HELPERS
    # ============================================================

    def normalize_git_url(self, url: str) -> str:
        """
        Normalise une URL Git pour pouvoir comparer correctement
        une URL publique avec une URL contenant un token.

        Exemple :

        https://github.com/user/repo.git

        et

        https://x-access-token:TOKEN@github.com/user/repo.git

        deviennent toutes les deux :

        https://github.com/user/repo.git
        """
        if not url:
            return ""

        try:
            parsed = urlparse(url.strip())

            hostname = parsed.hostname or ""

            hostname = hostname.lower()

            # Conserver le port uniquement s'il existe.
            netloc = hostname

            try:
                if parsed.port:
                    netloc = f"{hostname}:{parsed.port}"
            except ValueError:
                # URL malformée avec port invalide.
                netloc = hostname

            path = parsed.path.rstrip("/")

            # On supprime volontairement :
            # - username
            # - password/token
            # - query
            # - fragment
            return urlunparse(
                (
                    parsed.scheme.lower(),
                    netloc,
                    path,
                    "",
                    "",
                    "",
                )
            )

        except Exception:
            # Fallback simple si l'URL est inhabituelle.
            return url.split("@")[-1].rstrip("/")

    def _build_authenticated_url(
        self,
        github_url: str,
        auth_token: Optional[str],
    ) -> str:
        """
        Construit une URL HTTPS authentifiée pour GitHub.

        Le token n'est jamais retourné dans les logs.
        """
        if not auth_token:
            return github_url

        if github_url.startswith("https://"):
            return github_url.replace(
                "https://",
                f"https://x-access-token:{auth_token}@",
                1,
            )

        return github_url

    # ============================================================
    # CLONE
    # ============================================================

    def clone_repository(
        self,
        github_url: str,
        repository_id: str,
        auth_token: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> str:
        """
        Clone un repository GitHub localement.

        Retourne le chemin local du clone.

        auth_token:
            Nécessaire pour les repositories privés.

        branch:
            Si fournie, elle est utilisée.
            Sinon, la vraie branche par défaut est détectée.
        """

        local_path = os.path.normpath(
            os.path.join(
                self.clones_base_dir,
                str(repository_id),
            )
        )

        # IMPORTANT :
        # Ne jamais afficher auth_token ou clone_url authentifiée.
        print(
            f"📥 [GIT] CLONE START — "
            f"repo_id={repository_id} — "
            f"url={self.normalize_git_url(github_url)} — "
            f"branch_demandée={branch or '(auto-détection)'}"
        )

        # Supprimer un ancien clone.
        if os.path.exists(local_path):
            logger.warning(
                "Clone déjà existant pour %s, suppression avant re-clone.",
                repository_id,
            )

            print(
                f"🗑️ [GIT] SUPPRESSION ANCIEN CLONE — "
                f"repo_id={repository_id}"
            )

            self._remove_directory(local_path)

        # Construire URL authentifiée uniquement en mémoire.
        clone_url = self._build_authenticated_url(
            github_url,
            auth_token,
        )

        # Déterminer la branche.
        target_branch = branch

        if not target_branch:
            target_branch = self._detect_default_branch(
                github_url=github_url,
                clone_url=clone_url,
                repository_id=repository_id,
            )

        try:
            kwargs = {}

            if target_branch:
                kwargs["branch"] = target_branch

            Repo.clone_from(
                clone_url,
                local_path,
                **kwargs,
            )

        except GitCommandError as exc:
            print(
                f"❌ [GIT] CLONE ERROR — "
                f"repo_id={repository_id} — "
                f"branch='{target_branch}'"
            )

            logger.error(
                "Échec du clone pour %s: %s",
                self.normalize_git_url(github_url),
                exc,
            )

            self._remove_directory(local_path)

            error_text = str(exc).lower()

            if target_branch and "not found" in error_text:
                raise GitServiceError(
                    f"La branche '{target_branch}' "
                    f"n'existe pas sur {self.normalize_git_url(github_url)}."
                ) from exc

            raise GitServiceError(
                f"Impossible de cloner le repository: {exc}"
            ) from exc

        except Exception as exc:
            print(
                f"❌ [GIT] CLONE ERROR — "
                f"repo_id={repository_id} — "
                f"branch='{target_branch}'"
            )

            logger.exception(
                "Erreur inattendue pendant le clone de %s",
                self.normalize_git_url(github_url),
            )

            self._remove_directory(local_path)

            raise GitServiceError(
                f"Impossible de cloner le repository: {exc}"
            ) from exc

        print(
            f"✅ [GIT] CLONE TERMINÉ — "
            f"repo_id={repository_id} — "
            f"path={local_path} — "
            f"branch={target_branch or '(défaut du remote)'}"
        )

        return local_path

    # ============================================================
    # DEFAULT BRANCH
    # ============================================================

    def _detect_default_branch(
        self,
        github_url: str,
        clone_url: str,
        repository_id: str,
    ) -> Optional[str]:
        """
        Détecte la branche par défaut du repository distant via :

        git ls-remote --symref URL HEAD

        Retourne None si la détection échoue.
        """

        print(
            f"🌿 [GIT] BRANCH DETECT START — "
            f"repo_id={repository_id} — "
            f"url={self.normalize_git_url(github_url)}"
        )

        try:
            from git import cmd as git_cmd

            output = git_cmd.Git().ls_remote(
                "--symref",
                clone_url,
                "HEAD",
            )

            for line in output.splitlines():
                if line.startswith("ref:"):
                    parts = line.split()

                    if len(parts) < 2:
                        continue

                    ref = parts[1]

                    if ref.startswith("refs/heads/"):
                        detected = ref.rsplit("/", 1)[-1]

                        print(
                            f"🌿 [GIT] DEFAULT BRANCH — "
                            f"repo_id={repository_id} — "
                            f"branch={detected}"
                        )

                        return detected

        except Exception as exc:
            logger.warning(
                "Détection branche par défaut échouée pour %s: %s",
                self.normalize_git_url(github_url),
                exc,
            )

            print(
                f"🌿 [GIT] DEFAULT BRANCH — "
                f"repo_id={repository_id} — "
                f"détection impossible, clone sans --branch explicite"
            )

        return None

    # ============================================================
    # REMOVE DIRECTORY
    # ============================================================

    def _remove_directory(
        self,
        path: str,
        retries: int = 5,
        delay: float = 0.2,
    ) -> None:
        """
        Supprime récursivement un dossier.

        Gère notamment les fichiers read-only de .git sous Windows.
        """

        if not os.path.exists(path):
            return

        def _on_rm_error(
            func,
            target_path,
            exc_info,
        ):
            try:
                os.chmod(
                    target_path,
                    stat.S_IWRITE,
                )

                func(target_path)

            except Exception:
                pass

        for attempt in range(retries):
            try:
                shutil.rmtree(
                    path,
                    onerror=_on_rm_error,
                )
            except Exception as exc:
                logger.warning(
                    "Tentative %s/%s de suppression échouée pour %s: %s",
                    attempt + 1,
                    retries,
                    path,
                    exc,
                )

            if not os.path.exists(path):
                return

            time.sleep(delay)

        if os.path.exists(path):
            raise GitServiceError(
                "Impossible de supprimer complètement "
                f"l'ancien répertoire de clone '{path}' "
                "(fichiers verrouillés ou permissions insuffisantes)."
            )

    # ============================================================
    # FETCH
    # ============================================================

    def fetch(
        self,
        local_path: str,
        auth_token: Optional[str] = None,
    ) -> None:
        """
        Récupère les derniers commits depuis le remote,
        sans les fusionner.
        """

        repo = self._open_repo(local_path)

        try:
            origin = repo.remotes.origin

            if auth_token:
                self._inject_token_in_remote(
                    repo,
                    auth_token,
                )

            origin.fetch()

        except GitCommandError as exc:
            logger.error(
                "Échec du fetch sur %s: %s",
                local_path,
                exc,
            )

            raise GitServiceError(
                f"Impossible de fetch le repository: {exc}"
            ) from exc

    def _inject_token_in_remote(
        self,
        repo: Repo,
        auth_token: str,
    ) -> None:
        """
        Injecte temporairement le token dans l'URL du remote.

        Le token n'est jamais affiché dans les logs.
        """

        origin_url = repo.remotes.origin.url

        if not origin_url.startswith("https://"):
            return

        # Éviter de réinjecter plusieurs fois.
        if "x-access-token" in origin_url:
            return

        authenticated_url = origin_url.replace(
            "https://",
            f"https://x-access-token:{auth_token}@",
            1,
        )

        repo.remotes.origin.set_url(
            authenticated_url
        )

    # ============================================================
    # VERIFY REMOTE
    # ============================================================

    def verify_remote_url(
        self,
        local_path: str,
        expected_url: str,
    ) -> bool:
        """
        Vérifie que le clone local correspond bien au repository attendu.

        IMPORTANT :
        Cette comparaison ignore volontairement les credentials
        présents dans l'URL Git.

        Exemple :

        expected:
            https://github.com/user/repo.git

        origin:
            https://x-access-token:TOKEN@github.com/user/repo.git

        => True
        """

        repo = self._open_repo(local_path)

        try:
            origin_url = repo.remotes.origin.url
        except Exception as exc:
            raise GitServiceError(
                f"Impossible de récupérer l'origin du clone: {exc}"
            ) from exc

        normalized_expected = self.normalize_git_url(
            expected_url
        )

        normalized_origin = self.normalize_git_url(
            origin_url
        )

        if normalized_expected != normalized_origin:
            logger.error(
                "Remote mismatch: demandé=%s vs origin=%s",
                normalized_expected,
                normalized_origin,
            )

            return False

        return True

    # ============================================================
    # DIFF
    # ============================================================

    def get_diff(
        self,
        local_path: str,
        before_sha: str,
        after_sha: str,
        exclude_paths: Optional[list[str]] = None,
    ) -> list[FileChange]:
        """
        Calcule le diff entre deux commits.

        exclude_paths:
            Fichiers à ignorer systématiquement.
            Exemple : README.md pour éviter que le bot
            ne s'auto-déclenche.
        """

        repo = self._open_repo(local_path)

        exclude_paths = exclude_paths or []

        try:
            diff_index = repo.git.diff(
                before_sha,
                after_sha,
                name_status=True,
            )

        except GitCommandError as exc:
            logger.error(
                "Échec du diff %s..%s sur %s: %s",
                before_sha,
                after_sha,
                local_path,
                exc,
            )

            raise GitServiceError(
                f"Impossible de calculer le diff: {exc}"
            ) from exc

        changes: list[FileChange] = []

        for line in diff_index.splitlines():
            if not line.strip():
                continue

            parts = line.split("\t")

            status_code = parts[0]

            file_path = parts[-1]

            if file_path in exclude_paths:
                continue

            change_type = self._map_status_code(
                status_code
            )

            diff_excerpt = self._get_file_patch(
                repo,
                before_sha,
                after_sha,
                file_path,
            )

            changes.append(
                FileChange(
                    path=file_path,
                    change_type=change_type,
                    diff_excerpt=diff_excerpt,
                )
            )

        return changes

    def _map_status_code(
        self,
        code: str,
    ) -> str:
        """
        Convertit le status Git en type métier simple.
        """

        mapping = {
            "A": "added",
            "M": "modified",
            "D": "deleted",
            "R": "renamed",
        }

        if not code:
            return "modified"

        if code.startswith("R"):
            return "renamed"

        return mapping.get(
            code[0],
            "modified",
        )

    def _get_file_patch(
        self,
        repo: Repo,
        before_sha: str,
        after_sha: str,
        file_path: str,
        max_chars: int = 1500,
    ) -> str:
        """
        Récupère le patch détaillé d'un fichier.

        Le résultat est tronqué afin de limiter la taille
        envoyée plus tard aux services d'analyse.
        """

        try:
            patch = repo.git.diff(
                before_sha,
                after_sha,
                "--",
                file_path,
            )

            return patch[:max_chars]

        except GitCommandError:
            return ""

    # ============================================================
    # COMMIT + PUSH
    # ============================================================

    def commit_and_push(
        self,
        local_path: str,
        file_paths: list[str],
        commit_message: str,
        author_name: str = "readme-bot",
        author_email: str = "readme-bot@yourapp.io",
        branch: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> str:
        """
        git add + commit + push.

        Retourne le SHA du nouveau commit.

        Le bot utilise une identité dédiée afin que le Commit Detector
        puisse éventuellement ignorer ses propres commits.
        """

        repo = self._open_repo(local_path)

        try:
            repo.index.add(file_paths)

            # Aucun changement.
            if not repo.index.diff("HEAD"):
                logger.info(
                    "Aucun changement à committer."
                )

                return repo.head.commit.hexsha

            # Identité Git du bot.
            author = Actor(
                author_name,
                author_email,
            )

            # Création du commit.
            commit = repo.index.commit(
                commit_message,
                author=author,
                committer=author,
            )

            # Ajouter le token uniquement pour le push.
            if auth_token:
                self._inject_token_in_remote(
                    repo,
                    auth_token,
                )

            origin = repo.remotes.origin

            if branch:
                target_branch = branch
            else:
                try:
                    target_branch = repo.active_branch.name
                except TypeError:
                    target_branch = repo.head.reference.name

            origin.push(
                refspec=(
                    f"HEAD:refs/heads/{target_branch}"
                )
            )

            logger.info(
                "Commit + push réussi: %s",
                commit.hexsha,
            )

            return commit.hexsha

        except GitCommandError as exc:
            logger.error(
                "Échec commit/push sur %s: %s",
                local_path,
                exc,
            )

            raise GitServiceError(
                f"Impossible de committer/pusher: {exc}"
            ) from exc

    def _open_repo(
        self,
        local_path: str,
    ) -> Repo:
        """
        Ouvre un repository Git local.
        """

        try:
            return Repo(local_path)

        except (
            InvalidGitRepositoryError,
            NoSuchPathError,
        ) as exc:
            raise GitServiceError(
                f"Clone local introuvable ou invalide: {local_path}"
            ) from exc


    def get_current_head_sha(
        self,
        local_path: str,
    ) -> str:
        """
        Retourne le SHA du commit HEAD actuel.
        """

        repo = self._open_repo(local_path)

        return repo.head.commit.hexsha

