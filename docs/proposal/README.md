# Project Proposal (M1)

| File | Description |
|---|---|
| [M1_Wnesny_proposal.pdf](M1_Wnesny_proposal.pdf) | M1 proposal: *"wnesny — Interest-Based Ride Matching"* (2 pages). It replaces the previous Nabd proposal (*Smart Hospital and Blood Donor Finder*), which is still available in Git history. |

An updated version that matches the implemented design is in [../M1_Proposal_Updated_Wnesny.pdf](../M1_Proposal_Updated_Wnesny.pdf). The original stays here unchanged except for the correction below.

**Correction made on 15 Nov 2026:** section 1 of the PDF said *"Rafeeq (Arabic for 'companion') matches a driver and a rider…"*. It now says *"Wnesny (Arabic for 'keep me company') matches a driver and a rider…"*. The paragraph was re-broken so that "a good" moves to the next line; nothing else in the PDF was changed (all other text sits at the same positions). The original file is still available in Git history. The title line still reads "wnesny" in lower case, and the team number and supervisor fields are still empty.

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

**Decision recorded on 15 Nov 2026:** one accepted passenger per ride stays, so "available seats" in objective 2 is a documented design change and the report must say so. The other differences in this table still need a team decision (align the implementation or document them as approved design changes). In particular, gender and safety preferences are to be decided in M3.

