# Development Roadmap

This roadmap reflects the current state of the project: the database foundation is complete, and everything else is planned.

```mermaid
flowchart LR
    A["Database foundation<br/>models, constraints, migrations,<br/>services, seed data, 42 tests"]:::done
    B["Authentication<br/>sessions, CSRF"]:::next
    C["HTTP routes / API"]:::planned
    D["Frontend pages<br/>Bootstrap 5 + Jinja2"]:::planned
    E["AI matching engine<br/>scoring, ranking, explanations"]:::planned
    F["Synthetic data and<br/>statistical analysis"]:::planned
    G["Results dashboard and<br/>AI demo page"]:::planned
    H["Evaluation against<br/>project objectives"]:::planned

    A --> B --> C --> D
    C --> E
    E --> F --> G --> H
    D --> G

    classDef done fill:#d1fae5,stroke:#059669,color:#064e3b;
    classDef next fill:#fef3c7,stroke:#d97706,color:#78350f;
    classDef planned fill:#f3f4f6,stroke:#9ca3af,color:#374151,stroke-dasharray: 5 5;
```

## Status

| Phase | Scope | Status |
|-------|-------|--------|
| 1. Database foundation | Models, constraints, migrations, service layer, interest seed, tests | Done |
| 2. Authentication | Login, sessions, CSRF protection | Not started |
| 3. HTTP routes / API | Routes that call the service layer | Not started |
| 4. Frontend | At least 4 pages (Bootstrap 5 + Jinja2) | Not started |
| 5. AI matching engine | Compatibility scoring, ranking, explanations | Not started |
| 6. Data and statistics | Synthetic data generation, analysis | Not started |
| 7. Dashboard and demo | Results dashboard, AI demo page | Not started |
| 8. Evaluation | Check results against the M1 objectives | Not started |
