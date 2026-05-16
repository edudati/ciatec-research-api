"""Participant profile API integration tests."""

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
async def pi_headers(client: AsyncClient) -> dict[str, str]:
    email = f"pi-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="PI User",
                role="PI",
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


async def test_participant_crud_and_list(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = str(uuid.uuid4())[:8]
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"participant-user-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Study Subject",
        },
    )
    assert reg.status_code == 201
    target_user_id = reg.json()["user"]["id"]

    create = await client.post(
        "/api/v1/participants",
        headers=admin_headers,
        json={
            "userId": target_user_id,
            "birthDate": "1990-05-15",
            "biologicalSex": "M",
            "phone": "+5511999990000",
            "notes": "seed notes",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["userId"] == target_user_id
    assert body["birthDate"] == "1990-05-15"
    assert body["biologicalSex"] == "M"
    pid = body["id"]

    dup = await client.post(
        "/api/v1/participants",
        headers=admin_headers,
        json={"userId": target_user_id},
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "PARTICIPANT_PROFILE_EXISTS"

    got = await client.get(
        f"/api/v1/participants/{pid}",
        headers=admin_headers,
    )
    assert got.status_code == 200
    assert got.json()["id"] == pid

    patched = await client.patch(
        f"/api/v1/participants/{pid}",
        headers=admin_headers,
        json={"notes": "updated", "biologicalSex": "OTHER"},
    )
    assert patched.status_code == 200
    assert patched.json()["notes"] == "updated"
    assert patched.json()["biologicalSex"] == "OTHER"

    listed = await client.get(
        "/api/v1/participants",
        headers=admin_headers,
        params={"q": "Study Subject", "page": 1, "pageSize": 20},
    )
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] >= 1
    assert any(p["id"] == pid for p in data["participants"])


async def test_pi_can_list_participants(
    client: AsyncClient,
    pi_headers: dict[str, str],
) -> None:
    r = await client.get(
        "/api/v1/participants",
        headers=pi_headers,
        params={"page": 1, "pageSize": 5},
    )
    assert r.status_code == 200


async def test_player_forbidden_on_participants(
    client: AsyncClient,
) -> None:
    suffix = str(uuid.uuid4())[:8]
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"player-only-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player Only",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get(
        "/api/v1/participants",
        headers=headers,
    )
    assert r.status_code == 403
    assert r.json()["code"] == "FORBIDDEN"


async def test_create_participant_unknown_user_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    bad_id = str(uuid.uuid4())
    r = await client.post(
        "/api/v1/participants",
        headers=admin_headers,
        json={"userId": bad_id},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "USER_NOT_FOUND"
