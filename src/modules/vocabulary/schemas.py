"""Pydantic contracts for vocabulary API."""

from src.modules.auth.schemas import CamelModel


class VocabularySchemeCreateIn(CamelModel):
    code: str
    name: str
    description: str | None = None


class VocabularySchemeOut(CamelModel):
    id: str
    code: str
    name: str
    description: str | None = None
    created_at: str


class VocabularySchemeListResponse(CamelModel):
    schemes: list[VocabularySchemeOut]


class VocabularyTermCreateIn(CamelModel):
    code: str
    label: str
    description: str | None = None
    sort_order: int | None = None


class VocabularyTermPatchIn(CamelModel):
    label: str | None = None
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class VocabularyTermOut(CamelModel):
    id: str
    scheme_id: str
    code: str
    label: str
    description: str | None = None
    is_active: bool
    sort_order: int
    created_at: str


class VocabularyTermListResponse(CamelModel):
    terms: list[VocabularyTermOut]
