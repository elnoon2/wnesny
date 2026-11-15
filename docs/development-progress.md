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
- Replaced the Nabd proposal with the Wnesny M1 proposal in `docs/proposal/`. The name "Rafeeq" in section 1 of the proposal PDF was corrected to "Wnesny" on 15 Nov 2026.
- Rewrote the README and added architecture, testing and progress documentation.
- Hardened configuration: `WNESNY_ENV`, production fails fast without `SECRET_KEY`/`DATABASE_URL`, `postgres://` normalization.
- The seed script no longer calls `db.create_all()`; the schema is owned by migrations.
- Fixed ORM cascades so that deleting a user cannot silently delete their rides or requests.
- Added migration tests.

## Review fixes against the project idea (complete)

- Only the ride's driver can accept or reject requests (`accept_ride_request` and `reject_ride_request` now take `driver_id`).
- New `start_ride` and `complete_ride` so a ride can reach `completed`, which is what opens reviews.
- Rides can be cancelled only while scheduled; pending passengers are notified on cancellation. An accepted passenger can cancel while the ride is scheduled, which reopens the ride for new requests.
- Input checks: valid e-mail, password of at least 8 characters, non-empty and different addresses, departure in the future, coordinates in pairs, graduation year range.
- Database conflicts on acceptance and duplicate requests become clear service errors.
- An unknown `WNESNY_ENV` value now raises an error instead of silently using the development configuration.
- Diagram files moved to `docs/diagrams/`, the missing `docs/architecture.md` written, broken README links fixed, BOM removed from two Python files.

## Phase 2: Synthetic data layer, M2 (complete)

- `simulation/` package: ~50 Cairo areas, seeded generator (`python -m simulation.generate`), hidden rating model, validator and database loader.
- Dataset: 600 users, 32 interests, 3,000 completed trips with ratings, written to `data/raw/` (reproducible from the seed, not committed).
- Data dictionary and simulation model in `data/README.md`; first exploratory notebook `notebooks/01_eda.ipynb`.
- 29 new tests for the data layer (and 32 regression tests for the review fixes above); 103 automated tests passing in total.
- Open items: area coordinates are hand-typed approximations (verify against OpenStreetMap); gender preference is recorded in the data but not modelled in the schema.

## Next phases (planned)

1. M3: statistical analysis (confidence intervals, hypothesis tests, distribution fits, regression) and the AI matching prototype (CSP + Naive Bayes) with baselines.
2. Authentication and user profiles (Flask-Login, CSRF, forms).
3. Ride and request routes (blueprints).
4. Chat and notifications UI.
5. Frontend, dashboard, security review, final documentation.

