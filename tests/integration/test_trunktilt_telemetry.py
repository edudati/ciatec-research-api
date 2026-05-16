"""TrunkTilt telemetry API (F0-07)."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
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


async def _seed_trunktilt_catalog(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, str, str]:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={
            "name": "TrunkTilt",
            "slug": "trunktilt",
            "is_active": True,
        },
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
            "config": {},
            "is_active": True,
        },
    )
    assert l1.status_code == 201
    level_id = l1.json()["id"]
    return game_id, preset_id, level_id


async def _create_match(
    client: AsyncClient,
    player_headers: dict[str, str],
    game_id: str,
    level_id: str,
) -> str:
    m = await client.post(
        "/api/v1/sessions/matches",
        headers=player_headers,
        json={"game_id": game_id, "level_id": level_id},
    )
    assert m.status_code == 201
    return str(m.json()["id"])


async def test_world_batch_max_200_frames(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level_id = await _seed_trunktilt_catalog(client, admin_headers)
    match_id = await _create_match(client, player_headers, game_id, level_id)

    frames = [{"frame_id": i, "ball_x": float(i)} for i in range(200)]
    r = await client.post(
        f"/api/v1/trunktilt/matches/{match_id}/telemetry/world",
        headers=player_headers,
        json={"frames": frames},
    )
    assert r.status_code == 202
    data = r.json()
    assert data["match_id"] == match_id
    assert data["frames_received"] == 200
    assert data["rows_inserted"] == 200


async def test_world_duplicate_frame_id_second_request_inserts_zero(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level_id = await _seed_trunktilt_catalog(client, admin_headers)
    match_id = await _create_match(client, player_headers, game_id, level_id)

    body = {"frames": [{"frame_id": 1, "ball_x": 1.0}]}
    first = await client.post(
        f"/api/v1/trunktilt/matches/{match_id}/telemetry/world",
        headers=player_headers,
        json=body,
    )
    assert first.status_code == 202
    assert first.json()["rows_inserted"] == 1

    second = await client.post(
        f"/api/v1/trunktilt/matches/{match_id}/telemetry/world",
        headers=player_headers,
        json=body,
    )
    assert second.status_code == 202
    assert second.json()["frames_received"] == 1
    assert second.json()["rows_inserted"] == 0


async def test_world_wrong_game_match_returns_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    tt_game_id, _tt_preset_id, tt_level_id = await _seed_trunktilt_catalog(
        client, admin_headers
    )

    other = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Other Game", "is_active": True},
    )
    assert other.status_code == 201
    other_game_id = other.json()["id"]

    op = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={
            "game_id": other_game_id,
            "name": "Default",
            "is_default": True,
            "is_active": True,
        },
    )
    assert op.status_code == 201
    other_preset_id = op.json()["id"]

    ol = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": other_preset_id,
            "name": "L1",
            "order": 0,
            "config": {},
            "is_active": True,
        },
    )
    assert ol.status_code == 201
    other_level_id = ol.json()["id"]

    await _create_match(client, player_headers, tt_game_id, tt_level_id)

    wrong_match = await _create_match(
        client, player_headers, other_game_id, other_level_id
    )

    r = await client.post(
        f"/api/v1/trunktilt/matches/{wrong_match}/telemetry/world",
        headers=player_headers,
        json={"frames": [{"frame_id": 0}]},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "NOT_TRUNKTILT_MATCH"


async def test_telemetry_finished_match_returns_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level_id = await _seed_trunktilt_catalog(client, admin_headers)
    match_id = await _create_match(client, player_headers, game_id, level_id)

    fin = await client.post(
        f"/api/v1/matches/{match_id}/finish",
        headers=player_headers,
        json={"score": 1, "duration_ms": 100, "completed": True},
    )
    assert fin.status_code == 201

    r = await client.post(
        f"/api/v1/trunktilt/matches/{match_id}/telemetry/world",
        headers=player_headers,
        json={"frames": [{"frame_id": 0}]},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "MATCH_ALREADY_FINISHED"
