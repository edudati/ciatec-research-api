"""Tests for settings helpers not exercised by HTTP integration tests."""

import pytest

from src.core.config import Settings, _ttl_string_to_seconds


def test_ttl_string_to_seconds_variants() -> None:
    assert _ttl_string_to_seconds("120") == 120
    assert _ttl_string_to_seconds(" 5m ") == 300
    assert _ttl_string_to_seconds("2H") == 7200
    assert _ttl_string_to_seconds("1d") == 86400


def test_ttl_string_to_seconds_invalid() -> None:
    with pytest.raises(ValueError, match="empty"):
        _ttl_string_to_seconds("   ")
    with pytest.raises(ValueError, match="Invalid JWT TTL"):
        _ttl_string_to_seconds("not-a-ttl")


def test_settings_jwt_ttl_human_strings() -> None:
    s = Settings.model_validate(
        {
            "database_url": "postgresql://localhost/db",
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
            "jwt_expires_in": "10m",
            "jwt_refresh_expires_in": "2d",
        },
    )
    assert s.jwt_expires_in == 600
    assert s.jwt_refresh_expires_in == 2 * 86400


def test_settings_database_url_async_variants() -> None:
    same = Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://localhost/db",
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
        },
    ).database_url_async
    assert same.startswith("postgresql+asyncpg://")

    conv = Settings.model_validate(
        {
            "database_url": "postgresql://localhost/db",
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
        },
    ).database_url_async
    assert conv.startswith("postgresql+asyncpg://")

    legacy = Settings.model_validate(
        {
            "database_url": "postgres://localhost/db",
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
        },
    ).database_url_async
    assert legacy.startswith("postgresql+asyncpg://")


def test_settings_cors_origin_list() -> None:
    s = Settings.model_validate(
        {
            "database_url": "postgresql://localhost/db",
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
            "cors_origins": " http://a.com , http://b.com ",
        },
    )
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_settings_database_url_async_unknown_scheme() -> None:
    raw = "sqlite+aiosqlite:///./test.db"
    u = Settings.model_validate(
        {
            "database_url": raw,
            "jwt_secret": "s" * 16,
            "jwt_refresh_secret": "r" * 16,
        },
    ).database_url_async
    assert u == raw


def test_create_app_openapi_is_cached() -> None:
    from src.main import create_app

    app = create_app()
    first = app.openapi()
    second = app.openapi()
    assert first is second


@pytest.mark.asyncio
async def test_docs_and_redoc_routes() -> None:
    from httpx import ASGITransport, AsyncClient

    from src.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        d = await ac.get("/docs")
        assert d.status_code == 200
        assert "swagger" in d.text.lower()
        r = await ac.get("/redoc")
        assert r.status_code == 200
        assert "redoc" in r.text.lower()
