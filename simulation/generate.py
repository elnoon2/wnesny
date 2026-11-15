"""Seeded generator for the Wnesny synthetic dataset (M2).

Usage (from the repository root)::

    python -m simulation.generate                 # seed 42, writes to data/raw/
    python -m simulation.generate --seed 7 --users 800 --trips 4000

Output files (all CSV, UTF-8, header row, no index column):

    areas.csv, interests.csv, users.csv, user_interests.csv, trips.csv

Everything is simulated. No real person, phone number, e-mail or location is
used. The same seed always produces the same files. The data dictionary and the
list of simplifications are in ``data/README.md``.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from seed_interests import INITIAL_INTERESTS
from simulation import rating_model
from simulation.areas import AREAS

DEFAULT_SEED = 42
DEFAULT_USERS = 600
DEFAULT_TRIPS = 3000
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "raw"

# Simulated period (Cairo local clock time, no time-zone conversion).
START_DATE = datetime(2026, 8, 1)
DAYS = 92  # 1 Aug 2026 to 31 Oct 2026

ROLES = ("driver", "rider", "both")
ROLE_WEIGHTS = (0.35, 0.55, 0.10)
AGE_GROUPS = ("18-24", "25-34", "35-44", "45+")
AGE_WEIGHTS = (0.40, 0.35, 0.15, 0.10)
GENDER_PREFERENCES = ("no_preference", "same_gender")
GENDER_PREF_WEIGHTS = (0.85, 0.15)

# Interest "personas": each user belongs to one cluster and draws most of the
# interests from its categories. This makes shared interests vary between pairs.
CLUSTERS = {
    "tech_business": ("Technology", "Business"),
    "sports": ("Sports",),
    "arts_music": ("Arts & Culture", "Music"),
    "lifestyle_social": ("Lifestyle", "Gaming & Hobbies", "Social"),
}
CLUSTER_WEIGHTS = (0.35, 0.20, 0.25, 0.20)
IN_CLUSTER_SHARE = 0.80
INTERESTS_PER_USER_MEAN = 5.0  # Poisson mean, clipped to [1, 10]

# Trip model.
HOME_ORIGIN_PROBABILITY = 0.70
MIN_DISTANCE_KM = 3.0
CIRCUITY = 1.3  # road distance = straight-line distance x 1.3
PEAK_SHARE = 0.60
PEAK_HOURS = ((7, 10), (16, 20))
SPEED_PEAK_KMH = 22.0
SPEED_OFFPEAK_KMH = 38.0
DURATION_SIGMA = 0.20  # log-normal noise on the duration
DETOUR_SHAPE = 2.0  # gamma distribution of the pickup detour (minutes)
DETOUR_SCALE = 3.5
DETOUR_MAX = 25.0


@dataclass
class Dataset:
    areas: list[dict]
    interests: list[dict]
    users: list[dict]
    user_interests: list[dict]
    trips: list[dict]


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres (works with numpy arrays)."""
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def _build_areas() -> list[dict]:
    return [
        {
            "area_id": i,
            "name": name,
            "zone": zone,
            "latitude": lat,
            "longitude": lon,
            "popularity": pop,
        }
        for i, (name, zone, lat, lon, pop) in enumerate(AREAS, start=1)
    ]


def _build_interests() -> list[dict]:
    return [
        {"interest_id": i, "name": it["name"], "category": it["category"]}
        for i, it in enumerate(INITIAL_INTERESTS, start=1)
    ]


