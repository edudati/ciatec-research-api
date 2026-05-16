"""Match endpoints: preset, level, finish."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import get_access_user_id
from src.modules.matches.deps import get_matches_service
from src.modules.matches.schemas import (
    MatchFinishBody,
    MatchFinishOut,
    MatchLevelOut,
    MatchPresetOut,
)
from src.modules.matches.service import MatchesService

router = APIRouter(
    prefix="/api/v1/matches",
    tags=["Matches"],
    dependencies=[Depends(get_access_user_id)],
)


@router.get(
    "/preset",
    response_model=MatchPresetOut,
    summary="Preset for user and game",
    description=(
        "Returns (and seeds if missing) the user's preset and level summaries "
        "for a game."
    ),
)
async def get_match_preset(
    game_id: UUID = Query(..., description="Game UUID"),
    user_id: UUID = Depends(get_access_user_id),
    service: MatchesService = Depends(get_matches_service),
) -> MatchPresetOut:
    return await service.get_preset(user_id, game_id)


@router.get(
    "/level",
    response_model=MatchLevelOut,
    summary="Level config for preset",
    description="Returns a single active level (including config) scoped to a preset.",
)
async def get_match_level(
    preset_id: UUID = Query(...),
    level_id: UUID = Query(...),
    service: MatchesService = Depends(get_matches_service),
) -> MatchLevelOut:
    return await service.get_level(preset_id, level_id)


@router.post(
    "/{match_id}/finish",
    response_model=MatchFinishOut,
    summary="Finish match",
    description=(
        "Stores match result once. Re-send the same Idempotency-Key and body "
        "for safe retries (200). Finishing again without a matching key returns 409. "
        "When the daily session is linked to an enrollment, the first successful "
        "finish (201) also records a GAME_SESSION timeline event (system, no executor)."
    ),
    responses={
        200: {"description": "Idempotent replay", "model": MatchFinishOut},
        201: {"description": "Result stored", "model": MatchFinishOut},
        409: {
            "description": "Conflict (already finished or idempotency mismatch)",
            "model": ApiErrorResponse,
        },
    },
)
async def finish_match(
    match_id: UUID,
    payload: MatchFinishBody,
    user_id: UUID = Depends(get_access_user_id),
    service: MatchesService = Depends(get_matches_service),
    idempotency_key: str | None = Header(default=None, alias="idempotency-key"),
) -> JSONResponse:
    result = await service.finish_match(user_id, match_id, payload, idempotency_key)
    return JSONResponse(
        status_code=result.status_code,
        content=result.body.model_dump(mode="json"),
    )
