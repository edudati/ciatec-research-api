"""Instrument indications API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-ii-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin II",
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


async def _create_health_condition(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={
            "code": f"HC-{suf}",
            "name": "Test condition",
            "category": "neuro",
        },
    )
    assert r.status_code == 201
    return str(r.json()["id"])


async def _create_assessment(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/assessments",
        headers=admin_headers,
        json={
            "code": f"AST-{suf}",
            "name": "Motor screen",
            "type": "MOTOR",
        },
    )
    assert r.status_code == 201
    return str(r.json()["id"])


async def _create_questionnaire(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={
            "code": f"QST-{suf}",
            "name": "Screening form",
            "type": "PSYCHOLOGICAL",
        },
    )
    assert r.status_code == 201
    return str(r.json()["id"])


async def test_duplicate_indication_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    ast_id = await _create_assessment(client, admin_headers)
    body = {
        "instrumentType": "ASSESSMENT",
        "instrumentId": ast_id,
        "healthConditionId": hc_id,
        "indicationType": "INDICATED",
    }
    a = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json=body,
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json=body,
    )
    assert b.status_code == 409
    assert b.json()["code"] == "INDICATION_DUPLICATE"


async def test_instrument_not_found_404_wrong_kind(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    ast_id = await _create_assessment(client, admin_headers)
    r = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json={
            "instrumentType": "QUESTIONNAIRE",
            "instrumentId": ast_id,
            "healthConditionId": hc_id,
            "indicationType": "GOLD_STANDARD",
        },
    )
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


async def test_instrument_not_found_404_random_uuid(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    r = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json={
            "instrumentType": "ASSESSMENT",
            "instrumentId": str(uuid.uuid4()),
            "healthConditionId": hc_id,
            "indicationType": "COMMONLY_USED",
        },
    )
    assert r.status_code == 404


async def test_list_by_instrument_and_by_health_condition(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    ast_id = await _create_assessment(client, admin_headers)
    await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json={
            "instrumentType": "ASSESSMENT",
            "instrumentId": ast_id,
            "healthConditionId": hc_id,
            "indicationType": "INDICATED",
        },
    )
    by_inst = await client.get(
        "/api/v1/instruments/indications",
        params={"instrumentType": "ASSESSMENT", "instrumentId": ast_id},
    )
    assert by_inst.status_code == 200
    assert len(by_inst.json()["indications"]) == 1

    by_hc = await client.get(
        "/api/v1/instruments/indications",
        params={"healthConditionId": hc_id},
    )
    assert by_hc.status_code == 200
    assert len(by_hc.json()["indications"]) == 1


async def test_ambiguous_query_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    ast_id = await _create_assessment(client, admin_headers)
    r = await client.get(
        "/api/v1/instruments/indications",
        params={
            "healthConditionId": hc_id,
            "instrumentType": "ASSESSMENT",
            "instrumentId": ast_id,
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "INDICATIONS_QUERY_AMBIGUOUS"


async def test_delete_204(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    qid = await _create_questionnaire(client, admin_headers)
    created = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json={
            "instrumentType": "QUESTIONNAIRE",
            "instrumentId": qid,
            "healthConditionId": hc_id,
            "indicationType": "INDICATED",
        },
    )
    assert created.status_code == 201
    iid = created.json()["id"]
    d = await client.delete(
        f"/api/v1/instruments/indications/{iid}",
        headers=admin_headers,
    )
    assert d.status_code == 204
    listed = await client.get(
        "/api/v1/instruments/indications",
        params={"instrumentType": "QUESTIONNAIRE", "instrumentId": qid},
    )
    assert listed.status_code == 200
    assert listed.json()["indications"] == []


async def test_non_admin_cannot_post_or_delete_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    hc_id = await _create_health_condition(client, admin_headers)
    ast_id = await _create_assessment(client, admin_headers)
    created = await client.post(
        "/api/v1/instruments/indications",
        headers=admin_headers,
        json={
            "instrumentType": "ASSESSMENT",
            "instrumentId": ast_id,
            "healthConditionId": hc_id,
            "indicationType": "INDICATED",
        },
    )
    assert created.status_code == 201
    iid = created.json()["id"]

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pl-ii-{uuid.uuid4()}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Player",
        },
    )
    assert reg.status_code == 201
    player_headers = {"Authorization": f"Bearer {reg.json()['accessToken']}"}

    p = await client.post(
        "/api/v1/instruments/indications",
        headers=player_headers,
        json={
            "instrumentType": "ASSESSMENT",
            "instrumentId": ast_id,
            "healthConditionId": hc_id,
            "indicationType": "GOLD_STANDARD",
        },
    )
    assert p.status_code == 403

    d = await client.delete(
        f"/api/v1/instruments/indications/{iid}",
        headers=player_headers,
    )
    assert d.status_code == 403