def _build_users(rng, n_users, areas, interests):
    """Create users and their interests (long format, one row per pair)."""
    roles = rng.choice(ROLES, size=n_users, p=ROLE_WEIGHTS)
    ages = rng.choice(AGE_GROUPS, size=n_users, p=AGE_WEIGHTS)
    prefs = rng.choice(GENDER_PREFERENCES, size=n_users, p=GENDER_PREF_WEIGHTS)
    cluster_names = list(CLUSTERS)
    clusters = rng.choice(cluster_names, size=n_users, p=CLUSTER_WEIGHTS)
    # Home areas are chosen with the same popularity weights as trips.
    pop = np.array([a["popularity"] for a in areas], dtype=float)
    homes = rng.choice(len(areas), size=n_users, p=pop / pop.sum())
    seats = rng.integers(1, 4, size=n_users)

    by_category: dict[str, list[int]] = {}
    for it in interests:
        by_category.setdefault(it["category"], []).append(it["interest_id"])
    all_ids = [it["interest_id"] for it in interests]

    users, user_interests = [], []
    for idx in range(n_users):
        uid = idx + 1
        k = int(np.clip(rng.poisson(INTERESTS_PER_USER_MEAN), 1, 10))
        cluster_ids = [
            i for cat in CLUSTERS[str(clusters[idx])] for i in by_category[cat]
        ]
        chosen: set[int] = set()
        while len(chosen) < k:
            pool = cluster_ids if rng.random() < IN_CLUSTER_SHARE else all_ids
            chosen.add(int(rng.choice(pool)))
        for iid in sorted(chosen):
            user_interests.append({"user_id": uid, "interest_id": iid})
        users.append(
            {
                "user_id": uid,
                "role": str(roles[idx]),
                "age_group": str(ages[idx]),
                "home_area_id": int(homes[idx]) + 1,
                "gender_preference": str(prefs[idx]),
                "seats": int(seats[idx]),
                "avg_rating": "",  # filled after the trips exist
            }
        )
    return users, user_interests


def _random_departures(rng, n):
    """Peak / off-peak mixture of departure times over the simulated period."""
    is_peak = rng.random(n) < PEAK_SHARE
    day = rng.integers(0, DAYS, size=n)
    hour = np.empty(n, dtype=int)
    for i in range(n):
        if is_peak[i]:
            lo, hi = PEAK_HOURS[int(rng.integers(0, len(PEAK_HOURS)))]
            hour[i] = rng.integers(lo, hi)
        else:
            # Off-peak: 6-7, 10-16 and 20-23
            hour[i] = int(rng.choice([6, 10, 11, 12, 13, 14, 15, 20, 21, 22]))
    minute = rng.integers(0, 60, size=n)
    times = [
        START_DATE + timedelta(days=int(d), hours=int(h), minutes=int(m))
        for d, h, m in zip(day, hour, minute)
    ]
    return times, is_peak.astype(int)


def _build_trips(rng, n_trips, areas, users, user_interests):
    area_lat = np.array([a["latitude"] for a in areas])
    area_lon = np.array([a["longitude"] for a in areas])
    pop = np.array([a["popularity"] for a in areas], dtype=float)
    pop_p = pop / pop.sum()

    interest_sets: dict[int, set[int]] = {u["user_id"]: set() for u in users}
    for row in user_interests:
        interest_sets[row["user_id"]].add(row["interest_id"])

    driver_ids = np.array([u["user_id"] for u in users if u["role"] in ("driver", "both")])
    rider_ids = np.array([u["user_id"] for u in users if u["role"] in ("rider", "both")])
    home = {u["user_id"]: u["home_area_id"] - 1 for u in users}
    driver_effect = {int(d): rng.normal(0, rating_model.DRIVER_SD) for d in driver_ids}

    departures, is_peak = _random_departures(rng, n_trips)

    # Draw everything that needs the random generator in a fixed order.
    drivers = rng.choice(driver_ids, size=n_trips)
    riders = np.empty(n_trips, dtype=int)
    for i in range(n_trips):
        r = int(rng.choice(rider_ids))
        while r == drivers[i]:
            r = int(rng.choice(rider_ids))
        riders[i] = r

    origins = np.empty(n_trips, dtype=int)
    dests = np.empty(n_trips, dtype=int)
    dist_km = np.empty(n_trips)
    for i in range(n_trips):
        for _ in range(100):  # redraw until the trip is long enough
            o = home[int(drivers[i])] if rng.random() < HOME_ORIGIN_PROBABILITY else int(
                rng.choice(len(areas), p=pop_p)
            )
            d = int(rng.choice(len(areas), p=pop_p))
            km = float(haversine_km(area_lat[o], area_lon[o], area_lat[d], area_lon[d])) * CIRCUITY
            if o != d and km >= MIN_DISTANCE_KM:
                break
        else:  # pragma: no cover - cannot happen with this area list
            raise RuntimeError("Could not draw a valid origin/destination pair.")
        origins[i], dests[i], dist_km[i] = o, d, km

    speed = np.where(is_peak == 1, SPEED_PEAK_KMH, SPEED_OFFPEAK_KMH)
    duration = dist_km / speed * 60.0 * rng.lognormal(0.0, DURATION_SIGMA, size=n_trips)
    detour = np.minimum(rng.gamma(DETOUR_SHAPE, DETOUR_SCALE, size=n_trips), DETOUR_MAX)

    shared = np.array(
        [len(interest_sets[int(d)] & interest_sets[int(r)]) for d, r in zip(drivers, riders)]
    )
    d_eff = np.array([driver_effect[int(d)] for d in drivers])
    noise = rng.normal(0, rating_model.NOISE_SD, size=n_trips)
    rating = rating_model.to_rating(
        rating_model.latent_score(shared, detour, is_peak, d_eff, noise)
    )

    order = np.argsort(departures)  # trips sorted by departure time
    trips = []
    for new_id, i in enumerate(order, start=1):
        trips.append(
            {
                "trip_id": new_id,
                "driver_id": int(drivers[i]),
                "rider_id": int(riders[i]),
                "origin_area_id": int(origins[i]) + 1,
                "destination_area_id": int(dests[i]) + 1,
                "departure_at": departures[i].strftime("%Y-%m-%d %H:%M"),
                "distance_km": round(float(dist_km[i]), 2),
                "duration_min": round(float(duration[i]), 1),
                "detour_min": round(float(detour[i]), 1),
                "shared_interests": int(shared[i]),
                "is_peak": int(is_peak[i]),
                "rating": int(rating[i]),
            }
        )
    return trips


def _fill_avg_rating(users, trips):
    """avg_rating = mean rating received as a driver (empty if never rated)."""
    totals: dict[int, list[int]] = {}
    for t in trips:
        totals.setdefault(t["driver_id"], []).append(t["rating"])
    for u in users:
        got = totals.get(u["user_id"])
        u["avg_rating"] = round(sum(got) / len(got), 2) if got else ""


def generate(seed: int = DEFAULT_SEED, n_users: int = DEFAULT_USERS, n_trips: int = DEFAULT_TRIPS) -> Dataset:
    """Build the whole dataset in memory. Same arguments give the same data."""
    if n_users < 20:
        raise ValueError("n_users must be at least 20.")
    if n_trips < 1:
        raise ValueError("n_trips must be at least 1.")
    rng = np.random.default_rng(seed)
    areas = _build_areas()
    interests = _build_interests()
    users, user_interests = _build_users(rng, n_users, areas, interests)
    trips = _build_trips(rng, n_trips, areas, users, user_interests)
    _fill_avg_rating(users, trips)
    return Dataset(areas, interests, users, user_interests, trips)


FILES = {
    "areas": "areas.csv",
    "interests": "interests.csv",
    "users": "users.csv",
    "user_interests": "user_interests.csv",
    "trips": "trips.csv",
}


def write_csv(dataset: Dataset, out_dir: Path) -> dict[str, Path]:
    """Write the dataset as CSV files and return the paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, filename in FILES.items():
        rows = getattr(dataset, key)
        path = out_dir / filename
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        paths[key] = path
    return paths


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Wnesny synthetic dataset.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--users", type=int, default=DEFAULT_USERS)
    parser.add_argument("--trips", type=int, default=DEFAULT_TRIPS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    dataset = generate(args.seed, args.users, args.trips)
    paths = write_csv(dataset, args.out)
    print(f"Seed {args.seed}: wrote {len(paths)} files to {args.out}")
    for key, path in paths.items():
        print(f"  {path.name}: {len(getattr(dataset, key))} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
