"""Unit tests for the hash-chained audit log."""

from __future__ import annotations

import json
from pathlib import Path

from app.chain import GENESIS_HASH, AuditChain, compute_hash


def _make_chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / "audit.jsonl")


def test_genesis_prev_hash(tmp_path: Path) -> None:
    chain = _make_chain(tmp_path)
    record = chain.append(event_type="run.started", data={"run_id": "r1"}, tenant_id="t1")
    assert record.prev_hash == GENESIS_HASH
    assert record.hash == compute_hash(GENESIS_HASH, record.event_payload())


def test_chain_linkage_across_appends(tmp_path: Path) -> None:
    chain = _make_chain(tmp_path)
    first = chain.append(event_type="a", data={"n": 1})
    second = chain.append(event_type="b", data={"n": 2})
    third = chain.append(event_type="c", data={"n": 3})

    assert second.prev_hash == first.hash
    assert third.prev_hash == second.hash
    assert chain.head_hash == third.hash
    assert chain.verify() == (True, None)


def test_tamper_detection_at_correct_index(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    chain = AuditChain(log_path)
    for n in range(4):
        chain.append(event_type="evt", data={"n": n})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[2])
    tampered["data"]["n"] = 999  # mutate history
    new_lines = [*lines[:2], json.dumps(tampered), *lines[3:]]
    log_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    ok, first_bad_index = AuditChain(log_path).verify()
    assert ok is False
    assert first_bad_index == 2


def test_tamper_detection_unparseable_line(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    chain = AuditChain(log_path)
    chain.append(event_type="evt", data={})
    chain.append(event_type="evt", data={})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    log_path.write_text(lines[0] + "\nnot-json\n", encoding="utf-8")

    ok, first_bad_index = chain.verify()
    assert ok is False
    assert first_bad_index == 1


def test_resume_from_existing_file_keeps_chaining(tmp_path: Path) -> None:
    log_path = tmp_path / "audit.jsonl"
    first_chain = AuditChain(log_path)
    first_chain.append(event_type="a", data={"n": 1})
    last = first_chain.append(event_type="b", data={"n": 2})

    resumed = AuditChain(log_path)
    assert len(resumed) == 2
    assert resumed.head_hash == last.hash

    record = resumed.append(event_type="c", data={"n": 3})
    assert record.prev_hash == last.hash
    assert resumed.verify() == (True, None)


def test_recent_filters_by_tenant_and_limit(tmp_path: Path) -> None:
    chain = _make_chain(tmp_path)
    for n in range(5):
        chain.append(event_type="evt", data={"n": n}, tenant_id="t1" if n % 2 == 0 else "t2")

    t1_records = chain.recent(limit=50, tenant_id="t1")
    assert [r.data["n"] for r in t1_records] == [0, 2, 4]

    limited = chain.recent(limit=2)
    assert [r.data["n"] for r in limited] == [3, 4]
