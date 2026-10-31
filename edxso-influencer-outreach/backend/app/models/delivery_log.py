from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(Integer, primary_key=True, index=True)

    outreach_message_id = Column(
        Integer,
        ForeignKey("outreach_messages.id"),
        nullable=False,
        index=True,
    )

    event = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    details = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )