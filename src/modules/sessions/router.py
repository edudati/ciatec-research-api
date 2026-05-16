"""Session endpoints: start daily session, current session, create match."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.modules.auth.deps import get_access_user_id
from src.modules.matches.deps import get_matches_service
from src.modules.matches.service import MatchesService
from src.modules.sessions.deps import get_sessions_service
from src.modules.sessions.schemas import (
    CreateMatchBody,
    CurrentSessionResponse,
    MatchCreatedOut,
    SessionOut,
)
from src.modules.sessions.service import SessionsService

router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"],
    dependencies=[Depends(get_access_user_id)],
)


@router.post(
    "/start",
    response_model=SessionOut,
    summary="Start daily session",
    description=(
        "Creates one session per UTC calendar day for the user, "
        "or returns the existing one."
    ),
    responses={
        200: {"description": "Daily session already exists", "model": SessionOut},
        201: {"description": "Daily session created", "model": SessionOut},
    },
)
async def start_daily_session(
    response: Response,
    user_id: UUID = Depends(get_access_user_id),
    service: SessionsService = Depends(get_sessions_service),
) -> SessionOut:
    body, created = await service.start(user_id)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return body


@router.get(
    "/current",
    response_model=CurrentSessionResponse,
    summary="Current daily session",
    description="Returns today's session for the user, or null if none exists yet.",
)
async def get_current_session(
    user_id: UUID = Depends(get_access_user_id),
    service: SessionsService = Depends(get_sessions_service),
) -> CurrentSessionResponse:
    return await service.current(user_id)


@router.post(
    "/matches",
    response_model=MatchCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create match",
    description=(
        "Creates a match in today's session (creating the session if needed). "
        "Optional enrollment_id binds the daily session to a research enrollment "
        "(participant must own the enrollment); all matches that day then share "
        "that research context."
    ),
)
async def create_match(
    payload: CreateMatchBody,
    user_id: UUID = Depends(get_access_user_id),
    sessions: SessionsService = Depends(get_sessions_service),
    matches: MatchesService = Depends(get_matches_service),
) -> MatchCreatedOut:
    return await sessions.create_match(user_id, payload, matches)
