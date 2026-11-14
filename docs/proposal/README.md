# Project Proposal (M1)

| File | Description |
|---|---|
| [M1_Wnesny_proposal.pdf](M1_Wnesny_proposal.pdf) | M1 proposal: *"wnesny — Interest-Based Ride Matching"* (2 pages). It replaces the previous Nabd proposal (*Smart Hospital and Blood Donor Finder*), which is still available in Git history. |

The PDF is stored **exactly as supplied**; its content has not been edited.

> [!WARNING]
> **Pending correction: project name.** The title says **wnesny**, but the problem statement (section 1) still says *"**Rafeeq** (Arabic for 'companion') matches a driver and a rider…"*. Until the team supplies a corrected PDF, this document is **not final**. The official project name is **Wnesny (ونسني)**.

## Known differences between the proposal and the current implementation

These are recorded for transparency. They are not changes to the academic requirements.

| Topic | M1 proposal | Current implementation (database V1.0) |
|---|---|---|
| Passengers per ride | "available seats" / "seat capacity" | Exactly one accepted passenger per ride (partial unique index) |
| Database entities | users, drivers, riders, interests, user_interests, areas, ride_requests, trips, ratings, matches | users, user_profiles, interests, user_interests, rides, ride_requests, conversations, messages, reviews, notifications. Driver/rider are roles of one account, not separate tables. |
| Gender / safety preferences | Hard constraint | Not modelled yet |
| Location | ~50 coarse Cairo areas (OpenStreetMap) | Free-text addresses with optional latitude/longitude |
| AI component | CSP (backtracking, MRV, forward checking) + Naive Bayes ranking | Not implemented yet |
| Synthetic data, statistics, dashboard | Planned | Not implemented yet |

The team needs to decide whether to align the implementation with the proposal or to document these as approved design changes.

