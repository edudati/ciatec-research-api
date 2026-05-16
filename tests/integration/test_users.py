"""Users admin API integration tests."""

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


async def test_list_users_with_filters(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = str(uuid.uuid4())[:8]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"list-alpha-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Alpha Player",
        },
    )
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"list-beta-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Beta Tester",
        },
    )

    r = await client.get(
        "/api/v1/users",
        headers=admin_headers,
        params={"role": "PLAYER", "q": "alpha", "page": 1, "pageSize": 10},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any("alpha" in u["email"].lower() for u in data["users"])


async def test_create_user_invalid_role_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    bad = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "bad-role@example.com",
            "password": _VALID_PASSWORD,
            "name": "X",
            "role": "INVALID_ROLE",
        },
    )
    assert bad.status_code == 400
    err = bad.json()
    assert err["success"] is False
    assert err["code"] == "VALIDATION_ERROR"


async def test_patch_deleted_user_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": f"delpatch-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "To Delete",
            "role": "PLAYER",
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    del_r = await client.delete(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
    )
    assert del_r.status_code == 204

    patch_r = await client.patch(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"name": "Nope"},
    )
    assert patch_r.status_code == 404


async def test_delete_idempotent(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": f"idem-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Idem",
            "role": "PLAYER",
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    assert (
        await client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    ).status_code == 204


async def test_player_cannot_list_users_403(client: AsyncClient) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"player-only-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    r = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "FORBIDDEN"


async def test_create_duplicate_email_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    email = f"dup-admin-{uuid.uuid4()}@example.com"
    body = {
        "email": email,
        "password": _VALID_PASSWORD,
        "name": "First",
        "role": "RESEARCHER",
    }
    first = await client.post("/api/v1/users", headers=admin_headers, json=body)
    assert first.status_code == 201
    dup = await client.post("/api/v1/users", headers=admin_headers, json=body)
    assert dup.status_code == 409
    assert dup.json()["code"] == "EMAIL_IN_USE"
