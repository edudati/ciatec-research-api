"""Participant enrollment API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-enr-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin Enr",
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


async def _active_project_with_pi(
    client: AsyncClient, admin_headers: dict[str, str]
) -> str:
    pi_headers = await _user_headers(
        client,
        email=f"pi-e-{uuid.uuid4()}@example.com",
        name="PI Enr",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"E-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Enroll proj", "piUserId": pi_id},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    act = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert act.status_code == 200
    return str(pid)


async def test_enrollment_duplicate_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    part_headers = await _user_headers(
        client,
        email=f"pt-{uuid.uuid4()}@example.com",
        name="Participant",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    body = {"userId": uid, "role": "PARTICIPANT"}
    a = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json=body,
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json=body,
    )
    assert b.status_code == 409
    assert b.json()["code"] == "ENROLLMENT_DUPLICATE"


async def test_enrollment_draft_project_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"DR-{uuid.uuid4().hex[:8].upper()}"
    p = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Draft only"},
    )
    assert p.status_code == 201
    pid = p.json()["id"]

    part_headers = await _user_headers(
        client,
        email=f"pt2-{uuid.uuid4()}@example.com",
        name="P2",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    r = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "ENROLLMENT_PROJECT_DRAFT"


async def test_enrollment_exit_records_exited_at(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    part_headers = await _user_headers(
        client,
        email=f"pt3-{uuid.uuid4()}@example.com",
        name="P3",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    cr = await client.post(
        f"/api/v1/projects/{pid}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "CONTROL"},
    )
    assert cr.status_code == 201
    eid = cr.json()["id"]

    d = await client.request(
        "DELETE",
        f"/api/v1/projects/{pid}/enrollments/{eid}",
        headers=admin_headers,
        json={"exitReason": "withdrawn for test"},
    )
    assert d.status_code == 204

    g = await client.get(
        f"/api/v1/projects/{pid}/enrollments/{eid}",
        headers=admin_headers,
    )
    assert g.status_code == 200
    data = g.json()
    assert data["exitReason"] == "withdrawn for test"
    assert data["exitedAt"] is not None
    assert data["status"] == "WITHDRAWN"
