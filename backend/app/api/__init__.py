from app.api.auth import auth_bp
from app.api.repositories import repositories_bp
from app.api.readmes import readmes_bp
from app.api.pending_updates import pending_updates_bp
from app.api.webhooks import webhooks_bp
from app.api.notifications import notifications_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(repositories_bp)
    app.register_blueprint(readmes_bp)
    app.register_blueprint(pending_updates_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(notifications_bp)
