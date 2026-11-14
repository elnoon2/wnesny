import sys
from pathlib import Path
import pytest

# Ensure root workspace and legacy src are in sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from app import create_app
from app.extensions import db as _db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Session-wide test Flask application."""
    test_app = create_app(TestingConfig)
    return test_app


@pytest.fixture(scope="function")
def db_session(app):
    """Function-level clean database fixture with transaction isolation."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()
