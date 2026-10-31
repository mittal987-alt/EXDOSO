from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Influencer(Base):
    __tablename__ = "influencers"

    __table_args__ = (
        UniqueConstraint(
            "platform",
            "profile_url",
            name="uq_influencer_platform_profile",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    profile_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    follower_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    engagement_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Unknown",
    )

    content_themes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    contact_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        default="Not Found",
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    geography: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    qualification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Pending",
        index=True,
    )

    rejection_reasons: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )