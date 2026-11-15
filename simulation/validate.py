"""Integrity checks for the generated CSV files (the "cleaning" step of M2).

The generator builds the data itself, so these checks are a safety net: they
must still pass after anyone edits the generator, replaces a file or adds
survey data later. Rows are never silently changed or dropped; every problem
is reported with its file and row so a person can decide what to do.

Usage::

    python -m simulation.validate            # checks data/raw/
    python -m simulation.validate path/to/dir

Exit code 0 means the data is valid, 1 means at least one problem was found.
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

from simulation.generate import (
    AGE_GROUPS,
    DEFAULT_OUT,
    FILES,
    GENDER_PREFERENCES,
    ROLES,
    START_DATE,
    DAYS,
)

# Cairo greater-area bounding box (generous), used to catch swapped lat/lon.
LAT_RANGE = (29.7, 30.4)
LON_RANGE = (30.7, 31.9)

COLUMNS = {
    "areas": ["area_id", "name", "zone", "latitude", "longitude", "popularity"],
    "interests": ["interest_id", "name", "category"],
    "users": ["user_id", "role", "age_group", "home_area_id", "gender_preference", "seats", "avg_rating"],
    "user_interests": ["user_id", "interest_id"],
    "trips": [
        "trip_id", "driver_id", "rider_id", "origin_area_id", "destination_area_id",
        "departure_at", "distance_km", "duration_min", "detour_min",
        "shared_interests", "is_peak", "rating",
    ],
}


def read_tables(data_dir: Path) -> dict[str, list[dict]]:
    """Read the five CSV files. Raises FileNotFoundError if one is missing."""
    tables = {}
    for key, filename in FILES.items():
        with (Path(data_dir) / filename).open(newline="", encoding="utf-8") as fh:
            tables[key] = list(csv.DictReader(fh))
    return tables


def _num(value, caster, where, problems):
    try:
        return caster(value)
    except (TypeError, ValueError):
        problems.append(f"{where}: '{value}' is not a valid {caster.__name__}")
        return None


def validate_tables(tables: dict[str, list[dict]]) -> list[str]:
    """Return a list of problems (empty list means the data is valid)."""
    problems: list[str] = []

    # 1. Columns and non-empty files.
    for key, cols in COLUMNS.items():
        rows = tables.get(key)
        if not rows:
            problems.append(f"{FILES[key]}: file is empty or missing")
            continue
        if list(rows[0].keys()) != cols:
            problems.append(f"{FILES[key]}: columns are {list(rows[0].keys())}, expected {cols}")
    if problems:
        return problems  # later checks would fail on missing columns

    # 2. Primary keys: present, integer, unique.
    def ids(key, col):
        seen, out = set(), []
        for n, row in enumerate(tables[key], start=2):
            v = _num(row[col], int, f"{FILES[key]} line {n} {col}", problems)
            if v is None:
                continue
            if v in seen:
                problems.append(f"{FILES[key]} line {n}: duplicate {col} {v}")
            seen.add(v)
            out.append(v)
        return seen

    area_ids = ids("areas", "area_id")
    interest_ids = ids("interests", "interest_id")
    user_ids = ids("users", "user_id")
    trip_ids = ids("trips", "trip_id")
    if len({r["name"] for r in tables["interests"]}) != len(tables["interests"]):
        problems.append("interests.csv: duplicate interest names")
    if len({r["name"] for r in tables["areas"]}) != len(tables["areas"]):
        problems.append("areas.csv: duplicate area names")

    # 3. Areas.
    for n, r in enumerate(tables["areas"], start=2):
        lat = _num(r["latitude"], float, f"areas.csv line {n} latitude", problems)
        lon = _num(r["longitude"], float, f"areas.csv line {n} longitude", problems)
        if lat is not None and not LAT_RANGE[0] <= lat <= LAT_RANGE[1]:
            problems.append(f"areas.csv line {n}: latitude {lat} outside the Cairo range {LAT_RANGE}")
        if lon is not None and not LON_RANGE[0] <= lon <= LON_RANGE[1]:
            problems.append(f"areas.csv line {n}: longitude {lon} outside the Cairo range {LON_RANGE}")

    # 4. Users.
    roles = {}
    for n, r in enumerate(tables["users"], start=2):
        uid = _num(r["user_id"], int, f"users.csv line {n}", problems)
        if r["role"] not in ROLES:
            problems.append(f"users.csv line {n}: role '{r['role']}' not in {ROLES}")
        if r["age_group"] not in AGE_GROUPS:
            problems.append(f"users.csv line {n}: age_group '{r['age_group']}' not in {AGE_GROUPS}")
        if r["gender_preference"] not in GENDER_PREFERENCES:
            problems.append(f"users.csv line {n}: gender_preference '{r['gender_preference']}' invalid")
        if _num(r["home_area_id"], int, f"users.csv line {n} home_area_id", problems) not in area_ids:
            problems.append(f"users.csv line {n}: home_area_id {r['home_area_id']} is not in areas.csv")
        seats = _num(r["seats"], int, f"users.csv line {n} seats", problems)
        if seats is not None and not 1 <= seats <= 3:
            problems.append(f"users.csv line {n}: seats {seats} outside 1-3")
        if r["avg_rating"] != "":
            avg = _num(r["avg_rating"], float, f"users.csv line {n} avg_rating", problems)
            if avg is not None and not 1 <= avg <= 5:
                problems.append(f"users.csv line {n}: avg_rating {avg} outside 1-5")
        roles[uid] = r["role"]

    # 5. user_interests: foreign keys and no duplicate pairs.
    pairs = set()
    for n, r in enumerate(tables["user_interests"], start=2):
        u = _num(r["user_id"], int, f"user_interests.csv line {n} user_id", problems)
        i = _num(r["interest_id"], int, f"user_interests.csv line {n} interest_id", problems)
        if u not in user_ids:
            problems.append(f"user_interests.csv line {n}: unknown user_id {u}")
        if i not in interest_ids:
            problems.append(f"user_interests.csv line {n}: unknown interest_id {i}")
        if (u, i) in pairs:
            problems.append(f"user_interests.csv line {n}: duplicate pair ({u}, {i})")
        pairs.add((u, i))

    # 6. Trips.
    first, last = START_DATE, START_DATE + timedelta(days=DAYS)
    for n, r in enumerate(tables["trips"], start=2):
        where = f"trips.csv line {n}"
        d = _num(r["driver_id"], int, f"{where} driver_id", problems)
        rd = _num(r["rider_id"], int, f"{where} rider_id", problems)
        o = _num(r["origin_area_id"], int, f"{where} origin_area_id", problems)
        de = _num(r["destination_area_id"], int, f"{where} destination_area_id", problems)
        if d not in user_ids:
            problems.append(f"{where}: unknown driver_id {d}")
        elif roles.get(d) not in ("driver", "both"):
            problems.append(f"{where}: user {d} is a '{roles[d]}' and cannot drive")
        if rd not in user_ids:
            problems.append(f"{where}: unknown rider_id {rd}")
        elif roles.get(rd) not in ("rider", "both"):
            problems.append(f"{where}: user {rd} is a '{roles[rd]}' and cannot ride")
        if d is not None and d == rd:
            problems.append(f"{where}: driver and rider are the same user {d}")
        if o not in area_ids or de not in area_ids:
            problems.append(f"{where}: unknown origin or destination area")
        if o is not None and o == de:
            problems.append(f"{where}: origin and destination are the same area {o}")
        try:
            when = datetime.strptime(r["departure_at"], "%Y-%m-%d %H:%M")
            if not first <= when < last:
                problems.append(f"{where}: departure_at {r['departure_at']} outside the simulated period")
        except ValueError:
            problems.append(f"{where}: departure_at '{r['departure_at']}' is not 'YYYY-MM-DD HH:MM'")
        for col, low in (("distance_km", 0.0), ("duration_min", 0.0)):
            v = _num(r[col], float, f"{where} {col}", problems)
            if v is not None and v <= low:
                problems.append(f"{where}: {col} must be greater than {low}, got {v}")
        detour = _num(r["detour_min"], float, f"{where} detour_min", problems)
        if detour is not None and detour < 0:
            problems.append(f"{where}: detour_min is negative ({detour})")
        shared = _num(r["shared_interests"], int, f"{where} shared_interests", problems)
        if shared is not None and shared < 0:
            problems.append(f"{where}: shared_interests is negative")
        if r["is_peak"] not in ("0", "1"):
            problems.append(f"{where}: is_peak must be 0 or 1, got '{r['is_peak']}'")
        rating = _num(r["rating"], int, f"{where} rating", problems)
        if rating is not None and not 1 <= rating <= 5:
            problems.append(f"{where}: rating {rating} outside 1-5")

    # 7. shared_interests must match the real overlap in user_interests.
    sets: dict[int, set[int]] = {}
    for r in tables["user_interests"]:
        try:
            sets.setdefault(int(r["user_id"]), set()).add(int(r["interest_id"]))
        except ValueError:
            pass
    for n, r in enumerate(tables["trips"], start=2):
        try:
            d, rd, shared = int(r["driver_id"]), int(r["rider_id"]), int(r["shared_interests"])
        except ValueError:
            continue
        actual = len(sets.get(d, set()) & sets.get(rd, set()))
        if actual != shared:
            problems.append(f"trips.csv line {n}: shared_interests is {shared} but the users share {actual}")

    # 8. Duplicate trip rows (same people, route and time).
    seen = set()
    for n, r in enumerate(tables["trips"], start=2):
        key = (r["driver_id"], r["rider_id"], r["origin_area_id"], r["destination_area_id"], r["departure_at"])
        if key in seen:
            problems.append(f"trips.csv line {n}: duplicate of an earlier trip")
        seen.add(key)

    return problems


def validate_dir(data_dir: Path = DEFAULT_OUT) -> list[str]:
    """Read and validate the CSV files in ``data_dir``."""
    try:
        tables = read_tables(Path(data_dir))
    except FileNotFoundError as exc:
        return [f"missing file: {exc.filename}"]
    return validate_tables(tables)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    data_dir = Path(argv[0]) if argv else DEFAULT_OUT
    problems = validate_dir(data_dir)
    if problems:
        print(f"{len(problems)} problem(s) found in {data_dir}:")
        for p in problems[:50]:
            print(f"  - {p}")
        if len(problems) > 50:
            print(f"  ... and {len(problems) - 50} more")
        return 1
    print(f"OK: all checks passed in {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
