from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, UniqueConstraint
from app.extensions import db


class Review(db.Model):
    """Stores ratings and feedback submitted after a ride is completed."""
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating_range"),
        CheckConstraint("reviewer_id != reviewed_user_id", name="chk_no_self_review"),
        UniqueConstraint(
            "ride_id", "reviewer_id", "reviewed_user_id",
            name="uq_ride_reviewer_reviewed",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(
        db.Integer,
        db.ForeignKey("rides.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    reviewed_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    ride = db.relationship("Ride", back_populates="reviews")
    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewer_id],
        back_populates="reviews_given",
    )
    reviewed_user = db.relationship(
        "User",
        foreign_keys=[reviewed_user_id],
        back_populates="reviews_received",
    )

    def __init__(
        self,
        ride_id,
        reviewer_id,
        reviewed_user_id,
        rating,
        comment=None,
        created_at=None,
    ):
        if reviewer_id == reviewed_user_id:
            raise ValueError("Users cannot review themselves.")
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError(f"Rating must be an integer between 1 and 5. Got {rating}.")
        self.ride_id = ride_id
        self.reviewer_id = reviewer_id
        self.reviewed_user_id = reviewed_user_id
        self.rating = rating
        self.comment = comment.strip() if comment else None
        if created_at is not None:
            self.created_at = created_at

    def __repr__(self) -> str:
        return f"<Review id={self.id} ride_id={self.ride_id} reviewer={self.reviewer_id}->{self.reviewed_user_id} rating={self.rating}>"
