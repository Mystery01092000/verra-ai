"""Deterministic holdings consolidation — pure functions, no LLM anywhere.

Money math and advisory flags here are computed by deterministic code only
(project rule: figures come from calculators, never from a model). Every flag
carries an honest citation to the guideline it is derived from; the thresholds
below are common industry heuristics, not statutory requirements, and are
labelled as such.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

from .models import LOAN_TYPES, Holding, HoldingType, _HoldingsBase

# ── Advisory thresholds (industry heuristics — see citations below) ───────────

#: A single holding above this share of total assets is flagged as concentrated.
CONCENTRATION_LIMIT = 0.25

#: Common thumb rule: life cover should be at least this multiple of annual income.
LIFE_COVER_INCOME_MULTIPLE = 10.0

#: Liabilities/assets (or annual EMI/annual income) above this ratio is flagged.
DEBT_RATIO_LIMIT = 0.50


class CategoryGroup(StrEnum):
    equity = "equity"
    debt = "debt"
    retirement = "retirement"
    real_assets = "real_assets"
    cash = "cash"
    other = "other"


# Grouping decisions (documented per requirement):
# - equity: mutual_fund + stock (market-linked growth assets).
# - debt: bond + FD + RD + PPF + EPF. PPF/EPF double as retirement vehicles, but
#   each type is assigned to exactly ONE group so the percentage allocation sums
#   to 100%; they are classified as debt because they are fixed-income,
#   government-administered instruments.
# - retirement: NPS only (market-linked and locked until retirement, so it is
#   kept distinct from the fixed-income debt bucket).
# - real_assets: real_estate + gold.
# - cash: cash.
# - other: catch-all for anything not mapped above (insurance current values —
#   e.g. ULIP fund value or policy surrender value — and HoldingType.other).
#   Insurance *cover* (sum assured) is reported separately in insuranceCover,
#   not as an asset allocation.
_GROUP_BY_TYPE: Mapping[HoldingType, CategoryGroup] = {
    HoldingType.mutual_fund: CategoryGroup.equity,
    HoldingType.stock: CategoryGroup.equity,
    HoldingType.bond: CategoryGroup.debt,
    HoldingType.fixed_deposit: CategoryGroup.debt,
    HoldingType.recurring_deposit: CategoryGroup.debt,
    HoldingType.ppf: CategoryGroup.debt,
    HoldingType.epf: CategoryGroup.debt,
    HoldingType.nps: CategoryGroup.retirement,
    HoldingType.real_estate: CategoryGroup.real_assets,
    HoldingType.gold: CategoryGroup.real_assets,
    HoldingType.cash: CategoryGroup.cash,
}

#: Life-cover types: ULIPs bundle a life cover with the investment component,
#: so their sum assured counts toward total life cover alongside term/whole-life.
_LIFE_COVER_TYPES: frozenset[HoldingType] = frozenset(
    {HoldingType.insurance_life, HoldingType.insurance_ulip}
)


class FlagCode(StrEnum):
    concentration = "concentration"
    underinsured_life = "underinsured_life"
    high_debt_ratio = "high_debt_ratio"
    no_health_cover = "no_health_cover"


class GuidelineCitation(_HoldingsBase):
    """Honest sourcing for an advisory flag — names the guideline it derives from."""

    source: str
    rule: str


class AdvisoryFlag(_HoldingsBase):
    code: FlagCode
    message: str
    citation: GuidelineCitation


class CategoryBreakdown(_HoldingsBase):
    category: CategoryGroup
    amount: float
    percentage: float


class InsuranceCover(_HoldingsBase):
    life_sum_assured: float = 0.0
    health_sum_assured: float = 0.0


class ConsolidationResult(_HoldingsBase):
    total_assets: float
    total_liabilities: float
    net_worth: float
    breakdown: list[CategoryBreakdown]
    insurance_cover: InsuranceCover
    flags: list[AdvisoryFlag]
    citations: list[GuidelineCitation]


_CITATION_CONCENTRATION = GuidelineCitation(
    source="Industry heuristic — portfolio diversification guidance",
    rule=(
        f"No single holding should exceed {CONCENTRATION_LIMIT:.0%} of total assets "
        "(common diversification thumb rule, not a statutory limit)"
    ),
)
_CITATION_UNDERINSURED_LIFE = GuidelineCitation(
    source="Industry heuristic — life insurance adequacy thumb rule",
    rule=(
        f"Total life cover (sum assured) should be at least "
        f"{LIFE_COVER_INCOME_MULTIPLE:.0f}x annual income "
        "(widely used '10x income' thumb rule, not a statutory requirement)"
    ),
)
_CITATION_HIGH_DEBT_RATIO = GuidelineCitation(
    source="Industry heuristic — household debt-burden guidance",
    rule=(
        f"Total liabilities relative to assets, or annual EMI relative to annual "
        f"income, should stay below {DEBT_RATIO_LIMIT:.0%} "
        "(common lender/planner threshold, not a statutory limit)"
    ),
)
_CITATION_NO_HEALTH_COVER = GuidelineCitation(
    source="Industry heuristic — financial-planning protection checklist",
    rule=(
        "Every household portfolio should include health insurance cover "
        "(standard financial-planning guidance, not a statutory requirement)"
    ),
)


def _asset_holdings(holdings: Sequence[Holding]) -> tuple[Holding, ...]:
    return tuple(h for h in holdings if h.type not in LOAN_TYPES)


def _loan_holdings(holdings: Sequence[Holding]) -> tuple[Holding, ...]:
    return tuple(h for h in holdings if h.type in LOAN_TYPES)


def _liability_amount(loan: Holding) -> float:
    """Outstanding amount when reported; otherwise fall back to current value."""
    return loan.outstanding_amount if loan.outstanding_amount is not None else loan.current_value


def _build_breakdown(
    assets: Sequence[Holding], total_assets: float
) -> tuple[CategoryBreakdown, ...]:
    """Amounts and percentage allocation per category group (always all groups)."""
    amounts = {
        group: sum(
            h.current_value
            for h in assets
            if _GROUP_BY_TYPE.get(h.type, CategoryGroup.other) is group
        )
        for group in CategoryGroup
    }
    return tuple(
        CategoryBreakdown(
            category=group,
            amount=amount,
            percentage=(amount / total_assets * 100.0) if total_assets > 0 else 0.0,
        )
        for group, amount in amounts.items()
    )


def _insurance_cover(holdings: Sequence[Holding]) -> InsuranceCover:
    return InsuranceCover(
        life_sum_assured=sum(h.sum_assured or 0.0 for h in holdings if h.type in _LIFE_COVER_TYPES),
        health_sum_assured=sum(
            h.sum_assured or 0.0 for h in holdings if h.type is HoldingType.insurance_health
        ),
    )


def _concentration_flags(
    assets: Sequence[Holding], total_assets: float
) -> tuple[AdvisoryFlag, ...]:
    if total_assets <= 0:
        return ()
    concentrated = tuple(h for h in assets if h.current_value / total_assets > CONCENTRATION_LIMIT)
    if not concentrated:
        return ()
    names = ", ".join(f"'{h.name}'" for h in concentrated)
    return (
        AdvisoryFlag(
            code=FlagCode.concentration,
            message=(
                f"Holding(s) {names} each exceed {CONCENTRATION_LIMIT:.0%} of total "
                "assets; consider diversifying."
            ),
            citation=_CITATION_CONCENTRATION,
        ),
    )


def _underinsured_life_flags(
    cover: InsuranceCover, annual_income: float | None
) -> tuple[AdvisoryFlag, ...]:
    if annual_income is None or annual_income <= 0:
        return ()
    required = LIFE_COVER_INCOME_MULTIPLE * annual_income
    if cover.life_sum_assured >= required:
        return ()
    return (
        AdvisoryFlag(
            code=FlagCode.underinsured_life,
            message=(
                f"Total life cover {cover.life_sum_assured:,.0f} is below "
                f"{LIFE_COVER_INCOME_MULTIPLE:.0f}x annual income ({required:,.0f})."
            ),
            citation=_CITATION_UNDERINSURED_LIFE,
        ),
    )


def _high_debt_ratio_flags(
    loans: Sequence[Holding],
    total_assets: float,
    total_liabilities: float,
    annual_income: float | None,
) -> tuple[AdvisoryFlag, ...]:
    reasons: tuple[str, ...] = ()
    if total_liabilities > 0 and (
        total_assets <= 0 or total_liabilities / total_assets > DEBT_RATIO_LIMIT
    ):
        reasons = (*reasons, f"liabilities exceed {DEBT_RATIO_LIMIT:.0%} of total assets")
    annual_emi = sum((loan.emi or 0.0) * 12.0 for loan in loans)
    if annual_income is not None and annual_income > 0:
        if annual_emi / annual_income > DEBT_RATIO_LIMIT:
            reasons = (
                *reasons,
                f"annual EMI outgo exceeds {DEBT_RATIO_LIMIT:.0%} of annual income",
            )
    if not reasons:
        return ()
    return (
        AdvisoryFlag(
            code=FlagCode.high_debt_ratio,
            message=f"High debt burden: {'; '.join(reasons)}.",
            citation=_CITATION_HIGH_DEBT_RATIO,
        ),
    )


def _no_health_cover_flags(holdings: Sequence[Holding]) -> tuple[AdvisoryFlag, ...]:
    if any(h.type is HoldingType.insurance_health for h in holdings):
        return ()
    return (
        AdvisoryFlag(
            code=FlagCode.no_health_cover,
            message="No health insurance found in the portfolio.",
            citation=_CITATION_NO_HEALTH_COVER,
        ),
    )


def _dedupe_citations(flags: Sequence[AdvisoryFlag]) -> tuple[GuidelineCitation, ...]:
    seen: tuple[GuidelineCitation, ...] = ()
    for flag in flags:
        if flag.citation not in seen:
            seen = (*seen, flag.citation)
    return seen


def consolidate(
    holdings: Sequence[Holding], *, annual_income: float | None = None
) -> ConsolidationResult:
    """Consolidate holdings into totals, allocation breakdown and advisory flags.

    Pure and deterministic: same inputs always produce the same result. Flags
    are only emitted for non-empty portfolios (an empty portfolio has nothing
    to advise on). ``annual_income`` (optional) enables the income-relative
    checks (underinsured life cover, EMI-to-income debt burden).
    """
    assets = _asset_holdings(holdings)
    loans = _loan_holdings(holdings)
    total_assets = sum(h.current_value for h in assets)
    total_liabilities = sum(_liability_amount(loan) for loan in loans)
    cover = _insurance_cover(holdings)

    flags: tuple[AdvisoryFlag, ...] = ()
    if holdings:
        flags = (
            *_concentration_flags(assets, total_assets),
            *_underinsured_life_flags(cover, annual_income),
            *_high_debt_ratio_flags(loans, total_assets, total_liabilities, annual_income),
            *_no_health_cover_flags(holdings),
        )

    return ConsolidationResult(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=total_assets - total_liabilities,
        breakdown=list(_build_breakdown(assets, total_assets)),
        insurance_cover=cover,
        flags=list(flags),
        citations=list(_dedupe_citations(flags)),
    )
