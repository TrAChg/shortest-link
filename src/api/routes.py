"""FastAPI route handlers for URL Shortening, Redirection, and Analytics."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.session import AsyncSessionLocal, get_db
from src.schemas.url import URLAnalyticsResponse, URLCreate, URLResponse
from src.services.cache import cache_service
from src.services.shortener import ShortenerService

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
    """Creates a short link for the specified URL."""
    services = ShortenerService(db)
    try:
        new_short_url = await services.create_short_url(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return URLResponse(
        short_code=new_short_url.short_code,
        short_url=f"{settings.BASE_URL}/{new_short_url.short_code}",
        original_url=new_short_url.original_url,
        created_at=new_short_url.created_at,
        expires_at=new_short_url.expires_at,
    )


async def _log_click_in_background(
    short_code: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    referrer: str | None = None,
) -> None:
    """Background task to record click analytics in an isolated DB session."""
    async with AsyncSessionLocal() as session:
        service = ShortenerService(session)
        await service.record_click(
            short_code=short_code,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )


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
    """Redirects the client to the target URL using HTTP 307."""
    service = ShortenerService(db)
    target_url = await cache_service.get_url(short_code)
    if not target_url:
        target_url = await service.get_target_url(short_code)
        if not target_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found or has expired",
            )
        await cache_service.set_url(short_code, target_url)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")
    background_tasks.add_task(
        _log_click_in_background,
        short_code=short_code,
        ip_address=client_ip,
        user_agent=user_agent,
        referrer=referrer,
    )
    return RedirectResponse(
        url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
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
    """Returns total click count and recent access history for a short code."""
    service = ShortenerService(db)
    try:
        analytics = await service.get_analytics(short_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return analytics
