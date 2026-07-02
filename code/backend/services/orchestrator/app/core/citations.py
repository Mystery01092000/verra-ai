"""Citation normalization + extraction helpers (every figure must cite its source)."""

from __future__ import annotations

import re
from typing import Any

# Default source document for statutory rule citations emitted by the tax calculators.
DEFAULT_RULE_DOC_ID = "in-income-tax-act-1961"

_SECTION_PATTERN = re.compile(r"[Ss]ection\s+([0-9]+[0-9A-Za-z()\-]*)")


def normalize_citation(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a calculator/LLM citation dict onto the shared Citation wire shape."""
    rule = raw.get("rule") or raw.get("section")
    doc_id = raw.get("doc_id") or raw.get("docId") or DEFAULT_RULE_DOC_ID
    page = raw.get("page")
    return {
        "doc_id": str(doc_id),
        "page": int(page) if page is not None else None,
        "rule": str(rule) if rule is not None else None,
    }


def normalize_citations(raws: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of raw citation dicts (returns a new list)."""
    return [normalize_citation(raw) for raw in raws]


def extract_citations_from_text(text: str) -> list[dict[str, Any]]:
    """Extract statutory section citations (e.g. 'Section 80C') from LLM output text."""
    seen: dict[str, None] = {}
    for match in _SECTION_PATTERN.finditer(text):
        seen.setdefault(match.group(1), None)
    return [
        {"doc_id": DEFAULT_RULE_DOC_ID, "page": None, "rule": f"Section {section}"}
        for section in seen
    ]
