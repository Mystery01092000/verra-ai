"""Shared domain + orchestrator types (mirror docs/adr + System Design ERD)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _VerraBase(BaseModel):
    """Base model that serializes to camelCase on the wire while keeping snake_case in Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TenantType(StrEnum):
    firm = "firm"
    company = "company"
    individual = "individual"


class ModuleName(StrEnum):
    tax = "tax"
    books = "books"
    audit = "audit"
    compliance = "compliance"
    assistant = "assistant"


class RunStatus(StrEnum):
    planned = "planned"
    routed = "routed"
    executing = "executing"
    verifying = "verifying"
    awaiting_approval = "awaiting_approval"
    done = "done"
    failed = "failed"


class Budget(_VerraBase):
    max_usd: float | None = None
    max_tokens: int | None = None


class RunRequest(_VerraBase):
    tenant_id: str
    module: ModuleName
    capability: str = Field(examples=["tax_analysis"])
    input: dict[str, object] = {}
    context_refs: list[str] = []
    budget: Budget | None = None
    idempotency_key: str | None = None


class Citation(_VerraBase):
    doc_id: str
    page: int | None = None
    rule: str | None = None


class Cost(_VerraBase):
    usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0


class RunResult(_VerraBase):
    run_id: str
    status: RunStatus
    output: object | None = None
    citations: list[Citation] = []
    cost: Cost = Cost()
    receipt_id: str | None = None


class RunAccepted(_VerraBase):
    run_id: str
    stream: str
