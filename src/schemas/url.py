"""Pydantic request and response schemas for URL Shortener endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class URLCreate(BaseModel):
    """Creating a new short link."""

    url: HttpUrl = Field(..., description="Must include http:// or https://")
    custom_alias: str | None = Field(
        None,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="It's your custom link.",
    )
    expires_in_days: int | None = Field(
        None, ge=1, le=365, description="Validity duration in days."
    )


class URLResponse(BaseModel):
    """API response after successfully creating link."""

    short_code: str = Field(..., description="Unique alphanumeric short code")
    short_url: str = Field(..., description="Full clickable short URL")
    original_url: str = Field(..., description="Original destination URL")
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class ClickEventSchema(BaseModel):
    """Schema for individual click event details in analytics."""

    clicked_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    referrer: str | None = None

    model_config = {"from_attributes": True}


class URLAnalyticsResponse(BaseModel):
    """Click history for a short link."""

    short_code: str
    original_url: str
    total_clicks: int
    created_at: datetime
    expires_at: datetime | None = None
    recent_clicks: list[ClickEventSchema] = []

    model_config = {"from_attributes": True}
