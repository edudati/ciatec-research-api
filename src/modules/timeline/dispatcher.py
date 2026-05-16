"""Publish TimelineEvent after business transaction (arq or synchronous fallback)."""

from __future__ import annotations

import logging

from redis.asyncio import Redis

from src.core.config import get_settings
from src.core.database import AsyncSessionLocal
from src.modules.timeline.cache_store import invalidate_for_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.timeline.persist import insert_timeline_event_from_payload
from src.modules.timeline.runtime import get_timeline_arq_pool, get_timeline_redis

log = logging.getLogger(__name__)


async def persist_timeline_event_synchronously(
    payload: TimelineEventJobPayload,
    redis: Redis | None,
) -> None:
    async with AsyncSessionLocal() as session:
        await insert_timeline_event_from_payload(session, payload)
        await session.commit()
    if redis is not None:
        try:
            await invalidate_for_timeline_event(redis, payload)
        except Exception:
            log.exception("timeline cache invalidation failed after sync persist")


async def publish_timeline_event(payload: TimelineEventJobPayload) -> None:
    settings = get_settings()
    redis = get_timeline_redis()
    pool = get_timeline_arq_pool()
    if settings.timeline_events_async and redis is not None and pool is not None:
        try:
            from src.modules.timeline import arq_tasks

            job_name = arq_tasks.persist_timeline_event.__qualname__
            await pool.enqueue_job(
                job_name,
                payload.model_dump(mode="json"),
            )
            return
        except Exception:
            log.exception("arq enqueue failed; persisting timeline synchronously")
    await persist_timeline_event_synchronously(payload, redis)
