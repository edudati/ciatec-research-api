"""F10-02 project timeline export integration tests."""

import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient
from tests.integration.test_project_enrollments import (
    _active_project_with_pi,
    _user_headers,
)

from src.core.database import AsyncSessionLocal
from src.models.project_export_job import ProjectExportJob
from src.modules.project_exports.arq_tasks import generate_project_export
from src.modules.project_exports.constants import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_QUEUED,
    SCHEMA_VERSION,
)

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    from src.models.user import AuthUser, User
    from src.modules.auth.passwords import hash_password

    email = f"adm-pex-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin PEx",
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
    return {"Authorization": f"Bearer {login.json()['accessToken']}"}


async def _active_project_pi_headers(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, dict[str, str]]:
    pi_headers = await _user_headers(
        client,
        email=f"pi-pex-{uuid.uuid4()}@example.com",
        name="PI PEx",
        role="PI",
    )
    pi_id = (await client.get("/api/v1/auth/me", headers=pi_headers)).json()["id"]
    code = f"PEX-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Export proj", "piUserId": pi_id},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    act = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert act.status_code == 200
    return str(pid), pi_headers


async def _enrollment_timeline(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
) -> None:
    part_headers = await _user_headers(
        client,
        email=f"pt-pex-{uuid.uuid4()}@example.com",
        name="Participant PEx",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    r = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert r.status_code == 201


async def test_export_csv_forbidden_for_researcher_member(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid = await _active_project_with_pi(client, admin_headers)
    res_headers = await _user_headers(
        client,
        email=f"rs-pex-{uuid.uuid4()}@example.com",
        name="Researcher PEx",
        role="RESEARCHER",
    )
    rid = (await client.get("/api/v1/auth/me", headers=res_headers)).json()["id"]
    m = await client.post(
        f"/api/v1/projects/{pid}/members",
        headers=admin_headers,
        json={
            "userId": rid,
            "role": "RESEARCHER",
            "startDate": date.today().isoformat(),
        },
    )
    assert m.status_code == 201
    ex = await client.get(
        f"/api/v1/projects/{pid}/export?format=csv",
        headers=res_headers,
    )
    assert ex.status_code == 403


async def test_export_csv_pi_sees_header_and_row(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_headers = await _active_project_pi_headers(client, admin_headers)
    await _enrollment_timeline(client, admin_headers, pid)
    r = await client.get(
        f"/api/v1/projects/{pid}/export?format=csv",
        headers=pi_headers,
    )
    assert r.status_code == 200
    body = r.text
    assert "participantProfileId" in body
    assert body.count("\n") >= 2


async def test_export_json_bundle_schema(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_headers = await _active_project_pi_headers(client, admin_headers)
    await _enrollment_timeline(client, admin_headers, pid)
    r = await client.get(
        f"/api/v1/projects/{pid}/export?format=json",
        headers=pi_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["schemaVersion"] == SCHEMA_VERSION
    assert isinstance(data["timeline"], list)
    assert len(data["timeline"]) >= 1


async def test_export_invalid_format_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_headers = await _active_project_pi_headers(client, admin_headers)
    r = await client.get(
        f"/api/v1/projects/{pid}/export?format=xml",
        headers=pi_headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_generate_project_export_arq_task_completes(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_headers = await _active_project_pi_headers(client, admin_headers)
    await _enrollment_timeline(client, admin_headers, pid)
    admin_id = (await client.get("/api/v1/auth/me", headers=admin_headers)).json()["id"]
    job_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            ProjectExportJob(
                id=job_id,
                project_id=uuid.UUID(pid),
                requested_by_user_id=uuid.UUID(admin_id),
                format="csv",
                status=JOB_STATUS_QUEUED,
            ),
        )
        await session.commit()

    await generate_project_export({}, str(job_id))

    async with AsyncSessionLocal() as session:
        job = await session.get(ProjectExportJob, job_id)
        assert job is not None
        assert job.status == JOB_STATUS_COMPLETED
        assert job.row_count is not None and job.row_count >= 1
        assert job.result_path is not None
