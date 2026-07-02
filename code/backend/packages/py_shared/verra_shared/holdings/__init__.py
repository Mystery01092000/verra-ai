"""Holdings-consolidation domain: models + deterministic consolidation engine."""

from .consolidate import (
    CONCENTRATION_LIMIT,
    DEBT_RATIO_LIMIT,
    LIFE_COVER_INCOME_MULTIPLE,
    AdvisoryFlag,
    CategoryBreakdown,
    CategoryGroup,
    ConsolidationResult,
    FlagCode,
    GuidelineCitation,
    InsuranceCover,
    consolidate,
)
from .models import (
    LOAN_TYPES,
    Holding,
    HoldingCreate,
    HoldingType,
    mask_account,
)

__all__ = [
    # Models
    "Holding",
    "HoldingCreate",
    "HoldingType",
    "LOAN_TYPES",
    "mask_account",
    # Consolidation
    "consolidate",
    "ConsolidationResult",
    "CategoryBreakdown",
    "CategoryGroup",
    "InsuranceCover",
    "AdvisoryFlag",
    "FlagCode",
    "GuidelineCitation",
    "CONCENTRATION_LIMIT",
    "DEBT_RATIO_LIMIT",
    "LIFE_COVER_INCOME_MULTIPLE",
]
