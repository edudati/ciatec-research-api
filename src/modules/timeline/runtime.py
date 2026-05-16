"""Redis + arq lifecycle for timeline cache and async event writes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from src.core.config import Settings

if TYPE_CHECKING:
    from arq.connections import ArqRedis

log = logging.getLogger(__name__)

_redis: Redis | None = None
_arq_pool: ArqRedis | None = None


async def init_timeline_runtime(settings: Settings) -> None:
    global _redis, _arq_pool
    await shutdown_timeline_runtime()
    if settings.redis_url:
        client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            await client.ping()
        except Exception:
            log.exception("Redis ping failed; timeline cache and async queue disabled")
            await client.aclose()
            return
        _redis = client
        try:
            from arq import create_pool
            from arq.connections import RedisSettings

            redis_settings = RedisSettings.from_dsn(settings.redis_url)
            _arq_pool = await create_pool(redis_settings)
        except Exception:
            log.exception(
                "arq pool creation failed; async timeline writes "
                "and export jobs disabled",
            )
            _arq_pool = None


async def shutdown_timeline_runtime() -> None:
    global _redis, _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close(close_connections=True)
        _arq_pool = None
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_timeline_redis() -> Redis | None:
    return _redis


def get_timeline_arq_pool() -> ArqRedis | None:
    return _arq_pool


def reset_timeline_runtime_for_tests() -> None:
    """Clear references without closing (tests)."""
    global _redis, _arq_pool
    _redis = None
    _arq_pool = None
