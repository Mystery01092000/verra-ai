"""Wire schemas for the ingestion API (camelCase on the wire)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

IngestStatus = Literal["parsed", "needs_review", "unsupported"]


class _CamelBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class IngestRequest(_CamelBase):
    """Ingest a text document or a pre-extracted JSON payload."""

    document_id: str | None = None
    tenant_id: str | None = None
    content: str = Field(min_length=1)
    content_type: Literal["text", "json"] = "text"
    doc_type: str | None = None


class FieldMeta(_CamelBase):
    """Provenance for one extracted field."""

    confidence: float = Field(ge=0.0, le=1.0)
    section: str | None = None


class IngestResponse(_CamelBase):
    """Classification + extraction result with the human-review gate status."""

    document_id: str
    doc_type: str
    classification_confidence: float = Field(ge=0.0, le=1.0)
    extracted: dict[str, Any] = {}
    field_meta: dict[str, FieldMeta] = {}
    low_confidence_fields: list[str] = []
    flags: list[str] = []
    status: IngestStatus
