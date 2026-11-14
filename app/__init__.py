import os
from flask import Flask
from config import config_by_name
from app.extensions import db, migrate
import app.models  # Ensure all models are registered with SQLAlchemy


def create_app(config_name=None):
    """Application factory for Wnesny."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    if isinstance(config_name, str):
        app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    else:
        app.config.from_object(config_name)

    # Ensure instance folder exists for SQLite databases
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    return app
