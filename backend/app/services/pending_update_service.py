"""
Pending Update Service — CRUD et transitions d'état sur pending_updates.

Ce service ne contient aucune logique d'orchestration (pas d'appel git,
pas d'appel IA) — il gère uniquement le cycle de vie des propositions.
C'est Sync Orchestrator qui décide QUAND créer/approuver/rejeter ;
ce service décide COMMENT ces transitions sont persistées et validées.

Root-cause fixes appliqués ici (méthodes appelées qui n'existaient pas
sur PendingUpdateRepository — jamais exécuté avec succès jusqu'ici) :
- self.repo.get(id) -> get_by_id(id) (méthode réelle héritée de BaseRepository)
- self.repo.list_by_repository(...) -> find_by_repository(...)
- self.repo.update(id, status=..., ...) n'existe pas du tout : le repository
  réel expose des transitions dédiées (approve/reject/mark_stale) qui
  prennent l'INSTANCE PendingUpdate, pas son id — remplacé en conséquence.
- create(..., status="pending", created_at=...) : le repository réel ne
  déclare pas ces paramètres explicitement (le modèle les défaut déjà via
  PendingUpdateStatus.pending et utcnow()) ; les passer forçait un type
  incompatible (str "pending" vs colonne Enum). Retirés, les defaults du
  modèle s'appliquent normalement.
"""

import logging

logger = logging.getLogger(__name__)


class PendingUpdateError(Exception):
    pass


class PendingUpdateNotFoundError(PendingUpdateError):
    pass


class InvalidStatusTransitionError(PendingUpdateError):
    pass


VALID_STATUSES = {"pending", "approved", "rejected", "stale"}
TERMINAL_STATUSES = {"approved", "rejected", "stale"}


class PendingUpdateService:
    def __init__(self, pending_update_repository):
        """
        pending_update_repository : couche d'accès DB réelle
        (app.repositories.pending_update_repository.PendingUpdateRepository),
        injectée pour garder ce service testable sans DB réelle.
        """
        self.repo = pending_update_repository

    # ------------------------------------------------------------------
    # Création
    # ------------------------------------------------------------------
    def create(
        self,
        repository_id: str,
        commit_id: str,
        detected_change_id: str,
        base_readme_version_id: str,
        sections_diff: dict,
        proposed_content_md: str,
        proposed_sections_json: dict,
    ):
        pending_update = self.repo.create(
            repository_id=repository_id,
            commit_id=commit_id,
            detected_change_id=detected_change_id,
            base_readme_version_id=base_readme_version_id,
            sections_diff=sections_diff,
            proposed_content_md=proposed_content_md,
            proposed_sections_json=proposed_sections_json,
        )
        logger.info(f"PendingUpdate créé: {pending_update.id} pour repo {repository_id}")
        return pending_update

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------
    def get(self, pending_update_id: str):
        pending_update = self.repo.get_by_id(pending_update_id)
        if pending_update is None:
            raise PendingUpdateNotFoundError(f"PendingUpdate {pending_update_id} introuvable.")
        return pending_update

    def list_for_repository(self, repository_id: str, status=None) -> list:
        return self.repo.find_by_repository(repository_id, status=status)

    def get_active_pending(self, repository_id: str):
        """Retourne la proposition en statut 'pending' pour ce repo, s'il en existe une."""
        results = self.repo.find_pending_for_repository(repository_id)
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Transitions d'état
    # ------------------------------------------------------------------
    def mark_approved(self, pending_update_id: str, user_id: str):
        pending_update = self._require_pending_status(pending_update_id)
        return self.repo.approve(pending_update, resolved_by=user_id)

    def mark_rejected(self, pending_update_id: str, user_id: str, reason: str | None = None):
        pending_update = self._require_pending_status(pending_update_id)
        return self.repo.reject(pending_update, resolved_by=user_id, reason=reason)

    def mark_stale(self, pending_update_id: str):
        """
        Appelée quand un nouveau commit invalide une proposition en attente.
        Contrairement à approve/reject, aucun user_id — c'est une transition
        système, pas une action utilisateur.
        """
        pending_update = self.repo.get_by_id(pending_update_id)
        if pending_update is None:
            raise PendingUpdateNotFoundError(f"PendingUpdate {pending_update_id} introuvable.")

        if pending_update.status != "pending":
            # déjà résolue ou déjà stale — no-op silencieux, pas une erreur
            return pending_update

        logger.info(f"PendingUpdate {pending_update_id} marqué stale (nouveau commit détecté).")
        return self.repo.mark_stale(pending_update)

    def mark_existing_pending_as_stale(self, repository_id: str) -> None:
        """
        Appelée en tout début de Sync Orchestrator.process() —
        invalide toute proposition 'pending' existante avant d'en calculer une nouvelle.
        """
        active = self.get_active_pending(repository_id)
        if active is not None:
            self.mark_stale(active.id)

    # ------------------------------------------------------------------
    # Validation interne
    # ------------------------------------------------------------------
    def _require_pending_status(self, pending_update_id: str):
        pending_update = self.get(pending_update_id)
        if pending_update.status != "pending":
            raise InvalidStatusTransitionError(
                f"PendingUpdate {pending_update_id} a le statut '{pending_update.status}', "
                f"attendu 'pending'. Transition refusée."
            )
        return pending_update
