import os
from collections.abc import AsyncGenerator

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
from httpx import ASGITransport, AsyncClient

from src.db.models import Base
from src.db.session import engine
from src.main import app


@pytest.fixture(autouse=True)
async def clean_db() -> AsyncGenerator[None, None]:
    """Ensures each test starts with a clean, isolated database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
