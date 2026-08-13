"""
Commit Detector — point d'entrée unique, agnostique de la source
(webhook ou polling). Responsable de :
- idempotency (ne pas retraiter un commit déjà traité)
- anti-loop (ignorer les commits du bot lui-même)
- déclenchement du pipeline Git Service → Diff Analyzer → Sync Orchestrator

Root-cause fixes appliqués ici (bugs trouvés en traçant le workflow
webhook -> pending_update, jamais exécuté avec succès jusqu'ici) :
- repository_repository.get(...) n'existe pas -> get_by_id(...)
- repo.owner n'existe pas -> repo.user (nom réel de la relation)
- commit_repository.mark_processed() attend l'objet Commit, pas un id
- commit_repository.save_file_changes()/save_detected_change() n'existaient
  pas : ils sont remplacés par de vrais appels aux repositories dédiés
  (FileChangeRepository, DetectedChangeRepository), qui comblent un vide
  déjà présent dans l'architecture (modèles FileChange/DetectedChange
  existants mais jamais persistés faute de repository).
- Le DetectedChange retourné par DiffAnalyzerService est un dataclass en
  mémoire (pas de DB id) ; PendingUpdate.detected_change_id est une FK
  réelle vers detected_changes.id. Ce commit_detector persiste maintenant
  le dataclass avant de le transmettre à SyncOrchestrator, pour que l'id
  utilisé plus loin soit un vrai id de ligne DB
  j dnddjdjc nnnnnnnnnnnn mancbhgty chh cloodkcns ,cmkban ,ksmeryamd, nbcs.
"""

import logging
from dataclasses import dataclass

from app.services.git_service import GitService, GitServiceError
from app.services.diff_analyzer_service import DiffAnalyzerService
from app.services.sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

BOT_AUTHOR_EMAIL = "readme-bot@yourapp.io"
EXCLUDED_DIFF_PATHS = ["README.md", "readme.md"]


@dataclass
class PushEvent:
    repository_id: str
    before_sha: str
    after_sha: str
    author_email: str
    author_name: str
    branch: str


class CommitDetectorError(Exception):
    pass


