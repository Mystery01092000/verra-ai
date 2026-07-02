"""Prompt construction for LLM-backed plan steps (opportunities, QA answers, drafts)."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = (
    "You are Verra's tax and financial analysis agent operating under strict "
    "human-in-the-loop review. "
    "You operate under Indian regulatory frameworks: the Income-tax Act 1961 for tax "
    "matters; SEBI regulations for anything touching investments — investment advice "
    "must be suitable and risk-profiled per the SEBI (Investment Advisers) Regulations "
    "2013; FEMA and RBI rules for NRI accounts and remittances; and IRDAI regulations "
    "for insurance. "
    "Everything you produce is a DRAFT for a licensed professional (a SEBI-registered "
    "investment adviser or chartered accountant) to review and approve — never final "
    "advice, never something sent or filed. "
    "Cite the specific rule or section for every regulatory claim — use the rule ids and "
    "sources of the retrieved rules in the context. "
    "Every figure you mention must cite its source (statutory section, rule, or client "
    "document). "
    "Never recommend specific securities, funds, or schemes by name — discuss only "
    "categories and allocations. "
    "Do NOT compute money amounts yourself under any circumstance — use only the figures "
    "provided by the deterministic calculators and consolidation outputs in the context. "
    "If a figure is not in the context, say it is unavailable rather than estimating it."
)

# Keep prompts bounded so upstream context cannot blow the model context window.
_MAX_CONTEXT_CHARS = 12_000

_OPPORTUNITIES_INSTRUCTION = (
    "Given the computed tax position below (produced by deterministic calculators), identify "
    "deduction, credit, and timing opportunities for the client. For each opportunity cite the "
    "governing rule (e.g. Section 80C, Section 80CCD(1B)). Reference only figures already "
    "present in the context — do not derive new amounts."
)

_ANSWER_INSTRUCTION = (
    "Answer the question below grounded ONLY in the provided tool results and retrieved rules. "
    "Every claim and every figure must carry a citation to its source rule or document. If the "
    "provided context does not contain enough information to answer, say so explicitly instead "
    "of guessing."
)

_DRAFT_INSTRUCTION = (
    "Write a client-ready DRAFT letter summarizing the tax analysis below. Clearly mark it as a "
    "draft pending review by a licensed professional. Every figure must carry its citation and "
    "must be taken verbatim from the calculator results in the context."
)

_PORTFOLIO_INSIGHTS_INSTRUCTION = (
    "Review the consolidated portfolio below (produced by deterministic consolidation). "
    "Provide: (1) asset allocation observations against the client's profile, (2) "
    "tax-efficiency opportunities — e.g. harvesting long-term equity gains within the "
    "₹1.25 lakh Section 112A exemption — and (3) gaps in debt allocation or insurance "
    "cover. Tie EVERY observation to a retrieved rule, citing its rule id and source. "
    "Never name specific securities, funds, or schemes. Use only figures already present "
    "in the context."
)

_FINANCIAL_PLAN_INSTRUCTION = (
    "Write a goal-based DRAFT financial plan from the consolidated data below. Structure "
    "it as: goals, emergency fund adequacy, insurance adequacy (life and health), asset "
    "allocation by category, and tax planning. Every regulatory claim must cite a "
    "retrieved rule (rule id and source); every figure must be taken verbatim from the "
    "calculator and consolidation outputs in the context. Never recommend specific "
    "securities, funds, or schemes by name. Clearly mark the output as a DRAFT pending "
    "approval by a SEBI-registered investment adviser or licensed professional."
)

_GENERIC_INSTRUCTION = (
    "Complete the step described below using ONLY the provided context. Cite the source of "
    "every figure or rule you reference."
)


def _format_context(prior_steps: list[dict[str, Any]]) -> str:
    """Serialize prior step outputs (results + citations) as bounded JSON context."""
    entries = [
        {
            "id": out.get("step", {}).get("id"),
            "kind": out.get("step", {}).get("kind"),
            "tool": out.get("step", {}).get("tool"),
            "result": out.get("result"),
            "citations": out.get("citations", []),
            "error": out.get("error"),
        }
        for out in prior_steps
    ]
    rendered = json.dumps(entries, default=str, indent=2)
    return rendered[:_MAX_CONTEXT_CHARS]


_INSTRUCTIONS: dict[str, str] = {
    "opportunities": _OPPORTUNITIES_INSTRUCTION,
    "answer": _ANSWER_INSTRUCTION,
    "draft": _DRAFT_INSTRUCTION,
    "portfolio_insights": _PORTFOLIO_INSIGHTS_INSTRUCTION,
    "financial_plan": _FINANCIAL_PLAN_INSTRUCTION,
}


def _instruction_for(instruction_key: str) -> str:
    return _INSTRUCTIONS.get(instruction_key, _GENERIC_INSTRUCTION)


def build_messages(step: dict[str, Any], prior_steps: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build the user messages for an LLM-backed step from the step spec + prior results.

    Steps may override the kind-based instruction with an explicit `instruction`
    key (e.g. `portfolio_insights` for portfolio-analysis opportunities steps).
    """
    instruction_key = str(step.get("instruction") or step.get("kind", "unknown"))
    parts = [_instruction_for(instruction_key)]

    description = step.get("description")
    if description:
        parts.append(f"Step description: {description}")

    question = (step.get("input") or {}).get("question")
    if question:
        parts.append(f"Question: {question}")

    parts.append(
        f"Context (deterministic tool results + retrieved rules):\n{_format_context(prior_steps)}"
    )

    return [{"role": "user", "content": "\n\n".join(parts)}]
