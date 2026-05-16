"""Assessment templates API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-at-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin AT",
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
    code = f"BERG-{uuid.uuid4().hex[:8].upper()}"
    a = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": code,
            "name": "Berg Balance",
            "type": "MOTOR",
        },
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": code.lower(),
            "name": "Duplicate",
            "type": "MOTOR",
        },
    )
    assert b.status_code == 409
    assert b.json()["code"] == "CODE_IN_USE"


async def test_invalid_assessment_type_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    r = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": f"X-{uuid.uuid4().hex[:8]}",
            "name": "Bad type",
            "type": "NOT_A_REAL_TYPE",
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == "ASSESSMENT_TYPE_INVALID"


async def test_non_admin_cannot_create_or_patch_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-at-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    player_headers = {"Authorization": f"Bearer {token}"}

    c = await client.post(
        "/api/v1/instruments/assessments",
        headers=player_headers,
        json={"code": "NOPE99", "name": "Nope", "type": "MOTOR"},
    )
    assert c.status_code == 403

    created = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={"code": f"OK-{uuid.uuid4().hex[:6]}", "name": "Ok", "type": "COGNITIVE"},
    )
    assert created.status_code == 201
    tid = created.json()["id"]

    p = await client.patch(
        f"/api/v1/instruments/assessments/{tid}",
        headers=player_headers,
        json={"name": "Hacked"},
    )
    assert p.status_code == 403


async def test_public_list_and_get_active_only(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = uuid.uuid4().hex[:8]
    c1 = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": f"T1-{suffix}",
            "name": "One",
            "type": "FUNCTIONAL",
        },
    )
    assert c1.status_code == 201
    tid = c1.json()["id"]

    await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": f"T2-{suffix}",
            "name": "Two",
            "type": "PSYCHOLOGICAL",
        },
    )

    off = await client.patch(
        f"/api/v1/instruments/assessments/{tid}",
        headers=admin_headers,
        json={"isActive": False},
    )
    assert off.status_code == 200

    listed = await client.get(
        "/api/v1/instruments/assessments",
        params={"pageSize": 50},
    )
    assert listed.status_code == 200
    ids = {x["id"] for x in listed.json()["assessments"]}
    assert tid not in ids

    got = await client.get(f"/api/v1/instruments/assessments/{tid}")
    assert got.status_code == 404
