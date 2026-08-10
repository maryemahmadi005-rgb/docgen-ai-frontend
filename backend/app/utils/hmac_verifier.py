"""
HMAC Verifier — utilitaire pur, indépendant de GitHub Integration Service.

Séparé en tant qu'utilitaire générique (plutôt que méthode privée du service)
pour permettre sa réutilisation par d'autres intégrations futures
(ex: Stripe, GitLab) qui suivent le même schéma de signature.
"""

import hmac
import hashlib


def compute_hmac_sha256(secret: str, payload: bytes) -> str:
    """Calcule la signature HMAC-SHA256 d'un payload avec un secret donné."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_hmac_signature(secret: str, payload: bytes, signature_header: str | None, prefix: str = "sha256=") -> bool:
    """
    Vérifie une signature au format 'sha256=<hex>' (format GitHub standard).
    Comparaison en temps constant — protection contre les attaques par timing.
    """
    if not signature_header or not signature_header.startswith(prefix):
        return False

    expected = signature_header[len(prefix):]
    computed = compute_hmac_sha256(secret, payload)

    return hmac.compare_digest(computed, expected)