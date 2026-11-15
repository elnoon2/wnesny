# AI-use statement

Tools used, what for, and how the output was checked. Updated at M2; to be completed before M5.

| Tool | Used for | How output was checked |
| --- | --- | --- |
| Claude (Anthropic) | Writing the synthetic data layer in `simulation/` (area list, seeded generator, hidden rating model, validator, database loader), its 29 tests in `tests/test_simulation.py`, the first EDA notebook `notebooks/01_eda.ipynb`, and the data dictionary in `data/README.md` | The generator, validator and loader were run; the full suite passes (103 tests: 42 existing, 29 for the data layer and 32 for the review fixes); the loader was run on a freshly migrated SQLite database (600 users, 3,000 rides, requests and reviews, no foreign-key errors); the notebook was executed end to end and every number in `data/README.md` was compared with the generated files and notebook output |
| Claude (Anthropic) | Reviewing the existing code and docs against the project idea, fixing the problems found (driver-only accept/reject, ride lifecycle `start_ride` / `complete_ride`, input validation, configuration check, misplaced and missing docs) and writing 32 regression tests in `tests/test_review_fixes.py` | Each problem was first reproduced with a small script on the original code, then fixed and covered by a test; the 42 original tests were kept (only their calls were adapted to the new signatures) and all 103 tests pass |

No data was invented: every figure in the documents comes from running the project's own code on the simulated dataset.
The area coordinates are approximate values typed in by hand and are not from OpenStreetMap (see `data/README.md`).

**Team confirmation (complete before merging):** *name of the member who read and ran `simulation/`, the tests and the notebook,
and can explain each file at the viva.* Add one row per tool if anyone used another AI tool.
