"""Core business logic for URL shortening, redirection, and analytics."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base62 import encode_base62
from src.db.models import URL, ClickAnalytics
from src.schemas.url import (
    ClickEventSchema,
    URLAnalyticsResponse,
    URLCreate,
)


class ShortenerService:
    """Orchestrates database operations and Base62 encoding for short links."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_short_url(self, payload: URLCreate) -> URL:
        """Creates a new short link in the database."""
        if payload.custom_alias:
            short_link = payload.custom_alias
            find = await self.db.execute(
                select(URL).where(URL.short_code == short_link)
            )
            existing_url = find.scalar_one_or_none()
            if existing_url is not None:
                raise ValueError("Found another short-link in db")
            else:
                new_url = URL(
                    original_url=str(payload.url), short_code=short_link, is_custom=True
                )
                self.db.add(new_url)
                await self.db.commit()
                await self.db.refresh(new_url)
        else:
            expires_at = None
            if payload.expires_in_days:
                expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)
            new_url = URL(
                original_url=str(payload.url),
                short_code="",
                is_custom=False,
                expires_at=expires_at,
            )
            self.db.add(new_url)
            await (
                self.db.flush()
            )  # Tell db to generate key ID without finalizing the transaction
            new_url.short_code = encode_base62(new_url.id)
            await self.db.commit()
            await self.db.refresh(new_url)
        return new_url

    async def get_target_url(self, short_code: str) -> str | None:
        """Finds target URL by short code, checking expiration and active status."""
        find = await self.db.execute(
            select(URL).where(URL.short_code == short_code, URL.is_active)
        )
        exist_url = find.scalar_one_or_none()
        if exist_url is not None and (
            exist_url.expires_at is None or exist_url.expires_at >= datetime.now(UTC)
        ):
            return str(exist_url.original_url)
        return None

    async def record_click(
        self,
        short_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
    ) -> None:
        """Asynchronously persists a click event into the click_analytics table."""
        find = await self.db.execute(select(URL).where(URL.short_code == short_code))
        exist_url = find.scalar_one_or_none()
        if exist_url is not None:
            new_analytic = ClickAnalytics(
                url_id=exist_url.id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
            )
            self.db.add(new_analytic)
            await self.db.commit()

    async def get_analytics(self, short_code: str) -> URLAnalyticsResponse:
        """Retrieves total clicks count and recent click records for a short link."""
        find = await self.db.execute(select(URL).where(URL.short_code == short_code))
        exist_url = find.scalar_one_or_none()
        if exist_url is not None:
            query_total = select(func.count(ClickAnalytics.id)).where(
                ClickAnalytics.url_id == exist_url.id
            )
            total_clicks = (await self.db.execute(query_total)).scalar() or 0
            recent_query = (
                select(ClickAnalytics)
                .where(ClickAnalytics.url_id == exist_url.id)
                .order_by(ClickAnalytics.clicked_at.desc())
                .limit(10)
            )
            db_clicks = (await self.db.execute(recent_query)).scalars().all()
            recent_clicks = [ClickEventSchema.model_validate(c) for c in db_clicks]

            return URLAnalyticsResponse(
                short_code=short_code,
                original_url=exist_url.original_url,
                total_clicks=total_clicks,
                created_at=exist_url.created_at,
                expires_at=exist_url.expires_at,
                recent_clicks=recent_clicks,
            )
        else:
            raise ValueError("No url found.")
