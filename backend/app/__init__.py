from flask import Flask, jsonify

from app.config import get_config
from app.extensions import db, migrate, jwt, cors


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- CORS ---
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]
            }
        },
        supports_credentials=False,
        allow_headers=[
            "Content-Type",
            "Authorization",
        ],
        methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
    )

    # --- Modèles ---
    with app.app_context():
        from app import models  # noqa: F401

    # --- Blueprints ---
    from app.api import register_blueprints
    register_blueprints(app)

    # --- Health check ---
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Ressource introuvable"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Erreur interne du serveur"}), 500

    return app