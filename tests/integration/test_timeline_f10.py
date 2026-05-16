"""F10-01 integration: timeline dispatcher and persistence with Postgres."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import fakeredis
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from tests.integration.test_project_enrollments import (
    _active_project_with_pi,
    _user_headers,
)

from src.core.config import get_settings
from src.core.database import AsyncSessionLocal
from src.models.timeline_event import TimelineEvent
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password
from src.modules.timeline.arq_tasks import persist_timeline_event
from src.modules.timeline.dispatcher import publish_timeline_event
from src.modules.timeline.job_payload import TimelineEventJobPayload

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-f10-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin F10",
                role="ADMIN",
                is_first_access=False,
            ),
        )
        session.add(
            AuthUser(
                user_id=user_id,
                password_hash=hash_password(_VALID_PASSWORD),
            ),
        )
        await session.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _VALID_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def test_enrollment_creates_timeline_event_row(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    part_headers = await _user_headers(
        client,
        email=f"pt-f10-{uuid.uuid4()}@example.com",
        name="Participant F10",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    r = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert r.status_code == 201
    eid = r.json()["id"]
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == eid,
            TimelineEvent.event_type == "ENROLLMENT",
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
    assert row is not None


async def test_publish_timeline_event_fallback_when_enqueue_raises(
    client: AsyncClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    part_headers = await _user_headers(
        client,
        email=f"pt-f10fb-{uuid.uuid4()}@example.com",
        name="Participant F10 FB",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    r = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert r.status_code == 201
    eid = r.json()["id"]
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == eid,
            TimelineEvent.event_type == "ENROLLMENT",
        )
        te = (await session.execute(stmt)).scalar_one()
        payload = TimelineEventJobPayload(
            id=te.id,
            participant_profile_id=te.participant_profile_id,
            project_id=te.project_id,
            enrollment_id=te.enrollment_id,
            executor_id=te.executor_id,
            event_type=te.event_type,
            source_type=te.source_type,
            source_id=te.source_id,
            occurred_at=te.occurred_at.isoformat(),
            context=dict(te.context),
        )
        await session.delete(te)
        await session.commit()

    fake_settings = get_settings().model_copy(update={"timeline_events_async": True})
    monkeypatch.setattr(
        "src.modules.timeline.dispatcher.get_settings",
        lambda: fake_settings,
    )
    redis_f = fakeredis.FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr(
        "src.modules.timeline.dispatcher.get_timeline_redis",
        lambda: redis_f,
    )
    pool = MagicMock()
    pool.enqueue_job = AsyncMock(side_effect=RuntimeError("enqueue down"))
    monkeypatch.setattr(
        "src.modules.timeline.dispatcher.get_timeline_arq_pool",
        lambda: pool,
    )

    await publish_timeline_event(payload)

    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                select(TimelineEvent).where(TimelineEvent.id == payload.id),
            )
        ).scalar_one_or_none()
    assert row is not None


async def test_persist_timeline_event_task_reinserts_deleted_row(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    part_headers = await _user_headers(
        client,
        email=f"pt-f10arq-{uuid.uuid4()}@example.com",
        name="Participant F10 ARQ",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    r = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert r.status_code == 201
    eid = r.json()["id"]
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == eid,
            TimelineEvent.event_type == "ENROLLMENT",
        )
        te = (await session.execute(stmt)).scalar_one()
        payload = TimelineEventJobPayload(
            id=te.id,
            participant_profile_id=te.participant_profile_id,
            project_id=te.project_id,
            enrollment_id=te.enrollment_id,
            executor_id=te.executor_id,
            event_type=te.event_type,
            source_type=te.source_type,
            source_id=te.source_id,
            occurred_at=te.occurred_at.isoformat(),
            context=dict(te.context),
        )
        await session.delete(te)
        await session.commit()

    ctx: dict[str, Any] = {"redis": fakeredis.FakeAsyncRedis(decode_responses=True)}
    await persist_timeline_event(ctx, payload.model_dump(mode="json"))

    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                select(TimelineEvent).where(TimelineEvent.id == payload.id),
            )
        ).scalar_one_or_none()
    assert row is not None
