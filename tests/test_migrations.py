"""Verify that the Alembic migrations build the expected schema and that the
interest seed script is idempotent.

These tests use a temporary SQLite file, never the development database.
"""

from pathlib import Path

import pytest
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models import Interest
from config import TestingConfig
from seed_interests import INITIAL_INTERESTS, seed_interests

MIGRATIONS_DIR = str(Path(__file__).resolve().parents[1] / "migrations")

EXPECTED_TABLES = {
    "users",
    "user_profiles",
    "interests",
    "user_interests",
    "rides",
    "ride_requests",
    "conversations",
    "messages",
    "reviews",
    "notifications",
}


@pytest.fixture()
def migrated_app(tmp_path):
    """An app bound to a temporary SQLite file upgraded to the latest revision."""

    class MigrationTestConfig(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'migration_test.db').as_posix()}"

    flask_app = create_app(MigrationTestConfig)
    with flask_app.app_context():
        upgrade(directory=MIGRATIONS_DIR)
        yield flask_app
        db.session.remove()
        db.engine.dispose()


def test_migration_creates_all_ten_tables(migrated_app):
    tables = set(inspect(db.engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)
    assert "alembic_version" in tables


def test_migration_creates_single_accepted_partial_index(migrated_app):
    sql = db.session.execute(
        text(
            "SELECT sql FROM sqlite_master "
            "WHERE type='index' AND name='uq_accepted_request_per_ride'"
        )
    ).scalar_one()
    assert "UNIQUE" in sql.upper()
    assert "status = 'accepted'" in sql


def test_migration_creates_check_constraints(migrated_app):
    expected = {
        "rides": "chk_ride_status_valid",
        "ride_requests": "chk_request_status_valid",
        "user_profiles": "chk_education_visibility_valid",
        "reviews": "chk_no_self_review",
        "messages": "chk_message_content_not_empty",
    }
    for table, constraint in expected.items():
        ddl = db.session.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:t"),
            {"t": table},
        ).scalar_one()
        assert constraint in ddl, f"{constraint} missing from {table}"


def test_migration_downgrade_removes_tables(migrated_app):
    downgrade(directory=MIGRATIONS_DIR, revision="base")
    tables = set(inspect(db.engine).get_table_names())
    assert not (EXPECTED_TABLES & tables)


def test_seed_interests_is_idempotent(migrated_app):
    first = seed_interests(migrated_app)
    second = seed_interests(migrated_app)
    assert first == len(INITIAL_INTERESTS)
    assert second == 0
    assert db.session.query(Interest).count() == len(INITIAL_INTERESTS)

