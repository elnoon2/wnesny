"""Unit and integration tests for the Wnesny database service layer and business rules."""

from datetime import datetime, timezone, timedelta
import pytest
from app.services.database_service import (
    create_user,
    create_user_profile,
    assign_interests_to_user,
    create_ride,
    submit_ride_request,
    accept_ride_request,
    reject_ride_request,
    cancel_ride_request,
    cancel_ride,
    create_conversation_for_accepted_request,
    send_message,
    create_review,
    DatabaseServiceError,
)
from app.models import Interest, RideRequest, Notification


def test_driver_cannot_request_own_ride(db_session):
    """Business Rule: A driver cannot submit a request for their own ride."""
    driver = create_user("Omar Driver", "driver@wnesny.com", "Password123")
    ride = create_ride(
        driver_id=driver.id,
        origin_address="Dokki",
        destination_address="Badya",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    with pytest.raises(DatabaseServiceError, match="A driver cannot request to join their own ride"):
        submit_ride_request(ride_id=ride.id, passenger_id=driver.id)


def test_cannot_request_cancelled_or_completed_ride(db_session):
    """Business Rule: Cancelled or completed rides cannot receive new requests."""
    driver = create_user("Driver B", "driverb@wnesny.com", "Password123")
    passenger = create_user("Pass B", "passb@wnesny.com", "Password123")
    ride = create_ride(
        driver_id=driver.id,
        origin_address="Dokki",
        destination_address="Badya",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    # Cancel the ride
    cancel_ride(ride_id=ride.id, driver_id=driver.id, reason="Vehicle maintenance")

    with pytest.raises(DatabaseServiceError, match="Cannot request a ride with status 'cancelled'"):
        submit_ride_request(ride_id=ride.id, passenger_id=passenger.id)


def test_cannot_request_if_already_has_accepted_passenger(db_session):
    """Business Rule: If a ride already has an accepted passenger, new requests are rejected."""
    driver = create_user("Driver C", "driverc@wnesny.com", "Password123")
    p1 = create_user("Pass 1", "pass1@wnesny.com", "Password123")
    p2 = create_user("Pass 2", "pass2@wnesny.com", "Password123")

    ride = create_ride(
        driver_id=driver.id,
        origin_address="Maadi",
        destination_address="October",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    req1 = submit_ride_request(ride_id=ride.id, passenger_id=p1.id)
    accept_ride_request(req1.id)

    with pytest.raises(DatabaseServiceError, match="This ride already has an accepted passenger"):
        submit_ride_request(ride_id=ride.id, passenger_id=p2.id)


def test_transactional_acceptance_and_competing_requests(db_session):
    """Business Rule: Accepting a request automatically rejects competing requests, creates a conversation and notifications."""
    driver = create_user("Driver D", "driverd@wnesny.com", "Password123")
    p1 = create_user("Applicant 1", "app1@wnesny.com", "Password123")
    p2 = create_user("Applicant 2", "app2@wnesny.com", "Password123")

    ride = create_ride(
        driver_id=driver.id,
        origin_address="Zamalek",
        destination_address="Badya",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    req1 = submit_ride_request(ride_id=ride.id, passenger_id=p1.id)
    req2 = submit_ride_request(ride_id=ride.id, passenger_id=p2.id)

    # Accept req1
    accepted_req, conv = accept_ride_request(req1.id)

    assert accepted_req.status == "accepted"
    assert conv is not None
    assert conv.is_active is True
    assert conv.ride_request_id == req1.id

    # Verify req2 was automatically rejected
    db_session.refresh(req2)
    assert req2.status == "rejected"

    # Verify notifications were created
    p1_notif = Notification.query.filter_by(user_id=p1.id, type="request_accepted").first()
    assert p1_notif is not None

    p2_notif = Notification.query.filter_by(user_id=p2.id, type="request_rejected").first()
    assert p2_notif is not None


def test_ride_cancellation_preserves_history_and_deactivates_chat(db_session):
    """Business Rule: Cancelling an accepted ride preserves records, deactivates conversation, and notifies passenger."""
    driver = create_user("Driver E", "drivere@wnesny.com", "Password123")
    passenger = create_user("Pass E", "passe@wnesny.com", "Password123")

    ride = create_ride(
        driver_id=driver.id,
        origin_address="Nasr City",
        destination_address="Smart Village",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    req = submit_ride_request(ride_id=ride.id, passenger_id=passenger.id)
    _, conv = accept_ride_request(req.id)
    assert conv.is_active is True

    # Driver cancels the ride
    cancelled_ride = cancel_ride(ride_id=ride.id, driver_id=driver.id, reason="Emergency")
    assert cancelled_ride.status == "cancelled"

    # Check conversation is deactivated
    db_session.refresh(conv)
    assert conv.is_active is False

    # Check accepted request still preserved
    db_session.refresh(req)
    assert req.status == "accepted"

    # Check passenger received cancellation notification
    p_notif = Notification.query.filter_by(user_id=passenger.id, type="ride_cancelled").first()
    assert p_notif is not None
    assert "Emergency" in p_notif.content


def test_messaging_participant_authorization(db_session):
    """Business Rule: Only driver and accepted passenger can chat, and only while active."""
    driver = create_user("Driver F", "driverf@wnesny.com", "Password123")
    passenger = create_user("Pass F", "passf@wnesny.com", "Password123")
    intruder = create_user("Intruder", "intruder@wnesny.com", "Password123")

    ride = create_ride(
        driver_id=driver.id,
        origin_address="Heliopolis",
        destination_address="Badya",
        departure_at=datetime.now(timezone.utc) + timedelta(hours=6),
    )

    req = submit_ride_request(ride_id=ride.id, passenger_id=passenger.id)
    _, conv = accept_ride_request(req.id)

    # Driver sends message
    msg1 = send_message(conversation_id=conv.id, sender_id=driver.id, content="See you soon!")
    assert msg1.id is not None

    # Passenger sends message
    msg2 = send_message(conversation_id=conv.id, sender_id=passenger.id, content="Sounds great!")
    assert msg2.id is not None

    # Intruder tries to send message
    with pytest.raises(DatabaseServiceError, match="Only the driver and accepted passenger"):
        send_message(conversation_id=conv.id, sender_id=intruder.id, content="Hacked!")


def test_review_rules_and_participants_only(db_session):
    """Business Rule: Reviews are only permitted on completed rides between actual participants."""
    driver = create_user("Driver G", "driverg@wnesny.com", "Password123")
    passenger = create_user("Pass G", "passg@wnesny.com", "Password123")
    stranger = create_user("Stranger", "stranger@wnesny.com", "Password123")

    ride = create_ride(
        driver_id=driver.id,
        origin_address="Giza",
        destination_address="Badya",
        departure_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    req = submit_ride_request(ride_id=ride.id, passenger_id=passenger.id)
    accept_ride_request(req.id)

    # Attempt review while ride is still 'scheduled'
    with pytest.raises(DatabaseServiceError, match="Reviews can only be submitted after a ride is marked 'completed'"):
        create_review(ride_id=ride.id, reviewer_id=passenger.id, reviewed_user_id=driver.id, rating=5)

    # Mark ride completed
    ride.status = "completed"
    db_session.commit()

    # Stranger attempts review
    with pytest.raises(DatabaseServiceError, match="Reviews are only permitted between the driver and accepted passenger"):
        create_review(ride_id=ride.id, reviewer_id=stranger.id, reviewed_user_id=driver.id, rating=1)

    # Valid review
    rev = create_review(
        ride_id=ride.id,
        reviewer_id=passenger.id,
        reviewed_user_id=driver.id,
        rating=5,
        comment="Awesome trip!",
    )
    assert rev.id is not None

    # Duplicate review attempt
    with pytest.raises(DatabaseServiceError, match="You have already reviewed this user"):
        create_review(ride_id=ride.id, reviewer_id=passenger.id, reviewed_user_id=driver.id, rating=4)

