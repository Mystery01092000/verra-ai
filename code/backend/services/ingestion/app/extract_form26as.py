"""Pattern-based extraction of Form 26AS (Annual Tax Statement) fields."""

from __future__ import annotations

import re

from .extract_common import (
    AMOUNT,
    CONFIDENCE_EXACT,
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

_SECTION_MARKERS = (
    ("Part A", r"part\s+a\s*-"),
    ("Part C", r"part\s+c\s*-"),
)

_SECTION_CODE = r"([0-9]{3}[A-Z]{0,2})"

# Sr.No | deductor name | TAN | section | amount paid | tax deducted | tax deposited
_TDS_ROW = re.compile(
    r"^\s*[0-9]+\s+(.+?)\s+"
    + TAN
    + r"\s+"
    + _SECTION_CODE
    + r"\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s*$",
    re.MULTILINE,
)

# Sr.No | major head | minor head | tax | surcharge | cess | total | BSR | date | challan
_TAX_PAID_ROW = re.compile(
    r"^\s*[0-9]+\s+([0-9]{4})\s+([0-9]{3})\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s+([0-9]{7})\s+"
    + DDMMYYYY
    + r"\s+(\w+)\s*$",
    re.MULTILINE,
)


def _tds_entry_hits(text: str, locator: SectionLocator) -> tuple[FieldHit, ...]:
    hits: list[FieldHit] = []
    for index, match in enumerate(_TDS_ROW.finditer(text)):
        name, tan, section, paid, deducted, deposited = match.groups()
        entry = {
            "deductor_collector_name": name.strip(),
            "deductor_collector_tan": tan,
            "section_code": section,
            "amount_paid_credited": parse_amount(paid),
            "tax_deducted": parse_amount(deducted),
            "tax_deposited": parse_amount(deposited),
        }
        hits.append(
            FieldHit(("tds_entries", index), entry, CONFIDENCE_EXACT, locator(match.start()))
        )
    return tuple(hits)


def _tax_paid_hits(text: str, locator: SectionLocator) -> tuple[FieldHit, ...]:
    hits: list[FieldHit] = []
    for index, match in enumerate(_TAX_PAID_ROW.finditer(text)):
        major, minor, tax, surcharge, cess, total, bsr, deposited_on, challan = match.groups()
        entry = {
            "major_head": major,
            "minor_head": minor,
            "tax": parse_amount(tax),
            "surcharge": parse_amount(surcharge),
            "cess": parse_amount(cess),
            "total": parse_amount(total),
            "bsr_code": bsr,
            "date_of_deposit": parse_ddmmyyyy(deposited_on),
            "challan_serial_number": challan,
        }
        hits.append(
            FieldHit(("tax_paid_entries", index), entry, CONFIDENCE_EXACT, locator(match.start()))
        )
    return tuple(hits)


def extract_form26as(text: str) -> tuple[tuple[FieldHit, ...], tuple[str, ...]]:
    """Extract Form 26AS fields as (hits, flags); missing fields are omitted."""
    locator = make_section_locator(text, _SECTION_MARKERS)
    header_hits = collect_hits(
        labeled_hit(
            text,
            r"permanent\s+account\s+number\s*\(pan\)\s*[:\-]?\s*" + PAN,
            ("pan",),
            locator,
        ),
        labeled_hit(
            text,
            r"assessment\s+year\s*[:\-]?\s*([0-9]{4}\s*-\s*[0-9]{2,4})",
            ("assessment_year",),
            locator,
        ),
    )
    return (header_hits + _tds_entry_hits(text, locator) + _tax_paid_hits(text, locator), ())
