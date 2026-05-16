"""Business logic for participant x health condition temporal links."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.models.participant_condition import ParticipantCondition
from src.modules.participant_conditions.repository import (
    ParticipantConditionsRepository,
)
from src.modules.participant_conditions.schemas import (
    ParticipantConditionCreateIn,
    ParticipantConditionListResponse,
    ParticipantConditionOut,
    ParticipantConditionPatchIn,
)
from src.modules.vocabulary.service import VocabularyService


class ParticipantConditionsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ParticipantConditionsRepository(session)
        self._vocab = VocabularyService(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    @staticmethod
    def _date_iso(d: date | None) -> str | None:
        return d.isoformat() if d is not None else None

    @staticmethod
    def _normalize_severity(raw: str | None) -> str | None:
        if raw is None:
            return None
        s = raw.strip().upper()
        return s or None

    @staticmethod
    def _normalize_notes(raw: str | None) -> str | None:
        if raw is None:
            return None
        stripped = raw.strip()
        return stripped or None

    async def _validate_severity_code(self, code: str | None) -> None:
        if code is None:
            return
        if not await self._vocab.is_active_severity_code(code):
            raise ValidationError(
                "Invalid or inactive severity for scheme CONDITION_SEVERITY",
                code="VALIDATION_ERROR",
                issues=[
                    {
                        "field": "severity",
                        "msg": "Must match an active vocabulary term",
                    },
                ],
            )

    @staticmethod
    def _validate_diagnosed_resolved(
        diagnosed_at: date | None,
        resolved_at: date | None,
    ) -> None:
        if (
            diagnosed_at is not None
            and resolved_at is not None
            and resolved_at < diagnosed_at
        ):
            raise ValidationError(
                "resolvedAt must be on or after diagnosedAt",
                code="VALIDATION_ERROR",
                issues=[
                    {
                        "field": "resolvedAt",
                        "msg": "Must be >= diagnosedAt when both are set",
                    },
                ],
            )

    def _to_out(self, row: ParticipantCondition) -> ParticipantConditionOut:
        return ParticipantConditionOut(
            id=str(row.id),
            health_condition_id=str(row.health_condition_id),
            diagnosed_at=self._date_iso(row.diagnosed_at),
            resolved_at=self._date_iso(row.resolved_at),
            severity=row.severity,
            notes=row.notes,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _require_profile(self, participant_id: uuid.UUID) -> None:
        row = await self._repo.get_active_profile(participant_id)
        if row is None:
            raise NotFoundError("Participant profile not found", code="NOT_FOUND")

    async def list_for_participant(
        self,
        participant_id: uuid.UUID,
    ) -> ParticipantConditionListResponse:
        await self._require_profile(participant_id)
        rows = await self._repo.list_for_participant(participant_id)
        return ParticipantConditionListResponse(
            conditions=[self._to_out(r) for r in rows],
        )

    async def create(
        self,
        participant_id: uuid.UUID,
        body: ParticipantConditionCreateIn,
    ) -> ParticipantConditionOut:
        await self._require_profile(participant_id)
        hc = await self._repo.get_assignable_health_condition(body.health_condition_id)
        if hc is None:
            raise NotFoundError("Health condition not found", code="NOT_FOUND")
        sev = self._normalize_severity(body.severity)
        await self._validate_severity_code(sev)
        self._validate_diagnosed_resolved(body.diagnosed_at, body.resolved_at)
        row = ParticipantCondition(
            id=uuid.uuid4(),
            participant_profile_id=participant_id,
            health_condition_id=body.health_condition_id,
            diagnosed_at=body.diagnosed_at,
            resolved_at=body.resolved_at,
            severity=sev,
            notes=self._normalize_notes(body.notes),
        )
        self._repo.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def patch(
        self,
        participant_id: uuid.UUID,
        link_id: uuid.UUID,
        body: ParticipantConditionPatchIn,
    ) -> ParticipantConditionOut:
        await self._require_profile(participant_id)
        row = await self._repo.get_link_for_participant(participant_id, link_id)
        if row is None:
            raise NotFoundError("Participant condition not found", code="NOT_FOUND")
        data = body.model_dump(exclude_unset=True)
        if "diagnosed_at" in data:
            row.diagnosed_at = data["diagnosed_at"]
        if "resolved_at" in data:
            row.resolved_at = data["resolved_at"]
        if "severity" in data:
            sev = self._normalize_severity(data["severity"])
            await self._validate_severity_code(sev)
            row.severity = sev
        if "notes" in data:
            row.notes = self._normalize_notes(data["notes"])
        self._validate_diagnosed_resolved(row.diagnosed_at, row.resolved_at)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def delete(
        self,
        participant_id: uuid.UUID,
        link_id: uuid.UUID,
    ) -> None:
        await self._require_profile(participant_id)
        row = await self._repo.get_link_for_participant(participant_id, link_id)
        if row is None:
            raise NotFoundError("Participant condition not found", code="NOT_FOUND")
        await self._repo.delete(row)
        await self._session.commit()
