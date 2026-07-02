"""Wire models for orchestrator-local endpoints (camelCase, matching verra_shared style)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from verra_shared import RunStatus


class _ApiBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ApprovalRequest(_ApiBase):
    approver: str = Field(min_length=1)
    note: str | None = None


class RunSummary(_ApiBase):
    run_id: str
    status: RunStatus
    capability: str
    created_at: str
    citations_count: int
    summary: str | None = None
