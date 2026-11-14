"""Tests for all 11 database relationships in Wnesny."""

from datetime import datetime, timezone, timedelta
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
)


def test_user_profile_one_to_one(db_session):
    """Test User <-> UserProfile 1:1 relationship."""
    user = User(full_name="Sara Profile", email="sara.profile@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    profile = UserProfile(user_id=user.id, bio="AI Enthusiast", education_visibility="public")
    db_session.add(profile)
    db_session.commit()

    # Query back
    queried_user = db_session.get(User, user.id)
    assert queried_user.profile is not None
    assert queried_user.profile.bio == "AI Enthusiast"
    assert queried_user.profile.user.id == user.id


def test_user_interests_many_to_many(db_session):
    """Test User <-> Interest M:N relationship through user_interests."""
    u1 = User(full_name="User One", email="u1@example.com", password="Password123")
    u2 = User(full_name="User Two", email="u2@example.com", password="Password123")
    i1 = Interest(name="Padel", category="Sports")
    i2 = Interest(name="AI", category="Technology")
    db_session.add_all([u1, u2, i1, i2])
    db_session.commit()

    # User 1 has both interests
    u1.interests.extend([i1, i2])
    # User 2 has only AI
    u2.interests.append(i2)
    db_session.commit()

    assert len(u1.interests) == 2
    assert len(u2.interests) == 1
    assert len(i2.users) == 2
    assert u1 in i2.users
    assert u2 in i2.users
    assert u2 not in i1.users


def test_user_rides_one_to_many(db_session):
    """Test User <-> Ride 1:N relationship (driver owns rides)."""
    driver = User(full_name="Driver Multi", email="multi@example.com", password="Password123")
    db_session.add(driver)
    db_session.commit()

    r1 = Ride(
        driver_id=driver.id,
        origin_address="Point A",
        destination_address="Point B",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    r2 = Ride(
        driver_id=driver.id,
        origin_address="Point C",
        destination_address="Point D",
        departure_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    assert len(driver.rides_as_driver) == 2
    assert r1.driver == driver
    assert r2.driver == driver


def test_ride_and_requests_relationships(db_session):
    """Test Ride <-> RideRequest 1:N and User <-> RideRequest 1:N."""
    driver = User(full_name="Driver Rel", email="drel@example.com", password="Password123")
    p1 = User(full_name="Pass One", email="p1@example.com", password="Password123")
    p2 = User(full_name="Pass Two", email="p2@example.com", password="Password123")
    db_session.add_all([driver, p1, p2])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Start",
        destination_address="End",
        departure_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db_session.add(ride)
    db_session.commit()

    req1 = RideRequest(ride_id=ride.id, passenger_id=p1.id, message="Hi")
    req2 = RideRequest(ride_id=ride.id, passenger_id=p2.id, message="Hey")
    db_session.add_all([req1, req2])
    db_session.commit()

    assert len(ride.requests) == 2
    assert req1.ride == ride
    assert req2.ride == ride
    assert len(p1.ride_requests) == 1
    assert p1.ride_requests[0] == req1


def test_ride_request_and_conversation_one_to_one(db_session):
    """Test RideRequest <-> Conversation 1:1 relationship."""
    driver = User(full_name="D Conv", email="dconv@example.com", password="Password123")
    passenger = User(full_name="P Conv", email="pconv@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Origin",
        destination_address="Dest",
        departure_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    db_session.add(ride)
    db_session.commit()

    req = RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="accepted")
    db_session.add(req)
    db_session.commit()

    conv = Conversation(ride_request_id=req.id)
    db_session.add(conv)
    db_session.commit()

    assert req.conversation == conv
    assert conv.ride_request == req


def test_conversation_and_messages_relationships(db_session):
    """Test Conversation <-> Message 1:N and User <-> Message 1:N."""
    driver = User(full_name="D Msg", email="dmsg@example.com", password="Password123")
    passenger = User(full_name="P Msg", email="pmsg@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Start",
        destination_address="End",
        departure_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(ride)
    db_session.commit()

    req = RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="accepted")
    db_session.add(req)
    db_session.commit()

    conv = Conversation(ride_request_id=req.id)
    db_session.add(conv)
    db_session.commit()

    m1 = Message(conversation_id=conv.id, sender_id=driver.id, content="Are you ready?")
    m2 = Message(conversation_id=conv.id, sender_id=passenger.id, content="Yes, on my way!")
    db_session.add_all([m1, m2])
    db_session.commit()

    assert len(conv.messages) == 2
    assert conv.messages[0].sender == driver
    assert conv.messages[1].sender == passenger
    assert len(driver.sent_messages) == 1
    assert len(passenger.sent_messages) == 1


def test_reviews_relationships(db_session):
    """Test Ride <-> Review 1:N and User reviews_given / reviews_received."""
    driver = User(full_name="D RevRel", email="drevrel@example.com", password="Password123")
    passenger = User(full_name="P RevRel", email="prevrel@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Start",
        destination_address="End",
        departure_at=datetime.now(timezone.utc) - timedelta(hours=3),
        status="completed",
    )
    db_session.add(ride)
    db_session.commit()

    # Passenger reviews Driver
    r1 = Review(
        ride_id=ride.id,
        reviewer_id=passenger.id,
        reviewed_user_id=driver.id,
        rating=5,
        comment="Great driver!",
    )
    # Driver reviews Passenger
    r2 = Review(
        ride_id=ride.id,
        reviewer_id=driver.id,
        reviewed_user_id=passenger.id,
        rating=5,
        comment="Polite and on time!",
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    assert len(ride.reviews) == 2
    assert len(passenger.reviews_given) == 1
    assert len(passenger.reviews_received) == 1
    assert len(driver.reviews_given) == 1
    assert len(driver.reviews_received) == 1


def test_notifications_relationships(db_session):
    """Test User <-> Notification 1:N and Ride <-> Notification 1:N."""
    user = User(full_name="User NotifRel", email="unotif@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    ride = Ride(
        driver_id=user.id,
        origin_address="Start",
        destination_address="End",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()

    notif = Notification(
        user_id=user.id,
        ride_id=ride.id,
        type="new_request",
        title="New Request",
        content="Someone wants to join your ride.",
    )
    db_session.add(notif)
    db_session.commit()

    assert len(user.notifications) == 1
    assert user.notifications[0] == notif
    assert notif.ride == ride
    assert len(ride.notifications) == 1
