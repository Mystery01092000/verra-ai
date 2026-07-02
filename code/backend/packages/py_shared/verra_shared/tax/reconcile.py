"""TDS/TCS reconciliation across Form 16, Form 26AS, and AIS."""

from __future__ import annotations

from typing import Any

from .models import _TaxBase


class TDSEntry(_TaxBase):
    deductor_name: str | None = None
    tan: str | None = None
    section: str | None = None
    amount_paid: float = 0.0
    tax_deducted: float = 0.0
    source: str = "unknown"  # 'form_16' | 'form_26as' | 'ais'


class TDSMatchResult(_TaxBase):
    tan: str | None
    deductor_name: str | None
    tds_as_per_form16: float
    tds_as_per_26as: float
    tds_as_per_ais: float
    variance_16_vs_26as: float
    status: str  # 'matched' | 'minor_variance' | 'mismatch' | 'missing_in_26as'


class ReconciliationResult(_TaxBase):
    total_tds_form16: float
    total_tds_26as: float
    total_tds_ais: float
    net_tds_claimable: float  # lower of 26AS and AIS (government records are authoritative)
    matches: list[TDSMatchResult]
    unmatched_form16: list[TDSEntry]
    unmatched_26as: list[TDSEntry]
    flags: list[str]
    citations: list[dict[str, Any]]


def reconcile_tds(
    form16_entries: list[TDSEntry],
    form26as_entries: list[TDSEntry],
    ais_entries: list[TDSEntry],
    variance_threshold: float = 1.0,  # INR — treat as matched below this
) -> ReconciliationResult:
    """Cross-check TDS entries from Form 16, Form 26AS, and AIS.

    Form 26AS / AIS are the authoritative government records. If Form 16 shows
    a deduction that doesn't appear in 26AS, the credit cannot be claimed.
    """
    # Index 26AS and AIS by TAN for quick lookup.
    by_tan_26as: dict[str, list[TDSEntry]] = {}
    for e in form26as_entries:
        key = (e.tan or "UNKNOWN").upper()
        by_tan_26as.setdefault(key, []).append(e)

    by_tan_ais: dict[str, list[TDSEntry]] = {}
    for e in ais_entries:
        key = (e.tan or "UNKNOWN").upper()
        by_tan_ais.setdefault(key, []).append(e)

    matches: list[TDSMatchResult] = []
    unmatched_16: list[TDSEntry] = []
    flags: list[str] = []

    for entry in form16_entries:
        tan_key = (entry.tan or "UNKNOWN").upper()
        matched_26as = by_tan_26as.get(tan_key, [])
        matched_ais = by_tan_ais.get(tan_key, [])

        tds_26as = sum(e.tax_deducted for e in matched_26as)
        tds_ais = sum(e.tax_deducted for e in matched_ais)
        variance = abs(entry.tax_deducted - tds_26as)

        if not matched_26as:
            status = "missing_in_26as"
            flags.append(
                f"TAN {tan_key} ({entry.deductor_name}): TDS ₹{entry.tax_deducted:,.0f} "
                f"in Form 16 but not in Form 26AS — credit cannot be claimed."
            )
        elif variance <= variance_threshold:
            status = "matched"
        elif variance <= 100:
            status = "minor_variance"
            flags.append(
                f"TAN {tan_key}: minor variance ₹{variance:,.2f} "
                f"(Form 16: ₹{entry.tax_deducted:,.0f}, 26AS: ₹{tds_26as:,.0f})"
            )
        else:
            status = "mismatch"
            flags.append(
                f"TAN {tan_key}: MISMATCH — Form 16: ₹{entry.tax_deducted:,.0f}, "
                f"26AS: ₹{tds_26as:,.0f}. Variance: ₹{variance:,.0f}. "
                "Contact employer / deductor to resolve before filing."
            )

        if matched_26as:
            matches.append(
                TDSMatchResult(
                    tan=entry.tan,
                    deductor_name=entry.deductor_name,
                    tds_as_per_form16=entry.tax_deducted,
                    tds_as_per_26as=tds_26as,
                    tds_as_per_ais=tds_ais,
                    variance_16_vs_26as=tds_26as - entry.tax_deducted,
                    status=status,
                )
            )
        else:
            unmatched_16.append(entry)

    unmatched_26as = [
        e
        for tan, entries in by_tan_26as.items()
        for e in entries
        if not any((entry.tan or "UNKNOWN").upper() == tan for entry in form16_entries)
    ]

    total_tds_form16 = sum(e.tax_deducted for e in form16_entries)
    total_tds_26as = sum(e.tax_deducted for e in form26as_entries)
    total_tds_ais = sum(e.tax_deducted for e in ais_entries)
    # Authoritative credit = 26AS (government record); AIS may include additional sources.
    net_claimable = max(total_tds_26as, total_tds_ais)

    citations: list[dict[str, Any]] = [
        {
            "section": "199",
            "body": (
                "TDS credit is allowed to the deductee in whose hands income is assessed. "
                "Credit is based on Form 26AS / AIS entries, not just Form 16."
            ),
            "source_citation": "Income Tax Act, 1961, Section 199; Rule 37BA",
        }
    ]

    return ReconciliationResult(
        total_tds_form16=total_tds_form16,
        total_tds_26as=total_tds_26as,
        total_tds_ais=total_tds_ais,
        net_tds_claimable=net_claimable,
        matches=matches,
        unmatched_form16=unmatched_16,
        unmatched_26as=unmatched_26as,
        flags=flags,
        citations=citations,
    )
