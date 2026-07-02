"""Internal HTTP endpoints for deterministic tax tools.

These are called by external test harnesses and by the gateway's tool-proxy.
The Executor calls these functions directly (same process) to avoid HTTP overhead.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from verra_shared.tax import (
    AdvanceTaxInput,
    HRAInput,
    ReconciliationResult,
    SalaryExemptionsInput,
    TaxInput,
    TDSEntry,
    compare_regimes,
    compute_advance_tax,
    compute_hra_exemption,
    compute_salary_exemptions,
    compute_tax_liability_from_input,
    reconcile_tds,
)
from verra_shared.tax.compare import RegimeComparison
from verra_shared.tax.models import Regime

router = APIRouter(prefix="/internal/tools/tax", tags=["tax-tools"])


class CompareRegimesRequest(TaxInput):
    """Reuses TaxInput — both regimes are computed, so `regime` is optional here."""

    regime: Regime = Regime.new


class ReconcileTDSRequest(TaxInput):
    """Body for TDS reconciliation tool."""

    form16_entries: list[dict[str, Any]] = []
    form26as_entries: list[dict[str, Any]] = []
    ais_entries: list[dict[str, Any]] = []
    variance_threshold: float = 1.0


@router.post("/compute_tax_liability")
async def tool_compute_tax_liability(body: TaxInput) -> dict[str, Any]:
    try:
        result = compute_tax_liability_from_input(body)
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/compare_regimes")
async def tool_compare_regimes(body: CompareRegimesRequest) -> dict[str, Any]:
    """Run both old and new regime and return a comparison with a recommendation."""
    try:
        result: RegimeComparison = compare_regimes(
            assessment_year=body.assessment_year,
            taxpayer_type=body.taxpayer_type,
            age=body.age,
            income=body.income,
            deductions=body.deductions,
            tds_tcs_credit=body.tds_tcs_credit,
            advance_tax_paid=body.advance_tax_paid,
            foreign_tax_credit=body.foreign_tax_credit,
        )
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/compute_salary_exemptions")
async def tool_compute_salary_exemptions(body: SalaryExemptionsInput) -> dict[str, Any]:
    try:
        result = compute_salary_exemptions(body)
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/compute_hra_exemption")
async def tool_compute_hra(body: HRAInput) -> dict[str, Any]:
    try:
        result = compute_hra_exemption(body)
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/compute_advance_tax")
async def tool_compute_advance_tax(body: AdvanceTaxInput) -> dict[str, Any]:
    try:
        result = compute_advance_tax(body)
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/reconcile_tds")
async def tool_reconcile_tds(body: ReconcileTDSRequest) -> dict[str, Any]:
    try:
        form16 = [TDSEntry(**e) for e in body.form16_entries]
        f26as = [TDSEntry(**e) for e in body.form26as_entries]
        ais = [TDSEntry(**e) for e in body.ais_entries]
        result: ReconciliationResult = reconcile_tds(
            form16_entries=form16,
            form26as_entries=f26as,
            ais_entries=ais,
            variance_threshold=body.variance_threshold,
        )
        return result.model_dump(by_alias=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
