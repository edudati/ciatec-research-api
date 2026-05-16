"""Dependency providers for the matches module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.matches.service import MatchesService


def get_matches_service(db: AsyncSession = Depends(get_db)) -> MatchesService:
    return MatchesService(db)
