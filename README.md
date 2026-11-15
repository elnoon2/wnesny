# Wnesny : Interest-Based Ride Matching

Wnesny (Egyptian Arabic for "keep me company") is a ride-sharing and social-matching web platform. It connects drivers and passengers who travel in similar directions and share interests, so the trip is also good company.

**Integrated Mega Project, Fall 2026** | AI 306, CS 312, CO 208 | School of Computing and Data Science, Badya University

> [!IMPORTANT]
> **Project status: database foundation complete.** The data layer (models, constraints, migrations, service functions, seed data, tests) is implemented and tested. The web interface, authentication pages, HTTP routes and the AI matching engine are planned, not yet implemented. See [Current implementation status](#current-implementation-status).

## Table of contents

- [Project overview](#project-overview)
- [Problem statement](#problem-statement)
- [Proposed solution](#proposed-solution)
- [Objectives](#objectives)
- [Target users](#target-users)
- [Main features](#main-features)
- [Technical architecture](#technical-architecture)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Database schema overview](#database-schema-overview)
- [Installation](#installation)
- [Environment configuration](#environment-configuration)
- [Database migrations](#database-migrations)
- [Seed data](#seed-data)
- [Testing](#testing)
- [Current implementation status](#current-implementation-status)
- [Development roadmap](#development-roadmap)
- [Team](#team)
- [Documentation](#documentation)
- [License](#license)

## Project overview

Wnesny lets one registered account act as a driver on one trip and a passenger on another; there are no separate account types. A driver publishes a ride, passengers request to join, and the driver accepts exactly one passenger. Once accepted, the two can chat inside the platform. After the ride is completed, they can review each other.

What makes Wnesny different from ordinary ride-hailing is compatibility-based matching: besides route and time, it considers shared interests, optional education background (only when the user chooses to share it), and conversation preferences.

## Problem statement

Many drivers dislike driving alone on long trips, and many riders would enjoy company during a ride. Existing ride-hailing apps assign drivers and riders by distance only, so the person in the car is effectively a random stranger.

## Proposed solution

Wnesny matches a driver and a rider whose routes, departure times and interests fit, and explains why a match was suggested (for example, shared interests and compatible routes). Privacy is built into the data model: education details have a visibility setting (`public`, `matches_only`, `private`), and the platform stores coarse addresses and optional coordinates only. There is no live GPS tracking.

## Objectives

The academic objectives are defined in the M1 proposal and quoted here verbatim:

1. Raise the mean simulated trip-compatibility rating (1–5) by at least 0.5 points compared with random matching, over at least 1,000 simulated requests.
2. Satisfy all hard constraints (pickup detour ≤ 10 minutes, departure within ±15 minutes, available seats) in at least 95% of matches produced.
3. Match at least 90% of feasible requests, and produce a ranked list for 200 requests in under 5 seconds.
4. Deliver a working web application with at least 4 pages, a results dashboard, and an AI demo page usable by a non-technical person.

> [!NOTE]
> The current database (schema V1.0) supports one accepted passenger per ride, so "available seats" is always one. See [docs/proposal/README.md](docs/proposal/README.md) for the known differences between the proposal and the implementation.

## Target users

- Drivers who travel regularly and would prefer company on the road.
- Passengers who want a ride with someone they are likely to get along with.
- The general public. The platform is not limited to university students.

## Main features

| Feature | Status |
|---------|--------|
| User accounts with hashed passwords and normalized emails (data layer) | ✅ Implemented |
| Optional user profile with education-visibility privacy setting | ✅ Implemented |
| Interest catalogue (32 interests, 8 categories) and user–interest assignment | ✅ Implemented |
| Ride publishing with coordinate validation and status lifecycle | ✅ Implemented |
| Ride requests with at most one accepted passenger per ride | ✅ Implemented |
| Transaction-safe acceptance that auto-rejects competing pending requests | ✅ Implemented |
| Conversation created only after acceptance; participant-only messaging | ✅ Implemented (service layer) |
| Ride cancellation that preserves history, freezes chat and notifies the passenger | ✅ Implemented (service layer) |
| Reviews (1–5) only after completion, only between participants, no self-reviews | ✅ Implemented (service layer) |
| Persistent in-app notifications | ✅ Implemented (data + service layer) |
| Authentication pages, sessions, CSRF protection | ⏳ Planned |
| HTTP routes / API and web pages (Bootstrap + Jinja2) | ⏳ Planned |
| AI matching engine (compatibility scoring, ranking, explanations) | ⏳ Planned |
| Synthetic data generation, statistical analysis, dashboard | ⏳ Planned |

> [!NOTE]
> The database stores the information that the matching engine will need (interests, education with visibility, coordinates, departure times), but no matching algorithm is implemented yet.

## Technical architecture

Wnesny is a modular Flask application using the application factory pattern. Business rules live in a service layer, separate from the models; HTTP routes will call this layer once they are built.

- Architecture diagram: [docs/diagrams/architecture.md](docs/diagrams/architecture.md)
- Module responsibilities and design decisions: [docs/architecture.md](docs/architecture.md)

## Technology stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Web framework | Flask 3 |
| ORM | SQLAlchemy 2 via Flask-SQLAlchemy |
| Migrations | Flask-Migrate (Alembic) |
| Password hashing | Werkzeug security helpers |
| Configuration | python-dotenv + environment variables |
| Database | SQLite (development and tests), PostgreSQL-compatible schema |
| Testing | pytest |
| Planned frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Jinja2 |
| Planned analysis | NumPy, pandas, SciPy, statsmodels, Matplotlib, seaborn (see `requirements-analysis.txt`) |

## Repository structure

```text
wnesny/
├── app/
│   ├── __init__.py              # Application factory (create_app) + config validation
│   ├── extensions.py            # SQLAlchemy and Flask-Migrate instances; SQLite FK pragma
│   ├── models/                  # One file per model (10 tables)
│   │   ├── user.py, user_profile.py, interest.py (+ user_interests table)
│   │   ├── ride.py, ride_request.py, conversation.py, message.py
│   │   └── review.py, notification.py
│   └── services/
│       └── database_service.py  # Transactional business rules
├── migrations/                  # Alembic environment + initial migration
├── tests/                       # pytest suite (models, relationships, constraints, services, migrations)
├── docs/
│   ├── proposal/                # M1 project proposal (PDF)
│   ├── diagrams/                # Architecture and database relationship diagrams
│   ├── architecture.md
│   ├── database-schema.md       # Data dictionary + Mermaid ERD
│   ├── roadmap.md
│   ├── testing.md
│   ├── development-progress.md
│   └── ai_use_statement.md
├── data/raw/, data/cleaned/     # Reserved for planned synthetic datasets
├── notebooks/                   # Reserved for planned analysis notebooks
├── config.py                    # Development / Testing / Production configuration
├── run.py                       # Flask entry point + shell context
├── seed_interests.py            # Idempotent interest catalogue seed
├── requirements.txt             # App + test dependencies
├── requirements-analysis.txt    # Optional analysis dependencies
├── pytest.ini
└── .env.example
```

## Database schema overview

Ten tables, normalized to 3NF. Full data dictionary: [docs/database-schema.md](docs/database-schema.md). Relationship diagram: [docs/diagrams/database-relationships.md](docs/diagrams/database-relationships.md).

| Table | Purpose |
|-------|---------|
| `users` | Accounts (driver and passenger roles share one account) |
| `user_profiles` | Optional bio and education data plus `education_visibility` |
| `interests` | Predefined interest catalogue |
| `user_interests` | Many-to-many link between users and interests (composite PK) |
| `rides` | Rides published by drivers, with optional coordinates and a status |
| `ride_requests` | Passenger requests (pending, accepted, rejected, cancelled) |
| `conversations` | One chat per accepted request |
| `messages` | Chat messages (non-empty, read status) |
| `reviews` | Post-ride ratings (1–5) |
| `notifications` | Persistent in-app notifications |

**Key integrity rules enforced in the database:**

- Unique emails; unique interest names; composite PK on `user_interests`.
- `CHECK` constraints for statuses, education visibility, coordinate ranges, rating range, non-empty messages and no self-review.
- `UNIQUE (ride_id, passenger_id)`: one request per passenger per ride.
- Partial unique index `uq_accepted_request_per_ride ON ride_requests(ride_id) WHERE status = 'accepted'`: at most one accepted passenger per ride (SQLite ≥ 3.8 and PostgreSQL).
- `UNIQUE (ride_id, reviewer_id, reviewed_user_id)`: no duplicate reviews.
- Foreign keys enforced in SQLite via `PRAGMA foreign_keys=ON`; `RESTRICT` on driver/passenger/sender/reviewer keys, so history cannot be deleted by accident.

**Rules enforced in the service layer** (they need context across several tables): no requesting your own ride, requests only on scheduled rides, conversations only for accepted requests, messages only from the two participants in active conversations, reviews only after completion and only between participants.

## Installation

Prerequisites: Python 3.12+ and Git.

```bash
git clone <repository-url> wnesny
cd wnesny

python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
# Optional, for planned data analysis work:
# pip install -r requirements-analysis.txt
```

## Environment configuration

```bash
# Windows (PowerShell)
Copy-Item .env.example .env
# macOS / Linux
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `WNESNY_ENV` | No | `development` (default), `testing` or `production` |
| `SECRET_KEY` | Production | Long random string. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Production | SQLAlchemy URL. Defaults to `instance/wnesny_dev.db` in development. Relative SQLite paths resolve inside `instance/`. |
| `TEST_DATABASE_URL` | No | Overrides the test database (defaults to in-memory SQLite) |

The application refuses to start in production mode without `SECRET_KEY` and `DATABASE_URL`. Never commit `.env`.

PostgreSQL requires a driver (for example `pip install "psycopg[binary]"`). It is not included in `requirements.txt` because development uses SQLite.

## Database migrations

The schema is managed exclusively through Flask-Migrate (Alembic). The application never calls `db.create_all()` on real databases.

```bash
# Create or upgrade the database to the latest schema
flask --app run.py db upgrade

# Show the current revision
flask --app run.py db current

# After changing a model: generate, review, then apply a new migration
flask --app run.py db migrate -m "describe the change"
flask --app run.py db upgrade
```

## Seed data

```bash
python seed_interests.py
```

The script inserts 32 predefined interests across 8 categories (Technology, Business, Sports, Arts & Culture, Music, Lifestyle, Gaming & Hobbies, Social). It is idempotent: running it again inserts nothing new. It requires the schema to be migrated first and never creates tables itself.

To inspect the development database:

```bash
python -c "import sqlite3; c = sqlite3.connect('instance/wnesny_dev.db'); print([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"
```

## Testing

```bash
python -m pytest            # whole suite
python -m pytest -v         # verbose
python -m pytest tests/test_constraints.py
```

Tests run against isolated SQLite databases (in-memory, or a temporary file for migration tests). They never touch `instance/wnesny_dev.db`. Details: [docs/testing.md](docs/testing.md).

Last verified result: **42 passed, 0 failed** (Python 3.12.10, pytest 9.2.0, Windows).

## Current implementation status

| Area | Status |
|------|--------|
| Application factory, configuration, extensions | ✅ Done |
| 10 SQLAlchemy models with constraints and indexes | ✅ Done |
| Initial Alembic migration (verified by tests: upgrade, partial index, CHECKs, downgrade) | ✅ Done |
| Database service layer (requests, acceptance, cancellation, chat, reviews, notifications) | ✅ Done |
| Interest seed script | ✅ Done |
| Automated tests (42) | ✅ Passing |
| Authentication, sessions, CSRF | ⏳ Not started |
| HTTP routes / API | ⏳ Not started |
| Frontend pages | ⏳ Not started |
| AI matching engine and evaluation | ⏳ Not started |
| Synthetic data, statistics, dashboard | ⏳ Not started |

## Development roadmap

The database foundation is complete. Next steps are authentication, HTTP routes, frontend pages, the AI matching engine, synthetic data and analysis, and finally the dashboard and evaluation.

See the full roadmap with a diagram in [docs/roadmap.md](docs/roadmap.md).

## Team

Team members and lead roles, as listed in the M1 proposal:

| Member | Lead role |
|--------|-----------|
| Youssef Essam | Project manager |
| Nour Elkassy | Data and statistics lead |
| Mohamed Osama | AI lead |
| Toqa Waleed | Database and web lead |
| Nada Moataz | Quality and documentation lead |

Individual contributions are recorded in the Git history.

## Documentation

- [Architecture](docs/architecture.md)
- [Architecture diagram](docs/diagrams/architecture.md)
- [Database schema and ERD](docs/database-schema.md)
- [Database relationships diagram](docs/diagrams/database-relationships.md)
- [Testing](docs/testing.md)
- [Development progress](docs/development-progress.md)
- [Development roadmap](docs/roadmap.md)
- [Project proposal (M1)](docs/proposal/README.md)
- [AI-use statement](docs/ai_use_statement.md)

## License

No license has been selected yet. Until one is added, all rights are reserved by the project team.
