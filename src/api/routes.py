"""FastAPI route handlers for URL Shortening, Redirection, and Analytics."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.session import get_db
from src.schemas.url import URLAnalyticsResponse, URLCreate, URLResponse

router = APIRouter()
settings = get_settings()


@router.post(
    "/api/v1/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new short link",
)
async def shorten_url(
    payload: URLCreate,
    db: AsyncSession = Depends(get_db),
) -> URLResponse:
    """Creates a short link for the specified URL.

    - Validates target URL.
    - Generates Base62 code or assigns custom alias.
    - Saves to PostgreSQL and warms Redis cache.

    TODO (Student):
        1. Call ShortenerService.create_short_url(db, payload).
        2. Construct and return URLResponse with full clickable short_url.
    """
    raise NotImplementedError("TODO: Implement /api/v1/shorten endpoint yourself!")


@router.get(
    "/{short_code}",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=RedirectResponse,
    summary="Redirect short code to destination URL",
)
async def redirect_to_target(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Redirects the client to the target URL using HTTP 307.

    Redirection sequence:
    1. Check Redis cache first.
    2. On cache miss, query PostgreSQL database.
    3. If found in DB, populate Redis cache.
    4. Enqueue background task to log click analytics (IP, Referrer, User-Agent).
    5. If not found or expired, raise HTTPException(404).

    TODO (Student):
        Implement the cache-aside check and return RedirectResponse(url=target_url, status_code=307).
    """
    raise NotImplementedError(
        "TODO: Implement /{short_code} redirection endpoint yourself!"
    )


@router.get(
    "/api/v1/analytics/{short_code}",
    response_model=URLAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve analytics for a short link",
)
async def get_url_analytics(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> URLAnalyticsResponse:
    """Returns total click count and recent access history for a short code.

    TODO (Student):
        1. Call ShortenerService.get_analytics(db, short_code).
        2. If link does not exist, raise HTTPException(404).
        3. Return URLAnalyticsResponse.
    """
    raise NotImplementedError("TODO: Implement analytics endpoint yourself!")