class CommitDetector:
    def __init__(
        self,
        git_service: GitService,
        diff_analyzer: DiffAnalyzerService,
        sync_orchestrator: SyncOrchestrator,
        commit_repository,
        repository_repository,
        detected_change_repository,
        file_change_repository,
    ):
        self.git_service = git_service
        self.diff_analyzer = diff_analyzer
        self.sync_orchestrator = sync_orchestrator
        self.commit_repository = commit_repository
        self.repository_repository = repository_repository
        self.detected_change_repository = detected_change_repository
        self.file_change_repository = file_change_repository

    def handle_push_event(self, event: PushEvent) -> dict:
        """
        Point d'entrée unique — appelé par webhooks.py OU polling_task.py.
        Retourne un résumé de ce qui a été fait (utile pour logs/debug).
        """
        print(f"[COMMIT] handle_push_event repo_id={event.repository_id} "
              f"before={event.before_sha} after={event.after_sha} branch={event.branch}")

        repo = self.repository_repository.get_by_id(event.repository_id)
        if repo is None:
            raise CommitDetectorError(f"Repository {event.repository_id} introuvable.")

        # 1. Filtre de branche
        tracked = repo.tracked_branch or repo.default_branch
        if event.branch != tracked:
            print(f"[COMMIT] Push sur branche non suivie ({event.branch} != {tracked}), ignoré.")
            return {"status": "ignored", "reason": "branch_not_tracked"}

        # 2. Anti-loop : commit du bot lui-même
        if self._is_bot_author(event.author_email):
            print(f"[COMMIT] Commit du bot détecté ({event.author_email}), ignoré (anti-loop).")
            return {"status": "ignored", "reason": "bot_commit"}

        # 3. Idempotency : commit déjà traité ?
        if self.commit_repository.exists(repo.id, event.after_sha):
            print(f"[COMMIT] Commit {event.after_sha} déjà traité, ignoré (idempotency).")
            return {"status": "ignored", "reason": "already_processed"}

        if not repo.local_clone_path:
            # Le repo n'a jamais été cloné (aucun /generate initial exécuté) :
            # rien à fetch/diff. On le signale clairement plutôt que de
            # planter dans git_service avec un chemin None.
            print(f"[COMMIT] Repository {repo.id} n'a pas de local_clone_path — "
                  f"lancez /generate au moins une fois avant d'activer la sync.")
            return {"status": "ignored", "reason": "not_cloned_yet"}

        # 4. Enregistrement du commit
        commit = self.commit_repository.create(
            repository_id=repo.id,
            sha=event.after_sha,
            parent_sha=event.before_sha,
            author_name=event.author_name,
            author_email=event.author_email,
            is_bot_commit=False,
        )
        print(f"[COMMIT] Commit enregistré id={commit.id} sha={event.after_sha}")

        # 5. Fetch + diff via Git Service
        try:
            self.git_service.fetch(repo.local_clone_path, auth_token=self._get_auth_token(repo))
            file_changes = self.git_service.get_diff(
                repo.local_clone_path,
                before_sha=event.before_sha,
                after_sha=event.after_sha,
                exclude_paths=EXCLUDED_DIFF_PATHS,
            )
        except GitServiceError as e:
            print(f"[COMMIT] ERREUR git fetch/diff pour commit {event.after_sha}: {e}")
            logger.error(f"Échec git fetch/diff pour commit {event.after_sha}: {e}")
            # Pas de colonne DB pour un statut "failed" (on ne modifie pas le
            # schéma) : le commit reste non-marqué "processed", ce qui le
            # laisse visible via find_unprocessed() pour investigation/retry.
            return {"status": "error", "reason": "git_failure", "detail": str(e)}

        print(f"[CHANGE DETECTION START] Repository: {repo.full_name} "
              f"Before: {event.before_sha} After: {event.after_sha}")

        if not file_changes:
            print("[CHANGE DETECTION] Aucun fichier pertinent modifié.")
            self.commit_repository.mark_processed(commit)
            return {"status": "no_relevant_changes"}

        print(f"[CHANGE DETECTION] Files changed: {len(file_changes)}")

        # 6. Persist file_changes (comble le vide : modèle existait, jamais écrit)
        self.file_change_repository.create_bulk(commit.id, file_changes)

        # 7. Diff Analyzer (calcul en mémoire, ne persiste rien lui-même)
        detected_change_data = self.diff_analyzer.analyze(
            commit_id=commit.id,
            file_changes=file_changes,
            repo_context=repo.full_name,
        )

        # Persistance réelle en DB — obligatoire car PendingUpdate.detected_change_id
        # est une FK vers une vraie ligne detected_changes, pas un id en mémoire.
        detected_change_row = self.detected_change_repository.create(
            commit_id=commit.id,
            impact_category=detected_change_data.impact_category,
            affected_sections=detected_change_data.affected_sections,
            confidence_score=detected_change_data.confidence_score,
        )
        # On garde le dataclass pour les besoins en mémoire de SyncOrchestrator
        # (affected_sections, file_changes) mais on remplace commit_id par
        # l'id réel utilisable en FK pour la création du PendingUpdate.
        detected_change_data.commit_id = commit.id
        print(f"[CHANGE DETECTION] Detected changes: 1 (db_id={detected_change_row.id}, "
              f"impact={detected_change_data.impact_category}, "
              f"sections={detected_change_data.affected_sections})")

        # 8. Sync Orchestrator prend le relais (decide manual vs automatic)
        result = self.sync_orchestrator.process(
            repo.id, detected_change_data, detected_change_db_id=detected_change_row.id
        )

        self.commit_repository.mark_processed(commit)

        return {"status": "processed", "orchestrator_result": result}

    def _is_bot_author(self, author_email: str) -> bool:
        return (author_email or "").lower() == BOT_AUTHOR_EMAIL.lower()

    def _get_auth_token(self, repo) -> str | None:
        # repo.user est le nom réel de la relation (voir models/repository.py) ;
        # "repo.owner" n'existe pas et levait AttributeError avant ce fix.
        return getattr(repo.user, "github_token", None)
