# Development Progress

## Phase 1: Database foundation (complete)

- Flask application factory, configuration environments, extensions.
- 10 SQLAlchemy models with constraints, indexes and relationships.
- Initial Alembic migration `5ef329471ff1`.
- Database service layer with transactional business rules.
- Idempotent interest seed (32 interests, 8 categories).
- 42 automated tests passing.

## Repository migration: Nabd to Wnesny (complete)

The repository was originally created for **Nabd** (*Smart Hospital and Blood Donor Finder*). It now hosts **Wnesny (ونسني)** only:

- Removed the Nabd code (`src/smart_health/`), its tests, notebooks, Dockerfile and hospital data documentation. Everything is preserved in Git history and on the other team branches.
- Replaced the Nabd proposal with the Wnesny M1 proposal in `docs/proposal/`. The proposal is pending a name correction ("Rafeeq" appears in section 1).
- Rewrote the README and added architecture, testing and progress documentation.
- Hardened configuration: `WNESNY_ENV`, production fails fast without `SECRET_KEY`/`DATABASE_URL`, `postgres://` normalization.
- The seed script no longer calls `db.create_all()`; the schema is owned by migrations.
- Fixed ORM cascades so that deleting a user cannot silently delete their rides or requests.
- Added migration tests.

## Next phases (planned)

1. Authentication and user profiles (Flask-Login, CSRF, forms).
2. Ride and request routes (blueprints).
3. Chat and notifications UI.
4. AI matching engine and evaluation (see proposal section 5).
5. Synthetic data generation and statistical analysis (see proposal sections 3–4).
6. Frontend, dashboard, security review, final documentation.

