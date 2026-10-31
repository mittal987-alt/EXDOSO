from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.services.enrichment_service import enrich_influencer

from app.services.export_service import (
    export_influencers,
    export_outreach_messages,
    export_delivery_logs,
)
from app.database import Base, engine, get_db
from app.models.influencer import Influencer
from app.schemas.influencer import (
    InfluencerCreate,
    InfluencerResponse,
)
import os
import os
from app.models.outreach_message import OutreachMessage
from app.models.delivery_log import DeliveryLog

from app.services.sending_service import (
    send_all_pending,
    send_outreach_message,
    get_delivery_logs,
)

from app.services.schema_update import update_outreach_schema

from fastapi import HTTPException
from sqlalchemy import select
from app.models.outreach_message import OutreachMessage
from app.services.outreach_service import generate_outreach_drafts
from app.models.influencer import Influencer
from app.providers.youtube_provider import (
    YouTubeAPIError,
    YouTubeProvider,
)
from app.services.qualification_service import qualify_influencer
from dotenv import load_dotenv
from fastapi import Query
from sqlalchemy import select

from app.providers.youtube_provider import (
    YouTubeAPIError,
    YouTubeProvider,
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    update_outreach_schema(engine)

    yield


app = FastAPI(
    title="EDXSO Influencer Outreach API",
    description=(
        "AI-powered influencer discovery, filtering, "
        "personalization, and outreach."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "EDXSO Influencer Outreach API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post(
    "/api/influencers",
    response_model=InfluencerResponse,
    status_code=201,
)
def create_influencer(
    payload: InfluencerCreate,
    db: Session = Depends(get_db),
):
    profile_url = str(payload.profile_url).rstrip("/")

    existing = db.scalar(
        select(Influencer).where(
            Influencer.platform == payload.platform,
            Influencer.profile_url == profile_url,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This influencer profile already exists.",
        )

    influencer = Influencer(
        name=payload.name,
        platform=payload.platform,
        profile_url=profile_url,
        follower_count=payload.follower_count,
        engagement_rate=payload.engagement_rate,
        category=payload.category,
        content_themes=payload.content_themes,
        contact_email=payload.contact_email,
        website=str(payload.website) if payload.website else None,
        geography=payload.geography,
        source_url=str(payload.source_url) if payload.source_url else None,
    )

    db.add(influencer)
    db.commit()
    db.refresh(influencer)

    return influencer


@app.get(
    "/api/influencers",
    response_model=list[InfluencerResponse],
)
def list_influencers(
    db: Session = Depends(get_db),
):
    statement = select(Influencer).order_by(Influencer.id)

    return db.scalars(statement).all()


@app.get("/api/outreach/drafts")
def get_outreach_drafts(
    db: Session = Depends(get_db),
):
    """Return all stored outreach drafts."""

    drafts = db.scalars(
        select(OutreachMessage).order_by(
            OutreachMessage.influencer_id,
            OutreachMessage.channel,
        )
    ).all()

    return {
        "total": len(drafts),
        "drafts": [
            {
                "id": draft.id,
                "influencer_id": draft.influencer_id,
                "channel": draft.channel,
                "subject": draft.subject,
                "message": draft.message,
                "word_count": draft.word_count,
                "status": draft.status,
                "created_at": (
                    draft.created_at.isoformat()
                    if draft.created_at
                    else None
                ),
            }
            for draft in drafts
        ],
    }
@app.post("/api/outreach/generate")
def generate_outreach(
    db: Session = Depends(get_db),
):
    """
    Generate and store email and Instagram DM drafts for
    qualified influencers. No messages are sent.
    """

    influencers = db.scalars(
        select(Influencer).where(
            Influencer.qualification_status == "Qualified"
        )
    ).all()

    generated = 0
    skipped = 0
    results = []

    try:
        for influencer in influencers:
            drafts = generate_outreach_drafts(influencer)

            for draft in drafts:
                # Avoid generating a duplicate draft for the same
                # influencer and communication channel.
                existing = db.scalar(
                    select(OutreachMessage).where(
                        OutreachMessage.influencer_id == influencer.id,
                        OutreachMessage.channel == draft["channel"],
                    )
                )

                if existing:
                    skipped += 1
                    continue

                record = OutreachMessage(
                    influencer_id=influencer.id,
                    channel=draft["channel"],
                    subject=draft["subject"],
                    message=draft["message"],
                    word_count=draft["word_count"],
                    status="Draft",
                )

                db.add(record)
                db.flush()

                generated += 1

                results.append(
                    {
                        "id": record.id,
                        "influencer_id": influencer.id,
                        "influencer_name": influencer.name,
                        "channel": record.channel,
                        "subject": record.subject,
                        "message": record.message,
                        "word_count": record.word_count,
                        "status": record.status,
                    }
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "qualified_influencers": len(influencers),
        "drafts_generated": generated,
        "existing_drafts_skipped": skipped,
        "messages_sent": 0,
        "results": results,
    }

@app.post("/api/influencers/qualify")
async def qualify_all_influencers(
    db: Session = Depends(get_db),
):
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="YOUTUBE_API_KEY is not configured.",
        )

    influencers = db.scalars(
        select(Influencer).where(
            Influencer.platform == "YouTube",
            Influencer.qualification_status == "Pending",
        )
    ).all()

    provider = YouTubeProvider(api_key)
    results = []

    try:
        for influencer in influencers:
            result = await qualify_influencer(influencer, provider)
            results.append(result)

        db.commit()

    except YouTubeAPIError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"YouTube API request failed: {exc}",
        ) from exc

    except Exception:
        db.rollback()
        raise

    qualified = sum(
        result["qualification_status"] == "Qualified"
        for result in results
    )

    return {
        "processed": len(results),
        "qualified": qualified,
        "rejected": len(results) - qualified,
        "results": results,
    }

@app.post("/api/outreach/send/{message_id}")
def send_one_outreach(
    message_id: int,
    db: Session = Depends(get_db),
):
    result = send_outreach_message(db, message_id)

    if result["status"] == "Not Found":
        raise HTTPException(status_code=404, detail=result["detail"])

    if result["status"] == "Duplicate Prevented":
        raise HTTPException(status_code=409, detail=result["detail"])

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["detail"])

    return result

