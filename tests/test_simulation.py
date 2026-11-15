"""Tests for the synthetic data layer (generator, validator and loader)."""

import copy
import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import Interest, Review, Ride, RideRequest, User
from simulation import areas as areas_module
from simulation.generate import generate, write_csv
from simulation.load import LoadError, load_into_db
from simulation.validate import read_tables, validate_dir, validate_tables

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def dataset():
    return generate(seed=1, n_users=120, n_trips=400)


@pytest.fixture()
def tables(dataset):
    """Plain dict-of-rows copy of the dataset, as the validator reads it from CSV."""
    return {
        key: [{k: str(v) for k, v in row.items()} for row in getattr(dataset, key)]
        for key in ("areas", "interests", "users", "user_interests", "trips")
    }


# ---------------------------------------------------------------- generator

def test_generator_row_counts(dataset):
    assert len(dataset.areas) == 50
    assert len(dataset.interests) == 32
    assert len(dataset.users) == 120
    assert len(dataset.trips) == 400
    assert len(dataset.user_interests) >= 120  # every user has at least one interest


def test_generator_is_deterministic():
    a = generate(seed=5, n_users=60, n_trips=100)
    b = generate(seed=5, n_users=60, n_trips=100)
    c = generate(seed=6, n_users=60, n_trips=100)
    assert a.trips == b.trips and a.users == b.users
    assert a.trips != c.trips


def test_generator_rejects_bad_sizes():
    with pytest.raises(ValueError):
        generate(n_users=5)
    with pytest.raises(ValueError):
        generate(n_trips=0)


def test_areas_are_unique_and_inside_cairo():
    names = [a[0] for a in areas_module.AREAS]
    assert len(names) == len(set(names)) == 50
    for name, _zone, lat, lon, pop in areas_module.AREAS:
        assert 29.7 <= lat <= 30.4 and 30.7 <= lon <= 31.9, name
        assert pop >= 1


def test_write_csv_creates_five_files(dataset, tmp_path):
    paths = write_csv(dataset, tmp_path)
    assert {p.name for p in paths.values()} == {
        "areas.csv", "interests.csv", "users.csv", "user_interests.csv", "trips.csv",
    }
    assert validate_dir(tmp_path) == []


def test_ratings_follow_the_hidden_model_direction(dataset):
    """More shared interests -> higher mean rating; longer detour -> lower."""
    trips = dataset.trips
    many = [t["rating"] for t in trips if t["shared_interests"] >= 2]
    none = [t["rating"] for t in trips if t["shared_interests"] == 0]
    assert sum(many) / len(many) > sum(none) / len(none)
    long_detour = [t["rating"] for t in trips if t["detour_min"] > 12]
    short_detour = [t["rating"] for t in trips if t["detour_min"] < 4]
    assert sum(long_detour) / len(long_detour) < sum(short_detour) / len(short_detour)


def test_matcher_does_not_import_rating_model():
    """The matcher must not see the hidden rating model (avoids circular evaluation)."""
    pattern = re.compile(r"rating_model")
    offenders = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "app").rglob("*.py")
        if pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


# ---------------------------------------------------------------- validator

def test_valid_dataset_has_no_problems(tables):
    assert validate_tables(tables) == []


def test_validate_dir_reports_missing_files(tmp_path):
    problems = validate_dir(tmp_path)
    assert problems and "missing file" in problems[0]


@pytest.mark.parametrize(
    "table,row,column,value,expected",
    [
        ("trips", 0, "rating", "6", "rating 6 outside 1-5"),
        ("trips", 0, "detour_min", "-1", "negative"),
        ("trips", 0, "distance_km", "0", "distance_km must be greater than"),
        ("trips", 0, "is_peak", "2", "is_peak must be 0 or 1"),
        ("trips", 0, "departure_at", "2025-01-01 10:00", "outside the simulated period"),
        ("trips", 0, "driver_id", "999999", "unknown driver_id"),
        ("trips", 0, "rating", "abc", "not a valid int"),
        ("users", 0, "role", "pilot", "role 'pilot'"),
        ("users", 0, "home_area_id", "999", "not in areas.csv"),
        ("areas", 0, "latitude", "75.0", "outside the Cairo range"),
    ],
)
def test_validator_catches_bad_values(tables, table, row, column, value, expected):
    bad = copy.deepcopy(tables)
    bad[table][row][column] = value
    problems = validate_tables(bad)
    assert any(expected in p for p in problems), problems


