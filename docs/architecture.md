# Architecture Diagram

Wnesny is a modular Flask application built with the application factory pattern. Business rules live in a service layer, separate from the models. HTTP routes will call this layer once they are built.

Legend: solid boxes are implemented, dashed boxes are planned.

```mermaid
flowchart TD
    Browser["Browser<br/>(Bootstrap 5 + Jinja2 templates)"]:::planned
    Routes["HTTP routes / API<br/>(Flask blueprints)"]:::planned
    Auth["Authentication, sessions, CSRF"]:::planned
    AI["AI matching engine<br/>(scoring, ranking, explanations)"]:::planned
    Services["Service layer<br/>app/services/database_service.py"]:::done
    Models["SQLAlchemy models<br/>app/models/ (10 tables)"]:::done
    Ext["Extensions<br/>SQLAlchemy + Flask-Migrate"]:::done
    DB[("SQLite (dev and tests)<br/>PostgreSQL-compatible schema")]:::done

    Browser --> Routes
    Routes --> Auth
    Routes --> Services
    Routes --> AI
    AI --> Services
    Services --> Models
    Models --> Ext
    Ext --> DB

    classDef done fill:#d1fae5,stroke:#059669,color:#064e3b;
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#374151,stroke-dasharray: 5 5;
```

## Layer responsibilities

| Layer | Responsibility | Status |
|-------|----------------|--------|
| Browser / templates | User-facing pages | Planned |
| HTTP routes | Parse requests, call services, render responses | Planned |
| Authentication | Login, sessions, CSRF protection | Planned |
| AI matching engine | Compatibility scoring, ranking, explanations | Planned |
| Service layer | Transactional business rules (requests, acceptance, cancellation, chat, reviews, notifications) | Implemented |
| Models | Tables, constraints, indexes, relationships | Implemented |
| Extensions and migrations | Database session, Alembic migrations | Implemented |

See [architecture.md](../architecture.md) for module responsibilities and design decisions.
