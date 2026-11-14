from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    """Stores user accounts for both drivers and passengers."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    interests = db.relationship(
        "Interest",
        secondary="user_interests",
        back_populates="users",
    )
    rides_as_driver = db.relationship(
        "Ride",
        back_populates="driver",
        foreign_keys="Ride.driver_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ride_requests = db.relationship(
        "RideRequest",
        back_populates="passenger",
        foreign_keys="RideRequest.passenger_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sent_messages = db.relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.sender_id",
    )
    reviews_given = db.relationship(
        "Review",
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer",
    )
    reviews_received = db.relationship(
        "Review",
        foreign_keys="Review.reviewed_user_id",
        back_populates="reviewed_user",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(self, full_name, email, password=None, password_hash=None, is_active=True, created_at=None):
        self.full_name = full_name.strip() if full_name else ""
        self.email = self.normalize_email(email)
        if password:
            self.set_password(password)
        elif password_hash:
            self.password_hash = password_hash
        self.is_active = is_active
        if created_at is not None:
            self.created_at = created_at

    @staticmethod
    def normalize_email(email: str) -> str:
        """Strip and lowercase the email address."""
        if not email:
            raise ValueError("Email cannot be empty.")
        return email.strip().lower()

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}'>"
