"""Database service functions for Wnesny.

Encapsulates database operations and critical business rules:
- Transaction-safe request acceptance.
- Single accepted passenger enforcement.
- Safe rejection of competing pending requests.
- Automatic conversation creation upon acceptance.
- Cancellation handling with conversation deactivation and notifications.
- Participant verification for messaging and reviews.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.extensions import db
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


class DatabaseServiceError(Exception):
    """Base exception for service-level business rule violations."""
    pass


MAX_ADDRESS_LENGTH = 200  # matches the rides.origin_address / destination_address columns
MIN_GRADUATION_YEAR = 1950


def _as_utc(value: datetime) -> datetime:
    """Treat a naive datetime as UTC so it can be compared with aware ones."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _commit_or_raise(message: str) -> None:
    """Commit, turning a database integrity failure into a service error.

    This is what protects the "one accepted passenger per ride" and "one
    request per passenger" rules when two users act at the same moment: the
    database constraint wins, and the caller gets a clear error instead of a
    raw ``IntegrityError`` with a half-finished session.
    """
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DatabaseServiceError(message) from exc


def _get_ride_for_driver(request_id: int, driver_id: int) -> Tuple[RideRequest, Ride]:
    """Load a request and its ride, and check that ``driver_id`` owns the ride."""
    req = db.session.get(RideRequest, request_id)
    if not req:
        raise DatabaseServiceError(f"RideRequest with id {request_id} does not exist.")
    ride = db.session.get(Ride, req.ride_id)
    if not ride:
        raise DatabaseServiceError(f"Ride with id {req.ride_id} does not exist.")
    if ride.driver_id != driver_id:
        raise DatabaseServiceError("Only the driver of this ride can answer its requests.")
    return req, ride


def create_user(
    full_name: str,
    email: str,
    password: str,
    is_active: bool = True,
) -> User:
    """Create and persist a new user account with hashed password and normalized email."""
    if not full_name or not full_name.strip():
        raise DatabaseServiceError("Full name cannot be empty.")
    try:
        normalized_email = User.normalize_email(email)
    except ValueError as exc:
        raise DatabaseServiceError(str(exc)) from exc
    existing = db.session.scalar(select(User).filter_by(email=normalized_email))
    if existing:
        raise DatabaseServiceError(f"A user with email '{normalized_email}' already exists.")

    try:
        user = User(
            full_name=full_name,
            email=normalized_email,
            password=password,
            is_active=is_active,
        )
    except ValueError as exc:  # e.g. password too short
        raise DatabaseServiceError(str(exc)) from exc
    db.session.add(user)
    _commit_or_raise(f"A user with email '{normalized_email}' already exists.")
    return user


