from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery_log import DeliveryLog
from app.models.outreach_message import OutreachMessage


def _log_attempt(
    db: Session,
    message: OutreachMessage,
    status: str,
    details: str,
) -> None:
    db.add(
        DeliveryLog(
            outreach_message_id=message.id,
            event="simulated_send",
            status=status,
            details=details,
        )
    )


def send_outreach_message(
    db: Session,
    message_id: int,
) -> dict:
    """
    Simulate sending one outreach message.

    This function never sends real email or Instagram messages.
    """

    message = db.scalar(
        select(OutreachMessage).where(
            OutreachMessage.id == message_id
        )
    )

    if message is None:
        return {
            "success": False,
            "message_id": message_id,
            "status": "Not Found",
            "detail": "Outreach message does not exist.",
        }

    # Never send an already-sent message again.
    if message.status == "Sent":
        return {
            "success": False,
            "message_id": message.id,
            "status": "Duplicate Prevented",
            "detail": "This message has already been sent.",
        }

    # Only unsent drafts or previously failed messages are eligible.
    if message.status not in {"Draft", "Failed"}:
        return {
            "success": False,
            "message_id": message.id,
            "status": "Not Eligible",
            "detail": f"Cannot send a message with status {message.status}.",
        }

    message.attempt_count += 1

    try:
        # Phase 6 is simulation only: no external provider is contacted.
        message.status = "Sent"
        message.sent_at = datetime.now(timezone.utc)
        message.delivery_note = (
            "Simulated delivery completed successfully. "
            "No real message was sent."
        )

        _log_attempt(
            db,
            message,
            "Sent",
            message.delivery_note,
        )

        db.commit()

        return {
            "success": True,
            "message_id": message.id,
            "channel": message.channel,
            "status": message.status,
            "attempt_count": message.attempt_count,
            "detail": message.delivery_note,
        }

    except Exception:
        db.rollback()
        raise


def send_all_pending(
    db: Session,
) -> dict:
    """
    Simulate sending all messages that are still Draft.
    """

    pending_messages = db.scalars(
        select(OutreachMessage)
        .where(OutreachMessage.status == "Draft")
        .order_by(OutreachMessage.id)
    ).all()

    results = []

    for message in pending_messages:
        results.append(
            send_outreach_message(db, message.id)
        )

    successful = sum(
        result["success"] for result in results
    )

    return {
        "total_processed": len(results),
        "sent": successful,
        "failed": len(results) - successful,
        "results": results,
    }


def get_delivery_logs(
    db: Session,
    message_id: int | None = None,
) -> list[dict]:
    query = select(DeliveryLog).order_by(
        DeliveryLog.created_at.desc()
    )

    if message_id is not None:
        query = query.where(
            DeliveryLog.outreach_message_id == message_id
        )

    logs = db.scalars(query).all()

    return [
        {
            "id": log.id,
            "outreach_message_id": log.outreach_message_id,
            "event": log.event,
            "status": log.status,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]