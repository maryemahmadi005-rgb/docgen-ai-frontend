from __future__ import annotations

from urllib.parse import urlencode
import secrets

import requests
from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)

from app.container import get_container
from app.utils.encryption import EncryptionService


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ============================================================
# GitHub OAuth helpers
# ============================================================

def _oauth_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="github-oauth-state",
    )


def _create_github_state(user_id: str) -> str:
    return _oauth_serializer().dumps(
        {
            "user_id": str(user_id),
            "nonce": secrets.token_urlsafe(16),
        }
    )


def _decode_github_state(state: str) -> dict:
    try:
        return _oauth_serializer().loads(
            state,
            max_age=600,
        )
    except SignatureExpired as exc:
        raise ValueError("La session GitHub a expiré.") from exc
    except BadSignature as exc:
        raise ValueError("State GitHub invalide.") from exc


# ============================================================
# Register
# ============================================================

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify(
            {"error": "email et password sont requis"}
        ), 400

    container = get_container()

    if container.user_repository.email_exists(email):
        return jsonify(
            {"error": "Un compte existe déjà avec cet email"}
        ), 409

    user = container.user_repository.create(
        email=email,
        password_hash=generate_password_hash(password),
    )

    container.commit()

    access_token = create_access_token(
        identity=str(user.id)
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return (
        jsonify(
            {
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        ),
        201,
    )


# ============================================================
# Login
# ============================================================

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify(
            {"error": "email et password sont requis"}
        ), 400

    container = get_container()

    user = container.user_repository.find_by_email(email)

    if (
        not user
        or not user.password_hash
        or not check_password_hash(
            user.password_hash,
            password,
        )
    ):
        return jsonify(
            {"error": "Identifiants invalides"}
        ), 401

    access_token = create_access_token(
        identity=str(user.id)
    )

    refresh_token = create_refresh_token(
        identity=str(user.id)
    )

    return jsonify(
        {
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )


# ============================================================
# Refresh
# ============================================================

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()

    new_access_token = create_access_token(
        identity=identity
    )

    return jsonify(
        {
            "access_token": new_access_token
        }
    )


# ============================================================
# Current user
# ============================================================

@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()

    container = get_container()

    user = container.user_repository.get_by_id(identity)

    if not user:
        return jsonify(
            {"error": "Utilisateur introuvable"}
        ), 404

    return jsonify(user.to_dict())


# ============================================================
# GitHub OAuth - START
# ============================================================

@auth_bp.get("/github")
@jwt_required()
def github_authorize():
    """
    Retourne l'URL GitHub OAuth pour l'utilisateur connecté.
    """

    client_id = current_app.config.get(
        "GITHUB_CLIENT_ID"
    )

    redirect_uri = current_app.config.get(
        "GITHUB_REDIRECT_URI"
    )

    if not client_id:
        return jsonify(
            {
                "error":
                "GITHUB_CLIENT_ID n'est pas configuré"
            }
        ), 500

    if not redirect_uri:
        return jsonify(
            {
                "error":
                "GITHUB_REDIRECT_URI n'est pas configuré"
            }
        ), 500

    user_id = get_jwt_identity()

    state = _create_github_state(user_id)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "repo admin:repo_hook read:user user:email",
        "state": state,
    }

    authorization_url = (
        "https://github.com/login/oauth/authorize?"
        + urlencode(params)
    )

    return jsonify(
        {
            "authorization_url": authorization_url
        }
    )


# ============================================================
# GitHub OAuth - CALLBACK
# ============================================================

@auth_bp.get("/github/callback")
def github_callback():

    code = request.args.get("code")
    state = request.args.get("state")
    github_error = request.args.get("error")

    if github_error:
        frontend_url = current_app.config.get(
            "FRONTEND_URL",
            "http://localhost:5173",
        )

        return (
            f"{frontend_url.rstrip('/')}"
            "/settings/account"
            "?github=error"
        )

    if not code or not state:
        return jsonify(
            {"error": "Code ou state GitHub manquant"}
        ), 400

    # --------------------------------------------------------
    # Vérification state
    # --------------------------------------------------------

    try:
        state_data = _decode_github_state(state)
    except ValueError as exc:
        return jsonify(
            {"error": str(exc)}
        ), 400

    user_id = state_data.get("user_id")

    if not user_id:
        return jsonify(
            {
                "error":
                "Utilisateur GitHub introuvable dans le state"
            }
        ), 400

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    client_id = current_app.config.get(
        "GITHUB_CLIENT_ID"
    )

    client_secret = current_app.config.get(
        "GITHUB_CLIENT_SECRET"
    )

    redirect_uri = current_app.config.get(
        "GITHUB_REDIRECT_URI"
    )

    if not client_id or not client_secret:
        return jsonify(
            {
                "error":
                "Configuration GitHub OAuth incomplète"
            }
        ), 500

    if not redirect_uri:
        return jsonify(
            {
                "error":
                "GITHUB_REDIRECT_URI n'est pas configuré"
            }
        ), 500

    # --------------------------------------------------------
    # Code -> GitHub access token
    # --------------------------------------------------------

    try:
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=15,
        )

    except requests.RequestException as exc:
        current_app.logger.error(
            "Erreur réseau GitHub OAuth: %s",
            exc,
        )

        return jsonify(
            {
                "error":
                "Impossible de contacter GitHub"
            }
        ), 502

    if token_response.status_code != 200:
        current_app.logger.error(
            "GitHub OAuth token error: %s",
            token_response.text[:500],
        )

        return jsonify(
            {
                "error":
                "GitHub n'a pas accepté l'autorisation"
            }
        ), 400

    token_data = token_response.json()

    github_token = token_data.get(
        "access_token"
    )

    if not github_token:
        return jsonify(
            {
                "error":
                "GitHub n'a pas retourné de token",
                "details":
                token_data.get(
                    "error_description"
                ),
            }
        ), 400

    # --------------------------------------------------------
    # GitHub profile
    # --------------------------------------------------------

    try:
        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Accept":
                "application/vnd.github+json",
                "Authorization":
                f"Bearer {github_token}",
            },
            timeout=15,
        )

    except requests.RequestException as exc:
        current_app.logger.error(
            "Erreur récupération profil GitHub: %s",
            exc,
        )

        return jsonify(
            {
                "error":
                "Impossible de récupérer le profil GitHub"
            }
        ), 502

    if user_response.status_code != 200:
        return jsonify(
            {
                "error":
                "Impossible de récupérer le compte GitHub"
            }
        ), 400

    github_user = user_response.json()

    github_username = github_user.get("login")

    if not github_username:
        return jsonify(
            {
                "error":
                "Nom utilisateur GitHub introuvable"
            }
        ), 400

    # --------------------------------------------------------
    # User DB
    # --------------------------------------------------------

    container = get_container()

    user = container.user_repository.get_by_id(
        user_id
    )

    if not user:
        return jsonify(
            {
                "error":
                "Utilisateur de la plateforme introuvable"
            }
        ), 404

    # --------------------------------------------------------
    # Encrypt GitHub token
    # --------------------------------------------------------

    try:
        encryption = EncryptionService()

        encrypted_token = encryption.encrypt(
            github_token
        )

    except Exception as exc:
        container.rollback()

        current_app.logger.error(
            "Erreur chiffrement token GitHub: %s",
            exc,
        )

        return jsonify(
            {
                "error":
                "Impossible de sécuriser le token GitHub"
            }
        ), 500

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    user.github_username = github_username
    user.github_token = encrypted_token

    container.session.flush()
    container.commit()

    # --------------------------------------------------------
    # Redirect frontend
    # --------------------------------------------------------

    frontend_url = current_app.config.get(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    return (
        f"{frontend_url.rstrip('/')}"
        "/settings/account"
        "?github=connected"
    )