@app.get("/api/exports/influencers.csv")
def download_influencers_csv(
    db: Session = Depends(get_db),
):
    content = export_influencers(db)

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="influencers.csv"'
        },
    )


@app.get("/api/exports/outreach-messages.csv")
def download_outreach_csv(
    db: Session = Depends(get_db),
):
    content = export_outreach_messages(db)

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="outreach_messages.csv"'
        },
    )


@app.get("/api/exports/delivery-logs.csv")
def download_delivery_logs_csv(
    db: Session = Depends(get_db),
):
    content = export_delivery_logs(db)

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="delivery_logs.csv"'
        },
    )
@app.post("/api/outreach/send-pending")
def send_pending_outreach(
    db: Session = Depends(get_db),
):
    return send_all_pending(db)


@app.get("/api/outreach/delivery-logs")
def list_delivery_logs(
    message_id: int | None = None,
    db: Session = Depends(get_db),
):
    return {
        "logs": get_delivery_logs(db, message_id)
    }
@app.post("/api/influencers/enrich")
async def enrich_all_influencers(
    db: Session = Depends(get_db),
):
    """
    Enrich stored YouTube influencers with publicly available
    contact information, website links, and content descriptions.
    """

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="YOUTUBE_API_KEY is not configured.",
        )

    influencers = db.scalars(
        select(Influencer).where(
            Influencer.platform == "YouTube"
        )
    ).all()

    provider = YouTubeProvider(api_key)

    results = []
    enriched_count = 0
    review_count = 0

    try:
        for influencer in influencers:
            try:
                result = await enrich_influencer(
                    influencer,
                    provider,
                )

                results.append(result)

                if result["status"] == "Enriched":
                    enriched_count += 1
                else:
                    review_count += 1

            except YouTubeAPIError as exc:
                # Keep processing other channels when an individual
                # channel cannot be retrieved.
                results.append(
                    {
                        "id": influencer.id,
                        "name": influencer.name,
                        "status": "Needs Review",
                        "message": str(exc),
                    }
                )

                review_count += 1

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "processed": len(influencers),
        "enriched": enriched_count,
        "needs_review": review_count,
        "results": results,
    }

@app.post("/api/discovery/youtube")
async def discover_youtube_influencers(
    target: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="YOUTUBE_API_KEY is not configured.",
        )

    provider = YouTubeProvider(api_key)

    try:
        records = await provider.discover_fitness_channels(
            target=target
        )
    except YouTubeAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    inserted = 0
    duplicates = 0

    for record in records:
        profile_url = record["profile_url"].rstrip("/")

        existing = db.scalar(
            select(Influencer).where(
                Influencer.platform == record["platform"],
                Influencer.profile_url == profile_url,
            )
        )

        if existing:
            duplicates += 1
            continue

        record["profile_url"] = profile_url

        db.add(Influencer(**record))
        inserted += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "requested": target,
        "discovered": len(records),
        "inserted": inserted,
        "duplicates_skipped": duplicates,
        "message": (
            "Discovery completed. Review the records and "
            "their available metrics before qualification."
        ),
    }
@app.get(
    "/api/influencers/{influencer_id}",
    response_model=InfluencerResponse,
)
def get_influencer(
    influencer_id: int,
    db: Session = Depends(get_db),
):
    influencer = db.get(Influencer, influencer_id)

    if influencer is None:
        raise HTTPException(
            status_code=404,
            detail="Influencer not found.",
        )

    return influencer