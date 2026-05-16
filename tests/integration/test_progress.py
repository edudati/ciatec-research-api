"""Progress API (F0-06)."""

import uuid
from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import update

from src.core.database import AsyncSessionLocal
from src.models.progress import UserGame

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
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


async def _seed_game_two_levels(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, str, str, str]:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Progress Test Game", "is_active": True},
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


async def test_progress_start_creates_user_game_with_default_preset(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    game_id, preset_id, level1_id, level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pg-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Progress Player",
        },
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['accessToken']}"}

    r = await client.get(
        f"/api/v1/progress/start?game_id={game_id}",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["game"]["id"] == game_id
    assert data["preset"]["id"] == preset_id
    assert data["preset"]["name"] == "Default"
    assert data["current_level"]["id"] == level1_id
    by_id: dict[str, dict[str, Any]] = {lv["id"]: lv for lv in data["levels"]}
    assert by_id[level1_id]["unlocked"] is True
    assert by_id[level2_id]["unlocked"] is False


async def test_progress_start_levels_detail_summary_omits_config(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, _level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pg-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Progress Player",
        },
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['accessToken']}"}

    r = await client.get(
        f"/api/v1/progress/start?game_id={game_id}&levels_detail=summary",
        headers=headers,
    )
    assert r.status_code == 200
    lv = next(row for row in r.json()["levels"] if row["id"] == level1_id)
    assert "config" not in lv

    rf = await client.get(
        f"/api/v1/progress/start?game_id={game_id}&levels_detail=full",
        headers=headers,
    )
    assert rf.status_code == 200
    lvf = next(row for row in rf.json()["levels"] if row["id"] == level1_id)
    assert lvf.get("config") == {"difficulty": 1}


async def test_progress_start_normalizes_current_when_locked(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    game_id, _preset_id, level1_id, level2_id = await _seed_game_two_levels(
        client, admin_headers
    )

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pg-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Progress Player",
        },
    )
    assert reg.status_code == 201
    user_id = uuid.UUID(reg.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {reg.json()['accessToken']}"}

    first = await client.get(
        f"/api/v1/progress/start?game_id={game_id}",
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["current_level"]["id"] == level1_id

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserGame)
            .where(
                UserGame.user_id == user_id,
                UserGame.game_id == uuid.UUID(game_id),
            )
            .values(current_level_id=uuid.UUID(level2_id)),
        )
        await session.commit()

    second = await client.get(
        f"/api/v1/progress/start?game_id={game_id}",
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["current_level"]["id"] == level1_id

    third = await client.get(
        f"/api/v1/progress/start?game_id={game_id}",
        headers=headers,
    )
    assert third.status_code == 200
    assert third.json()["current_level"]["id"] == level1_id
