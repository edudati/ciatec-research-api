"""Project members API integration tests."""

import uuid
from datetime import date

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-mem-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin Mem",
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


async def test_invalid_member_role_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"M1-{uuid.uuid4().hex[:8].upper()}"
    p = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "M1"},
    )
    assert p.status_code == 201
    pid = p.json()["id"]

    rs = await _user_headers(
        client,
        email=f"rs-{uuid.uuid4()}@example.com",
        name="R",
        role="RESEARCHER",
    )
    me = await client.get("/api/v1/auth/me", headers=rs)
    assert me.status_code == 200
    uid = me.json()["id"]

    r = await client.post(
        f"/api/v1/projects/{pid}/members",
        headers=admin_headers,
        json={
            "userId": uid,
            "role": "NOT_A_PROJECT_MEMBER_ROLE",
            "startDate": str(date.today()),
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == "INVALID_PROJECT_MEMBER_ROLE"


async def test_duplicate_member_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"M2-{uuid.uuid4().hex[:8].upper()}"
    p = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "M2"},
    )
    assert p.status_code == 201
    pid = p.json()["id"]

    rs = await _user_headers(
        client,
        email=f"rs2-{uuid.uuid4()}@example.com",
        name="R2",
        role="RESEARCHER",
    )
    me = await client.get("/api/v1/auth/me", headers=rs)
    uid = me.json()["id"]
    body = {
        "userId": uid,
        "role": "RESEARCHER",
        "startDate": str(date.today()),
    }
    a = await client.post(
        f"/api/v1/projects/{pid}/members",
        headers=admin_headers,
        json=body,
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/projects/{pid}/members",
        headers=admin_headers,
        json=body,
    )
    assert b.status_code == 409
    assert b.json()["code"] == "PROJECT_MEMBER_DUPLICATE"


async def test_delete_last_pi_on_active_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pi_headers = await _user_headers(
        client,
        email=f"pi-m-{uuid.uuid4()}@example.com",
        name="PI M",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    assert me.status_code == 200
    pi_id = me.json()["id"]

    code = f"M3-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={
            "code": code,
            "name": "With PI only",
            "piUserId": pi_id,
        },
    )
    assert c.status_code == 201
    pid = c.json()["id"]

    act = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert act.status_code == 200

    lst = await client.get(
        f"/api/v1/projects/{pid}/members",
        headers=admin_headers,
    )
    assert lst.status_code == 200
    members = lst.json()["members"]
    pi_row = next(m for m in members if m["role"] == "PI")
    mid = pi_row["id"]

    d = await client.delete(
        f"/api/v1/projects/{pid}/members/{mid}",
        headers=admin_headers,
    )
    assert d.status_code == 422
    assert d.json()["code"] == "LAST_PI_REMOVAL"
