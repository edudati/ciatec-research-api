"""Participant condition links (F1-03) integration tests."""

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
    email = f"adm-pc-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin PC",
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


async def _create_participant_and_hc(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, str, str]:
    suffix = uuid.uuid4().hex[:8]
    hc = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"PC-{suffix}", "name": "Condition for PC tests"},
    )
    assert hc.status_code == 201
    hc_id = hc.json()["id"]

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"pc-user-{suffix}@example.com",
            "password": _VALID_PASSWORD,
            "name": "PC User",
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
    return profile_id, hc_id, suffix


async def test_crud_happy_path(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)

    post = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={
            "healthConditionId": hc_id,
            "diagnosedAt": "2024-01-15",
            "severity": "mild",
            "notes": "  episódio 1  ",
        },
    )
    assert post.status_code == 201
    body = post.json()
    assert body["healthConditionId"] == hc_id
    assert body["diagnosedAt"] == "2024-01-15"
    assert body["severity"] == "MILD"
    assert body["notes"] == "episódio 1"
    link_id = body["id"]

    listed = await client.get(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
    )
    assert listed.status_code == 200
    items = listed.json()["conditions"]
    assert len(items) == 1
    assert items[0]["id"] == link_id

    patch = await client.patch(
        f"/api/v1/participants/{profile_id}/conditions/{link_id}",
        headers=admin_headers,
        json={"resolvedAt": "2024-06-01"},
    )
    assert patch.status_code == 200
    assert patch.json()["resolvedAt"] == "2024-06-01"

    delete = await client.delete(
        f"/api/v1/participants/{profile_id}/conditions/{link_id}",
        headers=admin_headers,
    )
    assert delete.status_code == 204

    after = await client.get(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
    )
    assert after.status_code == 200
    assert after.json()["conditions"] == []


async def test_post_unknown_health_condition_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, _, _ = await _create_participant_and_hc(client, admin_headers)
    fake_hc = str(uuid.uuid4())
    r = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": fake_hc},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


async def test_post_inactive_health_condition_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, _, suffix = await _create_participant_and_hc(client, admin_headers)
    off = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"OFF-{suffix}", "name": "Inactive"},
    )
    assert off.status_code == 201
    hid = off.json()["id"]
    await client.patch(
        f"/api/v1/health-conditions/{hid}",
        headers=admin_headers,
        json={"isActive": False},
    )

    r = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hid},
    )
    assert r.status_code == 404


async def test_post_deleted_health_condition_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, _, suffix = await _create_participant_and_hc(client, admin_headers)
    gone = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"DEL-{suffix}", "name": "To delete"},
    )
    assert gone.status_code == 201
    hid = gone.json()["id"]
    await client.delete(
        f"/api/v1/health-conditions/{hid}",
        headers=admin_headers,
    )

    r = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hid},
    )
    assert r.status_code == 404


async def test_patch_delete_unknown_link_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, _, _ = await _create_participant_and_hc(client, admin_headers)
    bad = str(uuid.uuid4())
    p = await client.patch(
        f"/api/v1/participants/{profile_id}/conditions/{bad}",
        headers=admin_headers,
        json={"notes": "x"},
    )
    assert p.status_code == 404
    d = await client.delete(
        f"/api/v1/participants/{profile_id}/conditions/{bad}",
        headers=admin_headers,
    )
    assert d.status_code == 404


async def test_invalid_severity_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)
    r = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc_id, "severity": "CRITICAL"},
    )
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


async def test_patch_invalid_severity_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)
    post = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc_id, "severity": "MILD"},
    )
    assert post.status_code == 201
    link_id = post.json()["id"]
    r = await client.patch(
        f"/api/v1/participants/{profile_id}/conditions/{link_id}",
        headers=admin_headers,
        json={"severity": "INVALID"},
    )
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


async def test_multiple_active_conditions(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, hc1, suffix = await _create_participant_and_hc(client, admin_headers)
    hc2 = await client.post(
        "/api/v1/health-conditions",
        headers=admin_headers,
        json={"code": f"PC2-{suffix}", "name": "Second"},
    )
    assert hc2.status_code == 201
    hc2_id = hc2.json()["id"]

    a = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc1},
    )
    b = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc2_id},
    )
    assert a.status_code == 201
    assert b.status_code == 201

    listed = await client.get(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["conditions"]) == 2


async def test_resolved_before_diagnosed_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)
    r = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={
            "healthConditionId": hc_id,
            "diagnosedAt": "2024-06-01",
            "resolvedAt": "2024-01-01",
        },
    )
    assert r.status_code == 400


async def test_list_unknown_participant_404(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = str(uuid.uuid4())
    r = await client.get(
        f"/api/v1/participants/{pid}/conditions",
        headers=admin_headers,
    )
    assert r.status_code == 404


async def test_delete_health_condition_allowed_after_link_removed(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    """Removing the participant link clears HEALTH_CONDITION_IN_USE."""
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)
    post = await client.post(
        f"/api/v1/participants/{profile_id}/conditions",
        headers=admin_headers,
        json={"healthConditionId": hc_id},
    )
    assert post.status_code == 201
    link_id = post.json()["id"]

    await client.delete(
        f"/api/v1/participants/{profile_id}/conditions/{link_id}",
        headers=admin_headers,
    )

    d = await client.delete(
        f"/api/v1/health-conditions/{hc_id}",
        headers=admin_headers,
    )
    assert d.status_code == 204


async def test_orm_insert_without_temporal_fields_still_blocks_hc_delete(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    """Direct ORM row (NULL temporal columns) counts as in-use for health condition."""
    profile_id, hc_id, _ = await _create_participant_and_hc(client, admin_headers)
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
