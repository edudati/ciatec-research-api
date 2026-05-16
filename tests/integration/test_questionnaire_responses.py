"""Questionnaire responses API integration tests."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.self_report_token import SelfReportToken
from src.models.timeline_event import TimelineEvent
from src.models.user import AuthUser, User
from src.modules.auth.passwords import hash_password

_VALID_PASSWORD = "ValidPass1"


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    email = f"adm-qr-{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                id=user_id,
                email=email,
                name="Admin QR",
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
) -> tuple[str, str]:
    pi_headers = await _user_headers(
        client,
        email=f"pi-qr-{uuid.uuid4()}@example.com",
        name="PI QR",
        role="PI",
    )
    me = await client.get("/api/v1/auth/me", headers=pi_headers)
    pi_id = me.json()["id"]
    code = f"QR-{uuid.uuid4().hex[:8].upper()}"
    c = await client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"code": code, "name": "QR proj", "piUserId": pi_id},
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


async def _enrolled_participant_profile(
    client: AsyncClient,
    admin_headers: dict[str, str],
    project_id: str,
) -> tuple[str, str]:
    part_headers = await _user_headers(
        client,
        email=f"pt-qr-{uuid.uuid4()}@example.com",
        name="Participant QR",
        role="PARTICIPANT",
    )
    uid = (await client.get("/api/v1/auth/me", headers=part_headers)).json()["id"]
    cr = await client.post(
        f"/api/v1/projects/{project_id}/enrollments",
        headers=admin_headers,
        json={"userId": uid, "role": "PARTICIPANT"},
    )
    assert cr.status_code == 201
    return str(cr.json()["participantProfileId"]), str(uid)


async def _questionnaire_template(
    client: AsyncClient,
    admin_headers: dict[str, str],
    *,
    self_report: bool,
) -> str:
    suf = uuid.uuid4().hex[:8]
    r = await client.post(
        "/api/v1/instruments/questionnaires",
        headers=admin_headers,
        json={
            "code": f"QNR-{suf}",
            "name": "QR template",
            "type": "PSYCHOLOGICAL",
        },
    )
    assert r.status_code == 201
    tid = str(r.json()["id"])
    if self_report:
        p = await client.patch(
            f"/api/v1/instruments/questionnaires/{tid}",
            headers=admin_headers,
            json={"selfReport": True},
        )
        assert p.status_code == 200
    return tid


async def _add_text_item(
    client: AsyncClient,
    admin_headers: dict[str, str],
    template_id: str,
    *,
    code: str,
    order: int,
    required: bool = True,
) -> str:
    it = await client.post(
        f"/api/v1/instruments/questionnaires/{template_id}/items",
        headers=admin_headers,
        json={
            "code": code,
            "label": code,
            "type": "TEXT",
            "order": order,
            "isRequired": required,
        },
    )
    assert it.status_code == 201
    return str(it.json()["id"])


async def test_executor_null_mediated_questionnaire_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=False)
    r = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": None,
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "QUESTIONNAIRE_EXECUTOR_REQUIRED"


async def test_duplicate_answer_same_item_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=False)
    iid = await _add_text_item(client, admin_headers, tid, code="Q1", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": pi_id,
        },
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    a1 = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/answers",
        headers=admin_headers,
        json={"questionItemId": iid, "value": "first"},
    )
    assert a1.status_code == 200
    a2 = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/answers",
        headers=admin_headers,
        json={"questionItemId": iid, "value": "second"},
    )
    assert a2.status_code == 409
    assert a2.json()["code"] == "QUESTION_ANSWER_DUPLICATE"


async def test_timeline_event_on_mark_completed(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=True)
    iid = await _add_text_item(client, admin_headers, tid, code="Q1", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
        },
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    ans = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/answers",
        headers=admin_headers,
        json={
            "questionItemId": iid,
            "value": "done",
            "markCompleted": True,
        },
    )
    assert ans.status_code == 200
    assert ans.json()["status"] == "COMPLETED"
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == rid,
            TimelineEvent.event_type == "QUESTIONNAIRE",
            TimelineEvent.source_type == "QuestionnaireResponse",
        )
        res = await session.execute(stmt)
        ev = res.scalar_one_or_none()
    assert ev is not None
    assert str(ev.project_id) == pid
    assert ev.executor_id is None


async def test_self_report_send_link_submit_and_timeline(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=True)
    iid = await _add_text_item(client, admin_headers, tid, code="Q1", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
        },
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    sl = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/send-link",
        headers=admin_headers,
    )
    assert sl.status_code == 200
    token = sl.json()["token"]
    g = await client.get(f"/api/v1/self-report/{token}")
    assert g.status_code == 200
    assert g.json()["responseStatus"] == "PENDING"
    sub = await client.post(
        f"/api/v1/self-report/{token}/submit",
        json={"answers": [{"questionItemId": iid, "value": "from participant"}]},
    )
    assert sub.status_code == 200
    assert sub.json()["status"] == "COMPLETED"
    async with AsyncSessionLocal() as session:
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_id == rid,
            TimelineEvent.event_type == "QUESTIONNAIRE",
        )
        res = await session.execute(stmt)
        ev = res.scalar_one_or_none()
    assert ev is not None


async def test_self_report_token_expired_410(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=True)
    iid = await _add_text_item(client, admin_headers, tid, code="Qx", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={"participantProfileId": profile_id, "templateId": tid},
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    sl = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/send-link",
        headers=admin_headers,
    )
    assert sl.status_code == 200
    token = sl.json()["token"]
    async with AsyncSessionLocal() as session:
        stmt = select(SelfReportToken).where(SelfReportToken.token == uuid.UUID(token))
        res = await session.execute(stmt)
        trow = res.scalar_one()
        trow.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await session.commit()
    g = await client.get(f"/api/v1/self-report/{token}")
    assert g.status_code == 410
    assert g.json()["code"] == "SELF_REPORT_TOKEN_EXPIRED"
    p = await client.post(
        f"/api/v1/self-report/{token}/submit",
        json={"answers": [{"questionItemId": iid, "value": "x"}]},
    )
    assert p.status_code == 410


async def test_self_report_token_used_409(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=True)
    iid = await _add_text_item(client, admin_headers, tid, code="Qy", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={"participantProfileId": profile_id, "templateId": tid},
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    sl = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/send-link",
        headers=admin_headers,
    )
    assert sl.status_code == 200
    token = sl.json()["token"]
    s1 = await client.post(
        f"/api/v1/self-report/{token}/submit",
        json={"answers": [{"questionItemId": iid, "value": "once"}]},
    )
    assert s1.status_code == 200
    g = await client.get(f"/api/v1/self-report/{token}")
    assert g.status_code == 409
    s2 = await client.post(
        f"/api/v1/self-report/{token}/submit",
        json={"answers": [{"questionItemId": iid, "value": "twice"}]},
    )
    assert s2.status_code == 409


async def test_self_report_submit_incomplete_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, _pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=True)
    await _add_text_item(client, admin_headers, tid, code="R1", order=0, required=True)
    i2 = await _add_text_item(
        client, admin_headers, tid, code="R2", order=1, required=True
    )
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={"participantProfileId": profile_id, "templateId": tid},
    )
    assert cr.status_code == 201
    rid = cr.json()["id"]
    sl = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/send-link",
        headers=admin_headers,
    )
    assert sl.status_code == 200
    token = sl.json()["token"]
    sub = await client.post(
        f"/api/v1/self-report/{token}/submit",
        json={"answers": [{"questionItemId": i2, "value": "only one"}]},
    )
    assert sub.status_code == 422
    assert sub.json()["code"] == "QUESTIONNAIRE_INCOMPLETE"


async def test_send_self_report_link_non_self_report_422(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> None:
    pid, pi_id = await _active_project_with_pi(client, admin_headers)
    profile_id, _uid = await _enrolled_participant_profile(client, admin_headers, pid)
    tid = await _questionnaire_template(client, admin_headers, self_report=False)
    await _add_text_item(client, admin_headers, tid, code="M1", order=0)
    cr = await client.post(
        f"/api/v1/projects/{pid}/questionnaires",
        headers=admin_headers,
        json={
            "participantProfileId": profile_id,
            "templateId": tid,
            "executorId": pi_id,
        },
    )
    rid = cr.json()["id"]
    sl = await client.post(
        f"/api/v1/projects/{pid}/questionnaires/{rid}/send-link",
        headers=admin_headers,
    )
    assert sl.status_code == 422
    assert sl.json()["code"] == "QUESTIONNAIRE_NOT_SELF_REPORT"
