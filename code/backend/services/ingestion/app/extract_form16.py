"""Pattern-based extraction of Form 16 (Parts A and B) fields."""

from __future__ import annotations

import re

from .extract_common import (
    AMOUNT,
    CONFIDENCE_EXACT,
    CONFIDENCE_FUZZY,
    DDMMYYYY,
    PAN,
    TAN,
    FieldHit,
    SectionLocator,
    collect_hits,
    labeled_hit,
    make_section_locator,
    parse_amount,
    parse_ddmmyyyy,
)

_SECTION_MARKERS = (("Part A", r"\bpart\s+a\b"), ("Part B", r"\bpart\s+b\b"))

# Quarter rows: official "(Rs.)" table style, or narrative "…tax deducted: Rs. N".
_QUARTER_ROW = r"quarter\s+q([1-4])[^\n]*?(?:\(rs\.\)|[:\-])\s*" + AMOUNT
_TDS_TOTAL = r"total\s*\(rs\.\)\s*:?\s*" + AMOUNT

# (pattern, schema path, transform) for exact labeled amount matches in Part B.
# Section labels tolerate trailing descriptions before the colon
# (e.g. "Exemption under section 10(13A) House Rent Allowance: …").
_PART_B_AMOUNTS: tuple[tuple[str, tuple[str | int, ...]], ...] = (
    (r"gross\s+salary\s*[:\-]\s*" + AMOUNT, ("part_b", "gross_salary")),
    (r"section\s+10\(13a\)[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "house_rent_allowance_exempt")),
    (r"section\s+10\(5\)[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "leave_travel_allowance_exempt")),
    (
        r"standard\s+deduction[^\n]*?section\s+16\(ia\)\s*[:\-]\s*" + AMOUNT,
        ("part_b", "standard_deduction"),
    ),
    (r"section\s+16\(iii\)[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "professional_tax")),
    (
        r"income\s+chargeable\s+under\s+the\s+head\s+\"?salaries\"?\s*[:\-]\s*" + AMOUNT,
        ("part_b", "income_chargeable_under_salaries"),
    ),
    (r"section\s+80c\b[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "section_80c")),
    (r"section\s+80d\b[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "section_80d")),
    (r"section\s+80ccd\(1b\)[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "section_80ccd1b")),
    (r"section\s+80g\b[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "section_80g")),
    (r"section\s+80e\b[^\n:]*[:\-]\s*" + AMOUNT, ("part_b", "section_80e")),
    (r"net\s+tax\s+payable\s*[:\-]\s*" + AMOUNT, ("part_b", "net_tax_payable")),
)


def _tds_hits(text: str, locator: SectionLocator) -> tuple[tuple[FieldHit, ...], tuple[str, ...]]:
    """Derive Part A TDS total from the labeled total or the quarterly rows."""
    quarters = tuple(
        parsed
        for _, raw in re.findall(_QUARTER_ROW, text, re.IGNORECASE)
        if (parsed := parse_amount(raw)) is not None
    )
    total_match = re.search(_TDS_TOTAL, text, re.IGNORECASE)
    total = parse_amount(total_match.group(1)) if total_match else None

    flags: tuple[str, ...] = ()
    if total is not None and quarters and abs(sum(quarters) - total) > 0.01:
        flags = ("form16:tds_quarter_total_mismatch",)

    if total is not None and total_match is not None:
        hit = FieldHit(
            path=("part_a", "tds_deducted"),
            value=total,
            confidence=CONFIDENCE_EXACT,
            section=locator(total_match.start(1)),
        )
        return ((hit,), flags)
    if quarters:
        hit = FieldHit(
            path=("part_a", "tds_deducted"),
            value=round(sum(quarters), 2),
            confidence=CONFIDENCE_FUZZY,
            section="Part A",
        )
        return ((hit,), flags)
    return ((), flags)


def extract_form16(text: str) -> tuple[tuple[FieldHit, ...], tuple[str, ...]]:
    """Extract Form 16 fields as (hits, flags); missing fields are omitted."""
    locator = make_section_locator(text, _SECTION_MARKERS)
    assessment_year = labeled_hit(
        text,
        r"assessment\s+year\s*[:\-]?\s*([0-9]{4}\s*-\s*[0-9]{2,4})",
        ("assessment_year",),
        locator,
    )
    identity_hits = collect_hits(
        labeled_hit(
            text,
            r"name\s+(?:and\s+address\s+)?of\s+(?:the\s+)?employer\s*[:\-]?\s*\n?\s*([^\n]+)",
            ("part_a", "employer_name"),
            locator,
        ),
        labeled_hit(
            text,
            r"name\s+(?:and\s+designation\s+)?of\s+(?:the\s+)?employee\s*[:\-]?\s*\n?\s*([^\n]+)",
            ("part_a", "employee_name"),
            locator,
        ),
        labeled_hit(
            text,
            r"pan\s+of\s+(?:the\s+)?(?:deductor|employer)\s*[:\-]?\s*" + PAN,
            ("part_a", "employer_pan"),
            locator,
        ),
        labeled_hit(
            text,
            r"tan\s+of\s+(?:the\s+)?(?:deductor|employer)\s*[:\-]?\s*" + TAN,
            ("part_a", "employer_tan"),
            locator,
        ),
        labeled_hit(
            text,
            r"pan\s+of\s+(?:the\s+)?employee\s*[:\-]?\s*" + PAN,
            ("part_a", "employee_pan"),
            locator,
        ),
        assessment_year,
        FieldHit(
            ("part_a", "assessment_year"),
            assessment_year.value,
            assessment_year.confidence,
            assessment_year.section,
        )
        if assessment_year
        else None,
        labeled_hit(
            text,
            r"from\s*[:\-]?\s*" + DDMMYYYY,
            ("part_a", "period_from"),
            locator,
            transform=parse_ddmmyyyy,
        ),
        labeled_hit(
            text,
            r"to\s*[:\-]?\s*" + DDMMYYYY,
            ("part_a", "period_to"),
            locator,
            transform=parse_ddmmyyyy,
        ),
    )
    amount_hits = collect_hits(
        *(
            labeled_hit(text, pattern, path, locator, transform=parse_amount)
            for pattern, path in _PART_B_AMOUNTS
        )
    )
    tds_hits, flags = _tds_hits(text, locator)
    return (identity_hits + amount_hits + tds_hits, flags)
