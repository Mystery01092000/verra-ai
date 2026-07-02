"""Store tests: persistence replay, immutability of snapshots, corruption fail-fast."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.store import HoldingsStore
from verra_shared.holdings import Holding, HoldingType


def _holding(holding_id: str, **overrides: object) -> Holding:
    base: dict[str, object] = {
        "id": holding_id,
        "tenant_id": "t1",
        "client_id": "c1",
        "type": HoldingType.mutual_fund,
        "name": f"Holding {holding_id}",
        "current_value": 1000.0,
    }
    return Holding.model_validate({**base, **overrides})


def test_add_list_delete_roundtrip(tmp_path: Path) -> None:
    store = HoldingsStore(tmp_path / "holdings.jsonl")
    store.add(_holding("h1"))
    store.add(_holding("h2", type=HoldingType.gold))

    assert [h.id for h in store.list_for("t1", "c1")] == ["h1", "h2"]
    assert store.list_for("t1", "other-client") == ()

    assert store.delete("t1", "c1", "h1") is True
    assert [h.id for h in store.list_for("t1", "c1")] == ["h2"]
    assert store.delete("t1", "c1", "h1") is False  # already gone


def test_replay_rebuilds_state_across_restarts(tmp_path: Path) -> None:
    path = tmp_path / "holdings.jsonl"
    first = HoldingsStore(path)
    first.add(_holding("h1"))
    first.add(_holding("h2", maturity_date="2027-03-31", type=HoldingType.fixed_deposit))
    first.add(_holding("h3", tenant_id="t2", client_id="c9"))
    first.delete("t1", "c1", "h1")

    replayed = HoldingsStore(path)  # fresh instance, same file
    assert [h.id for h in replayed.list_for("t1", "c1")] == ["h2"]
    assert [h.id for h in replayed.list_for("t2", "c9")] == ["h3"]
    fd = replayed.list_for("t1", "c1")[0]
    assert fd.type is HoldingType.fixed_deposit
    assert str(fd.maturity_date) == "2027-03-31"


def test_snapshot_is_immutable_tuple(tmp_path: Path) -> None:
    store = HoldingsStore(tmp_path / "holdings.jsonl")
    store.add(_holding("h1"))
    snapshot = store.list_for("t1", "c1")
    assert isinstance(snapshot, tuple)
    store.add(_holding("h2"))
    assert len(snapshot) == 1  # earlier snapshot unaffected by later writes


def test_corrupt_store_fails_fast(tmp_path: Path) -> None:
    path = tmp_path / "holdings.jsonl"
    path.write_text('{"op": "add", "holding": {not json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="corrupt holdings store"):
        HoldingsStore(path)


def test_unknown_op_fails_fast(tmp_path: Path) -> None:
    path = tmp_path / "holdings.jsonl"
    path.write_text('{"op": "upsert", "tenantId": "t1", "clientId": "c1"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="unknown op"):
        HoldingsStore(path)
