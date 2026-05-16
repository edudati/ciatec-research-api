"""F10-01 unit tests: timeline cache (no Postgres / integration conftest)."""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import fakeredis
import pytest

from src.modules.timeline.cache_metrics import timeline_cache_metrics
from src.modules.timeline.cache_store import (
    cache_get_list,
    cache_set_list,
    invalidate_for_timeline_event,
)
from src.modules.timeline.job_payload import TimelineEventJobPayload
from src.modules.timeline.schemas import TimelineListResponse


@pytest.fixture(autouse=True)
def _reset_timeline_cache_metrics() -> Generator[None]:
    timeline_cache_metrics.reset_for_tests()
    yield


@pytest.mark.asyncio
async def test_timeline_cache_invalidation_deletes_matching_keys() -> None:
    r = fakeredis.FakeAsyncRedis(decode_responses=True)
    pp = uuid.uuid4()
    pr = uuid.uuid4()
    await r.set(f"tl:pp:{pp}:deadbeef", '{"items":[],"total":0,"page":1,"pageSize":10}')
    await r.set(f"tl:pr:{pr}:cafebabe", '{"items":[],"total":0,"page":1,"pageSize":10}')
    await r.set("tl:gl:feedface", '{"items":[],"total":0,"page":1,"pageSize":10}')
    payload = TimelineEventJobPayload(
        id=uuid.uuid4(),
        participant_profile_id=pp,
        project_id=pr,
        enrollment_id=None,
        executor_id=None,
        event_type="TEST",
        source_type="Test",
        source_id="1",
        occurred_at=datetime.now(UTC).isoformat(),
        context={},
    )
    await invalidate_for_timeline_event(r, payload)
    assert await r.get(f"tl:pp:{pp}:deadbeef") is None
    assert await r.get(f"tl:pr:{pr}:cafebabe") is None
    assert await r.get("tl:gl:feedface") is None


@pytest.mark.asyncio
async def test_timeline_cache_metrics_miss_then_hit() -> None:
    r = fakeredis.FakeAsyncRedis(decode_responses=True)
    key = "tl:gl:deadbeef00000000000000000000000"
    assert await cache_get_list(r, key) is None
    h, m = timeline_cache_metrics.snapshot()
    assert m == 1
    assert h == 0
    body = TimelineListResponse(items=[], total=0, page=1, page_size=10)
    await cache_set_list(r, key, body, 60)
    assert await cache_get_list(r, key) is not None
    h2, m2 = timeline_cache_metrics.snapshot()
    assert h2 == 1
    assert m2 == 1
