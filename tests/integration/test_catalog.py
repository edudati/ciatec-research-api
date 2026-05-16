"""Catalog API integration tests."""

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


async def test_inactive_game_hidden_from_public_catalog(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    create = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Hidden Game", "description": None, "is_active": True},
    )
    assert create.status_code == 201
    game_id = create.json()["id"]

    patch = await client.patch(
        f"/api/v1/admin/catalog/games/{game_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert patch.status_code == 200

    pub_list = await client.get(
        "/api/v1/catalog/games",
        headers=player_headers,
    )
    assert pub_list.status_code == 200
    ids = {g["id"] for g in pub_list.json()["games"]}
    assert game_id not in ids

    pub_one = await client.get(
        f"/api/v1/catalog/games/{game_id}",
        headers=player_headers,
    )
    assert pub_one.status_code == 404

    adm_list = await client.get(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
    )
    assert adm_list.status_code == 200
    adm_ids = {g["id"] for g in adm_list.json()["games"]}
    assert game_id in adm_ids


async def test_single_default_preset_per_game(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Default Test Game", "is_active": True},
    )
    assert g.status_code == 201
    game_id = g.json()["id"]

    p1 = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={
            "game_id": game_id,
            "name": "A",
            "is_default": True,
            "is_active": True,
        },
    )
    assert p1.status_code == 201
    assert p1.json()["is_default"] is True

    p2 = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={
            "game_id": game_id,
            "name": "B",
            "is_default": True,
            "is_active": True,
        },
    )
    assert p2.status_code == 201
    assert p2.json()["is_default"] is True

    lst = await client.get(
        f"/api/v1/admin/catalog/games/{game_id}/presets",
        headers=admin_headers,
    )
    assert lst.status_code == 200
    presets = lst.json()["presets"]
    defaults = [p for p in presets if p["is_default"]]
    assert len(defaults) == 1


async def test_duplicate_level_order_conflict(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Order Test Game", "is_active": True},
    )
    game_id = g.json()["id"]
    p = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={"game_id": game_id, "name": "P", "is_default": False},
    )
    preset_id = p.json()["id"]

    l1 = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": preset_id,
            "name": "L1",
            "order": 0,
            "config": {},
        },
    )
    assert l1.status_code == 201

    l2 = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": preset_id,
            "name": "L2",
            "order": 0,
            "config": {},
        },
    )
    assert l2.status_code == 409
    assert l2.json()["code"] == "LEVEL_ORDER_CONFLICT"


async def test_delete_game_soft_deletes_cascade_presets_and_levels(
    client: AsyncClient,
    admin_headers: dict[str, str],
    player_headers: dict[str, str],
) -> None:
    g = await client.post(
        "/api/v1/admin/catalog/games",
        headers=admin_headers,
        json={"name": "Cascade Delete Game", "is_active": True},
    )
    assert g.status_code == 201
    game_id = g.json()["id"]

    p = await client.post(
        "/api/v1/admin/catalog/presets",
        headers=admin_headers,
        json={
            "game_id": game_id,
            "name": "P1",
            "is_default": True,
            "is_active": True,
        },
    )
    assert p.status_code == 201
    preset_id = p.json()["id"]

    lv = await client.post(
        "/api/v1/admin/catalog/levels",
        headers=admin_headers,
        json={
            "preset_id": preset_id,
            "name": "L1",
            "order": 0,
            "config": {"k": 1},
        },
    )
    assert lv.status_code == 201
    level_id = lv.json()["id"]

    d1 = await client.delete(
        f"/api/v1/admin/catalog/games/{game_id}",
        headers=admin_headers,
    )
    assert d1.status_code == 204

    d2 = await client.delete(
        f"/api/v1/admin/catalog/games/{game_id}",
        headers=admin_headers,
    )
    assert d2.status_code == 204

    pub = await client.get(
        f"/api/v1/catalog/games/{game_id}",
        headers=player_headers,
    )
    assert pub.status_code == 404

    ag = await client.get(
        f"/api/v1/admin/catalog/games/{game_id}",
        headers=admin_headers,
    )
    assert ag.status_code == 200
    assert ag.json()["is_deleted"] is True
    assert ag.json()["is_active"] is False

    ap = await client.get(
        f"/api/v1/admin/catalog/presets/{preset_id}",
        headers=admin_headers,
    )
    assert ap.status_code == 200
    assert ap.json()["is_deleted"] is True
    assert ap.json()["is_active"] is False

    al = await client.get(
        f"/api/v1/admin/catalog/levels/{level_id}",
        headers=admin_headers,
    )
    assert al.status_code == 200
    assert al.json()["is_deleted"] is True
    assert al.json()["is_active"] is False
