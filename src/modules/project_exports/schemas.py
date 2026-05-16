"""Pydantic contracts for project timeline export."""

from typing import Literal

from pydantic import Field

from src.modules.auth.schemas import CamelModel

ExportFormat = Literal["csv", "json"]


class ProjectExportQueuedOut(CamelModel):
    job_id: str = Field(serialization_alias="jobId")
    status: Literal["queued"] = "queued"


class ProjectExportJobStatusOut(CamelModel):
    job_id: str = Field(serialization_alias="jobId")
    status: str
    ready: bool = Field(description="True when export file can be downloaded")
    row_count: int | None = Field(default=None, serialization_alias="rowCount")
    error_code: str | None = Field(default=None, serialization_alias="errorCode")
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
