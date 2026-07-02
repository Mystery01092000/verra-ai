"""Deterministic keyword/pattern document classification (no OCR, no model calls)."""

from __future__ import annotations

import re
from typing import Final

DOC_TYPE_UNKNOWN: Final = "unknown"

# Weighted signature patterns per supported doc type. Confidence is the sum of
# matched weights normalized by the total weight available for that doc type.
_PATTERN_WEIGHTS: Final[tuple[tuple[str, tuple[tuple[str, int], ...]], ...]] = (
    (
        "form16",
        (
            (r"form\s+no\.?\s*16\b", 3),
            (r"certificate\s+under\s+section\s+203\b", 3),
            (r"tax\s+deducted\s+at\s+source\s+on\s+salary", 2),
            (r"\bpart\s+a\b", 1),
            (r"\bpart\s+b\b", 1),
        ),
    ),
    (
        "form26as",
        (
            (r"form\s+26\s*as\b", 3),
            (r"annual\s+tax\s+statement", 3),
            (r"section\s+203aa", 2),
            (r"details\s+of\s+tax\s+deducted\s+at\s+source", 1),
        ),
    ),
    (
        "ais",
        (
            (r"annual\s+information\s+statement", 3),
            (r"\bais\b", 2),
            (r"\bsft\b", 1),
            (r"information\s+category", 1),
        ),
    ),
)


def _score(text: str, patterns: tuple[tuple[str, int], ...]) -> float:
    total = sum(weight for _, weight in patterns)
    if total == 0:
        return 0.0
    matched = sum(weight for pattern, weight in patterns if re.search(pattern, text, re.IGNORECASE))
    return round(matched / total, 3)


def classify_document(text: str) -> tuple[str, float]:
    """Classify raw document text into ``form16 | form26as | ais | unknown``.

    Returns the winning doc type and a normalized confidence in [0, 1].
    Unrecognized or empty text yields ``("unknown", 0.0)``.
    """
    if not text.strip():
        return (DOC_TYPE_UNKNOWN, 0.0)
    scored = tuple((doc_type, _score(text, patterns)) for doc_type, patterns in _PATTERN_WEIGHTS)
    best_type, best_confidence = max(scored, key=lambda item: item[1])
    if best_confidence <= 0.0:
        return (DOC_TYPE_UNKNOWN, 0.0)
    return (best_type, best_confidence)
