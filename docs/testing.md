# Testing

## Running the tests

```bash
python -m pytest          # whole suite (configured in pytest.ini)
python -m pytest -v       # verbose
python -m pytest tests/test_migrations.py
```

## Isolation

- `tests/conftest.py` builds the app with `TestingConfig`, which uses **in-memory SQLite**. Each test gets a freshly created schema that is dropped afterwards.
- `tests/test_migrations.py` runs the real Alembic migrations against a **temporary SQLite file** (pytest `tmp_path`).
- No test touches the development database `instance/wnesny_dev.db`.

## Test suites

| File | Tests | Covers |
|---|---|---|
| `tests/test_models.py` | 8 | Creation of each model, password hashing, email normalization, defaults |
| `tests/test_relationships.py` | 8 | All ORM relationships (1:1, 1:N, M:N, self-referencing reviews) |
| `tests/test_constraints.py` | 14 | Unique emails and interests, composite PK, invalid statuses and visibility, duplicate requests, **single accepted passenger (partial index)**, rating range, self-review, duplicate reviews, empty messages, history preservation on user deletion |
| `tests/test_database_service.py` | 7 | Own-ride requests, requests on cancelled rides, transactional acceptance with auto-rejection and notifications, cancellation preserving history, chat authorization, review rules |
| `tests/test_migrations.py` | 5 | Migration creates all 10 tables, the partial unique index and CHECK constraints; downgrade to base; seed idempotency |

## Latest verified result

```
python -m pytest
42 passed in 12.80s
```

Environment: Windows, Python 3.12.10, pytest 9.2.0, SQLAlchemy 2.1.8, Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.1.0.

> The 7 tests of the previous Nabd project (A* hospital search, data generation, blood-compatibility rules) were removed together with that code. They remain in Git history and on the other branches.

