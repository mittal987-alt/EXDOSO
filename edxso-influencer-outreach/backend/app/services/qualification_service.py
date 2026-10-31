import os
from urllib.parse import urlparse

from app.models.influencer import Influencer
from app.providers.youtube_provider import YouTubeProvider

from dotenv import load_dotenv

load_dotenv()
MIN_FOLLOWERS = int(os.getenv("MIN_FOLLOWERS", "1000"))
MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "100000"))
MIN_ENGAGEMENT_RATE = float(
    os.getenv("MIN_ENGAGEMENT_RATE", "2.0")
)
MIN_RECENT_VIDEOS = int(os.getenv("MIN_RECENT_VIDEOS", "3"))


def get_channel_id(source_url: str | None) -> str | None:
    """Extract a channel ID from the stored YouTube channel URL."""
    if not source_url:
        return None

    path_parts = [
        part
        for part in urlparse(source_url).path.split("/")
        if part
    ]

    if len(path_parts) >= 2 and path_parts[0] == "channel":
        return path_parts[1]

    return None


async def qualify_influencer(
    influencer: Influencer,
    provider: YouTubeProvider,
) -> dict:
    """Evaluate one influencer and update their qualification fields."""
    reasons: list[str] = []

    if influencer.platform.lower() != "youtube":
        reasons.append("Unsupported platform; YouTube only.")

    channel_id = get_channel_id(influencer.source_url)

    if not channel_id:
        reasons.append("Could not determine the YouTube channel ID.")

    if influencer.follower_count is None:
        reasons.append("Subscriber count is unavailable.")
    else:
        if influencer.follower_count < MIN_FOLLOWERS:
            reasons.append(
                f"Below minimum subscriber threshold ({MIN_FOLLOWERS})."
            )

        if influencer.follower_count > MAX_FOLLOWERS:
            reasons.append(
                f"Above maximum subscriber threshold ({MAX_FOLLOWERS})."
            )

    stats = {
        "video_count": 0,
        "average_views": None,
        "engagement_rate": None,
    }

    if channel_id:
        stats = await provider.get_recent_video_stats(channel_id)

    if stats["video_count"] < MIN_RECENT_VIDEOS:
        reasons.append(
            f"Fewer than {MIN_RECENT_VIDEOS} recent videos "
            "with public view counts."
        )

    engagement_rate = stats["engagement_rate"]

    if engagement_rate is None:
        reasons.append("Engagement rate could not be calculated.")
    elif engagement_rate < MIN_ENGAGEMENT_RATE:
        reasons.append(
            "Engagement proxy below minimum threshold "
            f"({MIN_ENGAGEMENT_RATE}%)."
        )

    influencer.engagement_rate = engagement_rate

    # Existing model does not have an average_views field, so we return
    # that metric in the endpoint result rather than persisting it.
    influencer.qualification_status = (
        "Qualified" if not reasons else "Rejected"
    )
    influencer.rejection_reasons = "; ".join(reasons) if reasons else None

    return {
        "id": influencer.id,
        "name": influencer.name,
        "platform": influencer.platform,
        "follower_count": influencer.follower_count,
        "recent_video_count": stats["video_count"],
        "average_views": stats["average_views"],
        "engagement_rate": engagement_rate,
        "qualification_status": influencer.qualification_status,
        "rejection_reasons": influencer.rejection_reasons,
    }