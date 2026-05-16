"""Health condition business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.models.health_condition import HealthCondition
from src.modules.health_conditions.repository import HealthConditionsRepository
from src.modules.health_conditions.schemas import (
    HealthConditionCreateIn,
    HealthConditionListResponse,
    HealthConditionOut,
    HealthConditionUpdateIn,
    parse_health_condition_list_sort,
    parse_order,
)


class HealthConditionsService:
    _SORT_COLUMNS = {
        "createdAt": HealthCondition.created_at,
        "name": HealthCondition.name,
        "code": HealthCondition.code,
        "updatedAt": HealthCondition.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = HealthConditionsRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: HealthCondition) -> HealthConditionOut:
        return HealthConditionOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            description=row.description,
            category=row.category,
            is_active=row.is_active,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def create(self, body: HealthConditionCreateIn) -> HealthConditionOut:
        code = body.code
        if await self._repo.code_taken(code, exclude_id=None):
            raise ConflictError(
                "Health condition code already in use",
                code="CODE_IN_USE",
            )
        row = HealthCondition(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            description=body.description,
            category=body.category.strip() if body.category else None,
            is_active=body.is_active,
        )
        self._repo.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def list_conditions(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None,
        sort: str,
        order: str,
        public_only: bool,
    ) -> HealthConditionListResponse:
        sort_key = parse_health_condition_list_sort(sort)
        sort_col = self._SORT_COLUMNS[sort_key]
        total = await self._repo.count_list(category=category, public_only=public_only)
        rows = await self._repo.list_page(
            page=page,
            page_size=page_size,
            category=category,
            public_only=public_only,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items = [self._to_out(r) for r in rows]
        return HealthConditionListResponse(
            conditions=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_public(self, hc_id: uuid.UUID) -> HealthConditionOut:
        row = await self._repo.get_public_by_id(hc_id)
        if row is None:
            raise NotFoundError("Health condition not found", code="NOT_FOUND")
        return self._to_out(row)

    async def update(
        self,
        hc_id: uuid.UUID,
        body: HealthConditionUpdateIn,
    ) -> HealthConditionOut:
        row = await self._repo.get_active_row_for_mutation(hc_id)
        if row is None:
            raise NotFoundError("Health condition not found", code="NOT_FOUND")
        if body.code is not None and body.code != row.code:
            if await self._repo.code_taken(body.code, exclude_id=row.id):
                raise ConflictError(
                    "Health condition code already in use",
                    code="CODE_IN_USE",
                )
            row.code = body.code
        if body.name is not None:
            row.name = body.name.strip()
        if body.description is not None:
            row.description = body.description
        if body.category is not None:
            row.category = body.category.strip() if body.category else None
        if body.is_active is not None:
            row.is_active = body.is_active
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)

    async def soft_delete(self, hc_id: uuid.UUID) -> None:
        row = await self._repo.get_active_row_for_mutation(hc_id)
        if row is None:
            return
        n_links = await self._repo.count_participant_links(hc_id)
        if n_links > 0:
            raise ConflictError(
                "Health condition is linked to a participant",
                code="HEALTH_CONDITION_IN_USE",
            )
        now = datetime.now(UTC)
        row.deleted_at = now
        row.is_active = False
        await self._session.commit()
