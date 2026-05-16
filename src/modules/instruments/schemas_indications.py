"""Pydantic contracts for instrument indications (camelCase JSON)."""

from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, Field, field_validator

from src.modules.auth.schemas import CamelModel

InstrumentKind = Literal["ASSESSMENT", "QUESTIONNAIRE"]


class InstrumentIndicationCreateIn(CamelModel):
    instrument_kind: InstrumentKind = Field(
        validation_alias=AliasChoices("instrumentType", "instrument_type"),
        serialization_alias="instrumentType",
    )
    instrument_id: UUID = Field(
        validation_alias=AliasChoices("instrumentId"),
    )
    health_condition_id: UUID = Field(
        validation_alias=AliasChoices("healthConditionId"),
    )
    indication_type: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("indicationType", "indication_type"),
        serialization_alias="indicationType",
    )

    @field_validator("instrument_kind", mode="before")
    @classmethod
    def normalize_instrument_kind(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("indication_type")
    @classmethod
    def normalize_indication_type(cls, v: str) -> str:
        return v.strip().upper()


class InstrumentIndicationOut(CamelModel):
    id: str
    instrument_kind: InstrumentKind = Field(
        validation_alias=AliasChoices("instrumentType", "instrument_type"),
        serialization_alias="instrumentType",
    )
    instrument_id: str = Field(serialization_alias="instrumentId")
    health_condition_id: str = Field(serialization_alias="healthConditionId")
    indication_type: str = Field(
        validation_alias=AliasChoices("indicationType", "indication_type"),
        serialization_alias="indicationType",
    )
    created_at: str = Field(serialization_alias="createdAt")


class InstrumentIndicationsListResponse(CamelModel):
    indications: list[InstrumentIndicationOut]
