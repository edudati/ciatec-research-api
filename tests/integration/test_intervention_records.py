"""Intervention records API integration tests."""

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
    email = f"adm-ir-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin IR",
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
        email=f"pi-ir-{uuid.uuid4()}@example.com",
        name="PI IR",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"IR-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "IR proj", "piUserId": pi_id},
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
) -> tuple[str, str, dict[str, str]]:
    part_headers = await _user_headers(
        client,
        email=f"pt-ir-{uuid.uuid4()}@example.com",
        name="Participant IR",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    cr = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert cr.status_code == 201
    return str(cr.json()["participantProfileId"]), str(uid), part_headers


async def _intervention_template_exercise(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"EX-{suf}",
            "name": "Walk",
            "type": "EXERCISE",
        },
    )
    assert r.status_code == 201
    return str(r.json()["id"])


async def _seed_game_two_levels(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, str, str, str]:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "IR Match Game", "is_active": True},
    )
    assert g.status_code == 201
    game_id = g.json()["id"]

    p = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={
            "game_id": game_id,
            "name": "Default",
            "is_default": True,
            "is_active": True,
        },
    )
    assert p.status_code == 201
    preset_id = p.json()["id"]

    l1 = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": preset_id,
            "name": "L1",
            "order": 0,
            "config": {"difficulty": 1},
            "is_active": True,
        },
    )
    assert l1.status_code == 201
    level1_id = l1.json()["id"]

    l2 = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": preset_id,
            "name": "L2",
            "order": 1,
            "config": {"difficulty": 2},
            "is_active": True,
        },
    )
    assert l2.status_code == 201
    level2_id = l2.json()["id"]

    return game_id, preset_id, level1_id, level2_id


async def test_executor_not_project_member_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, part_user_id, _ = await _enrolled_participant_profile(
        client, admin_headers, pid
    )
    tid = await _intervention_template_exercise(client, admin_headers)
    performed = datetime.now(UTC).isoformat()
    r = await client.post(
        f"/api/v1/projects/{pid}/interventions",
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


async def test_match_id_already_linked_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid, part_headers = await _enrolled_participant_profile(
        client, admin_headers, pid
    )
    game_id, _preset_id, level1_id, _level2_id = await _seed_game_two_levels(
        client, admin_headers
    )
    suf = uuid.uuid4().hex[:8]
    it = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"GM-{suf}",
            "name": "Game session",
            "type": "GAME",
            "gameId": game_id,
        },
    )
    assert it.status_code == 201
    tid = str(it.json()["id"])

    m = await client.post(
        "/api/v1/sessions/matches",
        headers=part_headers,
        json={"game_id": game_id, "level_id": level1_id},
    )
    assert m.status_code == 201
    match_id = m.json()["id"]

    performed = datetime.now(UTC).isoformat()
    body = {
        "participantProfileId": profile_id,
        "templateId": tid,
        "executorId": pi_id,
        "performedAt": performed,
        "matchId": match_id,
        "data": {},
    }
    first = await client.post(
        f"/api/v1/projects/{pid}/interventions",
        headers=admin_headers,
        json=body,
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/projects/{pid}/interventions",
        headers=admin_headers,
        json=body,
    )
    assert second.status_code == 409
    assert second.json()["code"] == "INTERVENTION_MATCH_ALREADY_LINKED"


async def test_timeline_event_created_on_post(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid, _ = await _enrolled_participant_profile(
        client, admin_headers, pid
    )
    tid = await _intervention_template_exercise(client, admin_headers)
    performed = datetime.now(UTC).isoformat()
    r = await client.post(
        f"/api/v1/projects/{pid}/interventions",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": pi_id,
            "performedAt": performed,
            "durationMinutes": 30,
            "data": {"sets": 3},
        },
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == rid,
            TimelineEvent.event_type == "INTERVENTION",
            TimelineEvent.source_type == "InterventionRecord",
        )
        res = await session.execute(stmt)
        ev = res.scalar_one_or_none()
    assert ev is not None
    assert str(ev.executor_id) == pi_id
    assert str(ev.project_id) == pid
