"""Core business logic for URL shortening, redirection, and analytics."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import URL
from src.schemas.url import URLAnalyticsResponse, URLCreate


class ShortenerService:
    """Orchestrates database operations and Base62 encoding for short links."""

    @staticmethod
    async def create_short_url(db: AsyncSession, payload: URLCreate) -> URL:
        """Creates a new short link in the database.

        If custom_alias is provided:
            1. Verify it does not already exist in the database.
            2. If it exists, raise an error (e.g. ValueError or HTTPException 409).
            3. If free, save with short_code = custom_alias and is_custom = True.

        If custom_alias is NOT provided:
            1. Insert the URL record with a temporary placeholder or compute next ID.
            2. Convert the auto-increment ID to Base62 using `encode_base62(url.id)`.
            3. Update the record with the generated short_code.

        Args:
            db: Active async database session.
            payload: Validated URLCreate schema.

        Returns:
            The newly created URL ORM instance.

        TODO (Student):
            Implement the creation workflow, commit to DB, and return the URL object.
        """
        raise NotImplementedError(
            "TODO: Implement create_short_url business logic yourself!"
        )

    @staticmethod
    async def get_target_url(db: AsyncSession, short_code: str) -> str | None:
        """Finds target URL by short code, checking expiration and active status.

        Args:
            db: Active async database session.
            short_code: The code to look up.

        Returns:
            The original destination URL if valid and active; None otherwise.

        TODO (Student):
            1. Query URL model where short_code == short_code and is_active == True.
            2. Check if expires_at is set and in the past.
            3. Return url.original_url or None.
        """
        raise NotImplementedError(
            "TODO: Implement get_target_url lookup logic yourself!"
        )

    @staticmethod
    async def record_click(
        db: AsyncSession,
        short_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
    ) -> None:
        """Asynchronously persists a click event into the click_analytics table.

        Args:
            db: Active async database session.
            short_code: The short code that was visited.
            ip_address: Client IP address.
            user_agent: Client User-Agent header.
            referrer: Client Referrer header.

        TODO (Student):
            1. Find the URL record corresponding to short_code.
            2. Insert ClickAnalytics(url_id=url.id, ip_address=ip_address, ...).
            3. Commit transaction.
        """
        raise NotImplementedError(
            "TODO: Implement record_click analytics logging yourself!"
        )

    @staticmethod
    async def get_analytics(db: AsyncSession, short_code: str) -> URLAnalyticsResponse:
        """Retrieves total clicks count and recent click records for a short link.

        Args:
            db: Active async database session.
            short_code: The short code to analyze.

        Returns:
            URLAnalyticsResponse with aggregate metrics.

        TODO (Student):
            1. Query URL model for short_code.
            2. Count total rows in click_analytics for this url_id.
            3. Query the 10 most recent click records.
            4. Construct and return URLAnalyticsResponse.
        """
        raise NotImplementedError("TODO: Implement get_analytics reporting yourself!")
