"""Instrument indication HTTP routes under /api/v1/instruments/indications."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.instruments.deps import get_instrument_indications_service
from src.modules.instruments.schemas_indications import (
    InstrumentIndicationCreateIn,
    InstrumentIndicationOut,
    InstrumentIndicationsListResponse,
)
from src.modules.instruments.service_indications import InstrumentIndicationsService

indications_router = APIRouter(prefix="/indications", tags=["Instruments"])


@indications_router.get(
    "",
    response_model=InstrumentIndicationsListResponse,
    response_model_by_alias=True,
    summary="List instrument indications",
    description=(
        "Either pass instrumentType+instrumentId together, or healthConditionId alone. "
        "Mixing both modes returns 422."
    ),
    responses={
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def list_instrument_indications(
    service: InstrumentIndicationsService = Depends(get_instrument_indications_service),
    instrument_type: str | None = Query(
        None,
        alias="instrumentType",
        description="ASSESSMENT or QUESTIONNAIRE (requires instrumentId)",
    ),
    instrument_id: UUID | None = Query(None, alias="instrumentId"),
    health_condition_id: UUID | None = Query(None, alias="healthConditionId"),
) -> InstrumentIndicationsListResponse:
    return await service.list_filtered(
        instrument_type=instrument_type,
        instrument_id=instrument_id,
        health_condition_id=health_condition_id,
    )


@indications_router.post(
    "",
    response_model=InstrumentIndicationOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create instrument indication",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_instrument_indication(
    body: InstrumentIndicationCreateIn,
    service: InstrumentIndicationsService = Depends(get_instrument_indications_service),
) -> InstrumentIndicationOut:
    return await service.create(body)


@indications_router.delete(
    "/{indication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete instrument indication",
    dependencies=[Depends(require_admin)],
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def delete_instrument_indication(
    indication_id: UUID,
    service: InstrumentIndicationsService = Depends(get_instrument_indications_service),
) -> Response:
    await service.delete(indication_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
