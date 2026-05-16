"""Intervention templates API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-it-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin IT",
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


async def test_create_duplicate_code_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"INT-{uuid.uuid4().hex[:8].upper()}"
    a = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": code,
            "name": "Intervention A",
            "type": "EXERCISE",
        },
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": code.lower(),
            "name": "Duplicate",
            "type": "GAME",
        },
    )
    assert b.status_code == 409
    assert b.json()["code"] == "CODE_IN_USE"


async def test_invalid_game_id_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    fake_game = str(uuid.uuid4())
    r = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"G-{uuid.uuid4().hex[:8]}",
            "name": "Bad game ref",
            "type": "GAME",
            "gameId": fake_game,
        },
    )
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


async def test_patch_invalid_game_id_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"P-{uuid.uuid4().hex[:8]}",
            "name": "No game",
            "type": "INTERVIEW",
        },
    )
    assert created.status_code == 201
    tid = created.json()["id"]
    r = await client.patch(
        f"/api/v1/instruments/interventions/{tid}",
        headers=admin_headers,
        json={"gameId": str(uuid.uuid4())},
    )
    assert r.status_code == 404


async def test_invalid_intervention_type_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    r = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"X-{uuid.uuid4().hex[:8]}",
            "name": "Bad type",
            "type": "NOT_A_REAL_TYPE",
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == "INTERVENTION_TYPE_INVALID"


async def test_non_admin_cannot_create_or_patch_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-it-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    player_headers = {"Authorization": f"Bearer {token}"}

    c = await client.post(
        "/api/v1/instruments/interventions",
        headers=player_headers,
        json={"code": "NOPE99", "name": "Nope", "type": "EXERCISE"},
    )
    assert c.status_code == 403

    created = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"OK-{uuid.uuid4().hex[:6]}",
            "name": "Ok",
            "type": "CONSULTATION",
        },
    )
    assert created.status_code == 201
    tid = created.json()["id"]

    p = await client.patch(
        f"/api/v1/instruments/interventions/{tid}",
        headers=player_headers,
        json={"name": "Hacked"},
    )
    assert p.status_code == 403


async def test_public_list_and_get(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = uuid.uuid4().hex[:8]
    c1 = await client.post(
        "/api/v1/instruments/interventions",
        headers=admin_headers,
        json={
            "code": f"L1-{suffix}",
            "name": "Listed one",
            "type": "CLINICAL_EXAM",
        },
    )
    assert c1.status_code == 201
    tid = c1.json()["id"]

    listed = await client.get(
        "/api/v1/instruments/interventions",
        params={"pageSize": 50},
    )
    assert listed.status_code == 200
    data = listed.json()
    assert "interventions" in data
    ids = {x["id"] for x in data["interventions"]}
    assert tid in ids

    got = await client.get(f"/api/v1/instruments/interventions/{tid}")
    assert got.status_code == 200
    assert got.json()["code"] == f"L1-{suffix}".upper()

    missing = await client.get(
        f"/api/v1/instruments/interventions/{uuid.uuid4()}",
    )
    assert missing.status_code == 404
