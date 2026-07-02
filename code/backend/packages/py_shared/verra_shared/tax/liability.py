"""Deterministic Indian income-tax liability calculator (AY 2025-26)."""

from __future__ import annotations

from typing import Any

from .constants import (
    CESS_RATE,
    DEDUCTION_CAPS,
    NEW_REGIME_SLABS,
    OLD_REGIME_SLABS,
    REBATE_87A,
    SURCHARGE_BRACKETS,
)
from .models import Deductions, IncomeHeads, Regime, TaxComputationResult, TaxInput, TaxpayerType


def _capped_deductions(
    deductions: Deductions, regime: Regime
) -> tuple[float, list[dict[str, Any]]]:
    """Apply regime-specific deduction caps and return total + citations."""
    if regime == Regime.new:
        # New regime: only standard deduction allowed (Finance Act 2024: cap is ₹75,000).
        std_capped = min(
            deductions.standard_deduction, DEDUCTION_CAPS["standard_deduction_new_regime"]
        )
        citation = {
            "section": "16(ia)",
            "field": "standard_deduction",
            "capped_amount": std_capped,
            "source": "Finance Act 2024 — standard deduction raised to ₹75,000 under new regime",
        }
        return std_capped, [citation]

    capped: dict[str, float] = {}
    citations: list[dict[str, Any]] = []

    capped["standard_deduction"] = min(
        deductions.standard_deduction, DEDUCTION_CAPS["standard_deduction"]
    )
    citations.append(
        {
            "section": "16(ia)",
            "field": "standard_deduction",
            "capped_amount": capped["standard_deduction"],
        }
    )

    capped["section_80c"] = min(deductions.section_80c, DEDUCTION_CAPS["80c"])
    citations.append(
        {"section": "80C", "field": "section_80c", "capped_amount": capped["section_80c"]}
    )

    capped["section_80d"] = min(deductions.section_80d, DEDUCTION_CAPS["80d_self"])
    citations.append(
        {"section": "80D", "field": "section_80d", "capped_amount": capped["section_80d"]}
    )

    capped["section_80ccd1b"] = min(deductions.section_80ccd1b, DEDUCTION_CAPS["80ccd1b"])
    citations.append(
        {
            "section": "80CCD(1B)",
            "field": "section_80ccd1b",
            "capped_amount": capped["section_80ccd1b"],
        }
    )

    capped["section_24"] = min(deductions.section_24, DEDUCTION_CAPS["24"])
    citations.append(
        {"section": "24(b)", "field": "section_24", "capped_amount": capped["section_24"]}
    )

    # 80G/80E/80TTA/other: apply as-is up to their own caps (v1 does not split further).
    capped["section_80g"] = deductions.section_80g
    capped["section_80e"] = deductions.section_80e
    capped["section_80tta"] = min(deductions.section_80tta, DEDUCTION_CAPS["80tta"])
    capped["other"] = deductions.other

    return sum(capped.values()), citations


def _apply_slabs(taxable_income: float, regime: Regime) -> float:
    """Apply income-tax slabs for the chosen regime."""
    slabs = OLD_REGIME_SLABS if regime == Regime.old else NEW_REGIME_SLABS
    tax = 0.0
    for _min, _max, rate in slabs:
        if taxable_income <= _min:
            break
        slab_top = _max if _max is not None else float("inf")
        taxable_in_slab = min(taxable_income, slab_top) - _min
        if taxable_in_slab > 0:
            tax += taxable_in_slab * rate
    return max(tax, 0.0)


def _surcharge(tax: float, taxable_income: float) -> float:
    """Apply surcharge based on total income (common brackets for AY 2025-26)."""
    for _min, _max, rate in SURCHARGE_BRACKETS:
        if taxable_income > _min and (_max is None or taxable_income <= _max):
            return tax * rate
    return 0.0


