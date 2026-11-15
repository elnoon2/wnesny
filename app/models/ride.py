from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from app.extensions import db


class Ride(db.Model):
    """Stores published ride offers created by drivers."""
    __tablename__ = "rides"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="chk_ride_status_valid",
        ),
        CheckConstraint(
            "origin_latitude IS NULL OR (origin_latitude >= -90.0 AND origin_latitude <= 90.0)",
            name="chk_origin_latitude_range",
        ),
        CheckConstraint(
            "origin_longitude IS NULL OR (origin_longitude >= -180.0 AND origin_longitude <= 180.0)",
            name="chk_origin_longitude_range",
        ),
        CheckConstraint(
            "destination_latitude IS NULL OR (destination_latitude >= -90.0 AND destination_latitude <= 90.0)",
            name="chk_destination_latitude_range",
        ),
        CheckConstraint(
            "destination_longitude IS NULL OR (destination_longitude >= -180.0 AND destination_longitude <= 180.0)",
            name="chk_destination_longitude_range",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    origin_address = db.Column(db.String(200), nullable=False)
    destination_address = db.Column(db.String(200), nullable=False)
    origin_latitude = db.Column(db.Float, nullable=True)
    origin_longitude = db.Column(db.Float, nullable=True)
    destination_latitude = db.Column(db.Float, nullable=True)
    destination_longitude = db.Column(db.Float, nullable=True)
    departure_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="scheduled", nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    driver = db.relationship(
        "User",
        back_populates="rides_as_driver",
        foreign_keys=[driver_id],
    )
    requests = db.relationship(
        "RideRequest",
        back_populates="ride",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviews = db.relationship(
        "Review",
        back_populates="ride",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    notifications = db.relationship(
        "Notification",
        back_populates="ride",
    )

    def __init__(
        self,
        driver_id,
        origin_address,
        destination_address,
        departure_at,
        origin_latitude=None,
        origin_longitude=None,
        destination_latitude=None,
        destination_longitude=None,
        notes=None,
        status="scheduled",
        created_at=None,
    ):
        self.driver_id = driver_id
        self.origin_address = origin_address.strip() if origin_address else ""
        self.destination_address = destination_address.strip() if destination_address else ""
        self.departure_at = departure_at
        self.origin_latitude = origin_latitude
        self.origin_longitude = origin_longitude
        self.destination_latitude = destination_latitude
        self.destination_longitude = destination_longitude
        self.notes = notes
        if status not in ("scheduled", "in_progress", "completed", "cancelled"):
            raise ValueError(f"Invalid ride status: {status}")
        self.status = status
        if created_at is not None:
            self.created_at = created_at

    # Convenience aliases
    @property
    def origin(self) -> str:
        return self.origin_address

    @property
    def destination(self) -> str:
        return self.destination_address

    @property
    def origin_lat(self):
        return self.origin_latitude

    @property
    def origin_lng(self):
        return self.origin_longitude

    @property
    def destination_lat(self):
        return self.destination_latitude

    @property
    def destination_lng(self):
        return self.destination_longitude

    def __repr__(self) -> str:
        return f"<Ride id={self.id} driver_id={self.driver_id} status='{self.status}' departure='{self.departure_at}'>"

