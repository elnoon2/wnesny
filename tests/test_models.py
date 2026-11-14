"""Unit tests for all ten Wnesny SQLAlchemy database models."""

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


def test_user_creation_and_password_hashing(db_session):
    """Test User creation, password hashing, and email normalization."""
    user = User(
        full_name="  Ahmed Hassan  ",
        email="  Ahmed.Hassan@Example.com  ",
        password="SecurePassword123!",
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.full_name == "Ahmed Hassan"
    assert user.email == "ahmed.hassan@example.com"
    assert user.password_hash != "SecurePassword123!"
    assert user.check_password("SecurePassword123!") is True
    assert user.check_password("WrongPassword") is False
    assert user.is_active is True
    assert "<User" in repr(user)


def test_user_profile_creation(db_session):
    """Test UserProfile creation and visibility defaults."""
    user = User(full_name="Fatima Ali", email="fatima@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    profile = UserProfile(
        user_id=user.id,
        bio="CS student passionate about AI and carpooling.",
        education_level="Undergraduate",
        institution="Badya University",
        field_of_study="Computer Science",
        academic_year="Year 3",
        graduation_year=2026,
        education_visibility="matches_only",
    )
    db_session.add(profile)
    db_session.commit()

    assert profile.user_id == user.id
    assert profile.institution == "Badya University"
    assert profile.education_visibility == "matches_only"
    assert "<UserProfile" in repr(profile)


def test_interest_creation(db_session):
    """Test Interest creation and category."""
    interest = Interest(name="Artificial Intelligence", category="Technology")
    db_session.add(interest)
    db_session.commit()

    assert interest.id is not None
    assert interest.name == "Artificial Intelligence"
    assert interest.category == "Technology"
    assert "<Interest" in repr(interest)


def test_ride_creation_and_properties(db_session):
    """Test Ride creation, coordinate storage, and convenience properties."""
    driver = User(full_name="Omar Driver", email="omar@example.com", password="Password123")
    db_session.add(driver)
    db_session.commit()

    departure = datetime.now(timezone.utc) + timedelta(hours=3)
    ride = Ride(
        driver_id=driver.id,
        origin_address="Dokki, Giza",
        destination_address="Badya City, 6th of October",
        departure_at=departure,
        origin_latitude=30.0382,
        origin_longitude=31.2118,
        destination_latitude=29.9702,
        destination_longitude=30.9312,
        notes="Non-smoking car, quiet music preferred.",
    )
    db_session.add(ride)
    db_session.commit()

    assert ride.id is not None
    assert ride.status == "scheduled"
    assert ride.origin == "Dokki, Giza"
    assert ride.destination == "Badya City, 6th of October"
    assert ride.origin_lat == 30.0382
    assert ride.origin_lng == 31.2118
    assert "<Ride" in repr(ride)


def test_ride_request_creation(db_session):
    """Test RideRequest creation with initial pending status."""
    driver = User(full_name="Driver One", email="driver1@example.com", password="Password123")
    passenger = User(full_name="Passenger One", email="passenger1@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Zamalek",
        destination_address="New Cairo",
        departure_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(ride)
    db_session.commit()

    req = RideRequest(
        ride_id=ride.id,
        passenger_id=passenger.id,
        message="Hello! I would love to ride with you.",
    )
    db_session.add(req)
    db_session.commit()

    assert req.id is not None
    assert req.status == "pending"
    assert req.message == "Hello! I would love to ride with you."
    assert req.created_at is not None
    assert req.updated_at is not None
    assert "<RideRequest" in repr(req)


def test_conversation_and_message_creation(db_session):
    """Test Conversation and Message creation."""
    driver = User(full_name="Driver User", email="duser@example.com", password="Password123")
    passenger = User(full_name="Pass User", email="puser@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Maadi",
        destination_address="Tagamoa",
        departure_at=datetime.now(timezone.utc) + timedelta(hours=5),
    )
    db_session.add(ride)
    db_session.commit()

    req = RideRequest(ride_id=ride.id, passenger_id=passenger.id, status="accepted")
    db_session.add(req)
    db_session.commit()

    conv = Conversation(ride_request_id=req.id, is_active=True)
    db_session.add(conv)
    db_session.commit()

    msg = Message(
        conversation_id=conv.id,
        sender_id=driver.id,
        content="I will meet you at Maadi Metro Station.",
    )
    db_session.add(msg)
    db_session.commit()

    assert conv.id is not None
    assert conv.is_active is True
    assert msg.id is not None
    assert msg.is_read is False
    assert msg.content == "I will meet you at Maadi Metro Station."
    assert "<Conversation" in repr(conv)
    assert "<Message" in repr(msg)


def test_review_creation(db_session):
    """Test Review creation and validation."""
    driver = User(full_name="Driver Rev", email="drev@example.com", password="Password123")
    passenger = User(full_name="Pass Rev", email="prev@example.com", password="Password123")
    db_session.add_all([driver, passenger])
    db_session.commit()

    ride = Ride(
        driver_id=driver.id,
        origin_address="Nasr City",
        destination_address="Downtown",
        departure_at=datetime.now(timezone.utc) - timedelta(hours=2),
        status="completed",
    )
    db_session.add(ride)
    db_session.commit()

    review = Review(
        ride_id=ride.id,
        reviewer_id=passenger.id,
        reviewed_user_id=driver.id,
        rating=5,
        comment="Great conversationalist and punctual driver!",
    )
    db_session.add(review)
    db_session.commit()

    assert review.id is not None
    assert review.rating == 5
    assert review.comment == "Great conversationalist and punctual driver!"
    assert "<Review" in repr(review)


def test_notification_creation(db_session):
    """Test Notification creation and read state."""
    user = User(full_name="Notif User", email="notif@example.com", password="Password123")
    db_session.add(user)
    db_session.commit()

    notif = Notification(
        user_id=user.id,
        type="request_accepted",
        title="Ride Confirmed",
        content="Your ride to Badya has been confirmed.",
    )
    db_session.add(notif)
    db_session.commit()

    assert notif.id is not None
    assert notif.is_read is False
    assert notif.type == "request_accepted"
    assert "<Notification" in repr(notif)

