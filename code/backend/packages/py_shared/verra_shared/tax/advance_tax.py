"""Advance tax instalment calculator (Section 211) and interest (234B, 234C)."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .constants import ADVANCE_TAX_INSTALMENTS, INTEREST_RATE_234B, INTEREST_RATE_234C
from .models import _TaxBase


class AdvanceTaxInput(_TaxBase):
    """Inputs for advance tax computation."""

    assessment_year: str
    estimated_tax_liability: float = Field(ge=0)
    advance_tax_paid: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of {date_label, amount} paid by each instalment deadline.",
    )


class InstalmentStatus(_TaxBase):
    due_date: str
    cumulative_pct: float
    amount_due: float
    amount_paid: float
    shortfall: float
    months_delayed: int
    interest_234c: float


class AdvanceTaxResult(_TaxBase):
    estimated_tax_liability: float
    instalments: list[InstalmentStatus]
    total_advance_paid: float
    shortfall_234b: float
    interest_234b: float
    interest_234c: float
    total_interest: float
    citations: list[dict[str, Any]]


def compute_advance_tax(inp: AdvanceTaxInput) -> AdvanceTaxResult:
    """Compute advance tax instalments and interest under Sections 234B and 234C.

    Section 234B applies when total advance tax paid < 90% of assessed liability.
    Section 234C applies when individual instalments are short-paid.

    This is a simplified v1 that assumes:
    - AY 2025-26 / FY 2024-25 instalment schedule.
    - Months delayed for 234C are estimated at 3 months per instalment gap.
    """
    if inp.assessment_year != "2025-26":
        raise ValueError("Only AY 2025-26 is supported in v1")

    liability = inp.estimated_tax_liability

    # Map paid amounts to instalment slots by position.
    paid_by_slot: list[float] = [0.0] * len(ADVANCE_TAX_INSTALMENTS)
    for i, payment in enumerate(inp.advance_tax_paid):
        if i < len(paid_by_slot):
            paid_by_slot[i] = float(payment.get("amount", 0.0))

    cumulative_paid = 0.0
    instalments: list[InstalmentStatus] = []
    total_234c = 0.0

    for idx, (due_date, cum_pct) in enumerate(ADVANCE_TAX_INSTALMENTS):
        amount_due = cum_pct * liability - (
            ADVANCE_TAX_INSTALMENTS[idx - 1][1] * liability if idx > 0 else 0.0
        )
        paid_this_slot = paid_by_slot[idx]
        cumulative_paid += paid_this_slot

        cumulative_due = cum_pct * liability
        shortfall = max(cumulative_due - cumulative_paid, 0.0)

        # 234C: 1% per month for 3 months on shortfall in each instalment.
        months = 3 if idx < len(ADVANCE_TAX_INSTALMENTS) - 1 else 1
        interest_234c = shortfall * INTEREST_RATE_234C * months
        total_234c += interest_234c

        instalments.append(
            InstalmentStatus(
                due_date=due_date,
                cumulative_pct=cum_pct,
                amount_due=amount_due,
                amount_paid=paid_this_slot,
                shortfall=shortfall,
                months_delayed=months if shortfall > 0 else 0,
                interest_234c=interest_234c,
            )
        )

    total_paid = sum(paid_by_slot)

    # 234B: if advance tax < 90% of liability, interest on shortfall from 1 Apr to assessment.
    threshold_90 = 0.90 * liability
    shortfall_234b = max(liability - total_paid, 0.0) if total_paid < threshold_90 else 0.0
    # Simplified: assume 1 month (assessment completes immediately after FY end).
    interest_234b = shortfall_234b * INTEREST_RATE_234B * 1

    citations: list[dict[str, Any]] = [
        {
            "section": "211",
            "body": (
                "Advance tax instalments: 15% by 15 Jun, 45% by 15 Sep, "
                "75% by 15 Dec, 100% by 15 Mar."
            ),
            "source_citation": "Income Tax Act, 1961, Section 211",
        },
        {
            "section": "234B",
            "body": "Interest at 1% per month where advance tax paid < 90% of assessed tax.",
            "source_citation": "Income Tax Act, 1961, Section 234B",
        },
        {
            "section": "234C",
            "body": "Interest at 1% per month for deferment of advance tax instalment.",
            "source_citation": "Income Tax Act, 1961, Section 234C",
        },
    ]

    return AdvanceTaxResult(
        estimated_tax_liability=liability,
        instalments=instalments,
        total_advance_paid=total_paid,
        shortfall_234b=shortfall_234b,
        interest_234b=interest_234b,
        interest_234c=total_234c,
        total_interest=interest_234b + total_234c,
        citations=citations,
    )
