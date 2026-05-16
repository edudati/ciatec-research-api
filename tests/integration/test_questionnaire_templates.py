"""Questionnaire templates API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-qt-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin QT",
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


async def _create_active_template(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={
            "code": f"PHQ-{suf}",
            "name": "PHQ-9",
            "type": "PSYCHOLOGICAL",
        },
    )
    assert r.status_code == 201
    return str(r.json()["id"])


async def test_item_invalid_type_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    r = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "Q1",
            "label": "First",
            "type": "FREE_TEXT",
            "order": 0,
        },
    )
    assert r.status_code == 400
    assert r.json()["code"] == "QUESTION_ITEM_TYPE_INVALID"


async def test_duplicate_item_order_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    a = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "A",
            "label": "A",
            "type": "TEXT",
            "order": 1,
        },
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "B",
            "label": "B",
            "type": "TEXT",
            "order": 1,
        },
    )
    assert b.status_code == 409
    assert b.json()["code"] == "QUESTION_ITEM_ORDER_IN_USE"


async def test_non_admin_item_mutations_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    it = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "X1",
            "label": "X",
            "type": "BOOLEAN",
            "order": 0,
        },
    )
    assert it.status_code == 201
    iid = it.json()["id"]

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-qt-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["accessToken"]
    h = {"Authorization": f"Bearer {token}"}

    c = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=h,
        json={
            "code": "Y1",
            "label": "Y",
            "type": "NUMBER",
            "order": 2,
        },
    )
    assert c.status_code == 403

    p = await client.patch(
        f"/api/v1/instruments/questionnaires/{tid}/items/{iid}",
        headers=h,
        json={"label": "Hacked"},
    )
    assert p.status_code == 403

    d = await client.delete(
        f"/api/v1/instruments/questionnaires/{tid}/items/{iid}",
        headers=h,
    )
    assert d.status_code == 403


async def test_list_get_patch_template_and_delete_item(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    lst = await client.get(
        "/api/v1/instruments/questionnaires",
        params={"pageSize": 20},
    )
    assert lst.status_code == 200
    assert any(x["id"] == tid for x in lst.json()["questionnaires"])

    one = await client.get(f"/api/v1/instruments/questionnaires/{tid}")
    assert one.status_code == 200
    assert one.json()["code"].startswith("PHQ-")

    patch_t = await client.patch(
        f"/api/v1/instruments/questionnaires/{tid}",
        headers=admin_headers,
        json={"name": "Renamed", "selfReport": True},
    )
    assert patch_t.status_code == 200
    assert patch_t.json()["name"] == "Renamed"
    assert patch_t.json()["selfReport"] is True

    it = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "DEL1",
            "label": "To delete",
            "type": "TEXT",
            "order": 5,
        },
    )
    assert it.status_code == 201
    iid = it.json()["id"]

    patch_i = await client.patch(
        f"/api/v1/instruments/questionnaires/{tid}/items/{iid}",
        headers=admin_headers,
        json={"label": "Updated label"},
    )
    assert patch_i.status_code == 200
    assert patch_i.json()["label"] == "Updated label"

    d = await client.delete(
        f"/api/v1/instruments/questionnaires/{tid}/items/{iid}",
        headers=admin_headers,
    )
    assert d.status_code == 204


async def test_duplicate_template_code_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"DUP-{uuid.uuid4().hex[:6]}"
    a = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={"code": code, "name": "A", "type": "COGNITIVE"},
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={"code": code.lower(), "name": "B", "type": "MOTOR"},
    )
    assert b.status_code == 409


async def test_items_not_visible_when_template_inactive(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "Z1",
            "label": "Z",
            "type": "NUMBER",
            "order": 0,
        },
    )
    off = await client.patch(
        f"/api/v1/instruments/questionnaires/{tid}",
        headers=admin_headers,
        json={"isActive": False},
    )
    assert off.status_code == 200

    items = await client.get(f"/api/v1/instruments/questionnaires/{tid}/items")
    assert items.status_code == 404


async def test_duplicate_item_code_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    a = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "SAME",
            "label": "A",
            "type": "BOOLEAN",
            "order": 0,
        },
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "same",
            "label": "B",
            "type": "TEXT",
            "order": 1,
        },
    )
    assert b.status_code == 409
    assert b.json()["code"] == "QUESTION_ITEM_CODE_IN_USE"


async def test_invalid_template_type_on_create_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    r = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={
            "code": f"BAD-{uuid.uuid4().hex[:6]}",
            "name": "Bad",
            "type": "NOT_A_TYPE",
        },
    )
    assert r.status_code == 400


async def test_public_list_items_active_template(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    tid = await _create_active_template(client, admin_headers)
    await client.post(
        f"/api/v1/instruments/questionnaires/{tid}/items",
        headers=admin_headers,
        json={
            "code": "P1",
            "label": "One",
            "type": "SCALE",
            "order": 0,
        },
    )
    listed = await client.get(
        f"/api/v1/instruments/questionnaires/{tid}/items",
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1
    assert listed.json()["items"][0]["code"] == "P1"
