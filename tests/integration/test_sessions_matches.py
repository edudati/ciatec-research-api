"""Sessions and matches API (F0-05)."""

import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select

from src.core.database import AsyncSessionLocal
from src.models.timeline_event import TimelineEvent

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    from src.core.database import AsyncSessionLocal
    from src.models.user import AuthUser, User
    from src.modules.auth.passwords import hash_password

    email = f"adm-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin User",
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


@pytest_asyncio.fixture
async def player_headers(client: AsyncClient) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player One",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _seed_game_two_levels(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, str, str, str]:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Match Test Game", "is_active": True},
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


async def _active_project_with_pi(
    client: AsyncClient, admin_headers: dict[str, str]
) -> tuple[str, str]:
    from src.models.user import AuthUser, User
    from src.modules.auth.passwords import hash_password

    email = f"pi-sm-{uuid.uuid4()}@example.com"
    pi_uid = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=pi_uid,
                email=email,
                name="PI SM",
                role="PI",
                is_first_access=False,
            ),
        )
        session.add(
            AuthUser(
                user_id=pi_uid,
                password_hash=hash_password(_VALID_PASSWORD),
            ),
        )
        await session.commit()
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _VALID_PASSWORD},
    )
    assert login.status_code == 200
    pi_headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"SM-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Session match proj", "piUserId": pi_id},
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


async def _enroll_user_in_project(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
    player_user_id: str,
) -> tuple[str, str]:
    cr = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": player_user_id, "role": "PARTICIPANT"},
    )
    assert cr.status_code == 201
    j = cr.json()
    return str(j["id"]), str(j["participantProfileId"])


async def test_create_match_locked_level_returns_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level1_id},
    )

    locked = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level2_id},
    )
    assert locked.status_code == 403
    assert locked.json()["code"] == "LEVEL_LOCKED"


async def test_finish_duplicate_without_key_returns_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, _level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level1_id},
    )
    assert m.status_code == 201
    match_id = m.json()["id"]

    body = {"score": 10, "duration_ms": 1000, "completed": True}
    first = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=player_headers,
        json=body,
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=player_headers,
        json=body,
    )
    assert second.status_code == 409
    assert second.json()["code"] == "MATCH_ALREADY_FINISHED"


async def test_finish_replay_same_idempotency_key_returns_200(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, _level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level1_id},
    )
    assert m.status_code == 201
    match_id = m.json()["id"]

    body = {"score": 5, "duration_ms": 2000, "completed": False}
    key = str(uuid.uuid4())
    headers = {**player_headers, "Idempotency-Key": key}

    first = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=headers,
        json=body,
    )
    assert first.status_code == 201

    replay = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=headers,
        json=body,
    )
    assert replay.status_code == 200
    assert replay.json()["score"] == body["score"]
    assert replay.json()["match_id"] == match_id


async def test_finish_with_enrollment_creates_game_session_timeline(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    player_uid = (await client.get("/api/v1/auth/me", headers=player_headers)).json()[
        "id"
    ]
    pid, _pi = await _active_project_with_pi(client, admin_headers)
    enroll_id, profile_id = await _enroll_user_in_project(
        client, admin_headers, pid, player_uid
    )
    game_id, _preset_id, level1_id, _l2 = await _seed_game_two_levels(
        client, admin_headers
    )
    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={
            "game_id": game_id,
            "level_id": level1_id,
            "enrollment_id": enroll_id,
        },
    )
    assert m.status_code == 201
    match_id = m.json()["id"]

    fin = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=player_headers,
        json={"score": 7, "duration_ms": 500, "completed": True},
    )
    assert fin.status_code == 201

    async with AsyncSessionLocal() as session:
        cnt = await session.scalar(
            select(func.count())
            .select_from(TimelineEvent)
            .where(
                TimelineEvent.source_id == str(match_id),
                TimelineEvent.event_type == "GAME_SESSION",
                TimelineEvent.source_type == "Match",
            ),
        )
        assert int(cnt or 0) == 1
        row = (
            await session.execute(
                select(TimelineEvent).where(TimelineEvent.source_id == str(match_id)),
            )
        ).scalar_one()
    assert str(row.project_id) == pid
    assert str(row.participant_profile_id) == profile_id
    assert str(row.enrollment_id) == enroll_id
    assert row.executor_id is None


async def test_finish_without_enrollment_no_timeline_event(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, _l2 = await _seed_game_two_levels(
        client, admin_headers
    )
    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level1_id},
    )
    assert m.status_code == 201
    match_id = m.json()["id"]
    fin = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=player_headers,
        json={"score": 1, "duration_ms": 100, "completed": True},
    )
    assert fin.status_code == 201
    async with AsyncSessionLocal() as session:
        cnt = await session.scalar(
            select(func.count())
            .select_from(TimelineEvent)
            .where(TimelineEvent.source_id == str(match_id)),
        )
    assert int(cnt or 0) == 0


async def test_finish_idempotent_replay_creates_single_timeline_event(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    player_uid = (await client.get("/api/v1/auth/me", headers=player_headers)).json()[
        "id"
    ]
    pid, _pi = await _active_project_with_pi(client, admin_headers)
    enroll_id, _prof = await _enroll_user_in_project(
        client, admin_headers, pid, player_uid
    )
    game_id, _preset_id, level1_id, _l2 = await _seed_game_two_levels(
        client, admin_headers
    )
    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={
            "game_id": game_id,
            "level_id": level1_id,
            "enrollment_id": enroll_id,
        },
    )
    assert m.status_code == 201
    match_id = m.json()["id"]
    body = {"score": 3, "duration_ms": 400, "completed": False}
    key = str(uuid.uuid4())
    h = {**player_headers, "Idempotency-Key": key}
    r1 = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=h,
        json=body,
    )
    assert r1.status_code == 201
    r2 = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=h,
        json=body,
    )
    assert r2.status_code == 200
    async with AsyncSessionLocal() as session:
        cnt = await session.scalar(
            select(func.count())
            .select_from(TimelineEvent)
            .where(TimelineEvent.source_id == str(match_id)),
        )
    assert int(cnt or 0) == 1


async def test_session_enrollment_mismatch_returns_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    player_uid = (await client.get("/api/v1/auth/me", headers=player_headers)).json()[
        "id"
    ]
    pid1, _ = await _active_project_with_pi(client, admin_headers)
    e1, _ = await _enroll_user_in_project(client, admin_headers, pid1, player_uid)
    pid2, _ = await _active_project_with_pi(client, admin_headers)
    e2, _ = await _enroll_user_in_project(client, admin_headers, pid2, player_uid)
    game_id, _preset_id, level1_id, _l2 = await _seed_game_two_levels(
        client, admin_headers
    )
    first = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={
            "game_id": game_id,
            "level_id": level1_id,
            "enrollment_id": e1,
        },
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={
            "game_id": game_id,
            "level_id": level1_id,
            "enrollment_id": e2,
        },
    )
    assert second.status_code == 409
    assert second.json()["code"] == "SESSION_ENROLLMENT_MISMATCH"
