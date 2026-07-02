"""Append-only, hash-chained audit log persisted as JSONL (ADR-0015).

Each record links to its predecessor via ``prev_hash``:

    hash = sha256(prev_hash + canonical_json(event_payload))

so mutating any historical record invalidates every subsequent hash.
Records are only ever appended — there is no update or delete API — and the
backing file is opened in append-only mode.
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS_HASH = "0" * 64


def canonical_json(payload: dict[str, Any]) -> str:
    """Serialize deterministically (sorted keys, compact separators) for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_hash(prev_hash: str, event_payload: dict[str, Any]) -> str:
    """Chain hash: sha256 over the previous hash concatenated with the event JSON."""
    return hashlib.sha256((prev_hash + canonical_json(event_payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditRecord:
    """One immutable link in the audit chain."""

    event_id: str
    ts: str
    type: str
    tenant_id: str
    agent: str
    data: dict[str, Any]
    prev_hash: str
    hash: str

    def event_payload(self) -> dict[str, Any]:
        """The hashed portion of the record (everything except the chain fields)."""
        return {
            "event_id": self.event_id,
            "ts": self.ts,
            "type": self.type,
            "tenant_id": self.tenant_id,
            "agent": self.agent,
            "data": self.data,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> AuditRecord:
        return AuditRecord(
            event_id=str(raw["event_id"]),
            ts=str(raw["ts"]),
            type=str(raw["type"]),
            tenant_id=str(raw.get("tenant_id", "")),
            agent=str(raw.get("agent", "system")),
            data=dict(raw.get("data", {})),
            prev_hash=str(raw["prev_hash"]),
            hash=str(raw["hash"]),
        )


class AuditChain:
    """Hash-chained, append-only event log backed by a JSONL file.

    On construction the existing file (if any) is loaded so the chain resumes
    from the last persisted hash rather than restarting at genesis.
    """

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self._lock = threading.Lock()
        self._records: tuple[AuditRecord, ...] = self._load()

    def __len__(self) -> int:
        return len(self._records)

    @property
    def head_hash(self) -> str:
        return self._records[-1].hash if self._records else GENESIS_HASH

    def append(
        self,
        *,
        event_type: str,
        data: dict[str, Any],
        tenant_id: str = "",
        agent: str = "system",
    ) -> AuditRecord:
        """Append a new event, linking it to the current chain head."""
        with self._lock:
            payload = {
                "event_id": str(uuid.uuid4()),
                "ts": datetime.now(UTC).isoformat(),
                "type": event_type,
                "tenant_id": tenant_id,
                "agent": agent,
                "data": dict(data),
            }
            prev_hash = self.head_hash
            record = AuditRecord.from_dict(
                {**payload, "prev_hash": prev_hash, "hash": compute_hash(prev_hash, payload)}
            )
            self._write(record)
            self._records = (*self._records, record)
            return record

    def recent(self, limit: int = 50, tenant_id: str | None = None) -> tuple[AuditRecord, ...]:
        """Most recent records (oldest first), optionally filtered by tenant."""
        records = self._records
        if tenant_id:
            records = tuple(r for r in records if r.tenant_id == tenant_id)
        return records[-limit:] if limit else records

    def verify(self) -> tuple[bool, int | None]:
        """Re-walk the on-disk chain; return (ok, index of first bad record)."""
        expected_prev = GENESIS_HASH
        for index, line in enumerate(self._read_lines()):
            try:
                record = AuditRecord.from_dict(json.loads(line))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                return (False, index)
            if record.prev_hash != expected_prev:
                return (False, index)
            if compute_hash(record.prev_hash, record.event_payload()) != record.hash:
                return (False, index)
            expected_prev = record.hash
        return (True, None)

    # ── persistence ───────────────────────────────────────────────────────────

    def _read_lines(self) -> tuple[str, ...]:
        if not self.log_path.exists():
            return ()
        text = self.log_path.read_text(encoding="utf-8")
        return tuple(line for line in text.splitlines() if line.strip())

    def _load(self) -> tuple[AuditRecord, ...]:
        try:
            return tuple(AuditRecord.from_dict(json.loads(line)) for line in self._read_lines())
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"corrupt audit log at {self.log_path}: {exc}") from exc

    def _write(self, record: AuditRecord) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(record.to_dict()) + "\n")
