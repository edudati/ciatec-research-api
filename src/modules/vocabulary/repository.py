"""Vocabulary persistence."""

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.participant_condition import ParticipantCondition
from src.models.vocabulary import VocabularyScheme, VocabularyTerm

ASSESSMENT_TYPE_SCHEME_CODE = "ASSESSMENT_TYPE"
INSTRUMENT_INDICATION_TYPE_SCHEME_CODE = "INSTRUMENT_INDICATION_TYPE"
INTERVENTION_TYPE_SCHEME_CODE = "INTERVENTION_TYPE"
CONDITION_SEVERITY_SCHEME_CODE = "CONDITION_SEVERITY"
PROJECT_MEMBER_ROLE_SCHEME_CODE = "PROJECT_MEMBER_ROLE"
ENROLLMENT_ROLE_SCHEME_CODE = "ENROLLMENT_ROLE"
ENROLLMENT_STATUS_SCHEME_CODE = "ENROLLMENT_STATUS"
TIMELINE_EVENT_TYPE_SCHEME_CODE = "TIMELINE_EVENT_TYPE"


class VocabularyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_schemes(self) -> list[VocabularyScheme]:
        stmt = select(VocabularyScheme).order_by(VocabularyScheme.code.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_scheme_by_id(self, scheme_id: uuid.UUID) -> VocabularyScheme | None:
        stmt = select(VocabularyScheme).where(VocabularyScheme.id == scheme_id).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def scheme_code_taken(
        self,
        code: str,
        *,
        exclude_id: uuid.UUID | None,
    ) -> bool:
        stmt = select(VocabularyScheme.id).where(VocabularyScheme.code == code)
        if exclude_id is not None:
            stmt = stmt.where(VocabularyScheme.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_scheme(self, row: VocabularyScheme) -> None:
        self._session.add(row)

    async def list_terms_for_scheme(
        self,
        scheme_id: uuid.UUID,
        *,
        active_only: bool,
    ) -> list[VocabularyTerm]:
        stmt = (
            select(VocabularyTerm)
            .where(VocabularyTerm.scheme_id == scheme_id)
            .order_by(VocabularyTerm.sort_order.asc(), VocabularyTerm.code.asc())
        )
        if active_only:
            stmt = stmt.where(VocabularyTerm.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_term_by_id(self, term_id: uuid.UUID) -> VocabularyTerm | None:
        stmt = (
            select(VocabularyTerm)
            .where(VocabularyTerm.id == term_id)
            .options(joinedload(VocabularyTerm.scheme))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def term_code_taken_in_scheme(
        self,
        scheme_id: uuid.UUID,
        code: str,
        *,
        exclude_id: uuid.UUID | None,
    ) -> bool:
        stmt = select(VocabularyTerm.id).where(
            VocabularyTerm.scheme_id == scheme_id,
            VocabularyTerm.code == code,
        )
        if exclude_id is not None:
            stmt = stmt.where(VocabularyTerm.id != exclude_id)
        stmt = stmt.limit(1)
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None

    def add_term(self, row: VocabularyTerm) -> None:
        self._session.add(row)

    async def count_participant_conditions_by_severity_code(self, code: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ParticipantCondition)
            .where(ParticipantCondition.severity == code)
        )
        result = await self._session.scalar(stmt)
        return int(result or 0)

    async def is_active_term_in_scheme(
        self,
        *,
        scheme_code: str,
        term_code: str,
    ) -> bool:
        stmt = (
            select(VocabularyTerm.id)
            .join(VocabularyScheme, VocabularyScheme.id == VocabularyTerm.scheme_id)
            .where(
                and_(
                    VocabularyScheme.code == scheme_code,
                    VocabularyTerm.code == term_code,
                    VocabularyTerm.is_active.is_(True),
                ),
            )
            .limit(1)
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none() is not None
