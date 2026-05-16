"""Vocabulary API integration tests."""

import uuid

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


def _scheme_id(code: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"ciatec-research-api.vocab:scheme:{code}",
        ),
    )


def _term_id(scheme_code: str, term_code: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"ciatec-research-api.vocab:term:{scheme_code}:{term_code}",
        ),
    )


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-vocab-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin Vocab",
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


async def test_list_schemes_contains_seeded_condition_severity(
    client: AsyncClient,
) -> None:
    r = await client.get("/api/v1/vocabulary/schemes")
    assert r.status_code == 200
    codes = {s["code"] for s in r.json()["schemes"]}
    assert "CONDITION_SEVERITY" in codes


async def test_duplicate_scheme_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    code = f"TMP_SCHEME_{uuid.uuid4().hex[:8].upper()}"
    a = await client.post(
        "/api/v1/vocabulary/schemes",
        headers=admin_headers,
        json={"code": code, "name": "One"},
    )
    assert a.status_code == 201
    b = await client.post(
        "/api/v1/vocabulary/schemes",
        headers=admin_headers,
        json={"code": code.lower(), "name": "Two"},
    )
    assert b.status_code == 409
    assert b.json()["code"] == "SCHEME_CODE_IN_USE"


async def test_duplicate_term_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    sid = _scheme_id("CONDITION_SEVERITY")
    r = await client.post(
        f"/api/v1/vocabulary/schemes/{sid}/terms",
        headers=admin_headers,
        json={"code": "MILD", "label": "Duplicate mild"},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "TERM_CODE_IN_USE"


async def test_inactive_term_hidden_from_public_list(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    suf = uuid.uuid4().hex[:8].upper()
    scheme_code = f"ZZ_SCHEME_{suf}"
    create_s = await client.post(
        "/api/v1/vocabulary/schemes",
        headers=admin_headers,
        json={"code": scheme_code, "name": "ZZ"},
    )
    assert create_s.status_code == 201
    scheme_uuid = create_s.json()["id"]

    create_t = await client.post(
        f"/api/v1/vocabulary/schemes/{scheme_uuid}/terms",
        headers=admin_headers,
        json={"code": f"T_{suf}", "label": "T"},
    )
    assert create_t.status_code == 201
    tid = create_t.json()["id"]

    off = await client.patch(
        f"/api/v1/vocabulary/terms/{tid}",
        headers=admin_headers,
        json={"isActive": False},
    )
    assert off.status_code == 200

    listed = await client.get(f"/api/v1/vocabulary/schemes/{scheme_uuid}/terms")
    assert listed.status_code == 200
    assert listed.json()["terms"] == []

    admin_list = await client.get(
        f"/api/v1/vocabulary/schemes/{scheme_uuid}/terms",
        headers=admin_headers,
        params={"includeInactive": "true"},
    )
    assert admin_list.status_code == 200
    assert len(admin_list.json()["terms"]) == 1


async def test_include_inactive_forbidden_without_admin(
    client: AsyncClient,
) -> None:
    sid = _scheme_id("CONDITION_SEVERITY")
    r = await client.get(
        f"/api/v1/vocabulary/schemes/{sid}/terms",
        params={"includeInactive": "true"},
    )
    assert r.status_code == 403


async def test_delete_term_in_use_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    """Participant condition severity references CONDITION_SEVERITY term code."""
    suffix = uuid.uuid4().hex[:8]
    hc = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"VUSE-{suffix}", "name": "HC"},
    )
    assert hc.status_code == 201
    hc_id = hc.json()["id"]

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"vuse-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "Subj",
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
    pid = prof.json()["id"]

    link = await client.post(
        f"/api/v1/participants/{pid}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc_id, "severity": "MILD"},
    )
    assert link.status_code == 201

    mild_id = _term_id("CONDITION_SEVERITY", "MILD")
    d = await client.delete(
        f"/api/v1/vocabulary/terms/{mild_id}",
        headers=admin_headers,
    )
    assert d.status_code == 409
    assert d.json()["code"] == "VOCABULARY_TERM_IN_USE"


async def test_player_cannot_create_scheme_403(
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
        "/api/v1/vocabulary/schemes",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "NOPE99", "name": "Nope"},
    )
    assert r.status_code == 403
