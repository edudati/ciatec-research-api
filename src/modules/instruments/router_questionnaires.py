"""Questionnaire template HTTP routes under /api/v1/instruments/questionnaires."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.instruments.deps import get_questionnaires_service
from src.modules.instruments.schemas_questionnaires import (
    QuestionItemCreateIn,
    QuestionItemOut,
    QuestionItemsListResponse,
    QuestionItemUpdateIn,
    QuestionnaireTemplateCreateIn,
    QuestionnaireTemplateOut,
    QuestionnaireTemplatesListResponse,
    QuestionnaireTemplateUpdateIn,
)
from src.modules.instruments.service_questionnaires import QuestionnairesService

questionnaires_router = APIRouter(prefix="/questionnaires", tags=["Instruments"])

SortField = Literal["createdAt", "name", "code", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@questionnaires_router.get(
    "",
    response_model=QuestionnaireTemplatesListResponse,
    response_model_by_alias=True,
    summary="List questionnaire templates",
    description="Public list: active templates only.",
)
async def list_questionnaire_templates(
    service: QuestionnairesService = Depends(get_questionnaires_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, name, code, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> QuestionnaireTemplatesListResponse:
    return await service.list_templates_public(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@questionnaires_router.get(
    "/{template_id}",
    response_model=QuestionnaireTemplateOut,
    response_model_by_alias=True,
    summary="Get questionnaire template by id",
    description="Public: active templates only.",
    responses={404: {"model": ApiErrorResponse}},
)
async def get_questionnaire_template(
    template_id: UUID,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionnaireTemplateOut:
    return await service.get_template_public(template_id)


@questionnaires_router.post(
    "",
    response_model=QuestionnaireTemplateOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create questionnaire template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_questionnaire_template(
    body: QuestionnaireTemplateCreateIn,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionnaireTemplateOut:
    return await service.create_template(body)


@questionnaires_router.patch(
    "/{template_id}",
    response_model=QuestionnaireTemplateOut,
    response_model_by_alias=True,
    summary="Update questionnaire template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_questionnaire_template(
    template_id: UUID,
    body: QuestionnaireTemplateUpdateIn,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionnaireTemplateOut:
    return await service.update_template(template_id, body)


@questionnaires_router.get(
    "/{template_id}/items",
    response_model=QuestionItemsListResponse,
    response_model_by_alias=True,
    summary="List question items for a template",
    description="Public when the template is active.",
    responses={404: {"model": ApiErrorResponse}},
)
async def list_question_items(
    template_id: UUID,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionItemsListResponse:
    return await service.list_items_public(template_id)


@questionnaires_router.post(
    "/{template_id}/items",
    response_model=QuestionItemOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create question item",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_question_item(
    template_id: UUID,
    body: QuestionItemCreateIn,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionItemOut:
    return await service.create_item(template_id, body)


@questionnaires_router.patch(
    "/{template_id}/items/{item_id}",
    response_model=QuestionItemOut,
    response_model_by_alias=True,
    summary="Update question item",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_question_item(
    template_id: UUID,
    item_id: UUID,
    body: QuestionItemUpdateIn,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> QuestionItemOut:
    return await service.update_item(template_id, item_id, body)


@questionnaires_router.delete(
    "/{template_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete question item",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def delete_question_item(
    template_id: UUID,
    item_id: UUID,
    service: QuestionnairesService = Depends(get_questionnaires_service),
) -> Response:
    await service.delete_item(template_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
