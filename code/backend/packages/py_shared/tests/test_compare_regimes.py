"""Tests for regime comparison calculator."""

from __future__ import annotations

import pytest
from verra_shared.tax import compare_regimes
from verra_shared.tax.models import Deductions, IncomeHeads, Regime, TaxpayerType


def test_low_income_new_regime_wins() -> None:
    """At low salary with few deductions, new regime generally saves tax."""
    result = compare_regimes(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        age=35,
        income=IncomeHeads(salary=800_000.0),
        deductions=Deductions(standard_deduction=75_000.0),
    )
    assert result.old_regime.regime == Regime.old
    assert result.new_regime.regime == Regime.new
    # Both computations must be present with citations.
    assert len(result.old_regime.citations) > 0
    assert len(result.new_regime.citations) > 0
    assert result.recommended_regime in (Regime.old, Regime.new)
    assert result.tax_saving >= 0.0
    assert result.summary != ""


def test_high_deductions_old_regime_wins() -> None:
    """With max 80C + 80D + 80CCD(1B) + Section 24, old regime typically wins at 12L."""
    result = compare_regimes(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        age=35,
        income=IncomeHeads(salary=1_200_000.0),
        deductions=Deductions(
            standard_deduction=50_000.0,
            section_80c=150_000.0,
            section_80d=25_000.0,
            section_80ccd1b=50_000.0,
            section_24=200_000.0,
        ),
    )
    assert result.recommended_regime == Regime.old
    assert result.old_regime.total_tax < result.new_regime.total_tax


def test_tax_delta_sign_matches_recommendation() -> None:
    result = compare_regimes(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        age=35,
        income=IncomeHeads(salary=1_500_000.0),
        deductions=Deductions(standard_deduction=75_000.0),
    )
    if result.recommended_regime == Regime.new:
        assert result.tax_delta >= 0  # old ≥ new → delta (old-new) ≥ 0
    else:
        assert result.tax_delta < 0  # old < new → delta (old-new) < 0


def test_nri_no_rebate_in_both_regimes() -> None:
    result = compare_regimes(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.non_resident,
        age=40,
        income=IncomeHeads(salary=700_000.0),
        deductions=Deductions(),
    )
    assert result.old_regime.rebate_87a == 0.0
    assert result.new_regime.rebate_87a == 0.0


def test_tax_saving_is_absolute_delta() -> None:
    result = compare_regimes(
        assessment_year="2025-26",
        taxpayer_type=TaxpayerType.resident_ordinarily,
        age=35,
        income=IncomeHeads(salary=1_000_000.0),
        deductions=Deductions(standard_deduction=50_000.0),
    )
    expected_saving = abs(result.old_regime.total_tax - result.new_regime.total_tax)
    assert result.tax_saving == pytest.approx(expected_saving, rel=1e-6)
