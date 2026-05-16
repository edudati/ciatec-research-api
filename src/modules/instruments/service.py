"""Assessment template business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.assessment_template import AssessmentTemplate
from src.modules.instruments.repository import AssessmentTemplatesRepository
from src.modules.instruments.schemas import (
    AssessmentTemplateCreateIn,
    AssessmentTemplateOut,
    AssessmentTemplatesListResponse,
    AssessmentTemplateUpdateIn,
    parse_assessment_template_list_sort,
    parse_order,
)
from src.modules.vocabulary.repository import (
    ASSESSMENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)


class AssessmentTemplatesService:
    _SORT_COLUMNS = {
        "createdAt": AssessmentTemplate.created_at,
        "name": AssessmentTemplate.name,
        "code": AssessmentTemplate.code,
        "updatedAt": AssessmentTemplate.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AssessmentTemplatesRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: AssessmentTemplate) -> AssessmentTemplateOut:
        return AssessmentTemplateOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            description=row.description,
            template_type=row.assessment_type,
            version=row.version,
            is_active=row.is_active,
            metadata=dict(row.template_metadata),
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _assert_valid_assessment_type(self, term_code: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=ASSESSMENT_TYPE_SCHEME_CODE,
            term_code=term_code,
        )
        if not ok:
            raise ValidationError(
                "Invalid or inactive assessment type",
                code="ASSESSMENT_TYPE_INVALID",
            )

    async def create(self, body: AssessmentTemplateCreateIn) -> AssessmentTemplateOut:
        await self._assert_valid_assessment_type(body.template_type)
        code = body.code
        if await self._repo.code_taken(code, exclude_id=None):
            raise ConflictError(
                "Assessment template code already in use",
                code="CODE_IN_USE",
            )
        row = AssessmentTemplate(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            description=body.description,
            assessment_type=body.template_type,
            version=body.version.strip(),
            is_active=body.is_active,
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
    ) -> AssessmentTemplatesListResponse:
        sort_key = parse_assessment_template_list_sort(sort)
        sort_col = self._SORT_COLUMNS[sort_key]
        total = await self._repo.count_list_public()
        rows = await self._repo.list_page_public(
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items = [self._to_out(r) for r in rows]
        return AssessmentTemplatesListResponse(
            assessments=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_public(self, template_id: uuid.UUID) -> AssessmentTemplateOut:
        row = await self._repo.get_public_by_id(template_id)
        if row is None:
            raise NotFoundError("Assessment template not found", code="NOT_FOUND")
        return self._to_out(row)

    async def update(
        self,
        template_id: uuid.UUID,
        body: AssessmentTemplateUpdateIn,
    ) -> AssessmentTemplateOut:
        row = await self._repo.get_for_admin_mutation(template_id)
        if row is None:
            raise NotFoundError("Assessment template not found", code="NOT_FOUND")
        if body.template_type is not None:
            await self._assert_valid_assessment_type(body.template_type)
        if body.code is not None and body.code != row.code:
            if await self._repo.code_taken(body.code, exclude_id=row.id):
                raise ConflictError(
                    "Assessment template code already in use",
                    code="CODE_IN_USE",
                )
            row.code = body.code
        if body.name is not None:
            row.name = body.name.strip()
        if body.description is not None:
            row.description = body.description
        if body.template_type is not None:
            row.assessment_type = body.template_type
        if body.version is not None:
            row.version = body.version.strip()
        if body.is_active is not None:
            row.is_active = body.is_active
        if body.metadata is not None:
            row.template_metadata = body.metadata
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_out(row)
