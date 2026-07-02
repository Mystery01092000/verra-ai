"""In-memory holdings store with JSONL append persistence.

State is keyed by ``(tenant_id, client_id)`` and every write appends an
operation record to a JSONL file so the store survives restarts::

    {"op": "add", "holding": {...}, "tenantId": "...", "clientId": "...", "ts": "..."}
    {"op": "delete", "holdingId": "...", "tenantId": "...", "clientId": "...", "ts": "..."}

On startup the file is replayed in order to rebuild the in-memory state.
Reads return immutable snapshots (tuples); internal state is replaced
wholesale on each write (new dict/tuples — never mutated in place) and all
writes are serialized through a lock.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from verra_shared.holdings import Holding

_State = dict[tuple[str, str], tuple[Holding, ...]]


def _with_added(state: _State, holding: Holding) -> _State:
    """Return a new state with ``holding`` appended (no mutation of ``state``)."""
    key = (holding.tenant_id, holding.client_id)
    return {**state, key: (*state.get(key, ()), holding)}


def _with_removed(state: _State, key: tuple[str, str], holding_id: str) -> _State:
    """Return a new state with the holding removed (no mutation of ``state``)."""
    remaining = tuple(h for h in state.get(key, ()) if h.id != holding_id)
    return {**state, key: remaining}


class HoldingsStore:
    """Thread-safe holdings store: in-memory reads, JSONL append durability."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self._lock = threading.Lock()
        self._state: _State = self._replay()

    # ── public API ─────────────────────────────────────────────────────────────

    def add(self, holding: Holding) -> Holding:
        """Persist and index a holding; returns the stored (unchanged) holding."""
        with self._lock:
            self._append_record(
                {
                    "op": "add",
                    "holding": holding.model_dump(by_alias=True, mode="json"),
                    "tenantId": holding.tenant_id,
                    "clientId": holding.client_id,
                    "ts": _now_iso(),
                }
            )
            self._state = _with_added(self._state, holding)
        return holding

    def list_for(self, tenant_id: str, client_id: str) -> tuple[Holding, ...]:
        """Immutable snapshot of the holdings for one tenant/client pair."""
        return self._state.get((tenant_id, client_id), ())

    def delete(self, tenant_id: str, client_id: str, holding_id: str) -> bool:
        """Delete by id; returns False when the holding is unknown."""
        key = (tenant_id, client_id)
        with self._lock:
            if not any(h.id == holding_id for h in self._state.get(key, ())):
                return False
            self._append_record(
                {
                    "op": "delete",
                    "holdingId": holding_id,
                    "tenantId": tenant_id,
                    "clientId": client_id,
                    "ts": _now_iso(),
                }
            )
            self._state = _with_removed(self._state, key, holding_id)
            return True

    # ── persistence ────────────────────────────────────────────────────────────

    def _append_record(self, record: dict[str, Any]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n")

    def _replay(self) -> _State:
        """Rebuild state by replaying the JSONL op log; fail fast on corruption."""
        state: _State = {}
        for index, line in enumerate(self._read_lines()):
            try:
                state = _apply_record(state, json.loads(line))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"corrupt holdings store at {self.store_path}, line {index}: {exc}"
                ) from exc
        return state

    def _read_lines(self) -> tuple[str, ...]:
        if not self.store_path.exists():
            return ()
        text = self.store_path.read_text(encoding="utf-8")
        return tuple(line for line in text.splitlines() if line.strip())


def _apply_record(state: _State, raw: dict[str, Any]) -> _State:
    """Apply one persisted op record to the state, returning the new state."""
    op = raw.get("op")
    if op == "add":
        return _with_added(state, Holding.model_validate(raw["holding"]))
    if op == "delete":
        key = (str(raw["tenantId"]), str(raw["clientId"]))
        return _with_removed(state, key, str(raw["holdingId"]))
    raise ValueError(f"unknown op {op!r}")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
