"""In-memory capability + tool registry for Verra.

TODO: replace with persistent registry backed by Postgres agent_versions / tool_defs tables.
"""

from __future__ import annotations

from typing import Any

CAPABILITIES: dict[str, dict[str, Any]] = {
    "tax:tax_analysis": {
        "module": "tax",
        "capability": "tax_analysis",
        "name": "Indian Tax Analysis",
        "description": "End-to-end tax computation for Indian residents and NRIs.",
        "version": "0.1.0",
        "planner_template": "tax_analysis",
        "required_tools": [
            "tax:retrieve_tax_rules",
            "tax:retrieve_client_docs",
            "tax:compute_salary_exemptions",
            "tax:compute_tax_liability",
            "tax:compare_regimes",
            "tax:reconcile_tds",
        ],
        "model_tier": "large",
        "approval_required": True,
    },
    "tax:tax_qa": {
        "module": "tax",
        "capability": "tax_qa",
        "name": "Indian Tax Q&A",
        "description": "Answer Indian tax rules and planning questions with citations.",
        "version": "0.1.0",
        "planner_template": "tax_qa",
        "required_tools": ["tax:retrieve_tax_rules", "tax:retrieve_client_docs"],
        "model_tier": "small",
        "approval_required": False,
    },
    "tax:tax_scenario": {
        "module": "tax",
        "capability": "tax_scenario",
        "name": "Tax Scenario Modeling",
        "description": "Compare tax outcomes under changed assumptions.",
        "version": "0.1.0",
        "planner_template": "tax_scenario",
        "required_tools": [
            "tax:compute_tax_liability",
            "tax:compare_regimes",
            "tax:build_scenario",
        ],
        "model_tier": "large",
        "approval_required": False,
    },
    "tax:document_reconcile": {
        "module": "tax",
        "capability": "document_reconcile",
        "name": "TDS/Income Reconciliation",
        "description": "Cross-check Form 16, Form 26AS, AIS for TDS and income mismatches.",
        "version": "0.1.0",
        "planner_template": "document_reconcile",
        "required_tools": [
            "tax:retrieve_client_docs",
            "tax:reconcile_tds",
        ],
        "model_tier": "small",
        "approval_required": False,
    },
    "assistant:portfolio_analysis": {
        "module": "assistant",
        "capability": "portfolio_analysis",
        "name": "Portfolio Analysis",
        "description": (
            "Consolidate client holdings and draft regulation-grounded allocation "
            "and tax-efficiency insights (SEBI-suitability aware)."
        ),
        "version": "0.1.0",
        "planner_template": "portfolio_analysis",
        "required_tools": [
            "holdings:fetch",
            "holdings:consolidate",
            "tax:retrieve_tax_rules",
        ],
        "model_tier": "medium",
        "approval_required": False,
    },
    "assistant:financial_planning": {
        "module": "assistant",
        "capability": "financial_planning",
        "name": "Financial Planning Draft",
        "description": (
            "Goal-based financial plan draft (advice-like): holdings consolidation, "
            "optional tax computation, rules grounding — requires human approval."
        ),
        "version": "0.1.0",
        "planner_template": "financial_planning",
        "required_tools": [
            "holdings:fetch",
            "holdings:consolidate",
            "tax:compute_tax_liability",
            "tax:retrieve_tax_rules",
        ],
        "model_tier": "large",
        "approval_required": True,
    },
    "assistant:general_qa": {
        "module": "assistant",
        "capability": "general_qa",
        "name": "General Regulatory Q&A",
        "description": (
            "Answer general finance/regulatory questions grounded on the versioned "
            "rules corpus with citations."
        ),
        "version": "0.1.0",
        "planner_template": "general_qa",
        "required_tools": ["tax:retrieve_tax_rules"],
        "model_tier": "medium",
        "approval_required": False,
    },
    "tax:filing_prep": {
        "module": "tax",
        "capability": "filing_prep",
        "name": "ITR Filing Preparation",
        "description": "Assemble draft ITR schedules and review package for human sign-off.",
        "version": "0.1.0",
        "planner_template": "filing_prep",
        "required_tools": [
            "tax:compute_tax_liability",
            "tax:compare_regimes",
            "tax:reconcile_tds",
            "tax:compute_advance_tax",
            "tax:generate_draft_output",
        ],
        "model_tier": "large",
        "approval_required": True,
    },
}

