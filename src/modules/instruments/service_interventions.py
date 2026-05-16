"""Intervention template business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.intervention_template import InterventionTemplate
from src.modules.instruments.repository_interventions import (
    InterventionTemplatesRepository,
)
from src.modules.instruments.schemas import parse_order
from src.modules.instruments.schemas_interventions import (
    InterventionTemplateCreateIn,
    InterventionTemplateOut,
    InterventionTemplatesListResponse,
    InterventionTemplateUpdateIn,
    parse_intervention_template_list_sort,
)
from src.modules.vocabulary.repository import (
    INTERVENTION_TYPE_SCHEME_CODE,
    VocabularyRepository,
)


class InterventionTemplatesService:
    _SORT_COLUMNS = {
        "createdAt": InterventionTemplate.created_at,
        "name": InterventionTemplate.name,
        "code": InterventionTemplate.code,
        "updatedAt": InterventionTemplate.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InterventionTemplatesRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: InterventionTemplate) -> InterventionTemplateOut:
        return InterventionTemplateOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            intervention_type=row.intervention_type,
            game_id=str(row.game_id) if row.game_id is not None else None,
            metadata=dict(row.template_metadata),
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _assert_valid_intervention_type(self, term_code: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=INTERVENTION_TYPE_SCHEME_CODE,
            term_code=term_code,
        )
        if not ok:
            raise ValidationError(
                "Invalid or inactive intervention type",
                code="INTERVENTION_TYPE_INVALID",
            )

    async def _assert_game_usable(self, game_id: uuid.UUID) -> None:
        if not await self._repo.usable_game_exists(game_id):
            raise NotFoundError("Game not found", code="NOT_FOUND")

    async def create(
        self,
        body: InterventionTemplateCreateIn,
    ) -> InterventionTemplateOut:
        await self._assert_valid_intervention_type(body.intervention_type)
        code = body.code
        if await self._repo.code_taken(code, exclude_id=None):
            raise ConflictError(
                "Intervention template code already in use",
                code="CODE_IN_USE",
            )
        game_id = body.game_id
        if game_id is not None:
            await self._assert_game_usable(game_id)
        row = InterventionTemplate(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            intervention_type=body.intervention_type,
            game_id=game_id,
            template_metadata=body.metadata,
        )
        self._repo.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        order: str,
    ) -> InterventionTemplatesListResponse:
        sort_key = parse_intervention_template_list_sort(sort)
        sort_col = self._SORT_COLUMNS[sort_key]
        total = await self._repo.count_all()
        rows = await self._repo.list_page(
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items = [self._to_out(r) for r in rows]
        return InterventionTemplatesListResponse(
            interventions=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, template_id: uuid.UUID) -> InterventionTemplateOut:
        row = await self._repo.get_by_id(template_id)
        if row is None:
            raise NotFoundError("Intervention template not found", code="NOT_FOUND")
        return self._to_out(row)

    async def update(
        self,
        template_id: uuid.UUID,
        body: InterventionTemplateUpdateIn,
    ) -> InterventionTemplateOut:
        row = await self._repo.get_by_id(template_id)
        if row is None:
            raise NotFoundError("Intervention template not found", code="NOT_FOUND")
        if body.intervention_type is not None:
            await self._assert_valid_intervention_type(body.intervention_type)
        if body.code is not None and body.code != row.code:
            if await self._repo.code_taken(body.code, exclude_id=row.id):
                raise ConflictError(
                    "Intervention template code already in use",
                    code="CODE_IN_USE",
                )
            row.code = body.code
        if body.name is not None:
            row.name = body.name.strip()
        if body.intervention_type is not None:
            row.intervention_type = body.intervention_type
        if "game_id" in body.model_fields_set:
            gid = body.game_id
            if gid is not None:
                await self._assert_game_usable(gid)
            row.game_id = gid
        if body.metadata is not None:
            row.template_metadata = body.metadata
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)
