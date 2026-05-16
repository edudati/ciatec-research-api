"""Dependency providers for vocabulary."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.vocabulary.service import VocabularyService


def get_vocabulary_service(
    db: AsyncSession = Depends(get_db),
) -> VocabularyService:
    return VocabularyService(db)
