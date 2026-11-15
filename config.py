"""Configuration classes for the Wnesny (ونسني) application.

Values are read from environment variables (optionally loaded from a local
``.env`` file). Secrets must never be hard-coded for production use.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root directory (the folder containing this file).
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

# Load environment variables from .env if present (never committed to Git).
load_dotenv(BASE_DIR / ".env")

_DEV_ONLY_SECRET = "wnesny-dev-only-insecure-secret-key"


def _normalize_database_url(url: str | None) -> str | None:
    """Accept the legacy ``postgres://`` scheme used by some hosts."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.getenv("SECRET_KEY", _DEV_ONLY_SECRET)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False


class DevelopmentConfig(Config):
    """Local development using a SQLite file in ``instance/``."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL")
    ) or f"sqlite:///{INSTANCE_DIR / 'wnesny_dev.db'}"


class TestingConfig(Config):
    """Automated tests: isolated in-memory SQLite database by default."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(Config):
    """Production: ``SECRET_KEY`` and ``DATABASE_URL`` must be provided.

    The values are validated by :func:`app.create_app` so that importing this
    module never fails in other environments.
    """

    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL"))


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
