"""Unit tests for the deterministic holdings consolidation engine."""

from __future__ import annotations

import pytest
from verra_shared.holdings import (
    CategoryGroup,
    FlagCode,
    Holding,
    HoldingType,
    consolidate,
    mask_account,
)


def _holding(**overrides: object) -> Holding:
    base: dict[str, object] = {
        "id": "h1",
        "tenant_id": "t1",
        "client_id": "c1",
        "type": HoldingType.mutual_fund,
        "name": "Test holding",
        "current_value": 100_000.0,
    }
    return Holding.model_validate({**base, **overrides})


def _flag_codes(holdings: list[Holding], annual_income: float | None = None) -> set[FlagCode]:
    return {f.code for f in consolidate(holdings, annual_income=annual_income).flags}


# ── Empty portfolio ────────────────────────────────────────────────────────────


def test_empty_portfolio_all_zero_and_no_flags() -> None:
    result = consolidate([])
    assert result.total_assets == 0
    assert result.total_liabilities == 0
    assert result.net_worth == 0
    assert result.flags == []
    assert result.citations == []
    assert all(row.amount == 0 and row.percentage == 0 for row in result.breakdown)


# ── Mixed portfolio math ───────────────────────────────────────────────────────


def test_mixed_portfolio_totals_breakdown_and_cover() -> None:
    holdings = [
        _holding(id="mf", type=HoldingType.mutual_fund, current_value=200_000),
        _holding(id="st", type=HoldingType.stock, current_value=100_000),
        _holding(id="fd", type=HoldingType.fixed_deposit, current_value=300_000),
        _holding(id="pf", type=HoldingType.ppf, current_value=100_000),
        _holding(id="np", type=HoldingType.nps, current_value=100_000),
        _holding(id="re", type=HoldingType.real_estate, current_value=150_000),
        _holding(id="au", type=HoldingType.gold, current_value=50_000),
        _holding(id="ca", type=HoldingType.cash, current_value=100_000),
        _holding(
            id="li",
            type=HoldingType.insurance_life,
            current_value=0,
            sum_assured=5_000_000,
            premium_annual=25_000,
        ),
        _holding(
            id="hi",
            type=HoldingType.insurance_health,
            current_value=0,
            sum_assured=1_000_000,
        ),
        _holding(
            id="hl",
            type=HoldingType.loan_home,
            current_value=0,
            outstanding_amount=400_000,
            emi=8_000,
        ),
    ]
    result = consolidate(holdings)

    assert result.total_assets == pytest.approx(1_100_000)
    assert result.total_liabilities == pytest.approx(400_000)
    assert result.net_worth == pytest.approx(700_000)

    amounts = {row.category: row.amount for row in result.breakdown}
    assert amounts[CategoryGroup.equity] == pytest.approx(300_000)
    assert amounts[CategoryGroup.debt] == pytest.approx(400_000)  # FD + PPF
    assert amounts[CategoryGroup.retirement] == pytest.approx(100_000)  # NPS
    assert amounts[CategoryGroup.real_assets] == pytest.approx(200_000)
    assert amounts[CategoryGroup.cash] == pytest.approx(100_000)
    assert amounts[CategoryGroup.other] == pytest.approx(0)  # insurance value is 0

    assert result.insurance_cover.life_sum_assured == pytest.approx(5_000_000)
    assert result.insurance_cover.health_sum_assured == pytest.approx(1_000_000)


def test_loan_liability_falls_back_to_current_value() -> None:
    result = consolidate([_holding(id="pl", type=HoldingType.loan_personal, current_value=75_000)])
    assert result.total_liabilities == pytest.approx(75_000)
    assert result.net_worth == pytest.approx(-75_000)


def test_percentages_sum_to_100_for_nonempty_assets() -> None:
    holdings = [
        _holding(id="a", type=HoldingType.stock, current_value=123_456.78),
        _holding(id="b", type=HoldingType.bond, current_value=98_765.43),
        _holding(id="c", type=HoldingType.gold, current_value=11_111.11),
        _holding(id="d", type=HoldingType.other, current_value=7_777.77),
    ]
    result = consolidate(holdings)
    assert sum(row.percentage for row in result.breakdown) == pytest.approx(100.0)


def test_ulip_value_counts_in_other_and_cover_in_life() -> None:
    result = consolidate(
        [
            _holding(
                id="u", type=HoldingType.insurance_ulip, current_value=50_000, sum_assured=1_500_000
            )
        ]
    )
    amounts = {row.category: row.amount for row in result.breakdown}
    assert amounts[CategoryGroup.other] == pytest.approx(50_000)
    assert result.insurance_cover.life_sum_assured == pytest.approx(1_500_000)


# ── Flags: trigger and clear ───────────────────────────────────────────────────


def _balanced_portfolio() -> list[Holding]:
    """Five equal asset holdings (20% each) + health cover: no flags expected."""
    return [
        _holding(id="1", type=HoldingType.mutual_fund, current_value=100_000),
        _holding(id="2", type=HoldingType.stock, current_value=100_000),
        _holding(id="3", type=HoldingType.fixed_deposit, current_value=100_000),
        _holding(id="4", type=HoldingType.gold, current_value=100_000),
        _holding(id="5", type=HoldingType.cash, current_value=100_000),
        _holding(id="6", type=HoldingType.insurance_health, current_value=0, sum_assured=500_000),
    ]


