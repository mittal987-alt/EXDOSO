from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    __table_args__ = (
        UniqueConstraint(
            "influencer_id",
            "channel",
            name="uq_outreach_influencer_channel",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    influencer_id = Column(
        Integer,
        ForeignKey("influencers.id"),
        nullable=False,
        index=True,
    )

    channel = Column(String(30), nullable=False)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="Draft",
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Number of attempts made to send this message.
    attempt_count = Column(Integer, nullable=False, default=0)

    # Result of the most recent sending attempt.
    delivery_note = Column(Text, nullable=True)