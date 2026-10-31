
import re
from urllib.parse import urlparse

from app.models.influencer import Influencer
from app.providers.youtube_provider import YouTubeProvider


EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

URL_PATTERN = re.compile(
    r"https?://[^\s<>\[\]\"']+",
    re.IGNORECASE,
)

THEME_KEYWORDS = {
    "Workout and Training": [
        "workout",
        "training",
        "exercise",
        "gym",
        "strength",
        "muscle",
        "fitness",
    ],
    "Nutrition and Diet": [
        "nutrition",
        "diet",
        "protein",
        "meal",
        "food",
        "healthy eating",
    ],
    "Weight Management": [
        "weight loss",
        "fat loss",
        "weight gain",
        "transformation",
    ],
    "Yoga and Wellness": [
        "yoga",
        "meditation",
        "wellness",
        "mindfulness",
        "flexibility",
    ],
    "Sports and Performance": [
        "sports",
        "athlete",
        "performance",
        "running",
        "endurance",
    ],
}


def extract_email(text: str) -> str:
    """
    Extract the first email address from publicly available text.

    This does not verify whether the address exists or belongs
    to the influencer.
    """
    if not text:
        return "Not Found"

    matches = EMAIL_PATTERN.findall(text)

    for email in matches:
        email = email.strip().rstrip(".,;:")

        # Ignore obvious placeholder/example addresses.
        domain = email.rsplit("@", 1)[-1].lower()

        if domain.endswith(".example"):
            continue

        if domain in {"example.com", "example.org", "example.net"}:
            continue

        return email

    return "Not Found"


def extract_urls(text: str) -> list[str]:
    """Extract unique HTTP(S) URLs from text."""

    if not text:
        return []

    urls = []

    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,;:!?)")

        try:
            parsed = urlparse(url)

            if parsed.scheme not in {"http", "https"}:
                continue

            if not parsed.hostname:
                continue

            # Avoid treating YouTube links as external websites.
            hostname = parsed.hostname.lower()

            if (
                hostname == "youtube.com"
                or hostname.endswith(".youtube.com")
                or hostname == "youtu.be"
            ):
                continue

            if url not in urls:
                urls.append(url)

        except ValueError:
            continue

    return urls


def detect_content_themes(text: str) -> list[str]:
    """
    Identify themes using explicit keyword matches.

    These are inferred themes, not verified classifications.
    """
    if not text:
        return []

    normalized_text = text.lower()
    themes = []

    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            themes.append(theme)

    return themes


def get_channel_id(influencer: Influencer) -> str | None:
    """Get the YouTube channel ID from the stored source URL."""

    source_url = influencer.source_url

    if not source_url:
        return None

    try:
        parsed = urlparse(source_url)
    except ValueError:
        return None

    hostname = (parsed.hostname or "").lower()

    if hostname not in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }:
        return None

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if len(parts) >= 2 and parts[0] == "channel":
        return parts[1]

    return None


async def enrich_influencer(
    influencer: Influencer,
    provider: YouTubeProvider,
) -> dict:
    """
    Enrich one influencer using public YouTube channel metadata.

    Existing contact information is preserved.
    No email verification is claimed by this service.
    """

    result = {
        "id": influencer.id,
        "name": influencer.name,
        "contact_email": influencer.contact_email or "Not Found",
        "website": influencer.website or "Not Found",
        "content_themes": influencer.content_themes or "Not Found",
        "status": "Enriched",
        "message": None,
    }

    channel_id = get_channel_id(influencer)

    if not channel_id:
        result["status"] = "Needs Review"
        result["message"] = (
            "Could not extract a YouTube channel ID from source_url."
        )
        return result

    channels = await provider.get_channels([channel_id])

    if not channels:
        result["status"] = "Needs Review"
        result["message"] = (
            "YouTube did not return details for this channel."
        )
        return result

    channel = channels[0]
    snippet = channel.get("snippet", {})

    description = snippet.get("description", "").strip()

    # Extract contact information only if no email is already stored.
    existing_email = influencer.contact_email

    if not existing_email or existing_email.strip().lower() in {
        "not found",
        "unknown",
        "none",
    }:
        email = extract_email(description)
        influencer.contact_email = email
    else:
        email = existing_email

    # Store a public external link if no website is already stored.
    existing_website = influencer.website

    if not existing_website or existing_website.strip().lower() in {
        "not found",
        "unknown",
        "none",
    }:
        urls = extract_urls(description)
        website = urls[0] if urls else "Not Found"

        influencer.website = (
            website if website != "Not Found" else None
        )
    else:
        website = existing_website

    # Preserve the original description when available.
    # If there is no description, store explicitly detected themes.
    existing_themes = influencer.content_themes

    if not existing_themes or existing_themes.strip().lower() in {
        "not found",
        "unknown",
        "none",
    }:
        themes = detect_content_themes(description)

        if description:
            influencer.content_themes = description[:2000]
        elif themes:
            influencer.content_themes = ", ".join(themes)
        else:
            influencer.content_themes = "Not Found"

    # Do not claim that an email is verified merely because it was found.
    influencer.email_verified = False

    result.update(
        {
            "name": snippet.get("title") or influencer.name,
            "contact_email": email or "Not Found",
            "website": website or "Not Found",
            "content_themes": (
                influencer.content_themes or "Not Found"
            ),
            "detected_themes": detect_content_themes(description),
            "email_verified": False,
            "status": "Enriched",
        }
    )

    return result
