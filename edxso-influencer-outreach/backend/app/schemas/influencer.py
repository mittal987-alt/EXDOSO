from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class InfluencerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    platform: str = Field(min_length=1, max_length=50)

    profile_url: HttpUrl

    follower_count: int | None = Field(
        default=None,
        ge=0,
    )

    engagement_rate: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    category: str = "Unknown"

    content_themes: str | None = None

    contact_email: str = "Not Found"

    website: HttpUrl | None = None

    geography: str | None = None

    source_url: HttpUrl | None = None


class InfluencerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    platform: str
    profile_url: str
    follower_count: int | None
    engagement_rate: float | None
    category: str
    content_themes: str | None
    contact_email: str
    qualification_status: str
    rejection_reasons: str | None