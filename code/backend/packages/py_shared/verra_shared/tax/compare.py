"""Regime comparison calculator — old vs new regime for AY 2025-26."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from .liability import compute_tax_liability
from .models import Deductions, IncomeHeads, Regime, TaxComputationResult, TaxpayerType, _TaxBase


class RegimeComparison(_TaxBase):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    assessment_year: str
    old_regime: TaxComputationResult
    new_regime: TaxComputationResult
    recommended_regime: Regime
    # Positive → old regime saves tax; negative → new regime saves tax.
    tax_delta: float
    tax_saving: float  # absolute saving in INR with the recommended regime
    summary: str
    citations: list[dict[str, Any]]


def compare_regimes(
    assessment_year: str,
    taxpayer_type: TaxpayerType,
    age: int,
    income: IncomeHeads,
    deductions: Deductions,
    tds_tcs_credit: float = 0.0,
    advance_tax_paid: float = 0.0,
    foreign_tax_credit: float = 0.0,
) -> RegimeComparison:
    """Compute tax under both regimes and recommend the lower-tax option.

    Note: The new regime disallows most deductions (80C, 80D, etc.) but allows
    a higher standard deduction (₹75,000 vs ₹50,000 under old regime for AY 2025-26).
    This function runs both regimes with the same inputs; callers should strip
    old-regime-specific deductions when computing the new regime if needed.
    """
    old = compute_tax_liability(
        assessment_year=assessment_year,
        taxpayer_type=taxpayer_type,
        regime=Regime.old,
        age=age,
        income=income,
        deductions=deductions,
        tds_tcs_credit=tds_tcs_credit,
        advance_tax_paid=advance_tax_paid,
        foreign_tax_credit=foreign_tax_credit,
    )
    new = compute_tax_liability(
        assessment_year=assessment_year,
        taxpayer_type=taxpayer_type,
        regime=Regime.new,
        age=age,
        income=income,
        deductions=deductions,
        tds_tcs_credit=tds_tcs_credit,
        advance_tax_paid=advance_tax_paid,
        foreign_tax_credit=foreign_tax_credit,
    )

    delta = old.total_tax - new.total_tax  # positive → old is worse, new saves
    recommended = Regime.new if delta >= 0 else Regime.old
    saving = abs(delta)

    if delta > 0:
        summary = (
            f"New regime saves ₹{saving:,.0f} in total tax "
            f"(₹{new.total_tax:,.0f} vs ₹{old.total_tax:,.0f} under old regime)."
        )
    elif delta < 0:
        summary = (
            f"Old regime saves ₹{saving:,.0f} in total tax "
            f"(₹{old.total_tax:,.0f} vs ₹{new.total_tax:,.0f} under new regime)."
        )
    else:
        summary = "Both regimes result in identical total tax."

    citations: list[dict[str, Any]] = [
        {
            "type": "rule",
            "section": "regime_choice",
            "body": (
                "Taxpayers can choose between old and new tax regime each year. "
                "The new regime has lower slab rates but restricts most deductions "
                "(Finance Act 2023/2024, Section 115BAC)."
            ),
            "source_citation": "Income Tax Act, 1961, Section 115BAC",
        }
    ]

    return RegimeComparison(
        assessment_year=assessment_year,
        old_regime=old,
        new_regime=new,
        recommended_regime=recommended,
        tax_delta=delta,
        tax_saving=saving,
        summary=summary,
        citations=citations,
    )