def test_validator_catches_same_driver_and_rider(tables):
    bad = copy.deepcopy(tables)
    bad["trips"][0]["rider_id"] = bad["trips"][0]["driver_id"]
    assert any("same user" in p for p in validate_tables(bad))


def test_validator_catches_rider_who_cannot_ride(tables):
    bad = copy.deepcopy(tables)
    driver_only = next(u["user_id"] for u in bad["users"] if u["role"] == "driver")
    bad["trips"][0]["rider_id"] = driver_only
    assert any("cannot ride" in p for p in validate_tables(bad))


def test_validator_catches_duplicate_ids_and_trips(tables):
    bad = copy.deepcopy(tables)
    bad["users"][1]["user_id"] = bad["users"][0]["user_id"]
    bad["trips"].append(dict(bad["trips"][0], trip_id="9999"))
    problems = validate_tables(bad)
    assert any("duplicate user_id" in p for p in problems)
    assert any("duplicate of an earlier trip" in p for p in problems)


def test_validator_catches_wrong_shared_interest_count(tables):
    bad = copy.deepcopy(tables)
    bad["trips"][0]["shared_interests"] = str(int(bad["trips"][0]["shared_interests"]) + 3)
    assert any("shared_interests is" in p for p in validate_tables(bad))


def test_validator_catches_unknown_interest_and_wrong_columns(tables):
    bad = copy.deepcopy(tables)
    bad["user_interests"][0]["interest_id"] = "9999"
    assert any("unknown interest_id" in p for p in validate_tables(bad))
    worse = copy.deepcopy(tables)
    worse["trips"] = [{k: v for k, v in r.items() if k != "rating"} for r in worse["trips"]]
    assert any("columns are" in p for p in validate_tables(worse))


# ------------------------------------------------------------------- loader

@pytest.fixture()
def csv_dir(dataset, tmp_path):
    write_csv(dataset, tmp_path)
    return tmp_path


def test_loader_fills_the_database(app, db_session, csv_dir):
    with app.app_context():
        counts = load_into_db(csv_dir)
        assert counts["users"] == 120
        assert counts["rides"] == counts["ride_requests"] == counts["reviews"] == 400
        assert db.session.scalar(select(func.count(User.id))) == 120
        assert db.session.scalar(select(func.count(Interest.id))) == 32
        assert db.session.scalar(select(func.count(Ride.id))) == 400
        assert db.session.scalar(select(func.count(Review.id))) == 400
        accepted = db.session.scalar(
            select(func.count(RideRequest.id)).where(RideRequest.status == "accepted")
        )
        assert accepted == 400
        assert db.session.scalar(select(func.count(Ride.id)).where(Ride.status != "completed")) == 0


def test_loader_keeps_ratings_and_relations(app, db_session, csv_dir, dataset):
    with app.app_context():
        load_into_db(csv_dir)
        first = dataset.trips[0]
        ride = db.session.get(Ride, 1)
        review = db.session.scalar(select(Review).where(Review.ride_id == ride.id))
        assert review.rating == first["rating"]
        assert review.reviewed_user_id == ride.driver_id
        assert review.reviewer_id != ride.driver_id
        assert ride.requests[0].passenger_id == review.reviewer_id


def test_loader_reuses_existing_interests(app, db_session, csv_dir):
    with app.app_context():
        db.session.add(Interest(name="Artificial Intelligence", category="Technology"))
        db.session.commit()
        counts = load_into_db(csv_dir)
        assert counts["interests"] == 31
        assert db.session.scalar(select(func.count(Interest.id))) == 32


def test_loader_refuses_to_run_twice(app, db_session, csv_dir):
    with app.app_context():
        load_into_db(csv_dir)
        with pytest.raises(LoadError, match="already"):
            load_into_db(csv_dir)
        assert db.session.scalar(select(func.count(User.id))) == 120


def test_loader_rejects_invalid_data_and_changes_nothing(app, db_session, csv_dir):
    trips = csv_dir / "trips.csv"
    text = trips.read_text(encoding="utf-8").splitlines()
    header = text[0].split(",")
    cols = text[1].split(",")
    cols[header.index("rating")] = "9"
    text[1] = ",".join(cols)
    trips.write_text("\n".join(text) + "\n", encoding="utf-8")
    with app.app_context():
        with pytest.raises(LoadError, match="validation"):
            load_into_db(csv_dir)
        assert db.session.scalar(select(func.count(User.id))) == 0
