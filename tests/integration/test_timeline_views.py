"""Timeline read API integration tests (F7-01)."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest_asyncio
from httpx import AsyncClient

from src.core.database import AsyncSessionLocal
from src.models.timeline_event import TimelineEvent
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-tl-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin TL",
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
) -> tuple[str, str]:
    pi_headers = await _user_headers(
        client,
        email=f"pi-tl-{uuid.uuid4()}@example.com",
        name="PI TL",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"TL-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "Timeline proj", "piUserId": pi_id},
    )
    assert c.status_code == 201
    pid = c.json()["id"]
    act = await client.patch(
        f"/api/v1/projects/{pid}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )
    assert act.status_code == 200
    return str(pid), str(pi_id)


async def _enrollment(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
) -> tuple[str, str, str]:
    part_headers = await _user_headers(
        client,
        email=f"pt-tl-{uuid.uuid4()}@example.com",
        name="Participant TL",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    cr = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert cr.status_code == 201
    body = cr.json()
    return str(body["participantProfileId"]), str(body["id"]), str(uid)


async def _add_project_member(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
    *,
    user_id: str,
    role: str,
) -> None:
    r = await client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=admin_headers,
        json={
            "userId": user_id,
            "role": role,
            "startDate": str(date.today()),
        },
    )
    assert r.status_code == 201


async def test_researcher_global_timeline_403(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    rs_headers = await _user_headers(
        client,
        email=f"rs-tl-{uuid.uuid4()}@example.com",
        name="RS TL",
        role="RESEARCHER",
    )
    pid, _pi = await _active_project_with_pi(client, admin_headers)
    me = await client.get("/api/v1/auth/me", headers=rs_headers)
    await _add_project_member(
        client,
        admin_headers,
        pid,
        user_id=me.json()["id"],
        role="RESEARCHER",
    )
    r = await client.get(
        "/api/v1/timeline",
        headers=rs_headers,
        params={"page": 1, "pageSize": 10},
    )
    assert r.status_code == 403


async def test_pagination_participant_timeline(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, enroll_id, _uid = await _enrollment(client, admin_headers, pid)
    base = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
    async with AsyncSessionLocal() as session:
        for i in range(3):
            session.add(
                TimelineEvent(
                    id=uuid.uuid4(),
                    participant_profile_id=uuid.UUID(profile_id),
                    project_id=uuid.UUID(pid),
                    enrollment_id=uuid.UUID(enroll_id),
                    executor_id=uuid.UUID(pi_id),
                    event_type="TL_PAG",
                    source_type="TestSource",
                    source_id=str(uuid.uuid4()),
                    occurred_at=base + timedelta(hours=i),
                    context={"i": i},
                ),
            )
        await session.commit()

    r1 = await client.get(
        f"/api/v1/participants/{profile_id}/timeline",
        headers=admin_headers,
        params={"page": 1, "pageSize": 2, "eventType": "TL_PAG"},
    )
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1["total"] == 3
    assert len(j1["items"]) == 2
    assert j1["page"] == 1
    assert j1["pageSize"] == 2
    times = [x["occurredAt"] for x in j1["items"]]
    assert times == sorted(times, reverse=True)

    r2 = await client.get(
        f"/api/v1/participants/{profile_id}/timeline",
        headers=admin_headers,
        params={"page": 2, "pageSize": 2, "eventType": "TL_PAG"},
    )
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["total"] == 3
    assert len(j2["items"]) == 1


async def test_filter_event_type(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, enroll_id, _uid = await _enrollment(client, admin_headers, pid)
    t0 = datetime(2024, 7, 1, 10, 0, 0, tzinfo=UTC)
    async with AsyncSessionLocal() as session:
        session.add(
            TimelineEvent(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                project_id=uuid.UUID(pid),
                enrollment_id=uuid.UUID(enroll_id),
                executor_id=uuid.UUID(pi_id),
                event_type="KEEP_ME",
                source_type="TestSource",
                source_id=str(uuid.uuid4()),
                occurred_at=t0,
                context={},
            ),
        )
        session.add(
            TimelineEvent(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                project_id=uuid.UUID(pid),
                enrollment_id=uuid.UUID(enroll_id),
                executor_id=uuid.UUID(pi_id),
                event_type="OTHER_TYPE",
                source_type="TestSource",
                source_id=str(uuid.uuid4()),
                occurred_at=t0 + timedelta(hours=1),
                context={},
            ),
        )
        await session.commit()

    r = await client.get(
        f"/api/v1/participants/{profile_id}/timeline",
        headers=admin_headers,
        params={"eventType": "KEEP_ME", "page": 1, "pageSize": 20},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["eventType"] == "KEEP_ME"


async def test_occurred_at_desc_order(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, enroll_id, _uid = await _enrollment(client, admin_headers, pid)
    t0 = datetime(2024, 8, 1, 8, 0, 0, tzinfo=UTC)
    async with AsyncSessionLocal() as session:
        for h in (1, 3, 2):
            session.add(
                TimelineEvent(
                    id=uuid.uuid4(),
                    participant_profile_id=uuid.UUID(profile_id),
                    project_id=uuid.UUID(pid),
                    enrollment_id=uuid.UUID(enroll_id),
                    executor_id=uuid.UUID(pi_id),
                    event_type="TL_ORDER",
                    source_type="TestSource",
                    source_id=str(uuid.uuid4()),
                    occurred_at=t0 + timedelta(hours=h),
                    context={"h": h},
                ),
            )
        await session.commit()

    r = await client.get(
        f"/api/v1/participants/{profile_id}/timeline",
        headers=admin_headers,
        params={"eventType": "TL_ORDER", "page": 1, "pageSize": 10},
    )
    assert r.status_code == 200
    occ = [item["occurredAt"] for item in r.json()["items"]]
    assert occ == sorted(occ, reverse=True)


async def test_project_timeline_researcher_only_own_executor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, enroll_id, _uid = await _enrollment(client, admin_headers, pid)
    rs_headers = await _user_headers(
        client,
        email=f"rs-proj-{uuid.uuid4()}@example.com",
        name="RS Proj",
        role="RESEARCHER",
    )
    rs_id = (await client.get("/api/v1/auth/me", headers=rs_headers)).json()["id"]
    await _add_project_member(
        client,
        admin_headers,
        pid,
        user_id=rs_id,
        role="RESEARCHER",
    )
    t0 = datetime(2024, 9, 1, 9, 0, 0, tzinfo=UTC)
    async with AsyncSessionLocal() as session:
        session.add(
            TimelineEvent(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                project_id=uuid.UUID(pid),
                enrollment_id=uuid.UUID(enroll_id),
                executor_id=uuid.UUID(pi_id),
                event_type="TL_RS",
                source_type="TestSource",
                source_id=str(uuid.uuid4()),
                occurred_at=t0,
                context={"by": "pi"},
            ),
        )
        session.add(
            TimelineEvent(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                project_id=uuid.UUID(pid),
                enrollment_id=uuid.UUID(enroll_id),
                executor_id=uuid.UUID(rs_id),
                event_type="TL_RS",
                source_type="TestSource",
                source_id=str(uuid.uuid4()),
                occurred_at=t0 + timedelta(hours=1),
                context={"by": "rs"},
            ),
        )
        await session.commit()

    r_rs = await client.get(
        f"/api/v1/projects/{pid}/timeline",
        headers=rs_headers,
        params={"eventType": "TL_RS", "page": 1, "pageSize": 20},
    )
    assert r_rs.status_code == 200
    assert r_rs.json()["total"] == 1
    assert r_rs.json()["items"][0]["executorId"] == rs_id

    r_ad = await client.get(
        f"/api/v1/projects/{pid}/timeline",
        headers=admin_headers,
        params={"eventType": "TL_RS", "page": 1, "pageSize": 20},
    )
    assert r_ad.status_code == 200
    assert r_ad.json()["total"] == 2


async def test_global_timeline_admin_ok(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, enroll_id, _uid = await _enrollment(client, admin_headers, pid)
    async with AsyncSessionLocal() as session:
        session.add(
            TimelineEvent(
                id=uuid.uuid4(),
                participant_profile_id=uuid.UUID(profile_id),
                project_id=uuid.UUID(pid),
                enrollment_id=uuid.UUID(enroll_id),
                executor_id=uuid.UUID(pi_id),
                event_type="TL_GLOBAL",
                source_type="TestSource",
                source_id=str(uuid.uuid4()),
                occurred_at=datetime(2024, 10, 1, tzinfo=UTC),
                context={},
            ),
        )
        await session.commit()

    r = await client.get(
        "/api/v1/timeline",
        headers=admin_headers,
        params={"eventType": "TL_GLOBAL", "page": 1, "pageSize": 10},
    )
    assert r.status_code == 200
    assert r.json()["total"] >= 1


async def test_from_date_after_to_date_400(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi = await _active_project_with_pi(client, admin_headers)
    profile_id, _, _ = await _enrollment(client, admin_headers, pid)
    r = await client.get(
        f"/api/v1/participants/{profile_id}/timeline",
        headers=admin_headers,
        params={
            "fromDate": "2024-12-31",
            "toDate": "2024-01-01",
            "page": 1,
            "pageSize": 10,
        },
    )
    assert r.status_code == 400
