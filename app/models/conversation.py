from datetime import datetime, timezone
from app.extensions import db


class Conversation(db.Model):
    """Stores chat conversations established after a ride request is accepted."""
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    ride_request_id = db.Column(
        db.Integer,
        db.ForeignKey("ride_requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    ride_request = db.relationship("RideRequest", back_populates="conversation")
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.sent_at",
    )

    def __init__(self, ride_request_id, is_active=True, created_at=None):
        self.ride_request_id = ride_request_id
        self.is_active = is_active
        if created_at is not None:
            self.created_at = created_at

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} request_id={self.ride_request_id} active={self.is_active}>"