TOOLS: dict[str, dict[str, Any]] = {
    # ── Deterministic calculators ─────────────────────────────────────────────
    "tax:compute_tax_liability": {
        "name": "compute_tax_liability",
        "module": "tax",
        "description": "Compute Indian income-tax liability deterministically (AY 2025-26).",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessmentYear": {"type": "string"},
                "taxpayerType": {
                    "type": "string",
                    "enum": ["resident_ordinarily", "resident_not_ordinarily", "non_resident"],
                },
                "regime": {"type": "string", "enum": ["old", "new"]},
                "age": {"type": "integer"},
                "income": {
                    "type": "object",
                    "properties": {
                        "salary": {"type": "number"},
                        "houseProperty": {"type": "number"},
                        "capitalGains": {"type": "number"},
                        "business": {"type": "number"},
                        "otherSources": {"type": "number"},
                        "foreign": {"type": "number"},
                    },
                },
                "deductions": {
                    "type": "object",
                    "properties": {
                        "standardDeduction": {"type": "number"},
                        "section80c": {"type": "number"},
                        "section80d": {"type": "number"},
                        "section80ccd1b": {"type": "number"},
                        "section80g": {"type": "number"},
                        "section24": {"type": "number"},
                        "section80e": {"type": "number"},
                        "section80tta": {"type": "number"},
                        "other": {"type": "number"},
                    },
                },
            },
            "required": ["assessmentYear", "taxpayerType", "regime", "income"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/compute_tax_liability",
    },
    "tax:compare_regimes": {
        "name": "compare_regimes",
        "module": "tax",
        "description": "Compare old vs new tax regime; returns recommended regime and tax saving.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessmentYear": {"type": "string"},
                "taxpayerType": {"type": "string"},
                "regime": {"type": "string"},
                "age": {"type": "integer"},
                "income": {"type": "object"},
                "deductions": {"type": "object"},
            },
            "required": ["assessmentYear", "taxpayerType", "income"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/compare_regimes",
    },
    "tax:compute_salary_exemptions": {
        "name": "compute_salary_exemptions",
        "module": "tax",
        "description": "Compute HRA, LTA, and standard deduction exemptions from salary income.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "basicSalary": {"type": "number"},
                "hraReceived": {"type": "number"},
                "rentPaid": {"type": "number"},
                "city": {"type": "string"},
                "ltaReceived": {"type": "number"},
                "actualTravelCost": {"type": "number"},
                "regime": {"type": "string", "enum": ["old", "new"]},
            },
            "required": ["basicSalary"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/compute_salary_exemptions",
    },
    "tax:compute_hra_exemption": {
        "name": "compute_hra_exemption",
        "module": "tax",
        "description": "Compute HRA exemption under Section 10(13A) and Rule 2A.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "basicSalary": {"type": "number"},
                "hraReceived": {"type": "number"},
                "rentPaid": {"type": "number"},
                "city": {"type": "string"},
            },
            "required": ["basicSalary", "hraReceived", "rentPaid"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/compute_hra_exemption",
    },
    "tax:compute_advance_tax": {
        "name": "compute_advance_tax",
        "module": "tax",
        "description": "Compute advance tax instalment schedule and interest under 234B/234C.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessmentYear": {"type": "string"},
                "estimatedTaxLiability": {"type": "number"},
                "advanceTaxPaid": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dateLabel": {"type": "string"},
                            "amount": {"type": "number"},
                        },
                    },
                },
            },
            "required": ["assessmentYear", "estimatedTaxLiability"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/compute_advance_tax",
    },
    "tax:reconcile_tds": {
        "name": "reconcile_tds",
        "module": "tax",
        "description": "Cross-check TDS entries from Form 16, Form 26AS, and AIS; flag mismatches.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "form16Entries": {"type": "array", "items": {"type": "object"}},
                "form26asEntries": {"type": "array", "items": {"type": "object"}},
                "aisEntries": {"type": "array", "items": {"type": "object"}},
                "varianceThreshold": {"type": "number"},
            },
            "required": [],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/reconcile_tds",
    },
    # ── Holdings service tools (HTTP, deterministic data fetch/aggregation) ──
    "holdings:fetch": {
        "name": "fetch",
        "module": "assistant",
        "description": "Fetch client holdings across accounts from the holdings service.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "tenantId": {"type": "string"},
                "clientId": {"type": "string"},
            },
            "required": ["tenantId", "clientId"],
        },
        "deterministic": True,
        "endpoint": "internal/holdings",
    },
    "holdings:consolidate": {
        "name": "consolidate",
        "module": "assistant",
        "description": (
            "Consolidate client holdings into a portfolio view (totals, allocation, "
            "unrealized gains) — deterministic aggregation, no LLM."
        ),
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "tenantId": {"type": "string"},
                "clientId": {"type": "string"},
                "annualIncome": {"type": "number"},
            },
            "required": ["tenantId", "clientId"],
        },
        "deterministic": True,
        "endpoint": "internal/holdings/consolidation",
    },
    # ── Retrieval / RAG tools (non-deterministic) ─────────────────────────────
    "tax:retrieve_tax_rules": {
        "name": "retrieve_tax_rules",
        "module": "tax",
        "description": (
            "Retrieve versioned Indian regulatory rules (income tax, SEBI, FEMA/RBI, "
            "IRDAI, GST) via deterministic keyword search over the rules corpus."
        ),
        "version": "0.2.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "assessmentYear": {"type": "string"},
                "section": {"type": "string"},
                "taxpayerType": {"type": "string"},
                "regulator": {
                    "type": "string",
                    "enum": ["income_tax", "sebi", "rbi_fema", "irdai", "gst", "mca"],
                },
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["query"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/retrieve_tax_rules",
    },
    "tax:retrieve_client_docs": {
        "name": "retrieve_client_docs",
        "module": "tax",
        "description": "Retrieve parsed client tax documents and doc_chunks for RAG.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "clientId": {"type": "string"},
                "assessmentYear": {"type": "string"},
                "docTypes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["clientId", "assessmentYear"],
        },
        "deterministic": False,
        "endpoint": "internal/tools/tax/retrieve_client_docs",
    },
    "tax:parse_indian_tax_document": {
        "name": "parse_indian_tax_document",
        "module": "tax",
        "description": "OCR + structured extraction for Form 16, 26AS, AIS, bank statements.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "documentId": {"type": "string"},
                "docType": {
                    "type": "string",
                    "enum": [
                        "form_16",
                        "form_26as",
                        "ais",
                        "bank_statement",
                        "capital_gains_statement",
                        "rental_agreement",
                        "foreign_income",
                    ],
                },
            },
            "required": ["documentId", "docType"],
        },
        "deterministic": False,
        "endpoint": "internal/tools/tax/parse_indian_tax_document",
    },
    "tax:build_scenario": {
        "name": "build_scenario",
        "module": "tax",
        "description": "Clone a base tax profile and recompute under new assumptions.",
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "baseProfileId": {"type": "string"},
                "assumptions": {"type": "object"},
            },
            "required": ["baseProfileId", "assumptions"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/build_scenario",
    },
    "tax:determine_residential_status": {
        "name": "determine_residential_status",
        "module": "tax",
        "description": (
            "Determine residential status (resident/RNOR/NRI) under Section 6 "
            "of the Income Tax Act."
        ),
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "daysInIndiaCurrentYear": {"type": "integer"},
                "daysInIndiaPrior4Years": {"type": "integer"},
                "daysInIndiaPrior7Years": {"type": "integer"},
                "indianCitizen": {"type": "boolean"},
                "priorStatus": {"type": "string"},
            },
            "required": ["daysInIndiaCurrentYear"],
        },
        "deterministic": True,
        "endpoint": "internal/tools/tax/determine_residential_status",
    },
    "tax:generate_draft_output": {
        "name": "generate_draft_output",
        "module": "tax",
        "description": (
            "Generate a draft computation report or ITR schedule (templated, "
            "requires human approval before delivery)."
        ),
        "version": "0.1.0",
        "input_schema": {
            "type": "object",
            "properties": {
                "runId": {"type": "string"},
                "outputType": {
                    "type": "string",
                    "enum": ["computation_sheet", "client_letter", "itr_schedule"],
                },
            },
            "required": ["runId", "outputType"],
        },
        "deterministic": False,
        "endpoint": "internal/tools/tax/generate_draft_output",
    },
}


def resolve_capability(module: str, capability: str) -> dict[str, Any] | None:
    return CAPABILITIES.get(f"{module}:{capability}")


def resolve_tool(name: str) -> dict[str, Any] | None:
    return TOOLS.get(name)


def list_capabilities(module: str | None = None) -> list[dict[str, Any]]:
    if module:
        return [c for c in CAPABILITIES.values() if c["module"] == module]
    return list(CAPABILITIES.values())


def list_tools(module: str | None = None) -> list[dict[str, Any]]:
    if module:
        return [t for t in TOOLS.values() if t["module"] == module]
    return list(TOOLS.values())
