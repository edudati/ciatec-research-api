"""Fixtures: ASGI HTTP client and async DB session."""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv

# Load project `.env` first so `os.environ.setdefault` does not mask local DB/JWT.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

# Fallbacks when `.env` / environment omit these (e.g. CI).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ciatec_research_api_v2_test",
)
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault(
    "JWT_SECRET",
    "test-jwt-secret-at-least-16-characters-long",
)
os.environ.setdefault(
    "JWT_REFRESH_SECRET",
    "test-refresh-secret-at-least-16-chars",
)

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Async HTTP client bound to the FastAPI app (no live server)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Async SQLAlchemy session (same engine as the app). Roll back after each test."""
    from src.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