def create_user_profile(
    user_id: int,
    bio: Optional[str] = None,
    education_level: Optional[str] = None,
    institution: Optional[str] = None,
    field_of_study: Optional[str] = None,
    academic_year: Optional[str] = None,
    graduation_year: Optional[int] = None,
    education_visibility: str = "matches_only",
) -> UserProfile:
    """Create a user's extended profile (raises if one already exists)."""
    user = db.session.get(User, user_id)
    if not user:
        raise DatabaseServiceError(f"User with id {user_id} does not exist.")

    max_year = datetime.now(timezone.utc).year + 10
    if graduation_year is not None and not (MIN_GRADUATION_YEAR <= graduation_year <= max_year):
        raise DatabaseServiceError(
            f"graduation_year must be between {MIN_GRADUATION_YEAR} and {max_year}."
        )
    if education_visibility not in ("public", "matches_only", "private"):
        raise DatabaseServiceError(
            "education_visibility must be 'public', 'matches_only' or 'private'."
        )

    existing_profile = db.session.get(UserProfile, user_id)
    if existing_profile:
        raise DatabaseServiceError(f"UserProfile for user_id {user_id} already exists.")

    profile = UserProfile(
        user_id=user_id,
        bio=bio,
        education_level=education_level,
        institution=institution,
        field_of_study=field_of_study,
        academic_year=academic_year,
        graduation_year=graduation_year,
        education_visibility=education_visibility,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def assign_interests_to_user(user_id: int, interest_ids: List[int]) -> User:
    """Assign a list of interests to a user, replacing duplicates and preserving uniqueness."""
    user = db.session.get(User, user_id)
    if not user:
        raise DatabaseServiceError(f"User with id {user_id} does not exist.")

    unique_ids = list(set(interest_ids))
    interests = db.session.scalars(
        select(Interest).filter(Interest.id.in_(unique_ids))
    ).all()

    if len(interests) != len(unique_ids):
        found_ids = {i.id for i in interests}
        missing = set(unique_ids) - found_ids
        raise DatabaseServiceError(f"Interests not found: {missing}")

    user.interests = interests
    db.session.commit()
    return user


def create_ride(
    driver_id: int,
    origin_address: str,
    destination_address: str,
    departure_at: datetime,
    origin_latitude: Optional[float] = None,
    origin_longitude: Optional[float] = None,
    destination_latitude: Optional[float] = None,
    destination_longitude: Optional[float] = None,
    notes: Optional[str] = None,
) -> Ride:
    """Publish a new scheduled ride offered by a driver."""
    driver = db.session.get(User, driver_id)
    if not driver:
        raise DatabaseServiceError(f"Driver with id {driver_id} does not exist.")
    if not driver.is_active:
        raise DatabaseServiceError("Inactive users cannot publish rides.")

    origin_address = (origin_address or "").strip()
    destination_address = (destination_address or "").strip()
    if not origin_address or not destination_address:
        raise DatabaseServiceError("Origin and destination addresses cannot be empty.")
    if len(origin_address) > MAX_ADDRESS_LENGTH or len(destination_address) > MAX_ADDRESS_LENGTH:
        raise DatabaseServiceError(
            f"Addresses must be at most {MAX_ADDRESS_LENGTH} characters long."
        )
    if origin_address.casefold() == destination_address.casefold():
        raise DatabaseServiceError("Origin and destination must be different places.")

    if _as_utc(departure_at) <= datetime.now(timezone.utc):
        raise DatabaseServiceError("Departure time must be in the future.")

    # Coordinates come in pairs: a latitude without a longitude is meaningless.
    if (origin_latitude is None) != (origin_longitude is None):
        raise DatabaseServiceError("Origin latitude and longitude must be given together.")
    if (destination_latitude is None) != (destination_longitude is None):
        raise DatabaseServiceError("Destination latitude and longitude must be given together.")

    # Validate coordinate ranges if provided
    for name, lat in [("origin_latitude", origin_latitude), ("destination_latitude", destination_latitude)]:
        if lat is not None and not (-90.0 <= lat <= 90.0):
            raise DatabaseServiceError(f"{name} must be between -90 and 90 degrees.")

    for name, lng in [("origin_longitude", origin_longitude), ("destination_longitude", destination_longitude)]:
        if lng is not None and not (-180.0 <= lng <= 180.0):
            raise DatabaseServiceError(f"{name} must be between -180 and 180 degrees.")

    ride = Ride(
        driver_id=driver_id,
        origin_address=origin_address,
        destination_address=destination_address,
        departure_at=departure_at,
        origin_latitude=origin_latitude,
        origin_longitude=origin_longitude,
        destination_latitude=destination_latitude,
        destination_longitude=destination_longitude,
        notes=notes,
        status="scheduled",
    )
    db.session.add(ride)
    db.session.commit()
    return ride


def submit_ride_request(
    ride_id: int,
    passenger_id: int,
    message: Optional[str] = None,
) -> RideRequest:
    """Submit a request to join an available ride."""
    passenger = db.session.get(User, passenger_id)
    if not passenger:
        raise DatabaseServiceError(f"Passenger with id {passenger_id} does not exist.")
    if not passenger.is_active:
        raise DatabaseServiceError("Inactive users cannot request rides.")

    ride = db.session.get(Ride, ride_id)
    if not ride:
        raise DatabaseServiceError(f"Ride with id {ride_id} does not exist.")

    # Rule: Driver cannot request their own ride
    if ride.driver_id == passenger_id:
        raise DatabaseServiceError("A driver cannot request to join their own ride.")

    # Rule: Can only request scheduled rides
    if ride.status != "scheduled":
        raise DatabaseServiceError(
            f"Cannot request a ride with status '{ride.status}'. Only scheduled rides accept requests."
        )

    # Rule: Check if ride already has an accepted passenger
    accepted_existing = db.session.scalar(
        select(RideRequest).filter_by(ride_id=ride_id, status="accepted")
    )
    if accepted_existing:
        raise DatabaseServiceError("This ride already has an accepted passenger.")

    # Rule: Prevent duplicate request by the same passenger
    duplicate = db.session.scalar(
        select(RideRequest).filter_by(ride_id=ride_id, passenger_id=passenger_id)
    )
    if duplicate:
        raise DatabaseServiceError("You have already submitted a request for this ride.")

    req = RideRequest(
        ride_id=ride_id,
        passenger_id=passenger_id,
        status="pending",
        message=message,
    )
    db.session.add(req)

    # Create notification for driver
    driver_notif = Notification(
        user_id=ride.driver_id,
        type="new_request",
        title="New Ride Request",
        content=f"{passenger.full_name} has requested to join your ride.",
        ride_id=ride_id,
    )
    db.session.add(driver_notif)

    _commit_or_raise("You have already submitted a request for this ride.")
    return req


def accept_ride_request(request_id: int, driver_id: int) -> Tuple[RideRequest, Conversation]:
    """Transactionally accept a ride request. Only the ride's driver may do this.

    Enforces the single-passenger rule:
    0. Checks that ``driver_id`` is the driver of the ride.
    1. Checks ride status is scheduled.
    2. Ensures no other request for this ride is already accepted.
    3. Marks this request as accepted.
    4. Automatically rejects competing pending requests.
    5. Creates a conversation between driver and accepted passenger.
    6. Sends notifications to the accepted and rejected passengers.
    """
    req, ride = _get_ride_for_driver(request_id, driver_id)

    if req.status != "pending":
        raise DatabaseServiceError(
            f"Cannot accept a request with status '{req.status}'. Only pending requests can be accepted."
        )

    if ride.status != "scheduled":
        raise DatabaseServiceError("Cannot accept a request for a cancelled or completed ride.")

    # Verify single-accepted passenger rule
    existing_accepted = db.session.scalar(
        select(RideRequest).filter_by(ride_id=req.ride_id, status="accepted")
    )
    if existing_accepted:
        raise DatabaseServiceError(
            f"Ride {req.ride_id} already has an accepted passenger (request {existing_accepted.id})."
        )

    # 1. Accept this request
    req.status = "accepted"
    req.updated_at = datetime.now(timezone.utc)

    # 2. Reject competing pending requests
    competing_requests = db.session.scalars(
        select(RideRequest).filter(
            RideRequest.ride_id == req.ride_id,
            RideRequest.id != req.id,
            RideRequest.status == "pending",
        )
    ).all()

    for comp_req in competing_requests:
        comp_req.status = "rejected"
        comp_req.updated_at = datetime.now(timezone.utc)
        # Notify rejected applicant
        db.session.add(
            Notification(
                user_id=comp_req.passenger_id,
                type="request_rejected",
                title="Ride Request Not Accepted",
                content="Another passenger was selected for this ride.",
                ride_id=req.ride_id,
            )
        )

    # 3. Create conversation
    conversation = Conversation(ride_request_id=req.id, is_active=True)
    db.session.add(conversation)

    # 4. Notify accepted passenger
    db.session.add(
        Notification(
            user_id=req.passenger_id,
            type="request_accepted",
            title="Ride Request Accepted",
            content="Your ride request was accepted! You can now chat with your driver.",
            ride_id=req.ride_id,
        )
    )

    _commit_or_raise("This ride already has an accepted passenger.")
    return req, conversation


def reject_ride_request(request_id: int, driver_id: int) -> RideRequest:
    """Reject a pending ride request. Only the ride's driver may do this."""
    req, _ride = _get_ride_for_driver(request_id, driver_id)

    if req.status != "pending":
        raise DatabaseServiceError(
            f"Cannot reject a request with status '{req.status}'. Only pending requests can be rejected."
        )

    req.status = "rejected"
    req.updated_at = datetime.now(timezone.utc)

    # Notify passenger
    db.session.add(
        Notification(
            user_id=req.passenger_id,
            type="request_rejected",
            title="Ride Request Rejected",
            content="Your ride request was declined by the driver.",
            ride_id=req.ride_id,
        )
    )

    db.session.commit()
    return req


def cancel_ride_request(request_id: int, user_id: int) -> RideRequest:
    """Allow a passenger to cancel their own pending or accepted request.

    Cancelling an accepted request (while the ride is still scheduled) frees the
    seat again: the ride stays scheduled and can receive new requests, the chat
    is frozen and the driver is notified.
    """
    req = db.session.get(RideRequest, request_id)
    if not req:
        raise DatabaseServiceError(f"RideRequest with id {request_id} does not exist.")

    if req.passenger_id != user_id:
        raise DatabaseServiceError("You can only cancel your own ride request.")

    if req.status not in ("pending", "accepted"):
        raise DatabaseServiceError(
            f"Cannot cancel a request with status '{req.status}'. "
            "Only pending or accepted requests can be cancelled by the passenger."
        )

    was_accepted = req.status == "accepted"
    if was_accepted:
        ride = db.session.get(Ride, req.ride_id)
        if ride is None or ride.status != "scheduled":
            raise DatabaseServiceError(
                "An accepted request can only be cancelled while the ride is still scheduled."
            )

    req.status = "cancelled"
    req.updated_at = datetime.now(timezone.utc)

    if was_accepted:
        if req.conversation:
            req.conversation.is_active = False
        passenger = db.session.get(User, user_id)
        db.session.add(
            Notification(
                user_id=ride.driver_id,
                type="request_cancelled",
                title="Passenger Cancelled",
                content=f"{passenger.full_name} cancelled their place on your ride. It is open for new requests.",
                ride_id=ride.id,
            )
        )

    db.session.commit()
    return req


def cancel_ride(ride_id: int, driver_id: int, reason: Optional[str] = None) -> Ride:
    """Cancel a scheduled ride.

    Preserves history:
    - Sets ride status to 'cancelled'.
    - If there was an accepted request, deactivates the conversation.
    - Notifies the accepted passenger.
    - Cancels any pending requests and notifies those passengers.
    """
    ride = db.session.get(Ride, ride_id)
    if not ride:
        raise DatabaseServiceError(f"Ride with id {ride_id} does not exist.")

    if ride.driver_id != driver_id:
        raise DatabaseServiceError("Only the driver can cancel their ride.")

    if ride.status != "scheduled":
        raise DatabaseServiceError(
            f"Only scheduled rides can be cancelled; this ride is '{ride.status}'."
        )

    ride.status = "cancelled"

    # Find accepted request if one exists
    accepted_req = db.session.scalar(
        select(RideRequest).filter_by(ride_id=ride_id, status="accepted")
    )
    if accepted_req:
        # Deactivate conversation
        if accepted_req.conversation:
            accepted_req.conversation.is_active = False

        # Notify accepted passenger
        content = f"Your ride scheduled for {ride.departure_at} was cancelled by the driver."
        if reason:
            content += f" Reason: {reason}"

        db.session.add(
            Notification(
                user_id=accepted_req.passenger_id,
                type="ride_cancelled",
                title="Ride Cancelled",
                content=content,
                ride_id=ride_id,
            )
        )

    # Reject any pending requests
    pending_requests = db.session.scalars(
        select(RideRequest).filter_by(ride_id=ride_id, status="pending")
    ).all()
    for preq in pending_requests:
        preq.status = "cancelled"
        preq.updated_at = datetime.now(timezone.utc)
        db.session.add(
            Notification(
                user_id=preq.passenger_id,
                type="ride_cancelled",
                title="Ride Cancelled",
                content="The driver cancelled this ride, so your request was closed.",
                ride_id=ride_id,
            )
        )

    db.session.commit()
    return ride


def _driver_ride_with_accepted_request(ride_id: int, driver_id: int) -> Tuple[Ride, RideRequest]:
    """Load a ride owned by ``driver_id`` together with its accepted request."""
    ride = db.session.get(Ride, ride_id)
    if not ride:
        raise DatabaseServiceError(f"Ride with id {ride_id} does not exist.")
    if ride.driver_id != driver_id:
        raise DatabaseServiceError("Only the driver can change the status of their ride.")
    accepted_req = db.session.scalar(
        select(RideRequest).filter_by(ride_id=ride_id, status="accepted")
    )
    if not accepted_req:
        raise DatabaseServiceError("The ride has no accepted passenger.")
    return ride, accepted_req


def start_ride(ride_id: int, driver_id: int) -> Ride:
    """Move a scheduled ride with an accepted passenger to 'in_progress'."""
    ride, _accepted = _driver_ride_with_accepted_request(ride_id, driver_id)
    if ride.status != "scheduled":
        raise DatabaseServiceError(
            f"Only scheduled rides can be started; this ride is '{ride.status}'."
        )
    ride.status = "in_progress"
    db.session.commit()
    return ride


def complete_ride(ride_id: int, driver_id: int) -> Ride:
    """Mark an in-progress ride as 'completed' and invite both people to review.

    Reviews are only possible on completed rides (see :func:`create_review`), so
    this is the step that opens them.
    """
    ride, accepted_req = _driver_ride_with_accepted_request(ride_id, driver_id)
    if ride.status != "in_progress":
        raise DatabaseServiceError(
            f"Only rides in progress can be completed; this ride is '{ride.status}'."
        )
    ride.status = "completed"
    for user_id, other in ((accepted_req.passenger_id, "driver"), (ride.driver_id, "passenger")):
        db.session.add(
            Notification(
                user_id=user_id,
                type="ride_completed",
                title="Ride Completed",
                content=f"Your ride is complete. You can now review your {other}.",
                ride_id=ride_id,
            )
        )
    db.session.commit()
    return ride


def create_conversation_for_accepted_request(ride_request_id: int) -> Conversation:
    """Create a conversation for an accepted request."""
    req = db.session.get(RideRequest, ride_request_id)
    if not req:
        raise DatabaseServiceError(f"RideRequest with id {ride_request_id} does not exist.")

    if req.status != "accepted":
        raise DatabaseServiceError(
            f"Cannot create conversation for request with status '{req.status}'. Request must be 'accepted'."
        )

    existing = db.session.scalar(
        select(Conversation).filter_by(ride_request_id=ride_request_id)
    )
    if existing:
        return existing

    conv = Conversation(ride_request_id=ride_request_id, is_active=True)
    db.session.add(conv)
    db.session.commit()
    return conv


def send_message(conversation_id: int, sender_id: int, content: str) -> Message:
    """Send a message within an active conversation between authorized participants."""
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        raise DatabaseServiceError(f"Conversation with id {conversation_id} does not exist.")

    if not conv.is_active:
        raise DatabaseServiceError("Cannot send messages in an inactive conversation.")

    req = conv.ride_request
    if not req or not req.ride:
        raise DatabaseServiceError("Conversation is not linked to a valid ride request.")

    driver_id = req.ride.driver_id
    passenger_id = req.passenger_id

    # Verify sender is authorized participant
    if sender_id not in (driver_id, passenger_id):
        raise DatabaseServiceError("Only the driver and accepted passenger can participate in this chat.")

    if not content or not content.strip():
        raise DatabaseServiceError("Message content cannot be empty.")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content.strip(),
    )
    db.session.add(msg)

    # Notify recipient
    recipient_id = passenger_id if sender_id == driver_id else driver_id
    sender_user = db.session.get(User, sender_id)
    sender_name = sender_user.full_name if sender_user else "Your ride partner"

    db.session.add(
        Notification(
            user_id=recipient_id,
            type="new_message",
            title=f"New Message from {sender_name}",
            content=content[:100] + ("..." if len(content) > 100 else ""),
            ride_id=req.ride_id,
        )
    )

    db.session.commit()
    return msg


