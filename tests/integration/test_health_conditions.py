"""Health conditions API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.participant_condition import ParticipantCondition
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-hc-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin HC",
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
    code = f"ICD-{uuid.uuid4().hex[:8].upper()}"
    a = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": code,
            "name": "First",
            "category": "neuro",
        },
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": code.lower(),
            "name": "Duplicate",
        },
    )
    assert b.status_code == 409
    assert b.json()["code"] == "CODE_IN_USE"


async def test_inactive_hidden_from_public_list_and_get(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = uuid.uuid4().hex[:8]
    c1 = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": f"X-{suffix}",
            "name": "Hidden soon",
            "category": "cat-a",
        },
    )
    assert c1.status_code == 201
    hid = c1.json()["id"]
    await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": f"Y-{suffix}",
            "name": "Stays visible",
            "category": "cat-b",
        },
    )
    off = await client.patch(
        f"/api/v1/health-conditions/{hid}",
        headers=admin_headers,
        json={"isActive": False},
    )
    assert off.status_code == 200

    listed = await client.get("/api/v1/health-conditions", params={"pageSize": 50})
    assert listed.status_code == 200
    ids = {x["id"] for x in listed.json()["conditions"]}
    assert hid not in ids

    got = await client.get(f"/api/v1/health-conditions/{hid}")
    assert got.status_code == 404


async def test_delete_blocked_when_linked_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suffix = uuid.uuid4().hex[:8]
    hc = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"LINK-{suffix}", "name": "Linked condition"},
    )
    assert hc.status_code == 201
    hc_id = hc.json()["id"]

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"subj-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Subject",
        },
    )
    assert reg.status_code == 201
    uid = reg.json()["user"]["id"]

    prof = await client.post(
        "/api/v1/participants",
        headers=admin_headers,
        json={"userId": uid},
    )
    assert prof.status_code == 201
    profile_id = prof.json()["id"]

    async with AsyncSessionLocal() as session:
        session.add(
            ParticipantCondition(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                health_condition_id=uuid.UUID(hc_id),
            ),
        )
        await session.commit()

    d = await client.delete(
        f"/api/v1/health-conditions/{hc_id}",
        headers=admin_headers,
    )
    assert d.status_code == 409
    assert d.json()["code"] == "HEALTH_CONDITION_IN_USE"


async def test_player_cannot_create_health_condition_403(
    client: AsyncClient,
) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    r = await client.post(
        "/api/v1/health-conditions",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "NOPE99", "name": "Nope"},
    )
    assert r.status_code == 403


async def test_category_filter_and_public_get(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suf = uuid.uuid4().hex[:6]
    await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": f"Z1-{suf}",
            "name": "Zebra one",
            "category": "alpha",
        },
    )
    c2 = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": f"Z2-{suf}",
            "name": "Zebra two",
            "category": "beta",
        },
    )
    assert c2.status_code == 201
    cid = c2.json()["id"]

    filt = await client.get(
        "/api/v1/health-conditions",
        params={"category": "BETA", "pageSize": 50},
    )
    assert filt.status_code == 200
    codes = {x["code"] for x in filt.json()["conditions"]}
    assert f"Z2-{suf}".upper() in codes
    assert f"Z1-{suf}".upper() not in codes

    one = await client.get(f"/api/v1/health-conditions/{cid}")
    assert one.status_code == 200
    assert one.json()["name"] == "Zebra two"
