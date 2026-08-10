"""
Encryption — chiffrement au repos des données sensibles
(github_token, webhook_secret).

Utilise Fernet (AES-128-CBC + HMAC) via la librairie `cryptography`.
La clé maîtresse doit venir d'une variable d'environnement, jamais du code.
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    pass


class EncryptionService:
    def __init__(self, master_key: str | None = None):
        """
        master_key : clé Fernet (32 bytes url-safe base64-encoded).
        Si non fournie, lue depuis la variable d'env ENCRYPTION_MASTER_KEY.

        Génération d'une clé (à faire une seule fois, hors code applicatif) :
            from cryptography.fernet import Fernet
            Fernet.generate_key()
        """
        key = master_key or os.environ.get("ENCRYPTION_MASTER_KEY")
        if not key:
            raise EncryptionError(
                "ENCRYPTION_MASTER_KEY manquante — impossible d'initialiser le chiffrement."
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as e:
            logger.error(f"Échec chiffrement: {e}")
            raise EncryptionError(f"Impossible de chiffrer la donnée: {e}") from e

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as e:
            logger.error("Échec déchiffrement: token invalide ou clé incorrecte.")
            raise EncryptionError("Impossible de déchiffrer: donnée corrompue ou mauvaise clé.") from e
        except Exception as e:
            logger.error(f"Échec déchiffrement: {e}")
            raise EncryptionError(f"Impossible de déchiffrer la donnée: {e}") from e