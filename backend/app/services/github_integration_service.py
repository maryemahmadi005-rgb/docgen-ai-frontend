"""
GitHub Integration Service — gestion des webhooks GitHub et de l'authentification.

Responsable de :
- créer/supprimer un webhook GitHub à la connexion/déconnexion d'un repo
- vérifier la signature HMAC des payloads entrants
- fournir les headers d'authentification pour les appels à l'API GitHub

Ce service ne connaît ni git local (GitPython), ni la logique métier
de synchronisation — uniquement les échanges HTTP avec l'API GitHub.
"""

import hmac
import hashlib
import logging
import secrets
import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubIntegrationError(Exception):
    pass


class GitHubIntegrationService:
    def __init__(self, webhook_callback_url: str, timeout: int = 15):
        """
        webhook_callback_url : URL publique de votre backend,
        ex. "https://yourapp.io/api/webhooks/github"
        """
        self.webhook_callback_url = webhook_callback_url
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Création du webhook — appelée par Repository Service à l'ajout d'un repo
    # ------------------------------------------------------------------
    def create_webhook(self, repository_id: str, full_name: str, auth_token: str | None) -> dict:
        """
        Enregistre un webhook GitHub sur l'événement 'push'.
        Retourne {"id": webhook_id, "secret": generated_secret}.

        Lève GitHubIntegrationError si la création échoue (ex: permissions
        insuffisantes — l'appelant doit alors basculer en mode polling).
        """
        if not auth_token:
            raise GitHubIntegrationError("Token GitHub requis pour créer un webhook.")

        secret = self._generate_secret()

        payload = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": self.webhook_callback_url,
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0",
            },
        }

        try:
            response = requests.post(
                f"{GITHUB_API_BASE}/repos/{full_name}/hooks",
                json=payload,
                headers=self._auth_headers(auth_token),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error(f"Échec réseau création webhook pour {full_name}: {e}")
            raise GitHubIntegrationError(f"Erreur réseau: {e}") from e

        if response.status_code == 404:
            raise GitHubIntegrationError(
                f"Repository {full_name} introuvable ou token sans accès."
            )
        if response.status_code == 403:
            raise GitHubIntegrationError(
                f"Permissions insuffisantes pour créer un webhook sur {full_name} "
                f"(admin requis)."
            )
        if response.status_code not in (200, 201):
            raise GitHubIntegrationError(
                f"Échec création webhook ({response.status_code}): {response.text[:200]}"
            )

        data = response.json()
        logger.info(f"Webhook créé pour {full_name}: id={data['id']}")

        return {"id": str(data["id"]), "secret": secret}

    # ------------------------------------------------------------------
    # Suppression du webhook — appelée par Repository Service à la suppression d'un repo
    # ------------------------------------------------------------------
    def delete_webhook(self, full_name: str, webhook_id: str, auth_token: str | None) -> None:
        if not auth_token:
            logger.warning(f"Pas de token disponible pour supprimer le webhook {webhook_id} sur {full_name}.")
            return

        try:
            response = requests.delete(
                f"{GITHUB_API_BASE}/repos/{full_name}/hooks/{webhook_id}",
                headers=self._auth_headers(auth_token),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.warning(f"Échec réseau suppression webhook {webhook_id}: {e}")
            raise GitHubIntegrationError(f"Erreur réseau: {e}") from e

        # 404 = déjà supprimé côté GitHub, on ne considère pas ça comme une erreur bloquante
        if response.status_code not in (204, 404):
            raise GitHubIntegrationError(
                f"Échec suppression webhook ({response.status_code}): {response.text[:200]}"
            )

    # ------------------------------------------------------------------
    # Vérification HMAC — utilisée par api/webhooks.py
    # ------------------------------------------------------------------
    def verify_signature(self, raw_body: bytes, signature_header: str | None, webhook_secret: str) -> bool:
        """
        Vérifie que le payload provient bien de GitHub, via comparaison
        en temps constant pour éviter les attaques par timing.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_signature = signature_header.removeprefix("sha256=")

        computed = hmac.new(
            key=webhook_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, expected_signature)

    # ------------------------------------------------------------------
    # Vérification d'accès au repo (utilisée avant clone, optionnel)
    # ------------------------------------------------------------------
    def check_repository_access(self, full_name: str, auth_token: str | None) -> dict:
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{full_name}",
                headers=self._auth_headers(auth_token),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise GitHubIntegrationError(f"Erreur réseau: {e}") from e

        if response.status_code == 404:
            raise GitHubIntegrationError(f"Repository {full_name} introuvable ou inaccessible.")
        if response.status_code != 200:
            raise GitHubIntegrationError(f"Erreur GitHub API ({response.status_code}).")

        data = response.json()
        return {
            "default_branch": data.get("default_branch", "main"),
            "private": data.get("private", False),
            "permissions": data.get("permissions", {}),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _auth_headers(self, auth_token: str | None) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _generate_secret(self) -> str:
        return secrets.token_hex(32)