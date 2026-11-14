"""Database constraint tests for Wnesny."""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    UserProfile,
    Interest,
    Ride,
    RideRequest,
    Conversation,
    Message,
    Review,
    Notification,
    user_interests,
)


def test_unique_email_constraint(db_session):
    """Test that duplicate emails are rejected by unique constraint."""
    u1 = User(full_name="User One", email="same@example.com", password="Password123")
    db_session.add(u1)
    db_session.commit()

    u2 = User(full_name="User Two", email="same@example.com", password="Password123")
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_interest_name_constraint(db_session):
    """Test that duplicate interest names are rejected."""
    i1 = Interest(name="Robotics", category="Technology")
    db_session.add(i1)
    db_session.commit()

    i2 = Interest(name="Robotics", category="Engineering")
    db_session.add(i2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_interests_composite_primary_key(db_session):
    """Test that duplicate user-interest assignments are rejected by composite primary key."""
    user = User(full_name="User Test", email="utest@example.com", password="Password123")
    interest = Interest(name="Tennis", category="Sports")
    db_session.add_all([user, interest])
    db_session.commit()

    # Insert raw row into association table
    ins1 = user_interests.insert().values(user_id=user.id, interest_id=interest.id)
    db_session.execute(ins1)
    db_session.commit()

    # Attempt duplicate insert
    ins2 = user_interests.insert().values(user_id=user.id, interest_id=interest.id)
    with pytest.raises(IntegrityError):
        db_session.execute(ins2)
        db_session.commit()
    db_session.rollback()


def test_invalid_education_visibility_rejected(db_session):
    """Test that invalid education visibility values are rejected."""
    user = User(full_name="Edu User", email="edu@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    with pytest.raises(ValueError):
        UserProfile(user_id=user.id, education_visibility="invalid_visibility")


def test_invalid_ride_status_rejected(db_session):
    """Test that invalid ride statuses are rejected."""
    driver = User(full_name="Driver Test", email="dtest@example.com", password="Password123")
    db_session.add(driver)
    db_session.commit()

    with pytest.raises(ValueError):
        Ride(
            driver_id=driver.id,
            origin_address="A",
            destination_address="B",
            departure_at=datetime.now(timezone.utc),
            status="flying",
        )


def test_invalid_request_status_rejected(db_session):
    """Test that invalid request statuses are rejected."""
    driver = User(full_name="D ReqTest", email="dreq@example.com", password="Password123")
    passenger = User(full_name="P ReqTest", email="preq@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc),
    )
    db_session.add(ride)
    db_session.commit()

    with pytest.raises(ValueError):
        RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="unknown_status")


def test_duplicate_ride_request_rejected(db_session):
    """Test that duplicate requests by the same passenger for the same ride are rejected."""
    driver = User(full_name="D Dup", email="ddup@example.com", password="Password123")
    passenger = User(full_name="P Dup", email="pdup@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()

    req1 = RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="pending")
    db_session.add(req1)
    db_session.commit()

    # Second request by same passenger for same ride
    req2 = RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="pending")
    db_session.add(req2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_single_accepted_passenger_partial_index(db_session):
    """CRITICAL: Enforce at most ONE accepted request per ride via partial unique index."""
    driver = User(full_name="D Single", email="dsingle@example.com", password="Password123")
    p1 = User(full_name="Pass One", email="p1single@example.com", password="Password123")
    p2 = User(full_name="Pass Two", email="p2single@example.com", password="Password123")
    db_session.add_all([driver, p1, p2])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()

    # First passenger request is accepted
    req1 = RideRequest(ride_id=ride.id, passenger_id=p1.id, status="accepted")
    db_session.add(req1)
    db_session.commit()

    # Second passenger request also attempts to be accepted for the same ride
    req2 = RideRequest(ride_id=ride.id, passenger_id=p2.id, status="accepted")
    db_session.add(req2)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_no_self_review_constraint(db_session):
    """Test that users cannot review themselves."""
    user = User(full_name="Self Rev", email="selfrev@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    ride = Ride(
        driver_id=user.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc),
        status="completed",
    )
    db_session.add(ride)
    db_session.commit()

    with pytest.raises(ValueError):
        Review(
            ride_id=ride.id,
            reviewer_id=user.id,
            reviewed_user_id=user.id,
            rating=5,
        )


def test_rating_range_constraint(db_session):
    """Test that ratings outside 1-5 are rejected."""
    u1 = User(full_name="U1 Rate", email="u1rate@example.com", password="Password123")
    u2 = User(full_name="U2 Rate", email="u2rate@example.com", password="Password123")
    db_session.add_all([u1, u2])
    db_session.commit()

    ride = Ride(
        driver_id=u1.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc),
        status="completed",
    )
    db_session.add(ride)
    db_session.commit()

    with pytest.raises(ValueError):
        Review(ride_id=ride.id, reviewer_id=u1.id, reviewed_user_id=u2.id, rating=6)

    with pytest.raises(ValueError):
        Review(ride_id=ride.id, reviewer_id=u1.id, reviewed_user_id=u2.id, rating=0)


def test_unique_review_per_ride_and_pair(db_session):
    """Test that duplicate reviews for the same ride, reviewer, and reviewed user are rejected."""
    driver = User(full_name="D DupRev", email="dduprev@example.com", password="Password123")
    passenger = User(full_name="P DupRev", email="pduprev@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc),
        status="completed",
    )
    db_session.add(ride)
    db_session.commit()

    r1 = Review(
        ride_id=ride.id,
        reviewer_id=passenger.id,
        reviewed_user_id=driver.id,
        rating=5,
    )
    db_session.add(r1)
    db_session.commit()

    # Attempt second review by same reviewer for same ride and driver
    r2 = Review(
        ride_id=ride.id,
        reviewer_id=passenger.id,
        reviewed_user_id=driver.id,
        rating=4,
    )
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_empty_message_rejected(db_session):
    """Test that empty message content is rejected."""
    user = User(full_name="Msg User", email="muser@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    with pytest.raises(ValueError):
        Message(conversation_id=1, sender_id=user.id, content="   ")



def test_deleting_driver_with_rides_is_blocked_and_history_preserved(db_session):
    """Deleting a user who drove a ride must fail; the ride must survive."""
    driver = User(full_name="Hist Driver", email="hist.driver@example.com", password="Password123")
    db_session.add(driver)
    db_session.commit()
    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()
    ride_id = ride.id

    # Load the collection so an ORM-level cascade would apply if configured.
    assert len(driver.rides_as_driver) == 1
    db_session.delete(driver)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.get(Ride, ride_id) is not None


def test_deleting_passenger_with_requests_is_blocked(db_session):
    """Deleting a user who requested a ride must fail; the request must survive."""
    driver = User(full_name="D Keep", email="dkeep@example.com", password="Password123")
    passenger = User(full_name="P Keep", email="pkeep@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()
    ride = Ride(
        driver_id=driver.id,
        origin_address="A",
        destination_address="B",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()
    req = RideRequest(ride_id=ride.id, passenger_id=passenger.id)
    db_session.add(req)
    db_session.commit()
    req_id = req.id

    assert len(passenger.ride_requests) == 1
    db_session.delete(passenger)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.get(RideRequest, req_id) is not None
