"""Assessment records API integration tests."""

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.timeline_event import TimelineEvent
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-ar-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin AR",
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


async def _user_headers(
    client: AsyncClient,
    *,
    email: str,
    name: str,
    role: str,
) -> dict[str, str]:
    uid = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=uid,
                email=email,
                name=name,
                role=role,
                is_first_access=False,
            ),
        )
        session.add(
            AuthUser(
                user_id=uid,
                password_hash=hash_password(_VALID_PASSWORD),
            ),
        )
        await session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _VALID_PASSWORD},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['accessToken']}"}


async def _active_project_with_pi(
    client: AsyncClient, admin_headers: dict[str, str]
) -> tuple[str, str]:
    pi_headers = await _user_headers(
        client,
        email=f"pi-ar-{uuid.uuid4()}@example.com",
        name="PI AR",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"AR-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Assess proj", "piUserId": pi_id},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    act = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert act.status_code == 200
    return str(pid), str(pi_id)


async def _enrolled_participant_profile(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
) -> tuple[str, str]:
    part_headers = await _user_headers(
        client,
        email=f"pt-ar-{uuid.uuid4()}@example.com",
        name="Participant AR",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    cr = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert cr.status_code == 201
    return str(cr.json()["participantProfileId"]), str(uid)


async def _assessment_template(
    client: AsyncClient,
    admin_headers: dict[str, str],
    *,
    active: bool = True,
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": f"AR-T-{suf}",
            "name": "Template AR",
            "type": "MOTOR",
        },
    )
    assert r.status_code == 201
    tid = str(r.json()["id"])
    if not active:
        off = await client.patch(
            f"/api/v1/instruments/assessments/{tid}",
            headers=admin_headers,
            json={"isActive": False},
        )
        assert off.status_code == 200
    return tid


async def test_executor_not_project_member_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, part_user_id = await _enrolled_participant_profile(
        client, admin_headers, pid
    )
    tid = await _assessment_template(client, admin_headers, active=True)
    performed = datetime.now(UTC).isoformat()
    r = await client.post(
        f"/api/v1/projects/{pid}/assessments",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": part_user_id,
            "performedAt": performed,
            "data": {},
        },
    )
    assert r.status_code == 403
    assert r.json()["code"] == "EXECUTOR_NOT_PROJECT_MEMBER"


async def test_inactive_template_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _ = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _assessment_template(client, admin_headers, active=False)
    performed = datetime.now(UTC).isoformat()
    r = await client.post(
        f"/api/v1/projects/{pid}/assessments",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": pi_id,
            "performedAt": performed,
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "ASSESSMENT_TEMPLATE_INACTIVE"


async def test_timeline_event_created_on_post(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _ = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _assessment_template(client, admin_headers, active=True)
    performed = datetime.now(UTC).isoformat()
    r = await client.post(
        f"/api/v1/projects/{pid}/assessments",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": pi_id,
            "performedAt": performed,
            "score": "42.5",
        },
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == rid,
            TimelineEvent.event_type == "ASSESSMENT",
            TimelineEvent.source_type == "AssessmentRecord",
        )
        res = await session.execute(stmt)
        ev = res.scalar_one_or_none()
    assert ev is not None
    assert str(ev.executor_id) == pi_id
    assert str(ev.project_id) == pid
