import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()


class Config:
    """Configuration de base, commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod")

    # --- Base de données ---
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "readme_sync_db")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- JWT / Auth ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # --- GitHub ---
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
    GITHUB_WEBHOOK_CALLBACK_URL = os.environ.get(
        "GITHUB_WEBHOOK_CALLBACK_URL",
        "",
        )
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.environ.get(
        "GITHUB_REDIRECT_URI",
        "http://127.0.0.1:5000/api/auth/github/callback",
        )
    FRONTEND_URL = os.environ.get(
        "FRONTEND_URL",
        "http://localhost:5173",
        )
    WEBHOOK_SECRET_DEFAULT = os.environ.get("WEBHOOK_SECRET_DEFAULT", "")

    # --- Encryption (Fernet key pour github_token / webhook_secret) ---
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

    # --- CORS ---
    # Origines autorisées à appeler l'API depuis le navigateur (frontend Vite).
    # Surchargeable via la variable d'env CORS_ORIGINS ("origin1,origin2,...").
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5174,"
            "http://127.0.0.1:5174,"
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:3000,"
            "http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # --- Git clones locaux ---
    CLONES_BASE_DIR = os.environ.get("CLONES_BASE_DIR", "/data/repo_clones")

    # --- Ollama / AI ---
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
    OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))
    # Budget de tokens en sortie pour Ollama. Anciennement présent dans le
    # .env (GENERATE_NUM_PREDICT) mais jamais lu par le code — c'était la
    # cause de la troncature JSON (Ollama retombait sur sa limite par défaut).
    OLLAMA_NUM_PREDICT = int(os.environ.get("GENERATE_NUM_PREDICT", "2048"))


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None):
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env_name, DevelopmentConfig)