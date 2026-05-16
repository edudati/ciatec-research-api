"""Vocabulary HTTP routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import get_optional_active_user, require_admin
from src.modules.vocabulary.deps import get_vocabulary_service
from src.modules.vocabulary.schemas import (
    VocabularySchemeCreateIn,
    VocabularySchemeListResponse,
    VocabularySchemeOut,
    VocabularyTermCreateIn,
    VocabularyTermListResponse,
    VocabularyTermOut,
    VocabularyTermPatchIn,
)
from src.modules.vocabulary.service import VocabularyService

router = APIRouter(prefix="/api/v1/vocabulary", tags=["Vocabulary"])


@router.get(
    "/schemes",
    response_model=VocabularySchemeListResponse,
    response_model_by_alias=True,
    summary="List vocabulary schemes",
)
async def list_schemes(
    service: VocabularyService = Depends(get_vocabulary_service),
) -> VocabularySchemeListResponse:
    return await service.list_schemes()


@router.post(
    "/schemes",
    response_model=VocabularySchemeOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create vocabulary scheme",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_scheme(
    body: VocabularySchemeCreateIn,
    service: VocabularyService = Depends(get_vocabulary_service),
) -> VocabularySchemeOut:
    return await service.create_scheme(body)


@router.get(
    "/schemes/{scheme_id}/terms",
    response_model=VocabularyTermListResponse,
    response_model_by_alias=True,
    summary="List terms for a vocabulary scheme",
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_terms(
    scheme_id: UUID,
    service: VocabularyService = Depends(get_vocabulary_service),
    requester: User | None = Depends(get_optional_active_user),
    include_inactive: bool = Query(False, alias="includeInactive"),
) -> VocabularyTermListResponse:
    return await service.list_terms(
        scheme_id,
        include_inactive=include_inactive,
        requester=requester,
    )


@router.post(
    "/schemes/{scheme_id}/terms",
    response_model=VocabularyTermOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create vocabulary term",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_term(
    scheme_id: UUID,
    body: VocabularyTermCreateIn,
    service: VocabularyService = Depends(get_vocabulary_service),
) -> VocabularyTermOut:
    return await service.create_term(scheme_id, body)


@router.patch(
    "/terms/{term_id}",
    response_model=VocabularyTermOut,
    response_model_by_alias=True,
    summary="Update vocabulary term",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_term(
    term_id: UUID,
    body: VocabularyTermPatchIn,
    service: VocabularyService = Depends(get_vocabulary_service),
) -> VocabularyTermOut:
    return await service.patch_term(term_id, body)


@router.delete(
    "/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate vocabulary term",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def delete_term(
    term_id: UUID,
    service: VocabularyService = Depends(get_vocabulary_service),
) -> Response:
    await service.delete_term(term_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
