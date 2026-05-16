"""Normalize questionnaire answer payloads (shared by mediated and self-report)."""

from __future__ import annotations

from typing import Any

from src.core.exceptions import ValidationError

AnswerValue = str | int | float | bool | list[Any]


def json_leaf(value: Any) -> Any:
    if isinstance(value, dict):
        raise ValidationError(
            "Nested objects are not allowed in answer values",
            code="QUESTION_ANSWER_VALUE_INVALID",
        )
    if isinstance(value, list):
        return [json_leaf(x) for x in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, str | int | float):
        return value
    if value is None:
        return value
    raise ValidationError(
        "Unsupported JSON type in answer value",
        code="QUESTION_ANSWER_VALUE_INVALID",
    )


def normalize_answer_value(value: AnswerValue) -> Any:
    if isinstance(value, dict):
        raise ValidationError(
            "Answer value must not be an object",
            code="QUESTION_ANSWER_VALUE_INVALID",
        )
    if isinstance(value, list):
        return [json_leaf(x) for x in value]
    return json_leaf(value)