def _marginal_relief(tax_before_rebate: float, surcharge: float, taxable_income: float) -> float:
    """Apply marginal relief so total tax does not exceed income above slab threshold.

    Marginal relief ensures that the additional tax payable (including surcharge) on
    income just above a surcharge threshold does not exceed the income that crosses
    the threshold. This is a simplified v1 implementation.
    """
    for _min, _max, _rate in SURCHARGE_BRACKETS:
        if taxable_income > _min:
            income_excess = taxable_income - _min
            # Tax that would have been payable at the previous surcharge rate on the threshold.
            previous_rate = 0.0
            for _p_min, p_max, p_rate in SURCHARGE_BRACKETS:
                if p_max == _min:
                    previous_rate = p_rate
                    break
            tax_at_threshold = tax_before_rebate * (1 + previous_rate)
            tax_with_surcharge = tax_before_rebate + surcharge
            additional_tax = tax_with_surcharge - tax_at_threshold
            if additional_tax > income_excess:
                return max(surcharge - (additional_tax - income_excess), 0.0)
    return surcharge


def compute_tax_liability(
    assessment_year: str,
    taxpayer_type: TaxpayerType,
    regime: Regime,
    age: int,
    income: IncomeHeads,
    deductions: Deductions,
    tds_tcs_credit: float = 0.0,
    advance_tax_paid: float = 0.0,
    foreign_tax_credit: float = 0.0,
) -> TaxComputationResult:
    """Compute Indian income-tax liability deterministically for AY 2025-26."""
    if assessment_year != "2025-26":
        raise ValueError("Only AY 2025-26 is supported in v1")

    gross_total_income = sum(income.model_dump().values())
    total_deductions, deduction_citations = _capped_deductions(deductions, regime)
    taxable_income = max(gross_total_income - total_deductions, 0.0)

    # NRI: no rebate 87A; slabs differ only for old regime (not handled in v1).
    is_nri = taxpayer_type == TaxpayerType.non_resident

    tax_before_rebate = _apply_slabs(taxable_income, regime)

    # Rebate 87A: resident individuals only, for taxable income up to 7L.
    rebate = 0.0
    if not is_nri and regime == Regime.new and taxable_income <= REBATE_87A["new_regime_threshold"]:
        rebate = min(tax_before_rebate, REBATE_87A["max_amount"])
    elif (
        not is_nri and regime == Regime.old and taxable_income <= REBATE_87A["old_regime_threshold"]
    ):
        rebate = min(tax_before_rebate, REBATE_87A["max_amount"])

    tax_after_rebate = max(tax_before_rebate - rebate, 0.0)
    surcharge = _surcharge(tax_after_rebate, taxable_income)
    surcharge = _marginal_relief(tax_after_rebate, surcharge, taxable_income)

    tax_plus_surcharge = tax_after_rebate + surcharge
    cess = tax_plus_surcharge * CESS_RATE

    total_tax = tax_plus_surcharge + cess
    net_tax_refund_due = total_tax - tds_tcs_credit - advance_tax_paid - foreign_tax_credit

    effective_tax_rate = (total_tax / taxable_income) if taxable_income > 0 else 0.0

    citations: list[dict[str, Any]] = [
        {"type": "rule", "section": "slabs", "regime": regime.value},
        {"type": "rule", "section": "rebate_87a", "amount": rebate},
        {"type": "rule", "section": "cess", "rate": CESS_RATE},
        *deduction_citations,
    ]

    return TaxComputationResult(
        assessment_year=assessment_year,
        taxpayer_type=taxpayer_type,
        regime=regime,
        gross_total_income=gross_total_income,
        total_deductions=total_deductions,
        taxable_income=taxable_income,
        tax_liability=tax_before_rebate,
        surcharge=surcharge,
        cess=cess,
        rebate_87a=rebate,
        total_tax=total_tax,
        tds_tcs_credit=tds_tcs_credit,
        advance_tax_paid=advance_tax_paid,
        foreign_tax_credit=foreign_tax_credit,
        net_tax_refund_due=net_tax_refund_due,
        effective_tax_rate=effective_tax_rate,
        citations=citations,
    )


def compute_tax_liability_from_input(inp: TaxInput) -> TaxComputationResult:
    """Convenience wrapper that accepts a TaxInput model."""
    return compute_tax_liability(
        assessment_year=inp.assessment_year,
        taxpayer_type=inp.taxpayer_type,
        regime=inp.regime,
        age=inp.age,
        income=inp.income,
        deductions=inp.deductions,
        tds_tcs_credit=inp.tds_tcs_credit,
        advance_tax_paid=inp.advance_tax_paid,
        foreign_tax_credit=inp.foreign_tax_credit,
    )