def test_balanced_portfolio_has_no_flags() -> None:
    assert _flag_codes(_balanced_portfolio()) == set()


def test_concentration_triggers_and_clears() -> None:
    concentrated = [
        _holding(id="big", type=HoldingType.stock, name="Single stock", current_value=800_000),
        _holding(id="rest", type=HoldingType.cash, current_value=200_000),
        _holding(id="hi", type=HoldingType.insurance_health, current_value=0, sum_assured=1),
    ]
    assert FlagCode.concentration in _flag_codes(concentrated)
    assert FlagCode.concentration not in _flag_codes(_balanced_portfolio())


def test_underinsured_life_triggers_clears_and_requires_income() -> None:
    portfolio = [
        *_balanced_portfolio(),
        _holding(id="li", type=HoldingType.insurance_life, current_value=0, sum_assured=2_000_000),
    ]
    # 2,000,000 < 10 x 1,000,000 → flagged
    assert FlagCode.underinsured_life in _flag_codes(portfolio, annual_income=1_000_000)
    # 2,000,000 >= 10 x 200,000 → clear
    assert FlagCode.underinsured_life not in _flag_codes(portfolio, annual_income=200_000)
    # No income provided → check skipped entirely
    assert FlagCode.underinsured_life not in _flag_codes(portfolio)


def test_high_debt_ratio_triggers_on_liabilities_and_clears() -> None:
    indebted = [
        *_balanced_portfolio(),  # assets 500,000
        _holding(id="hl", type=HoldingType.loan_home, current_value=0, outstanding_amount=300_000),
    ]
    assert FlagCode.high_debt_ratio in _flag_codes(indebted)  # 300k/500k = 60%

    modest = [
        *_balanced_portfolio(),
        _holding(
            id="vl", type=HoldingType.loan_vehicle, current_value=0, outstanding_amount=100_000
        ),
    ]
    assert FlagCode.high_debt_ratio not in _flag_codes(modest)  # 100k/500k = 20%


def test_high_debt_ratio_triggers_on_emi_to_income() -> None:
    portfolio = [
        *_balanced_portfolio(),
        _holding(
            id="hl",
            type=HoldingType.loan_home,
            current_value=0,
            outstanding_amount=100_000,  # 20% of assets — below the asset-ratio limit
            emi=30_000,  # 360,000/yr vs income 600,000 = 60%
        ),
    ]
    assert FlagCode.high_debt_ratio in _flag_codes(portfolio, annual_income=600_000)
    assert FlagCode.high_debt_ratio not in _flag_codes(portfolio, annual_income=2_000_000)


def test_no_health_cover_triggers_and_clears() -> None:
    without_health = [_holding(id="1", type=HoldingType.cash, current_value=10_000)]
    assert FlagCode.no_health_cover in _flag_codes(without_health)
    assert FlagCode.no_health_cover not in _flag_codes(_balanced_portfolio())


def test_every_flag_carries_a_citation_and_citations_are_collected() -> None:
    result = consolidate(
        [_holding(id="big", type=HoldingType.stock, current_value=1_000_000)],
        annual_income=1_000_000,
    )
    assert result.flags, "expected at least one flag"
    assert all(f.citation.source and f.citation.rule for f in result.flags)
    assert {f.citation.rule for f in result.flags} == {c.rule for c in result.citations}


# ── Masking ────────────────────────────────────────────────────────────────────


def test_mask_account_keeps_last_4_only() -> None:
    assert mask_account("1234567890") == "****7890"
    assert mask_account("AB-99-12345678") == "****5678"


def test_mask_account_short_values_fully_masked_and_idempotent() -> None:
    assert mask_account("1234") == "****"
    assert mask_account("12") == "****"
    assert mask_account(mask_account("1234567890")) == "****7890"


def test_holding_masked_returns_new_copy_without_mutation() -> None:
    holding = _holding(folio_or_account="FOLIO-123456789")
    masked = holding.masked()
    assert masked.folio_or_account == "****6789"
    assert holding.folio_or_account == "FOLIO-123456789"  # original untouched
    assert masked is not holding


def test_holding_masked_noop_when_no_folio() -> None:
    holding = _holding()
    assert holding.masked().folio_or_account is None


# ── Validation ─────────────────────────────────────────────────────────────────


def test_negative_current_value_rejected() -> None:
    with pytest.raises(ValueError):
        _holding(current_value=-1)


def test_camel_case_wire_format() -> None:
    holding = Holding.model_validate(
        {
            "id": "h1",
            "tenantId": "t1",
            "clientId": "c1",
            "type": "fixed_deposit",
            "name": "FD",
            "currentValue": 1000,
            "maturityDate": "2027-03-31",
        }
    )
    dumped = holding.model_dump(by_alias=True, mode="json")
    assert dumped["tenantId"] == "t1"
    assert dumped["currentValue"] == 1000
    assert dumped["maturityDate"] == "2027-03-31"
