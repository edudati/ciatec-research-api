"""Participant profile business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import BiologicalSex
from src.core.exceptions import ConflictError, NotFoundError
from src.models.participant_profile import ParticipantProfile
from src.modules.participants.repository import ParticipantsRepository
from src.modules.participants.schemas import (
    ParticipantCreateIn,
    ParticipantListResponse,
    ParticipantOut,
    ParticipantUpdateIn,
    parse_order,
    parse_participant_list_sort,
)


class ParticipantsService:
    _SORT_COLUMNS = {
        "createdAt": ParticipantProfile.created_at,
        "updatedAt": ParticipantProfile.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ParticipantsRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: ParticipantProfile) -> ParticipantOut:
        bio: BiologicalSex | None = None
        if row.biological_sex is not None:
            bio = BiologicalSex(row.biological_sex)
        return ParticipantOut(
            id=str(row.id),
            user_id=str(row.user_id),
            birth_date=row.birth_date.isoformat() if row.birth_date else None,
            biological_sex=bio,
            phone=row.phone,
            notes=row.notes,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def create(self, body: ParticipantCreateIn) -> ParticipantOut:
        if not await self._repo.is_user_active(body.user_id):
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        existing = await self._repo.get_active_by_user_id(body.user_id)
        if existing is not None:
            raise ConflictError(
                "Participant profile already exists for this user",
                code="PARTICIPANT_PROFILE_EXISTS",
            )
        profile_id = uuid.uuid4()
        phone_val: str | None = None
        if body.phone is not None:
            stripped = body.phone.strip()
            phone_val = stripped or None
        row = ParticipantProfile(
            id=profile_id,
            user_id=body.user_id,
            birth_date=body.birth_date,
            biological_sex=body.biological_sex.value if body.biological_sex else None,
            phone=phone_val,
            notes=body.notes,
        )
        self._repo.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def get_by_id(self, profile_id: uuid.UUID) -> ParticipantOut:
        row = await self._repo.get_active_by_id(profile_id)
        if row is None:
            raise NotFoundError("Participant profile not found", code="NOT_FOUND")
        return self._to_out(row)

    async def update(
        self,
        profile_id: uuid.UUID,
        body: ParticipantUpdateIn,
    ) -> ParticipantOut:
        row = await self._repo.get_active_by_id(profile_id)
        if row is None:
            raise NotFoundError("Participant profile not found", code="NOT_FOUND")
        if body.birth_date is not None:
            row.birth_date = body.birth_date
        if body.biological_sex is not None:
            row.biological_sex = body.biological_sex.value
        if body.phone is not None:
            stripped = body.phone.strip()
            row.phone = stripped or None
        if body.notes is not None:
            row.notes = body.notes
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_participants(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None,
        sort: str,
        order: str,
    ) -> ParticipantListResponse:
        sort_key = parse_participant_list_sort(sort)
        sort_col = self._SORT_COLUMNS[sort_key]
        total = await self._repo.count_list(q=q)
        rows = await self._repo.list_page(
            page=page,
            page_size=page_size,
            q=q,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items = [self._to_out(r) for r in rows]
        return ParticipantListResponse(
            participants=items,
            total=total,
            page=page,
            page_size=page_size,
        )
