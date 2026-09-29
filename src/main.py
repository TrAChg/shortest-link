"""FastAPI application entrypoint for ShortestLink."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.config import get_settings
from src.db.models import Base
from src.db.session import engine
from src.services.cache import cache_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown lifecycle events."""
    # Startup: Create tables if not exist (for dev/sqlite) & connect Redis
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        await cache_service.connect()
    except Exception as e:  # noqa: BLE001 - Allow app to start even if optional local Redis is offline
        print(f"[WARNING] Could not connect to Redis: {e}")

    yield

    # Shutdown: Disconnect Redis & dispose engine
    await cache_service.disconnect()
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory for ShortestLink."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="High-performance URL Shortener service built with FastAPI, PostgreSQL, and Redis.",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(api_router)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": settings.APP_NAME}

    return app


app = create_app()
