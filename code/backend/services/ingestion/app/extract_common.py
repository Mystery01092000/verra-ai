"""Shared primitives for pattern-based structured extraction.

Confidence encodes pattern strength: exact labeled match 0.95, fuzzy/derived
match 0.7, inferred value 0.5. Fields that cannot be located are omitted —
never invented.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime
from typing import Final, NamedTuple

CONFIDENCE_EXACT: Final = 0.95
CONFIDENCE_FUZZY: Final = 0.7
CONFIDENCE_INFERRED: Final = 0.5

# Optional currency marker (Rs. / INR / ₹) before the numeric amount — real-world
# documents write amounts both ways; the capture group stays on the digits.
AMOUNT: Final = r"(?:(?:rs\.?|inr|₹)\s*)?([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
PAN: Final = r"([A-Z]{5}[0-9]{4}[A-Z])"
TAN: Final = r"([A-Z]{4}[0-9]{5}[A-Z])"
DDMMYYYY: Final = r"([0-9]{2}/[0-9]{2}/[0-9]{4})"

FieldPath = tuple[str | int, ...]
SectionLocator = Callable[[int], str | None]
Transform = Callable[[str], object | None]


class FieldHit(NamedTuple):
    """One extracted field with schema path, provenance section, and confidence."""

    path: FieldPath
    value: object
    confidence: float
    section: str | None = None


def parse_amount(raw: str) -> float | None:
    """Parse an Indian-formatted amount string (e.g. ``1,81,500.00``) to float."""
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def parse_ddmmyyyy(raw: str) -> date | None:
    """Parse a ``dd/mm/yyyy`` date string; returns None when invalid."""
    try:
        return datetime.strptime(raw, "%d/%m/%Y").date()
    except ValueError:
        return None


def make_section_locator(text: str, markers: tuple[tuple[str, str], ...]) -> SectionLocator:
    """Build a locator mapping a character offset to the enclosing section name.

    ``markers`` is an ordered tuple of ``(section_name, regex)``; the locator
    returns the name of the last marker starting at or before the offset.
    """
    found: list[tuple[int, str]] = []
    for name, pattern in markers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            found.append((match.start(), name))
    ordered = tuple(sorted(found))

    def locate(offset: int) -> str | None:
        section: str | None = None
        for start, name in ordered:
            if start <= offset:
                section = name
        return section

    return locate


def labeled_hit(
    text: str,
    pattern: str,
    path: FieldPath,
    locator: SectionLocator,
    *,
    confidence: float = CONFIDENCE_EXACT,
    transform: Transform | None = None,
) -> FieldHit | None:
    """Search ``pattern`` (group 1 = value) and produce a FieldHit, or None."""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).strip()
    value = transform(raw) if transform else raw
    if value is None:
        return None
    return FieldHit(path=path, value=value, confidence=confidence, section=locator(match.start(1)))


def collect_hits(*hits: FieldHit | None) -> tuple[FieldHit, ...]:
    """Drop unmatched (None) results, preserving order."""
    return tuple(hit for hit in hits if hit is not None)
