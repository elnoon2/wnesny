"""Wnesny (ونسني) Flask application package."""

import os

from flask import Flask

from app.extensions import db, migrate
from config import INSTANCE_DIR, config_by_name

import app.models  # noqa: F401  (registers all models with SQLAlchemy metadata)


def create_app(config_name=None) -> Flask:
    """Application factory for Wnesny.

    Args:
        config_name: An environment name (``development``, ``testing``,
            ``production``) or a configuration class. Defaults to the
            ``WNESNY_ENV`` environment variable, then ``development``.
            An unknown name raises ``ValueError``.
    """
    if config_name is None:
        config_name = os.getenv("WNESNY_ENV", "development")

    flask_app = Flask(__name__, instance_path=os.fspath(INSTANCE_DIR))

    if isinstance(config_name, str):
        # A typo such as "prodcution" must not silently start the insecure
        # development configuration, so unknown names fail fast.
        config_class = config_by_name.get(config_name)
        if config_class is None:
            raise ValueError(
                f"Unknown environment '{config_name}'. "
                f"Use one of: {', '.join(sorted(config_by_name))}."
            )
    else:
        config_class = config_name
    flask_app.config.from_object(config_class)

    _validate_config(flask_app)

    # Ensure the instance folder (used for local SQLite files) exists.
    os.makedirs(flask_app.instance_path, exist_ok=True)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    return flask_app


def _validate_config(flask_app: Flask) -> None:
    """Fail fast when production is started without required settings."""
    if flask_app.config.get("TESTING") or flask_app.config.get("DEBUG"):
        return
    missing = [
        key
        for key in ("SECRET_KEY", "SQLALCHEMY_DATABASE_URI")
        if not flask_app.config.get(key)
    ]
    if missing:
        raise RuntimeError(
            "Missing required production configuration: " + ", ".join(missing)
        )
