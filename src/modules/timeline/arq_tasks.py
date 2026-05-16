"""arq worker task: persist TimelineEvent and invalidate timeline list cache."""

from __future__ import annotations

import logging
from typing import Any

from src.core.database import AsyncSessionLocal
from src.modules.timeline.cache_store import invalidate_for_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.timeline.persist import insert_timeline_event_from_payload

log = logging.getLogger(__name__)


async def persist_timeline_event(
    ctx: dict[str, Any],
    payload_dict: dict[str, Any],
) -> None:
    payload = TimelineEventJobPayload.model_validate(payload_dict)
    async with AsyncSessionLocal() as session:
        await insert_timeline_event_from_payload(session, payload)
        await session.commit()
    redis = ctx.get("redis")
    if redis is not None:
        try:
            await invalidate_for_timeline_event(redis, payload)
        except Exception:
            log.exception("timeline cache invalidation failed in arq worker")
