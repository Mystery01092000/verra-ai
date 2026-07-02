"""Pure guardrail checks: PII detection/masking, prompt-injection, citations.

All functions are side-effect free and return immutable tuples of findings.
PII values are always masked in findings — full values are never echoed back.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

MASK_CHAR = "*"
_UNMASKED_EDGE = 2
_SNIPPET_MAX_LEN = 60

_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Indian PAN, e.g. ABCDE1234F
    ("pii.pan", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    # Aadhaar: 12 digits, optionally grouped 4-4-4 with spaces/dashes
    ("pii.aadhaar", re.compile(r"(?<![\d-])\d{4}[ -]?\d{4}[ -]?\d{4}(?![\d-])")),
    # US SSN, e.g. 123-45-6789
    ("pii.ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("pii.email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    # Phone: optional country code + 10 digits with common separators
    (
        "pii.phone",
        re.compile(r"(?<![\d-])(?:\+?\d{1,3}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}(?![\d-])"),
    ),
)

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "injection.ignore_instructions",
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions", re.IGNORECASE),
    ),
    (
        "injection.disregard_rules",
        re.compile(
            r"disregard\s+(?:all\s+)?(?:your\s+|the\s+)?(?:rules|instructions|guidelines|policies)",
            re.IGNORECASE,
        ),
    ),
    ("injection.system_prompt_probe", re.compile(r"system\s+prompt", re.IGNORECASE)),
    (
        "injection.roleplay_jailbreak",
        re.compile(
            r"\b(?:jailbreak|DAN\s+mode|do\s+anything\s+now|developer\s+mode)\b", re.IGNORECASE
        ),
    ),
    (
        "injection.roleplay_impersonation",
        re.compile(
            r"(?:pretend\s+(?:to\s+be|you\s+are)|you\s+are\s+now\s+|act\s+as\s+if\s+you\s+"
            r"(?:have\s+no|are\s+not\s+bound))",
            re.IGNORECASE,
        ),
    ),
)

_MONEY_PATTERN = re.compile(
    r"[$₹£€]\s?\d|\b\d[\d,]*(?:\.\d+)?\s?(?:USD|INR|GBP|EUR|dollars|rupees)\b", re.IGNORECASE
)

MONEY_BEARING_ACTIONS = frozenset(
    {"tax_calculation", "filing_preparation", "refund_estimate", "payment", "money_output"}
)


@dataclass(frozen=True)
class GuardrailResult:
    """Outcome of evaluating content against all guardrail policies."""

    allowed: bool
    flagged: tuple[dict[str, str], ...]
    masked_content: str | None


def mask_value(value: str) -> str:
    """Mask a PII value, keeping at most the first/last two characters."""
    if len(value) <= 2 * _UNMASKED_EDGE:
        return MASK_CHAR * len(value)
    masked_middle = MASK_CHAR * (len(value) - 2 * _UNMASKED_EDGE)
    return value[:_UNMASKED_EDGE] + masked_middle + value[-_UNMASKED_EDGE:]


def detect_pii(text: str) -> tuple[dict[str, str], ...]:
    """Detect PII; findings carry only masked samples, never the raw value."""
    findings: list[dict[str, str]] = []
    for pii_type, pattern in _PII_PATTERNS:
        findings.extend(
            {"type": pii_type, "masked": mask_value(match.group(0))}
            for match in pattern.finditer(text)
        )
    return tuple(findings)


def mask_pii(text: str) -> str:
    """Return a copy of the text with every detected PII value masked."""
    masked = text
    for _, pattern in _PII_PATTERNS:
        masked = pattern.sub(lambda match: mask_value(match.group(0)), masked)
    return masked


def check_prompt_injection(text: str) -> tuple[dict[str, str], ...]:
    """Heuristic prompt-injection / jailbreak detection."""
    return tuple(
        {"type": name, "match": match.group(0)[:_SNIPPET_MAX_LEN]}
        for name, pattern in _INJECTION_PATTERNS
        if (match := pattern.search(text)) is not None
    )


def check_citations(payload: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    """Flag missing citations when the payload declares they are required."""
    requires = bool(payload.get("requiresCitations") or payload.get("requires_citations"))
    if not requires:
        return ()
    citations = payload.get("citations") or []
    if isinstance(citations, Sequence) and len(citations) > 0:
        return ()
    return ({"type": "missing_citations", "detail": "citations required but none provided"},)


def is_money_bearing(text: str, action: str = "") -> bool:
    """True when the content or declared action carries monetary figures."""
    if action in MONEY_BEARING_ACTIONS:
        return True
    return bool(_MONEY_PATTERN.search(text))


def evaluate(
    content: str,
    *,
    citation_context: Mapping[str, Any] | None = None,
    action: str = "",
) -> GuardrailResult:
    """Apply all checks and the blocking policy.

    Policy: prompt-injection always blocks; missing citations block only for
    money-bearing output; PII alone is flagged (with masked content) but allowed.
    """
    pii_findings = detect_pii(content)
    injection_findings = check_prompt_injection(content)
    citation_findings = check_citations(citation_context or {})

    blocks_on_citations = bool(citation_findings) and is_money_bearing(content, action)
    allowed = not injection_findings and not blocks_on_citations

    return GuardrailResult(
        allowed=allowed,
        flagged=(*pii_findings, *injection_findings, *citation_findings),
        masked_content=mask_pii(content) if pii_findings else None,
    )
