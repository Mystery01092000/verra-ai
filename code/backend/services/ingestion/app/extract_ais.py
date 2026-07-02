"""Pattern-based extraction of AIS (Annual Information Statement) fields."""

from __future__ import annotations

import re

from .extract_common import (
    AMOUNT,
    CONFIDENCE_EXACT,
    CONFIDENCE_INFERRED,
    PAN,
    TAN,
    FieldHit,
    SectionLocator,
    collect_hits,
    labeled_hit,
    make_section_locator,
    parse_amount,
)

_SECTION_MARKERS = (
    ("Part B", r"part\s+b\s*-"),
    ("SFT Information", r"sft\s+information"),
)

# category (Section nnn) | source name | TAN | amount paid | tax deducted
_TDS_ROW = re.compile(
    r"^\s*(.+?)\s+\(section\s+([0-9]{3}[A-Z]{0,2})\)\s+(.+?)\s+"
    + TAN
    + r"\s+"
    + AMOUNT
    + r"\s+"
    + AMOUNT
    + r"\s*$",
    re.MULTILINE | re.IGNORECASE,
)

_SFT_ROW = re.compile(r"^\s*(SFT-[0-9]{3})\s+(.+?)\s+" + AMOUNT + r"\s*$", re.MULTILINE)


def _assessment_year_hits(text: str, locator: SectionLocator) -> tuple[FieldHit, ...]:
    exact = labeled_hit(
        text,
        r"assessment\s+year\s*[:\-]?\s*([0-9]{4}\s*-\s*[0-9]{2,4})",
        ("assessment_year",),
        locator,
    )
    if exact:
        return (exact,)
    fy_match = re.search(r"financial\s+year\s*[:\-]?\s*([0-9]{4})-([0-9]{2})", text, re.IGNORECASE)
    if not fy_match:
        return ()
    start_year = int(fy_match.group(1)) + 1
    end_suffix = (int(fy_match.group(2)) + 1) % 100
    inferred = f"{start_year}-{end_suffix:02d}"
    return (
        FieldHit(
            ("assessment_year",),
            inferred,
            CONFIDENCE_INFERRED,
            locator(fy_match.start(1)),
        ),
    )


def _row_hits(text: str, locator: SectionLocator) -> tuple[FieldHit, ...]:
    hits: list[FieldHit] = []
    income_counts = {"salary_income": 0, "other_income": 0}
    for index, match in enumerate(_TDS_ROW.finditer(text)):
        category, section, source, tan, paid, deducted = match.groups()
        section_name = locator(match.start())
        tds_entry = {
            "deductor_name": source.strip(),
            "deductor_tan": tan,
            "section": section,
            "amount_paid": parse_amount(paid),
            "tax_deducted": parse_amount(deducted),
        }
        hits.append(FieldHit(("tds_entries", index), tds_entry, CONFIDENCE_EXACT, section_name))
        income_key = "salary_income" if "salary" in category.lower() else "other_income"
        income_entry = {
            "information_category": category.strip(),
            "information_description": f"{category.strip()} (Section {section})",
            "information_source": source.strip(),
            "amount": parse_amount(paid),
        }
        hits.append(
            FieldHit(
                (income_key, income_counts[income_key]),
                income_entry,
                CONFIDENCE_EXACT,
                section_name,
            )
        )
        income_counts = {**income_counts, income_key: income_counts[income_key] + 1}
    for index, match in enumerate(_SFT_ROW.finditer(text)):
        code, description, amount = match.groups()
        entry = {
            "information_category": code,
            "information_description": description.strip(),
            "amount": parse_amount(amount),
        }
        hits.append(
            FieldHit(("sft_entries", index), entry, CONFIDENCE_EXACT, locator(match.start()))
        )
    return tuple(hits)


def extract_ais(text: str) -> tuple[tuple[FieldHit, ...], tuple[str, ...]]:
    """Extract AIS fields as (hits, flags); missing fields are omitted."""
    locator = make_section_locator(text, _SECTION_MARKERS)
    header_hits = collect_hits(
        labeled_hit(
            text,
            r"permanent\s+account\s+number\s*\(pan\)\s*[:\-]?\s*" + PAN,
            ("pan",),
            locator,
        ),
    )
    return (
        header_hits + _assessment_year_hits(text, locator) + _row_hits(text, locator),
        (),
    )
