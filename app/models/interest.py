from app.extensions import db

# Many-to-many association table between Users and Interests
user_interests = db.Table(
    "user_interests",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "interest_id",
        db.Integer,
        db.ForeignKey("interests.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Interest(db.Model):
    """Stores predefined interest catalogue items for social compatibility matching."""
    __tablename__ = "interests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)

    # Relationships
    users = db.relationship(
        "User",
        secondary=user_interests,
        back_populates="interests",
    )

    def __init__(self, name: str, category: str):
        self.name = name.strip() if name else ""
        self.category = category.strip() if category else ""

    def __repr__(self) -> str:
        return f"<Interest id={self.id} name='{self.name}' category='{self.category}'>"

