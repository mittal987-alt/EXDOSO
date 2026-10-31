
import re

from app.models.influencer import Influencer


def _clean_text(value: str | None, fallback: str) -> str:
    """Normalize text and handle missing values."""

    if not value:
        return fallback

    value = value.strip()

    if value.lower() in {
        "not found",
        "unknown",
        "none",
        "n/a",
    }:
        return fallback

    return re.sub(r"\s+", " ", value)


def _word_count(text: str) -> int:
    """Count words consistently."""

    return len(re.findall(r"\b[\w'-]+\b", text))


def generate_email(influencer: Influencer) -> dict:
    """Generate a personalized email containing 60–90 words."""

    name = _clean_text(influencer.name, "there")
    themes = _clean_text(
        influencer.content_themes,
        "fitness and wellness",
    )
    niche = _clean_text(
        influencer.category,
        "fitness content",
    )

    # Keep personalization concise.
    theme_words = themes.split()[:5]
    niche_words = niche.split()[:3]

    message = ""

    # Reduce personalization if unusually long names or fields
    # cause the email to exceed the required word limit.
    while True:
        short_themes = " ".join(theme_words) or "fitness"
        short_niche = " ".join(niche_words) or "fitness"

        message = (
            f"Hi {name},\n\n"
            f"I came across your YouTube channel and noticed your "
            f"content about {short_themes}. Your work in "
            f"{short_niche} may be a good fit for a potential "
            f"creator collaboration.\n\n"
            f"We would love to share our campaign details and learn "
            f"what kinds of partnerships interest you. If this sounds "
            f"relevant, would you be open to reviewing the opportunity "
            f"and discussing whether it aligns with your audience?\n\n"
            f"Thank you for your time. I look forward to hearing from you."
        )

        count = _word_count(message)

        if 60 <= count <= 90:
            break

        if count > 90 and theme_words:
            theme_words.pop()
            continue

        if count > 90 and niche_words:
            niche_words.pop()
            continue

        if count > 90:
            name = "there"
            continue

        raise ValueError(
            f"Could not generate an email within 60–90 words. "
            f"Actual count: {count}."
        )

    return {
        "channel": "Email",
        "subject": "Potential Creator Collaboration",
        "message": message,
        "word_count": _word_count(message),
    }


def generate_instagram_dm(influencer: Influencer) -> dict:
    """Generate a personalized Instagram DM containing 15–30 words."""

    name = _clean_text(influencer.name, "there")
    themes = _clean_text(
        influencer.content_themes,
        "fitness content",
    )

    theme_words = themes.split()[:3]

    message = (
        f"Hi {name}! We noticed your content about "
        f"{' '.join(theme_words)} and would love to discuss "
        f"a potential creator collaboration. Would you be open "
        f"to hearing more?"
    )

    count = _word_count(message)

    # Shorten the greeting if the creator's name makes the DM too long.
    if count > 30:
        message = (
            f"Hi there! We liked your fitness content and would love "
            f"to discuss a potential creator collaboration. "
            f"Would you be open to hearing more?"
        )
        count = _word_count(message)

    if not 15 <= count <= 30:
        raise ValueError(
            f"Instagram DM must contain 15–30 words; got {count}."
        )

    return {
        "channel": "Instagram DM",
        "subject": None,
        "message": message,
        "word_count": count,
    }


def generate_outreach_drafts(influencer: Influencer) -> list[dict]:
    """Generate both drafts for a qualified influencer."""

    if influencer.qualification_status != "Qualified":
        raise ValueError(
            "Outreach drafts can only be generated for qualified influencers."
        )

    return [
        generate_email(influencer),
        generate_instagram_dm(influencer),
    ]
