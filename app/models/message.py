from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from app.extensions import db


class Message(db.Model):
    """Stores individual messages within a ride's active conversation."""
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "length(trim(content)) > 0",
            name="chk_message_content_not_empty",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship(
        "User",
        back_populates="sent_messages",
        foreign_keys=[sender_id],
    )

    def __init__(self, conversation_id, sender_id, content, is_read=False, sent_at=None):
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.content = content.strip()
        self.is_read = is_read
        if sent_at is not None:
            self.sent_at = sent_at

    def __repr__(self) -> str:
        return f"<Message id={self.id} conv_id={self.conversation_id} sender_id={self.sender_id} read={self.is_read}>"
