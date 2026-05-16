"""Dependency providers for project members."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_members.service import ProjectMembersService


def get_project_members_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectMembersService:
    return ProjectMembersService(db)
