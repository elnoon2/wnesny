from sqlalchemy import CheckConstraint
from app.extensions import db


class UserProfile(db.Model):
    """Stores extended user profile information and privacy settings."""
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "education_visibility IN ('public', 'matches_only', 'private')",
            name="chk_education_visibility_valid",
        ),
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bio = db.Column(db.Text, nullable=True)
    education_level = db.Column(db.String(50), nullable=True)
    institution = db.Column(db.String(150), nullable=True)
    field_of_study = db.Column(db.String(100), nullable=True)
    academic_year = db.Column(db.String(30), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    education_visibility = db.Column(
        db.String(20),
        default="matches_only",
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="profile")

    def __init__(
        self,
        user_id=None,
        bio=None,
        education_level=None,
        institution=None,
        field_of_study=None,
        academic_year=None,
        graduation_year=None,
        education_visibility="matches_only",
    ):
        if user_id is not None:
            self.user_id = user_id
        self.bio = bio
        self.education_level = education_level
        self.institution = institution
        self.field_of_study = field_of_study
        self.academic_year = academic_year
        self.graduation_year = graduation_year
        if education_visibility not in ("public", "matches_only", "private"):
            raise ValueError(
                f"Invalid education_visibility: {education_visibility}. "
                "Must be one of 'public', 'matches_only', 'private'."
            )
        self.education_visibility = education_visibility

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} visibility='{self.education_visibility}'>"
