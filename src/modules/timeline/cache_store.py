"""Redis cache keys, read-through, and invalidation for timeline lists."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from src.modules.timeline.cache_metrics import timeline_cache_metrics
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.timeline.schemas import TimelineListResponse


def _stable_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def timeline_list_cache_key(
    *,
    scope: str,
    participant_profile_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
    force_executor_id: uuid.UUID | None,
    event_type: str | None,
    executor_id: uuid.UUID | None,
    occurred_from: datetime | None,
    occurred_to: datetime | None,
    page: int,
    page_size: int,
) -> str:
    payload = {
        "scope": scope,
        "participant_profile_id": str(participant_profile_id)
        if participant_profile_id
        else None,
        "project_id": str(project_id) if project_id else None,
        "force_executor_id": str(force_executor_id) if force_executor_id else None,
        "event_type": event_type,
        "executor_id": str(executor_id) if executor_id else None,
        "occurred_from": occurred_from.isoformat() if occurred_from else None,
        "occurred_to": occurred_to.isoformat() if occurred_to else None,
        "page": page,
        "page_size": page_size,
    }
    h = hashlib.sha256(_stable_json(payload).encode()).hexdigest()[:32]
    if scope == "participant" and participant_profile_id is not None:
        return f"tl:pp:{participant_profile_id}:{h}"
    if scope == "project" and project_id is not None:
        return f"tl:pr:{project_id}:{h}"
    if scope == "global":
        return f"tl:gl:{h}"
    return f"tl:other:{h}"


async def cache_get_list(redis: Redis, key: str) -> TimelineListResponse | None:
    raw = await redis.get(key)
    if raw is None:
        timeline_cache_metrics.record_miss()
        return None
    timeline_cache_metrics.record_hit()
    return TimelineListResponse.model_validate_json(raw)


async def cache_set_list(
    redis: Redis,
    key: str,
    value: TimelineListResponse,
    ttl_seconds: int,
) -> None:
    await redis.setex(
        key,
        ttl_seconds,
        value.model_dump_json(by_alias=True),
    )


async def invalidate_for_timeline_event(
    redis: Redis,
    payload: TimelineEventJobPayload,
) -> None:
    pp = payload.participant_profile_id
    pr = payload.project_id
    p1 = f"tl:pp:{pp}:*"
    async for key in redis.scan_iter(match=p1):
        await redis.unlink(key)
    p2 = f"tl:pr:{pr}:*"
    async for key in redis.scan_iter(match=p2):
        await redis.unlink(key)
    async for key in redis.scan_iter(match="tl:gl:*"):
        await redis.unlink(key)
