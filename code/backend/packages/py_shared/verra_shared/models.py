"""Shared domain + orchestrator types (mirror docs/adr + System Design ERD)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TenantType(str, Enum):
    firm = "firm"
    company = "company"
    individual = "individual"


class ModuleName(str, Enum):
    tax = "tax"
    books = "books"
    audit = "audit"
    compliance = "compliance"
    assistant = "assistant"


class RunStatus(str, Enum):
    planned = "planned"
    routed = "routed"
    executing = "executing"
    verifying = "verifying"
    awaiting_approval = "awaiting_approval"
    done = "done"
    failed = "failed"


class Budget(BaseModel):
    max_usd: float | None = None
    max_tokens: int | None = None


class RunRequest(BaseModel):
    tenant_id: str
    module: ModuleName
    capability: str = Field(examples=["tax_analysis"])
    input: dict = {}
    context_refs: list[str] = []
    budget: Budget | None = None
    idempotency_key: str | None = None


class Citation(BaseModel):
    doc_id: str
    page: int | None = None
    rule: str | None = None


class Cost(BaseModel):
    usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0


class RunResult(BaseModel):
    run_id: str
    status: RunStatus
    output: object | None = None
    citations: list[Citation] = []
    cost: Cost = Cost()
    receipt_id: str | None = None