def create_review(
    ride_id: int,
    reviewer_id: int,
    reviewed_user_id: int,
    rating: int,
    comment: Optional[str] = None,
) -> Review:
    """Submit a review between participants after a ride has completed."""
    if reviewer_id == reviewed_user_id:
        raise DatabaseServiceError("Users cannot review themselves.")

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        raise DatabaseServiceError("Rating must be an integer between 1 and 5.")

    ride = db.session.get(Ride, ride_id)
    if not ride:
        raise DatabaseServiceError(f"Ride with id {ride_id} does not exist.")

    if ride.status != "completed":
        raise DatabaseServiceError("Reviews can only be submitted after a ride is marked 'completed'.")

    # Find accepted passenger
    accepted_req = db.session.scalar(
        select(RideRequest).filter_by(ride_id=ride_id, status="accepted")
    )
    if not accepted_req:
        raise DatabaseServiceError("Ride has no accepted passenger on record.")

    valid_participants = {ride.driver_id, accepted_req.passenger_id}
    if reviewer_id not in valid_participants or reviewed_user_id not in valid_participants:
        raise DatabaseServiceError("Reviews are only permitted between the driver and accepted passenger.")

    # Check for existing review
    existing = db.session.scalar(
        select(Review).filter_by(
            ride_id=ride_id,
            reviewer_id=reviewer_id,
            reviewed_user_id=reviewed_user_id,
        )
    )
    if existing:
        raise DatabaseServiceError("You have already reviewed this user for this ride.")

    rev = Review(
        ride_id=ride_id,
        reviewer_id=reviewer_id,
        reviewed_user_id=reviewed_user_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(rev)
    db.session.commit()
    return rev


def create_notification(
    user_id: int,
    notif_type: str,
    title: str,
    content: str,
    ride_id: Optional[int] = None,
) -> Notification:
    """Create and persist an in-app notification."""
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        content=content,
        ride_id=ride_id,
    )
    db.session.add(notif)
    db.session.commit()
    return notif

