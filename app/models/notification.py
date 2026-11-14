from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    """Stores in-app notifications for users regarding ride events."""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ride_id = db.Column(
        db.Integer,
        db.ForeignKey("rides.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = db.relationship("User", back_populates="notifications")
    ride = db.relationship("Ride", back_populates="notifications")

    def __init__(self, user_id, type, title, content, ride_id=None, is_read=False, created_at=None):
        self.user_id = user_id
        self.type = type
        self.title = title.strip() if title else ""
        self.content = content.strip() if content else ""
        self.ride_id = ride_id
        self.is_read = is_read
        if created_at is not None:
            self.created_at = created_at

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type='{self.type}' read={self.is_read}>"
