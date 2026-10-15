
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier: str | None = None
    reporting_period: str | None = None
    activity: str | None = None
    quantity: float | None = None
    unit: str | None = None
    emissions_value: float | None = None

    source_filename: str
    source_type: str
    sheet_name: str | None = None
    row_number: int | None = None
    page_number: int | None = None

    raw_fields: dict[str, Any] = Field(default_factory=dict)


class DocumentExtractionResult(BaseModel):
    source_filename: str
    source_type: str
    records: list[DocumentRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
