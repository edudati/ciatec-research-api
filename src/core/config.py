import re
from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_TTL_SUFFIX = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)


def _ttl_string_to_seconds(raw: str) -> int:
    """Parse `900`, `30m`, `2h`, `7d` into seconds."""
    s = raw.strip()
    if not s:
        msg = "TTL string is empty"
        raise ValueError(msg)
    if s.isdigit():
        return int(s, 10)
    m = _TTL_SUFFIX.match(s)
    if not m:
        msg = f"Invalid JWT TTL (use seconds or suffix s/m/h/d): {raw!r}"
        raise ValueError(msg)
    n = int(m.group(1))
    unit = m.group(2).lower()
    mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return n * mult[unit]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(
        default="development",
        validation_alias=AliasChoices("ENV", "env", "ENVIRONMENT"),
        description="Runtime environment label.",
    )
    app_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_URL", "app_url"),
        description="Public base URL of the API (links, callbacks).",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("PORT", "port"),
        description="Suggested HTTP port (e.g. for Docker/compose docs).",
    )

    database_url: str = Field(
        ...,
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="PostgreSQL URL (postgresql:// or postgresql+asyncpg://).",
    )
    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
        description="Comma-separated list of allowed CORS origins.",
    )
    database_echo: bool = Field(
        default=False,
        validation_alias=AliasChoices("DATABASE_ECHO", "database_echo"),
    )

    jwt_secret: str = Field(
        ...,
        min_length=16,
        validation_alias=AliasChoices("JWT_SECRET", "jwt_secret"),
        description="HS256 secret for access tokens.",
    )
    jwt_refresh_secret: str = Field(
        ...,
        min_length=16,
        validation_alias=AliasChoices("JWT_REFRESH_SECRET", "jwt_refresh_secret"),
        description="Pepper for refresh token material.",
    )
    jwt_expires_in: int = Field(
        default=900,
        ge=30,
        validation_alias=AliasChoices(
            "JWT_EXPIRES_IN",
            "JWT_ACCESS_EXPIRE_SECONDS",
            "jwt_expires_in",
        ),
        description="Access JWT lifetime in seconds.",
    )
    jwt_refresh_expires_in: int = Field(
        default=604_800,
        ge=300,
        validation_alias=AliasChoices(
            "JWT_REFRESH_EXPIRES_IN",
            "JWT_REFRESH_EXPIRE_SECONDS",
            "jwt_refresh_expires_in",
        ),
        description="Refresh token row lifetime in seconds.",
    )
    jwt_issuer: str | None = Field(
        default=None,
        validation_alias=AliasChoices("JWT_ISSUER", "jwt_issuer"),
    )
    jwt_audience: str | None = Field(
        default=None,
        validation_alias=AliasChoices("JWT_AUDIENCE", "jwt_audience"),
    )
    self_report_token_ttl_seconds: int = Field(
        default=259_200,
        ge=60,
        le=31_536_000,
        validation_alias=AliasChoices(
            "SELF_REPORT_TOKEN_TTL_SECONDS",
            "self_report_token_ttl_seconds",
        ),
        description="Self-report fill link lifetime in seconds (default 72h).",
    )
    redis_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
        description="Redis URL for timeline cache and arq queue (optional).",
    )
    timeline_cache_ttl_seconds: int = Field(
        default=120,
        ge=5,
        le=86400,
        validation_alias=AliasChoices(
            "TIMELINE_CACHE_TTL_SECONDS",
            "timeline_cache_ttl_seconds",
        ),
        description="TTL for timeline list cache entries.",
    )
    timeline_cache_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "TIMELINE_CACHE_ENABLED",
            "timeline_cache_enabled",
        ),
        description="Use Redis timeline list cache when redis_url is set.",
    )
    timeline_events_async: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "TIMELINE_EVENTS_ASYNC",
            "timeline_events_async",
        ),
        description="Enqueue TimelineEvent persistence via arq after business commit.",
    )
    project_export_async_min_rows: int = Field(
        default=5000,
        ge=1,
        le=10_000_000,
        validation_alias=AliasChoices(
            "PROJECT_EXPORT_ASYNC_MIN_ROWS",
            "project_export_async_min_rows",
        ),
        description=(
            "Minimum timeline row count (or explicit async=true) for async export."
        ),
    )
    project_export_batch_size: int = Field(
        default=500,
        ge=50,
        le=5000,
        validation_alias=AliasChoices(
            "PROJECT_EXPORT_BATCH_SIZE",
            "project_export_batch_size",
        ),
        description="Rows per DB batch when exporting project timeline.",
    )
    project_export_storage_dir: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "PROJECT_EXPORT_STORAGE_DIR",
            "project_export_storage_dir",
        ),
        description="Absolute directory for async export files (default: system temp).",
    )

    @model_validator(mode="before")
    @classmethod
    def _self_report_token_ttl_human(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for key in ("SELF_REPORT_TOKEN_TTL", "self_report_token_ttl"):
            val = out.get(key)
            if isinstance(val, str) and val.strip() and not val.strip().isdigit():
                out["self_report_token_ttl_seconds"] = _ttl_string_to_seconds(val)
                break
        return out

    @model_validator(mode="before")
    @classmethod
    def _jwt_ttl_human_units(cls, data: Any) -> Any:
        """Allow `JWT_EXPIRES_IN=30m` and `JWT_REFRESH_EXPIRES_IN=7d` style values."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for key in (
            "JWT_EXPIRES_IN",
            "jwt_expires_in",
            "JWT_REFRESH_EXPIRES_IN",
            "jwt_refresh_expires_in",
        ):
            val = out.get(key)
            if isinstance(val, str) and val.strip() and not val.strip().isdigit():
                out[key] = _ttl_string_to_seconds(val)
        return out

    @model_validator(mode="before")
    @classmethod
    def _legacy_jwt_ttl_from_minutes_or_days(cls, data: Any) -> Any:
        """Support JWT_ACCESS_EXPIRE_MINUTES and JWT_REFRESH_EXPIRE_DAYS."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "JWT_EXPIRES_IN" not in out and "jwt_expires_in" not in out:
            for key in ("JWT_ACCESS_EXPIRE_MINUTES", "jwt_access_expire_minutes"):
                raw = out.get(key)
                if raw not in (None, ""):
                    try:
                        out["JWT_EXPIRES_IN"] = int(str(raw), 10) * 60
                    except ValueError:
                        pass
                    break
        if "JWT_REFRESH_EXPIRES_IN" not in out and "jwt_refresh_expires_in" not in out:
            for key in ("JWT_REFRESH_EXPIRE_DAYS", "jwt_refresh_expire_days"):
                raw = out.get(key)
                if raw not in (None, ""):
                    try:
                        out["JWT_REFRESH_EXPIRES_IN"] = int(str(raw), 10) * 24 * 3600
                    except ValueError:
                        pass
                    break
        return out

    @property
    def database_url_async(self) -> str:
        url = self.database_url.strip()
        if "+asyncpg" in url:
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
