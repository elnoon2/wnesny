"""Regression tests for the issues found in the idea-vs-code review.

Each test names the rule from the Wnesny idea that it protects.
"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.models import Notification, RideRequest
from app.services import database_service as svc
from app.services.database_service import DatabaseServiceError

ROOT = Path(__file__).resolve().parent.parent


def tomorrow(days=1):
    return datetime.now(timezone.utc) + timedelta(days=days)


@pytest.fixture()
def people(db_session):
    """A driver, two passengers and an outsider."""
    return {
        name: svc.create_user(name.title(), f"{name}@wnesny.com", "Password123")
        for name in ("driver", "ana", "omar", "outsider")
    }


@pytest.fixture()
def ride_with_request(people):
    ride = svc.create_ride(people["driver"].id, "Maadi", "Badya", tomorrow())
    req = svc.submit_ride_request(ride.id, people["ana"].id)
    return ride, req


# --------------------------------------------------------------- configuration

def test_unknown_environment_name_fails_fast():
    """A typo like 'prodcution' must not silently run the insecure dev config."""
    with pytest.raises(ValueError, match="Unknown environment 'prodcution'"):
        create_app("prodcution")


def test_known_environment_names_still_work():
    assert create_app("testing").config["TESTING"] is True


# ---------------------------------------- only the driver answers ride requests

def test_only_the_driver_can_accept(people, ride_with_request):
    """Idea: the DRIVER accepts exactly one passenger."""
    ride, req = ride_with_request
    for impostor in ("ana", "outsider"):
        with pytest.raises(DatabaseServiceError, match="Only the driver"):
            svc.accept_ride_request(req.id, people[impostor].id)
    assert req.status == "pending"
    accepted, _conv = svc.accept_ride_request(req.id, people["driver"].id)
    assert accepted.status == "accepted"


def test_only_the_driver_can_reject(people, ride_with_request):
    _ride, req = ride_with_request
    with pytest.raises(DatabaseServiceError, match="Only the driver"):
        svc.reject_ride_request(req.id, people["omar"].id)
    assert svc.reject_ride_request(req.id, people["driver"].id).status == "rejected"


def test_accept_unknown_request(people):
    with pytest.raises(DatabaseServiceError, match="does not exist"):
        svc.accept_ride_request(9999, people["driver"].id)


def test_database_conflict_becomes_a_service_error(people, ride_with_request, monkeypatch):
    """If two accepts race, the DB constraint wins and the caller gets a clear error."""
    _ride, req = ride_with_request

    def boom():
        raise IntegrityError("INSERT", {}, Exception("uq_accepted_request_per_ride"))

    monkeypatch.setattr(svc.db.session, "commit", boom)
    with pytest.raises(DatabaseServiceError, match="already has an accepted passenger"):
        svc.accept_ride_request(req.id, people["driver"].id)


# --------------------------------------------------------------- ride lifecycle

def test_full_lifecycle_opens_reviews(people, ride_with_request, db_session):
    """Idea: after the ride is completed, the two can review each other."""
    ride, req = ride_with_request
    svc.accept_ride_request(req.id, people["driver"].id)

    with pytest.raises(DatabaseServiceError, match="Only rides in progress"):
        svc.complete_ride(ride.id, people["driver"].id)  # cannot skip 'in_progress'

    assert svc.start_ride(ride.id, people["driver"].id).status == "in_progress"
    assert svc.complete_ride(ride.id, people["driver"].id).status == "completed"

    kinds = {
        (n.user_id, n.type)
        for n in db_session.query(Notification).filter_by(ride_id=ride.id)
    }
    assert (people["ana"].id, "ride_completed") in kinds
    assert (people["driver"].id, "ride_completed") in kinds

    svc.create_review(ride.id, people["ana"].id, people["driver"].id, 5)
    svc.create_review(ride.id, people["driver"].id, people["ana"].id, 4)


def test_lifecycle_needs_driver_and_accepted_passenger(people, ride_with_request):
    ride, req = ride_with_request
    with pytest.raises(DatabaseServiceError, match="no accepted passenger"):
        svc.start_ride(ride.id, people["driver"].id)
    svc.accept_ride_request(req.id, people["driver"].id)
    with pytest.raises(DatabaseServiceError, match="Only the driver"):
        svc.start_ride(ride.id, people["ana"].id)
    svc.start_ride(ride.id, people["driver"].id)
    with pytest.raises(DatabaseServiceError, match="Only scheduled rides can be started"):
        svc.start_ride(ride.id, people["driver"].id)


def test_ride_in_progress_cannot_be_cancelled(people, ride_with_request):
    ride, req = ride_with_request
    svc.accept_ride_request(req.id, people["driver"].id)
    svc.start_ride(ride.id, people["driver"].id)
    with pytest.raises(DatabaseServiceError, match="Only scheduled rides can be cancelled"):
        svc.cancel_ride(ride.id, people["driver"].id)


def test_cancelling_a_ride_notifies_pending_passengers(people, ride_with_request, db_session):
    ride, _req = ride_with_request
    svc.submit_ride_request(ride.id, people["omar"].id)
    svc.cancel_ride(ride.id, people["driver"].id)
    for name in ("ana", "omar"):
        assert db_session.query(Notification).filter_by(
            user_id=people[name].id, type="ride_cancelled", ride_id=ride.id
        ).count() == 1
    assert {r.status for r in db_session.query(RideRequest)} == {"cancelled"}


# ----------------------------------------- passenger cancels after being accepted

def test_accepted_passenger_can_cancel_and_ride_reopens(people, ride_with_request, db_session):
    """The seat is freed: chat frozen, driver told, another passenger can be accepted."""
    ride, req = ride_with_request
    _acc, conv = svc.accept_ride_request(req.id, people["driver"].id)

    assert svc.cancel_ride_request(req.id, people["ana"].id).status == "cancelled"
    assert conv.is_active is False
    assert ride.status == "scheduled"
    assert db_session.query(Notification).filter_by(
        user_id=people["driver"].id, type="request_cancelled", ride_id=ride.id
    ).count() == 1
    with pytest.raises(DatabaseServiceError, match="Conversation|inactive"):
        svc.send_message(conv.id, people["ana"].id, "hello?")

    new_req = svc.submit_ride_request(ride.id, people["omar"].id)
    svc.accept_ride_request(new_req.id, people["driver"].id)
    assert new_req.status == "accepted"


def test_accepted_request_cannot_be_cancelled_once_ride_started(people, ride_with_request):
    ride, req = ride_with_request
    svc.accept_ride_request(req.id, people["driver"].id)
    svc.start_ride(ride.id, people["driver"].id)
    with pytest.raises(DatabaseServiceError, match="still scheduled"):
        svc.cancel_ride_request(req.id, people["ana"].id)


def test_only_the_passenger_can_cancel_their_request(people, ride_with_request):
    _ride, req = ride_with_request
    with pytest.raises(DatabaseServiceError, match="only cancel your own"):
        svc.cancel_ride_request(req.id, people["omar"].id)


# ---------------------------------------------------------------- ride validation

@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"origin_address": "   "}, "cannot be empty"),
        ({"destination_address": ""}, "cannot be empty"),
        ({"destination_address": "maadi"}, "must be different"),
        ({"origin_address": "x" * 201}, "at most 200"),
        ({"departure_at": datetime(2001, 1, 1, tzinfo=timezone.utc)}, "in the future"),
        ({"departure_at": datetime(2001, 1, 1)}, "in the future"),  # naive datetime
        ({"origin_latitude": 30.0}, "given together"),
        ({"destination_longitude": 31.2}, "given together"),
        ({"origin_latitude": 95.0, "origin_longitude": 31.0}, "between -90 and 90"),
    ],
)
def test_create_ride_rejects_bad_input(people, kwargs, message):
    args = {
        "driver_id": people["driver"].id,
        "origin_address": "Maadi",
        "destination_address": "Badya",
        "departure_at": tomorrow(),
    }
    args.update(kwargs)
    with pytest.raises(DatabaseServiceError, match=message):
        svc.create_ride(**args)


def test_create_ride_accepts_complete_coordinates(people):
    ride = svc.create_ride(
        people["driver"].id, " Maadi ", "Badya", tomorrow(),
        origin_latitude=29.96, origin_longitude=31.25,
    )
    assert ride.origin_address == "Maadi" and ride.origin_longitude == 31.25


# ------------------------------------------------------------ account and profile

@pytest.mark.parametrize("email", ["not-an-email", "a@b", "a b@c.com", "@c.com", "   "])
def test_create_user_rejects_bad_email(db_session, email):
    with pytest.raises(DatabaseServiceError):
        svc.create_user("Someone", email, "Password123")


def test_create_user_rejects_short_password_and_blank_name(db_session):
    with pytest.raises(DatabaseServiceError, match="at least 8"):
        svc.create_user("Someone", "s@wnesny.com", "short")
    with pytest.raises(DatabaseServiceError, match="Full name"):
        svc.create_user("  ", "s@wnesny.com", "Password123")


def test_profile_validates_graduation_year_and_visibility(people):
    uid = people["ana"].id
    with pytest.raises(DatabaseServiceError, match="graduation_year"):
        svc.create_user_profile(uid, graduation_year=1800)
    with pytest.raises(DatabaseServiceError, match="education_visibility"):
        svc.create_user_profile(uid, education_visibility="everyone")
    assert svc.create_user_profile(uid, graduation_year=2028).graduation_year == 2028


# ------------------------------------------------------------------ repository

def test_python_files_have_no_bom():
    bad = [
        str(p.relative_to(ROOT))
        for p in list((ROOT / "app").rglob("*.py")) + [ROOT / "run.py", ROOT / "config.py"]
        if p.read_bytes().startswith(b"\xef\xbb\xbf")
    ]
    assert bad == []


def test_relative_markdown_links_point_to_existing_files():
    """README and docs must not link to files that do not exist."""
    link = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
    broken = []
    for md in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md"), *(ROOT / "data").rglob("*.md")]:
        for target in link.findall(md.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("<"):
                continue  # external URL or placeholder
            if not (md.parent / target).resolve().exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    assert broken == []
