"""Load the synthetic CSV files into the Wnesny database (M2).

Usage (after ``flask --app run.py db upgrade``)::

    python -m simulation.generate        # creates data/raw/*.csv
    python -m simulation.load            # validates, then loads into the configured database

What is loaded
--------------
* ``interests.csv``       -> ``interests`` (matched by name, missing ones are added)
* ``users.csv``           -> ``users`` (fake names and ``example.com`` e-mails, one shared dummy password hash)
* ``user_interests.csv``  -> ``user_interests``
* ``trips.csv``           -> ``rides`` (status ``completed``), one accepted ``ride_requests`` row per trip
                             and one ``reviews`` row (rider rates driver)

``areas.csv`` has no table: the current schema stores origin and destination as
an address string plus optional coordinates, so the area name and its
coordinates are copied into the ride. Chat messages and notifications are not
simulated.

The loader inserts rows directly (it does not call the service layer, which
would refuse reviews for past rides and create conversations). All database
constraints still apply. It refuses to run twice: if simulated users already
exist it stops without changing anything.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import insert, select
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Interest, Review, Ride, RideRequest, User, user_interests
from simulation.generate import DEFAULT_OUT, START_DATE
from simulation.validate import read_tables, validate_tables

EMAIL_PREFIX = "sim.user"
EMAIL_DOMAIN = "example.com"  # reserved for documentation, never a real mailbox
DUMMY_PASSWORD = "simulated-password"  # not secret: these accounts are fake


class LoadError(Exception):
    """The data could not be loaded (invalid data, or already loaded)."""


def _email(user_id: int) -> str:
    return f"{EMAIL_PREFIX}{user_id:04d}@{EMAIL_DOMAIN}"


def load_into_db(data_dir: Path = DEFAULT_OUT) -> dict[str, int]:
    """Validate and load the CSV files. Must run inside an app context.

    Returns the number of rows inserted per table. Raises :class:`LoadError`
    if the data is invalid or simulated users are already in the database.
    """
    tables = read_tables(Path(data_dir))
    problems = validate_tables(tables)
    if problems:
        raise LoadError(f"{len(problems)} validation problem(s); first: {problems[0]}")

    already = db.session.scalar(
        select(User.id).where(User.email.like(f"{EMAIL_PREFIX}%@{EMAIL_DOMAIN}")).limit(1)
    )
    if already is not None:
        raise LoadError("Simulated users are already in the database; nothing was changed.")

    created_at = START_DATE.replace(tzinfo=timezone.utc) - timedelta(days=30)
    counts = {"interests": 0, "users": 0, "user_interests": 0, "rides": 0, "ride_requests": 0, "reviews": 0}

    try:
        # Interests: reuse rows that exist (same name), add the missing ones.
        interest_map: dict[int, int] = {}
        for row in tables["interests"]:
            obj = db.session.scalar(select(Interest).where(Interest.name == row["name"]))
            if obj is None:
                obj = Interest(name=row["name"], category=row["category"])
                db.session.add(obj)
                db.session.flush()
                counts["interests"] += 1
            interest_map[int(row["interest_id"])] = obj.id

        # Users.
        password_hash = generate_password_hash(DUMMY_PASSWORD)
        user_map: dict[int, int] = {}
        for row in tables["users"]:
            uid = int(row["user_id"])
            user = User(
                full_name=f"Sim User {uid:04d}",
                email=_email(uid),
                password_hash=password_hash,
                created_at=created_at,
            )
            db.session.add(user)
            db.session.flush()
            user_map[uid] = user.id
            counts["users"] += 1

        db.session.execute(
            insert(user_interests),
            [
                {"user_id": user_map[int(r["user_id"])], "interest_id": interest_map[int(r["interest_id"])]}
                for r in tables["user_interests"]
            ],
        )
        counts["user_interests"] = len(tables["user_interests"])

        # Trips -> rides, accepted requests and reviews.
        areas = {int(a["area_id"]): a for a in tables["areas"]}
        for t in tables["trips"]:
            departure = datetime.strptime(t["departure_at"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            origin, dest = areas[int(t["origin_area_id"])], areas[int(t["destination_area_id"])]
            ride = Ride(
                driver_id=user_map[int(t["driver_id"])],
                origin_address=origin["name"],
                destination_address=dest["name"],
                origin_latitude=float(origin["latitude"]),
                origin_longitude=float(origin["longitude"]),
                destination_latitude=float(dest["latitude"]),
                destination_longitude=float(dest["longitude"]),
                departure_at=departure,
                status="completed",
                created_at=departure - timedelta(days=1),
            )
            db.session.add(ride)
            db.session.flush()
            passenger = user_map[int(t["rider_id"])]
            db.session.add(
                RideRequest(
                    ride_id=ride.id,
                    passenger_id=passenger,
                    status="accepted",
                    created_at=departure - timedelta(hours=12),
                    updated_at=departure - timedelta(hours=6),
                )
            )
            db.session.add(
                Review(
                    ride_id=ride.id,
                    reviewer_id=passenger,
                    reviewed_user_id=ride.driver_id,
                    rating=int(t["rating"]),
                    created_at=departure + timedelta(minutes=float(t["duration_min"]) + 5),
                )
            )
            counts["rides"] += 1
            counts["ride_requests"] += 1
            counts["reviews"] += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return counts


def main(argv=None) -> int:
    from app import create_app

    argv = sys.argv[1:] if argv is None else argv
    data_dir = Path(argv[0]) if argv else DEFAULT_OUT
    app = create_app()
    with app.app_context():
        from sqlalchemy import inspect

        if not inspect(db.engine).has_table(User.__tablename__):
            print("The database has no tables. Run 'flask --app run.py db upgrade' first.")
            return 1
        try:
            counts = load_into_db(data_dir)
        except LoadError as exc:
            print(f"Not loaded: {exc}")
            return 1
    print("Loaded:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
