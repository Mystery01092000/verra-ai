"""Unit tests for the Critic scoring signals and citation helpers."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.citations import extract_citations_from_text, normalize_citation
from app.core.critic import Critic


def _step(
    *,
    result: Any = None,
    error: str | None = None,
    citations: list[dict[str, Any]] | None = None,
    llm: bool = False,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "step": {"id": "s", "kind": "compute"},
        "result": result,
        "citations": citations or [],
    }
    if error is not None:
        out["error"] = error
    if llm:
        out["llm"] = True
    return out


def _verify(
    steps: list[dict[str, Any]], capability: dict[str, Any] | None = None
) -> dict[str, Any]:
    return asyncio.run(Critic().verify(steps, capability))


def test_confidence_full_when_all_signals_pass() -> None:
    steps = [
        _step(result={"totalTax": 100.0}, citations=[{"rule": "Section 87A"}]),
        _step(result={"content": "cited"}, citations=[{"rule": "Section 80C"}], llm=True),
    ]
    verdict = _verify(steps, {"approval_required": False})
    assert verdict["confidence"] == 1.0
    assert verdict["ok"] is True
    assert verdict["needs_approval"] is False


def test_uncited_llm_answer_gates_run() -> None:
    steps = [
        _step(result={"totalTax": 100.0}, citations=[{"rule": "Section 87A"}]),
        _step(result={"content": "no citations here"}, citations=[], llm=True),
    ]
    verdict = _verify(steps, {"approval_required": False})
    assert verdict["llm_grounded"] is False
    assert verdict["needs_approval"] is True  # hard gate, regardless of confidence


def test_uncited_money_result_lowers_confidence() -> None:
    steps = [_step(result={"totalTax": 100.0}, citations=[])]
    verdict = _verify(steps, {"approval_required": False})
    assert verdict["money_cited_fraction"] == 0.0
    assert verdict["needs_approval"] is True


def test_failed_steps_lower_success_fraction() -> None:
    steps = [
        _step(result={"documents": []}),
        _step(error="boom"),
    ]
    verdict = _verify(steps, {"approval_required": False})
    assert verdict["success_fraction"] == 0.5
    assert verdict["ok"] is False


def test_approval_required_capability_always_gates() -> None:
    steps = [_step(result={"totalTax": 1.0}, citations=[{"rule": "Section 4"}])]
    verdict = _verify(steps, {"approval_required": True})
    assert verdict["confidence"] == 1.0
    assert verdict["needs_approval"] is True


def test_extract_citations_dedupes_sections() -> None:
    text = "Use Section 80C twice: Section 80C, and Section 80CCD(1B) once."
    citations = extract_citations_from_text(text)
    assert [c["rule"] for c in citations] == ["Section 80C", "Section 80CCD(1B)"]


def test_normalize_citation_maps_calculator_shape() -> None:
    normalized = normalize_citation({"section": "16(ia)", "field": "standard_deduction"})
    assert normalized["rule"] == "16(ia)"
    assert normalized["doc_id"]
    assert normalized["page"] is None
