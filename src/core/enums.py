"""Shared domain enumerations."""

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    PI = "PI"
    PARTICIPANT = "PARTICIPANT"
    PLAYER = "PLAYER"


class BiologicalSex(StrEnum):
    M = "M"
    F = "F"
    OTHER = "OTHER"


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
