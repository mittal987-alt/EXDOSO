
import csv
import io
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.influencer import Influencer
from app.models.outreach_message import OutreachMessage
from app.models.delivery_log import DeliveryLog


def _csv_response(rows: list[dict]) -> str:
    """Convert a list of dictionaries into CSV text."""
    if not rows:
        return ""

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0].keys()),
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()


def export_influencers(db: Session) -> str:
    influencers = db.scalars(
        select(Influencer).order_by(Influencer.id)
    ).all()

    rows = [
        {
            "id": item.id,
            "name": item.name,
            "platform": item.platform,
            "profile_url": item.profile_url,
            "follower_count": item.follower_count,
            "engagement_rate": item.engagement_rate,
            "category": item.category,
            "content_themes": item.content_themes,
            "contact_email": item.contact_email,
            "email_verified": item.email_verified,
            "website": item.website,
            "geography": item.geography,
            "source_url": item.source_url,
            "qualification_status": item.qualification_status,
            "rejection_reasons": item.rejection_reasons,
            "collected_at": (
                item.collected_at.isoformat()
                if item.collected_at
                else ""
            ),
        }
        for item in influencers
    ]

    return _csv_response(rows)


def export_outreach_messages(db: Session) -> str:
    messages = db.scalars(
        select(OutreachMessage).order_by(OutreachMessage.id)
    ).all()

    rows = [
        {
            "id": item.id,
            "influencer_id": item.influencer_id,
            "channel": item.channel,
            "subject": item.subject or "",
            "message": item.message,
            "word_count": item.word_count,
            "status": item.status,
            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else ""
            ),
            "sent_at": (
                item.sent_at.isoformat()
                if item.sent_at
                else ""
            ),
            "attempt_count": item.attempt_count,
            "delivery_note": item.delivery_note or "",
        }
        for item in messages
    ]

    return _csv_response(rows)


def export_delivery_logs(db: Session) -> str:
    logs = db.scalars(
        select(DeliveryLog).order_by(DeliveryLog.id)
    ).all()

    rows = [
        {
            "id": item.id,
            "outreach_message_id": item.outreach_message_id,
            "event": item.event,
            "status": item.status,
            "details": item.details or "",
            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else ""
            ),
        }
        for item in logs
    ]

    return _csv_response(rows)
