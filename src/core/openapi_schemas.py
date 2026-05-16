"""Pydantic models reused only for OpenAPI documentation (error envelopes)."""

from typing import Literal

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    """Standard JSON error body returned by global exception handlers."""

    success: Literal[False] = False
    code: str
    message: str
