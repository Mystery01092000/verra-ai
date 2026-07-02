"""Pydantic models for the holdings-consolidation domain (camelCase wire format)."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

#: Number of trailing characters left visible when masking an account/folio number.
MASK_VISIBLE_SUFFIX = 4

#: Prefix used in place of the hidden portion of an account/folio number.
MASK_PREFIX = "****"


class _HoldingsBase(BaseModel):
    """Base model: camelCase on the wire, snake_case in Python (matches _VerraBase)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class HoldingType(StrEnum):
    mutual_fund = "mutual_fund"
    stock = "stock"
    bond = "bond"
    fixed_deposit = "fixed_deposit"
    recurring_deposit = "recurring_deposit"
    ppf = "ppf"
    epf = "epf"
    nps = "nps"
    insurance_life = "insurance_life"
    insurance_health = "insurance_health"
    insurance_ulip = "insurance_ulip"
    loan_home = "loan_home"
    loan_personal = "loan_personal"
    loan_vehicle = "loan_vehicle"
    loan_education = "loan_education"
    real_estate = "real_estate"
    gold = "gold"
    cash = "cash"
    other = "other"


#: Holding types that represent liabilities rather than assets.
LOAN_TYPES: frozenset[HoldingType] = frozenset(
    {
        HoldingType.loan_home,
        HoldingType.loan_personal,
        HoldingType.loan_vehicle,
        HoldingType.loan_education,
    }
)


def mask_account(value: str) -> str:
    """Mask an account/folio number keeping only the last 4 characters visible.

    Values of 4 characters or fewer are fully masked so nothing leaks.
    Idempotent: masking an already-masked value yields the same result.
    """
    suffix = value[-MASK_VISIBLE_SUFFIX:] if len(value) > MASK_VISIBLE_SUFFIX else ""
    return f"{MASK_PREFIX}{suffix}"


class HoldingCreate(_HoldingsBase):
    """A holding as submitted by a client — everything except the server-assigned id."""

    tenant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    type: HoldingType
    name: str = Field(min_length=1, max_length=500)
    institution: str | None = None
    current_value: float = Field(ge=0)
    invested_value: float | None = Field(default=None, ge=0)
    units: float | None = Field(default=None, ge=0)
    folio_or_account: str | None = None
    currency: str = "INR"
    as_of_date: date | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    # Insurance-specific
    premium_annual: float | None = Field(default=None, ge=0)
    sum_assured: float | None = Field(default=None, ge=0)
    # Loan-specific
    outstanding_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0)
    emi: float | None = Field(default=None, ge=0)
    # Deposit-specific
    maturity_date: date | None = None


class Holding(HoldingCreate):
    """A stored holding (server-assigned id).

    ``folio_or_account`` must never be echoed in full on responses — use
    :meth:`masked` to obtain a response-safe copy.
    """

    id: str = Field(min_length=1)

    def masked(self) -> Holding:
        """Return a new copy with the folio/account number masked (last 4 kept)."""
        if self.folio_or_account is None:
            return self
        return self.model_copy(update={"folio_or_account": mask_account(self.folio_or_account)})
