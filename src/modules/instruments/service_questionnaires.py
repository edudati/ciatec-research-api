"""Questionnaire template and question item business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.question_item import QuestionItem
from src.models.questionnaire_template import QuestionnaireTemplate
from src.modules.instruments.repository_questionnaires import QuestionnairesRepository
from src.modules.instruments.schemas import parse_order
from src.modules.instruments.schemas_questionnaires import (
    QuestionItemCreateIn,
    QuestionItemOut,
    QuestionItemsListResponse,
    QuestionItemUpdateIn,
    QuestionnaireTemplateCreateIn,
    QuestionnaireTemplateOut,
    QuestionnaireTemplatesListResponse,
    QuestionnaireTemplateUpdateIn,
    parse_questionnaire_template_list_sort,
)
from src.modules.vocabulary.repository import (
    ASSESSMENT_TYPE_SCHEME_CODE,
    VocabularyRepository,
)

QUESTION_ITEM_TYPES = frozenset(
    {
        "SCALE",
        "MULTIPLE_CHOICE",
        "TEXT",
        "BOOLEAN",
        "NUMBER",
    }
)


class QuestionnairesService:
    _TEMPLATE_SORT_COLUMNS = {
        "createdAt": QuestionnaireTemplate.created_at,
        "name": QuestionnaireTemplate.name,
        "code": QuestionnaireTemplate.code,
        "updatedAt": QuestionnaireTemplate.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = QuestionnairesRepository(session)
        self._vocab = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_template_out(self, row: QuestionnaireTemplate) -> QuestionnaireTemplateOut:
        return QuestionnaireTemplateOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            description=row.description,
            self_report=row.self_report,
            template_type=row.assessment_type,
            version=row.version,
            is_active=row.is_active,
            metadata=dict(row.template_metadata),
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    def _to_item_out(self, row: QuestionItem) -> QuestionItemOut:
        opts = dict(row.item_options) if row.item_options is not None else None
        return QuestionItemOut(
            id=str(row.id),
            questionnaire_template_id=str(row.questionnaire_template_id),
            code=row.code,
            label=row.label,
            item_type=row.item_type,
            display_order=row.display_order,
            options=opts,
            is_required=row.is_required,
            created_at=self._dt_iso(row.created_at),
            updated_at=self._dt_iso(row.updated_at),
        )

    async def _assert_valid_template_type(self, term_code: str) -> None:
        ok = await self._vocab.is_active_term_in_scheme(
            scheme_code=ASSESSMENT_TYPE_SCHEME_CODE,
            term_code=term_code,
        )
        if not ok:
            raise ValidationError(
                "Invalid or inactive questionnaire template type",
                code="ASSESSMENT_TYPE_INVALID",
            )

    @staticmethod
    def _assert_valid_item_type(term_code: str) -> None:
        if term_code not in QUESTION_ITEM_TYPES:
            raise ValidationError(
                "Invalid question item type",
                code="QUESTION_ITEM_TYPE_INVALID",
            )

    async def create_template(
        self,
        body: QuestionnaireTemplateCreateIn,
    ) -> QuestionnaireTemplateOut:
        await self._assert_valid_template_type(body.template_type)
        code = body.code
        if await self._repo.template_code_taken(code, exclude_id=None):
            raise ConflictError(
                "Questionnaire template code already in use",
                code="CODE_IN_USE",
            )
        row = QuestionnaireTemplate(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            description=body.description,
            self_report=body.self_report,
            assessment_type=body.template_type,
            version=body.version.strip(),
            is_active=body.is_active,
            template_metadata=body.metadata,
        )
        self._repo.add_template(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_template_out(row)

    async def list_templates_public(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        order: str,
    ) -> QuestionnaireTemplatesListResponse:
        sort_key = parse_questionnaire_template_list_sort(sort)
        sort_col = self._TEMPLATE_SORT_COLUMNS[sort_key]
        total = await self._repo.count_templates_public()
        rows = await self._repo.list_templates_page_public(
            page=page,
            page_size=page_size,
            sort_column=sort_col,
            order_desc=parse_order(order),
        )
        items = [self._to_template_out(r) for r in rows]
        return QuestionnaireTemplatesListResponse(
            questionnaires=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_template_public(
        self,
        template_id: uuid.UUID,
    ) -> QuestionnaireTemplateOut:
        row = await self._repo.get_template_public_by_id(template_id)
        if row is None:
            raise NotFoundError("Questionnaire template not found", code="NOT_FOUND")
        return self._to_template_out(row)

    async def update_template(
        self,
        template_id: uuid.UUID,
        body: QuestionnaireTemplateUpdateIn,
    ) -> QuestionnaireTemplateOut:
        row = await self._repo.get_template_by_id(template_id)
        if row is None:
            raise NotFoundError("Questionnaire template not found", code="NOT_FOUND")
        if body.template_type is not None:
            await self._assert_valid_template_type(body.template_type)
        if body.code is not None and body.code != row.code:
            if await self._repo.template_code_taken(body.code, exclude_id=row.id):
                raise ConflictError(
                    "Questionnaire template code already in use",
                    code="CODE_IN_USE",
                )
            row.code = body.code
        if body.name is not None:
            row.name = body.name.strip()
        if body.description is not None:
            row.description = body.description
        if body.self_report is not None:
            row.self_report = body.self_report
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
        return self._to_template_out(row)

    async def list_items_public(
        self,
        template_id: uuid.UUID,
    ) -> QuestionItemsListResponse:
        template = await self._repo.get_template_public_by_id(template_id)
        if template is None:
            raise NotFoundError("Questionnaire template not found", code="NOT_FOUND")
        rows = await self._repo.list_items_for_template_ordered(template_id)
        return QuestionItemsListResponse(
            items=[self._to_item_out(r) for r in rows],
        )

    async def create_item(
        self,
        template_id: uuid.UUID,
        body: QuestionItemCreateIn,
    ) -> QuestionItemOut:
        template = await self._repo.get_template_by_id(template_id)
        if template is None:
            raise NotFoundError("Questionnaire template not found", code="NOT_FOUND")
        self._assert_valid_item_type(body.item_type)
        if await self._repo.item_code_taken(
            template_id, body.code, exclude_item_id=None
        ):
            raise ConflictError(
                "Question item code already in use in this template",
                code="QUESTION_ITEM_CODE_IN_USE",
            )
        if await self._repo.item_order_taken(
            template_id,
            body.display_order,
            exclude_item_id=None,
        ):
            raise ConflictError(
                "Question item order already in use in this template",
                code="QUESTION_ITEM_ORDER_IN_USE",
            )
        row = QuestionItem(
            id=uuid.uuid4(),
            questionnaire_template_id=template_id,
            code=body.code,
            label=body.label.strip(),
            item_type=body.item_type,
            display_order=body.display_order,
            item_options=body.options,
            is_required=body.is_required,
        )
        self._repo.add_item(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_item_out(row)

    async def update_item(
        self,
        template_id: uuid.UUID,
        item_id: uuid.UUID,
        body: QuestionItemUpdateIn,
    ) -> QuestionItemOut:
        row = await self._repo.get_item_by_template_and_id(template_id, item_id)
        if row is None:
            raise NotFoundError("Question item not found", code="NOT_FOUND")
        if body.item_type is not None:
            self._assert_valid_item_type(body.item_type)
        if body.code is not None and body.code != row.code:
            if await self._repo.item_code_taken(
                template_id,
                body.code,
                exclude_item_id=row.id,
            ):
                raise ConflictError(
                    "Question item code already in use in this template",
                    code="QUESTION_ITEM_CODE_IN_USE",
                )
            row.code = body.code
        if body.label is not None:
            row.label = body.label.strip()
        if body.item_type is not None:
            row.item_type = body.item_type
        if body.display_order is not None and body.display_order != row.display_order:
            if await self._repo.item_order_taken(
                template_id,
                body.display_order,
                exclude_item_id=row.id,
            ):
                raise ConflictError(
                    "Question item order already in use in this template",
                    code="QUESTION_ITEM_ORDER_IN_USE",
                )
            row.display_order = body.display_order
        if body.options is not None:
            row.item_options = body.options
        if body.is_required is not None:
            row.is_required = body.is_required
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_item_out(row)

    async def delete_item(self, template_id: uuid.UUID, item_id: uuid.UUID) -> None:
        row = await self._repo.get_item_by_template_and_id(template_id, item_id)
        if row is None:
            raise NotFoundError("Question item not found", code="NOT_FOUND")
        await self._repo.delete_item(row)
        await self._session.commit()
