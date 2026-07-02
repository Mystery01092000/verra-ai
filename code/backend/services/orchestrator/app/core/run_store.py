"""In-memory run state store (immutable snapshots). TODO: back with Temporal/Postgres."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any

from verra_shared import RunStatus

# Rough blended token pricing used for cost accounting until billing lands.
_USD_PER_1K_INPUT_TOKENS = 0.003
_USD_PER_1K_OUTPUT_TOKENS = 0.015


@dataclass(frozen=True)
class RunState:
    """Immutable snapshot of a run; every transition produces a new instance."""

    run_id: str
    tenant_id: str
    module: str
    capability: str
    status: RunStatus = RunStatus.planned
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    steps: tuple[dict[str, Any], ...] = ()
    citations: tuple[dict[str, Any], ...] = ()
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    output: dict[str, Any] | None = None
    confidence: float | None = None
    receipt_id: str | None = None
    approver: str | None = None
    approval_note: str | None = None
    resolved_at: datetime | None = None

    def with_status(self, status: RunStatus) -> RunState:
        return replace(self, status=status)

    def with_step(self, step_output: dict[str, Any]) -> RunState:
        """Append a step result, accumulating citations and model-usage cost."""
        usage: dict[str, Any] = step_output.get("usage") or {}
        tokens_in = int(usage.get("inputTokens", 0))
        tokens_out = int(usage.get("outputTokens", 0))
        cost_delta = (
            tokens_in / 1000.0 * _USD_PER_1K_INPUT_TOKENS
            + tokens_out / 1000.0 * _USD_PER_1K_OUTPUT_TOKENS
        )
        return replace(
            self,
            steps=(*self.steps, step_output),
            citations=(*self.citations, *step_output.get("citations", [])),
            tokens_in=self.tokens_in + tokens_in,
            tokens_out=self.tokens_out + tokens_out,
            cost_usd=round(self.cost_usd + cost_delta, 6),
        )

    def with_result(
        self, status: RunStatus, output: dict[str, Any] | None, confidence: float
    ) -> RunState:
        return replace(self, status=status, output=output, confidence=confidence)

    def with_resolution(self, status: RunStatus, approver: str, note: str | None) -> RunState:
        return replace(
            self,
            status=status,
            approver=approver,
            approval_note=note,
            resolved_at=datetime.now(UTC),
        )

    def to_status_payload(self) -> dict[str, Any]:
        """Shape consumed by the RunResult response model."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "output": self.output,
            "citations": list(self.citations),
            "cost": {
                "usd": self.cost_usd,
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out,
            },
            "receipt_id": self.receipt_id,
            "confidence": self.confidence,
        }

    def to_summary(self) -> dict[str, Any]:
        """Compact shape for run listings (approvals inbox)."""
        return {
            "run_id": self.run_id,
            "status": self.status,
            "capability": self.capability,
            "created_at": self.created_at.isoformat(),
            "citations_count": len(self.citations),
            "summary": self._summary_text(),
        }

    def _summary_text(self, max_chars: int = 200) -> str | None:
        final = (self.output or {}).get("final")
        if isinstance(final, dict):
            content = final.get("content")
            if isinstance(content, str):
                return content[:max_chars]
        return None


class RunStore:
    """Process-local registry of run snapshots keyed by run_id."""

    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}

    def put(self, state: RunState) -> RunState:
        self._runs[state.run_id] = state
        return state

    def get(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def list(self, status: RunStatus | None = None, limit: int = 50) -> list[RunState]:
        runs = sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)
        if status is not None:
            runs = [r for r in runs if r.status is status]
        return runs[:limit]
