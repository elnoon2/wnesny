from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, UniqueConstraint, Index, text
from app.extensions import db


class RideRequest(db.Model):
    """Stores passenger requests to join specific rides."""
    __tablename__ = "ride_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'cancelled')",
            name="chk_request_status_valid",
        ),
        # Prevents duplicate requests by the same passenger for the same ride
        UniqueConstraint("ride_id", "passenger_id", name="uq_ride_passenger"),
        # Partial unique index enforcing the core rule: AT MOST ONE ACCEPTED REQUEST PER RIDE.
        # Both SQLite (>=3.8.0) and PostgreSQL natively support partial unique indexes with WHERE clause.
        Index(
            "uq_accepted_request_per_ride",
            "ride_id",
            unique=True,
            sqlite_where=text("status = 'accepted'"),
            postgresql_where=text("status = 'accepted'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(
        db.Integer,
        db.ForeignKey("rides.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    passenger_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    ride = db.relationship("Ride", back_populates="requests")
    passenger = db.relationship(
        "User",
        back_populates="ride_requests",
        foreign_keys=[passenger_id],
    )
    conversation = db.relationship(
        "Conversation",
        back_populates="ride_request",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __init__(
        self,
        ride_id,
        passenger_id,
        status="pending",
        message=None,
        created_at=None,
        updated_at=None,
    ):
        self.ride_id = ride_id
        self.passenger_id = passenger_id
        if status not in ("pending", "accepted", "rejected", "cancelled"):
            raise ValueError(f"Invalid request status: {status}")
        self.status = status
        self.message = message
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def __repr__(self) -> str:
        return f"<RideRequest id={self.id} ride_id={self.ride_id} passenger_id={self.passenger_id} status='{self.status}'>"
