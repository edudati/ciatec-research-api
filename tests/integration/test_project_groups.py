"""Project groups API integration tests."""

import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.participant_enrollment import ParticipantEnrollment
from src.models.participant_profile import ParticipantProfile
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-grp-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin Grp",
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


async def _create_project(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    code = f"GRP-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Group test project"},
    )
    assert c.status_code == 201
    return str(c.json()["id"])


async def test_duplicate_group_name_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _create_project(client, admin_headers)
    a = await client.post(
        f"/api/v1/projects/{pid}/groups",
        headers=admin_headers,
        json={"name": "Intervenção"},
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/projects/{pid}/groups",
        headers=admin_headers,
        json={"name": "Intervenção"},
    )
    assert b.status_code == 409
    assert b.json()["code"] == "GROUP_NAME_IN_USE"


async def test_duplicate_group_name_case_insensitive_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _create_project(client, admin_headers)
    a = await client.post(
        f"/api/v1/projects/{pid}/groups",
        headers=admin_headers,
        json={"name": "Arm A"},
    )
    assert a.status_code == 201
    b = await client.post(
        f"/api/v1/projects/{pid}/groups",
        headers=admin_headers,
        json={"name": "  arm a  "},
    )
    assert b.status_code == 409
    assert b.json()["code"] == "GROUP_NAME_IN_USE"


async def test_delete_group_with_active_enrollment_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _create_project(client, admin_headers)
    g = await client.post(
        f"/api/v1/projects/{pid}/groups",
        headers=admin_headers,
        json={"name": "Cohort X"},
    )
    assert g.status_code == 201
    gid = uuid.UUID(g.json()["id"])
    project_id = uuid.UUID(pid)

    user_id = uuid.uuid4()
    profile_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=f"part-{uuid.uuid4()}@example.com",
                name="Participant",
                role="PARTICIPANT",
                is_first_access=False,
            ),
        )
        session.add(
            AuthUser(
                user_id=user_id,
                password_hash=hash_password(_VALID_PASSWORD),
            ),
        )
        session.add(
            ParticipantProfile(
                id=profile_id,
                user_id=user_id,
            ),
        )
        session.add(
            ParticipantEnrollment(
                id=uuid.uuid4(),
                project_id=project_id,
                participant_profile_id=profile_id,
                group_id=gid,
                role="PARTICIPANT",
                status="ACTIVE",
                enrolled_at=datetime.now(UTC),
                exited_at=None,
            ),
        )
        await session.commit()

    d = await client.delete(
        f"/api/v1/projects/{pid}/groups/{gid}",
        headers=admin_headers,
    )
    assert d.status_code == 409
    assert d.json()["code"] == "GROUP_HAS_ACTIVE_ENROLLMENTS"
