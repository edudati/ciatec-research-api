"""Vocabulary business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from src.models.user import User
from src.models.vocabulary import VocabularyScheme, VocabularyTerm
from src.modules.vocabulary.repository import (
    CONDITION_SEVERITY_SCHEME_CODE,
    VocabularyRepository,
)
from src.modules.vocabulary.schemas import (
    VocabularySchemeCreateIn,
    VocabularySchemeListResponse,
    VocabularySchemeOut,
    VocabularyTermCreateIn,
    VocabularyTermListResponse,
    VocabularyTermOut,
    VocabularyTermPatchIn,
)


class VocabularyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = VocabularyRepository(session)

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    @staticmethod
    def _normalize_code(raw: str) -> str:
        s = raw.strip().upper()
        if not s:
            raise ValidationError("code is required", code="VALIDATION_ERROR")
        return s

    def _scheme_out(self, row: VocabularyScheme) -> VocabularySchemeOut:
        return VocabularySchemeOut(
            id=str(row.id),
            code=row.code,
            name=row.name,
            description=row.description,
            created_at=self._dt_iso(row.created_at),
        )

    def _term_out(self, row: VocabularyTerm) -> VocabularyTermOut:
        return VocabularyTermOut(
            id=str(row.id),
            scheme_id=str(row.scheme_id),
            code=row.code,
            label=row.label,
            description=row.description,
            is_active=row.is_active,
            sort_order=row.sort_order,
            created_at=self._dt_iso(row.created_at),
        )

    async def list_schemes(self) -> VocabularySchemeListResponse:
        rows = await self._repo.list_schemes()
        return VocabularySchemeListResponse(
            schemes=[self._scheme_out(r) for r in rows],
        )

    async def create_scheme(
        self,
        body: VocabularySchemeCreateIn,
    ) -> VocabularySchemeOut:
        code = self._normalize_code(body.code)
        if await self._repo.scheme_code_taken(code, exclude_id=None):
            raise ConflictError(
                "Vocabulary scheme code already in use",
                code="SCHEME_CODE_IN_USE",
            )
        row = VocabularyScheme(
            id=uuid.uuid4(),
            code=code,
            name=body.name.strip(),
            description=body.description,
        )
        self._repo.add_scheme(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._scheme_out(row)

    async def _get_scheme_or_404(self, scheme_id: uuid.UUID) -> VocabularyScheme:
        row = await self._repo.get_scheme_by_id(scheme_id)
        if row is None:
            raise NotFoundError("Vocabulary scheme not found", code="NOT_FOUND")
        return row

    async def list_terms(
        self,
        scheme_id: uuid.UUID,
        *,
        include_inactive: bool,
        requester: User | None,
    ) -> VocabularyTermListResponse:
        await self._get_scheme_or_404(scheme_id)
        if include_inactive:
            if requester is None or requester.role != UserRole.ADMIN.value:
                raise ForbiddenError(
                    "Admin access required for includeInactive",
                    code="FORBIDDEN",
                )
        rows = await self._repo.list_terms_for_scheme(
            scheme_id,
            active_only=not include_inactive,
        )
        return VocabularyTermListResponse(terms=[self._term_out(r) for r in rows])

    async def _raise_if_severity_term_in_use(self, term: VocabularyTerm) -> None:
        if term.scheme.code != CONDITION_SEVERITY_SCHEME_CODE:
            return
        n = await self._repo.count_participant_conditions_by_severity_code(term.code)
        if n > 0:
            raise ConflictError(
                "Vocabulary term is in use",
                code="VOCABULARY_TERM_IN_USE",
            )

    async def create_term(
        self,
        scheme_id: uuid.UUID,
        body: VocabularyTermCreateIn,
    ) -> VocabularyTermOut:
        await self._get_scheme_or_404(scheme_id)
        code = self._normalize_code(body.code)
        if await self._repo.term_code_taken_in_scheme(
            scheme_id,
            code,
            exclude_id=None,
        ):
            raise ConflictError(
                "Vocabulary term code already in use for this scheme",
                code="TERM_CODE_IN_USE",
            )
        sort_order = body.sort_order if body.sort_order is not None else 0
        row = VocabularyTerm(
            id=uuid.uuid4(),
            scheme_id=scheme_id,
            code=code,
            label=body.label.strip(),
            description=body.description,
            is_active=True,
            sort_order=sort_order,
        )
        self._repo.add_term(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._term_out(row)

    async def patch_term(
        self,
        term_id: uuid.UUID,
        body: VocabularyTermPatchIn,
    ) -> VocabularyTermOut:
        row = await self._repo.get_term_by_id(term_id)
        if row is None:
            raise NotFoundError("Vocabulary term not found", code="NOT_FOUND")
        data = body.model_dump(exclude_unset=True)
        was_active = row.is_active
        if "label" in data and data["label"] is not None:
            row.label = str(data["label"]).strip()
        if "description" in data:
            row.description = data["description"]
        if "sort_order" in data and data["sort_order"] is not None:
            row.sort_order = int(data["sort_order"])
        if "is_active" in data and data["is_active"] is not None:
            new_active = bool(data["is_active"])
            if was_active and not new_active:
                await self._raise_if_severity_term_in_use(row)
            row.is_active = new_active
        await self._session.commit()
        await self._session.refresh(row)
        return self._term_out(row)

    async def delete_term(self, term_id: uuid.UUID) -> None:
        row = await self._repo.get_term_by_id(term_id)
        if row is None:
            return
        if not row.is_active:
            return
        await self._raise_if_severity_term_in_use(row)
        row.is_active = False
        await self._session.commit()

    async def is_active_severity_code(self, code: str) -> bool:
        c = code.strip().upper()
        if not c:
            return False
        return await self._repo.is_active_term_in_scheme(
            scheme_code=CONDITION_SEVERITY_SCHEME_CODE,
            term_code=c,
        )
