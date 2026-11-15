"""Shared pytest fixtures for the Wnesny test suite.

Tests always run against an isolated SQLite database (in-memory by default),
never against the development database in ``instance/``.
"""

import pytest

from app import create_app
from app.extensions import db as _db
from config import TestingConfig


@pytest.fixture(scope="session")
def app():
    """Session-wide Flask application configured for testing."""
    return create_app(TestingConfig)


@pytest.fixture(scope="function")
def db_session(app):
    """Provide a fresh schema for each test and drop it afterwards."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()
