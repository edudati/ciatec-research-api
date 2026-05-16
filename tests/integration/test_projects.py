"""Projects API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-prj-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin Prj",
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


async def test_duplicate_project_code_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"PRJ-{uuid.uuid4().hex[:8].upper()}"
    a = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "A"},
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code.lower(), "name": "B"},
    )
    assert b.status_code == 409
    assert b.json()["code"] == "PROJECT_CODE_IN_USE"


async def test_activate_without_pi_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"NOP-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "No PI"},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    p = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert p.status_code == 422
    assert p.json()["code"] == "ACTIVE_REQUIRES_PI"


async def test_cross_project_get_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    rs = await _user_headers(
        client,
        email=f"rs-{uuid.uuid4()}@example.com",
        name="Researcher",
        role="RESEARCHER",
    )
    code = f"ISO-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Isolated"},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    g = await client.get(f"/api/v1/projects/{pid}", headers=rs)
    assert g.status_code == 403


async def test_create_with_pi_and_activate(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pi_email = f"pi-{uuid.uuid4()}@example.com"
    pi_headers = await _user_headers(
        client,
        email=pi_email,
        name="PI User",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    assert me.status_code == 200
    pi_id = me.json()["id"]

    code = f"OK-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={
            "code": code,
            "name": "With PI",
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
    assert act.json()["status"] == "ACTIVE"

    listed = await client.get("/api/v1/projects", headers=pi_headers)
    assert listed.status_code == 200
    ids = {p["id"] for p in listed.json()["projects"]}
    assert pid in ids
