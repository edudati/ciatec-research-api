"""Instrument indication business logic."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
    ValidationError,
)
from src.models.instrument_indication import InstrumentIndication
from src.modules.instruments.repository_indications import (
    InstrumentIndicationsRepository,
)
from src.modules.instruments.schemas_indications import (
    InstrumentIndicationCreateIn,
    InstrumentIndicationOut,
    InstrumentIndicationsListResponse,
    InstrumentKind,
)
from src.modules.vocabulary.repository import (
    INSTRUMENT_INDICATION_TYPE_SCHEME_CODE,
    VocabularyRepository,
)


@dataclass(frozen=True)
class _ListByInstrumentSpec:
    instrument_type: str
    instrument_id: uuid.UUID


@dataclass(frozen=True)
class _ListByHealthSpec:
    health_condition_id: uuid.UUID


class InstrumentIndicationsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InstrumentIndicationsRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: InstrumentIndication) -> InstrumentIndicationOut:
        kind = cast(InstrumentKind, row.instrument_type)
        return InstrumentIndicationOut(
            id=str(row.id),
            instrument_kind=kind,
            instrument_id=str(row.instrument_id),
            health_condition_id=str(row.health_condition_id),
            indication_type=row.indication_type,
            created_at=self._dt_iso(row.created_at),
        )

    async def _assert_valid_indication_type(self, term_code: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=INSTRUMENT_INDICATION_TYPE_SCHEME_CODE,
            term_code=term_code,
        )
        if not ok:
            raise ValidationError(
                "Invalid or inactive indication type",
                code="INDICATION_TYPE_INVALID",
            )

    async def _assert_instrument_exists(
        self,
        instrument_type: str,
        instrument_id: uuid.UUID,
    ) -> None:
        if instrument_type == "ASSESSMENT":
            ok = await self._repo.assessment_template_exists(instrument_id)
        elif instrument_type == "QUESTIONNAIRE":
            ok = await self._repo.questionnaire_template_exists(instrument_id)
        else:
            ok = False
        if not ok:
            raise NotFoundError("Instrument not found", code="NOT_FOUND")

    async def create(
        self,
        body: InstrumentIndicationCreateIn,
    ) -> InstrumentIndicationOut:
        await self._assert_valid_indication_type(body.indication_type)
        itype = body.instrument_kind
        iid = body.instrument_id
        await self._assert_instrument_exists(itype, iid)
        hc_ok = await self._repo.usable_health_condition_exists(
            body.health_condition_id,
        )
        if not hc_ok:
            raise NotFoundError("Health condition not found", code="NOT_FOUND")
        if await self._repo.triple_exists(
            instrument_type=itype,
            instrument_id=iid,
            health_condition_id=body.health_condition_id,
        ):
            raise ConflictError(
                "This indication already exists",
                code="INDICATION_DUPLICATE",
            )
        row = InstrumentIndication(
            id=uuid.uuid4(),
            instrument_type=itype,
            instrument_id=iid,
            health_condition_id=body.health_condition_id,
            indication_type=body.indication_type,
        )
        self._repo.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    def _parse_list_query(
        self,
        *,
        instrument_type: str | None,
        instrument_id: uuid.UUID | None,
        health_condition_id: uuid.UUID | None,
    ) -> _ListByInstrumentSpec | _ListByHealthSpec:
        has_inst = instrument_type is not None or instrument_id is not None
        has_hc = health_condition_id is not None

        if has_inst and has_hc:
            raise UnprocessableEntityError(
                "Use either instrumentType+instrumentId or healthConditionId, not both",
                code="INDICATIONS_QUERY_AMBIGUOUS",
            )
        if has_inst:
            if instrument_type is None or instrument_id is None:
                raise UnprocessableEntityError(
                    "instrumentType and instrumentId are required together",
                    code="INDICATIONS_QUERY_INCOMPLETE",
                )
            it = instrument_type.strip().upper()
            if it not in ("ASSESSMENT", "QUESTIONNAIRE"):
                raise UnprocessableEntityError(
                    "instrumentType must be ASSESSMENT or QUESTIONNAIRE",
                    code="INDICATIONS_QUERY_INVALID",
                )
            return _ListByInstrumentSpec(
                instrument_type=it,
                instrument_id=instrument_id,
            )
        if has_hc:
            assert health_condition_id is not None
            return _ListByHealthSpec(health_condition_id=health_condition_id)

        raise UnprocessableEntityError(
            "Provide instrumentType+instrumentId or healthConditionId",
            code="INDICATIONS_QUERY_REQUIRED",
        )

    async def list_filtered(
        self,
        *,
        instrument_type: str | None,
        instrument_id: uuid.UUID | None,
        health_condition_id: uuid.UUID | None,
    ) -> InstrumentIndicationsListResponse:
        spec = self._parse_list_query(
            instrument_type=instrument_type,
            instrument_id=instrument_id,
            health_condition_id=health_condition_id,
        )
        if isinstance(spec, _ListByInstrumentSpec):
            await self._assert_instrument_exists(
                spec.instrument_type,
                spec.instrument_id,
            )
            rows = await self._repo.list_by_instrument(
                instrument_type=spec.instrument_type,
                instrument_id=spec.instrument_id,
            )
        else:
            hc_exists = await self._repo.usable_health_condition_exists(
                spec.health_condition_id,
            )
            if not hc_exists:
                raise NotFoundError("Health condition not found", code="NOT_FOUND")
            rows = await self._repo.list_by_health_condition(
                health_condition_id=spec.health_condition_id,
            )
        return InstrumentIndicationsListResponse(
            indications=[self._to_out(r) for r in rows],
        )

    async def delete(self, indication_id: uuid.UUID) -> None:
        deleted = await self._repo.delete_by_id(indication_id)
        if not deleted:
            raise NotFoundError("Indication not found", code="NOT_FOUND")
        await self._session.commit()
