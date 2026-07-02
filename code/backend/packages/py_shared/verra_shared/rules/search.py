"""Deterministic keyword search over the regulatory rules corpus (no LLM).

Scoring is plain token overlap over title + summary + section, with tag matches
weighted higher. Filters (regulator, tags, taxpayer type) are applied before
scoring. Results are fully deterministic: ties break on rule id.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .corpus import RULES_CORPUS
from .models import AppliesTo, RegulatoryRule

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_TAG_WEIGHT = 2.0
_NRI_TAXPAYER_TYPES = frozenset({"nri", "non_resident", "non-resident", "nonresident"})


def _tokenize(text: str) -> frozenset[str]:
    return frozenset(_TOKEN_RE.findall(text.lower()))


def _allowed_applies_to(taxpayer_type: str | None) -> frozenset[AppliesTo] | None:
    """Map a taxpayer type string onto the applies_to buckets it may see."""
    if taxpayer_type is None:
        return None
    normalized = taxpayer_type.strip().lower()
    if not normalized:
        return None
    if normalized in _NRI_TAXPAYER_TYPES:
        return frozenset({AppliesTo.nri, AppliesTo.all})
    if "resident" in normalized:  # resident, resident_ordinarily, resident_not_ordinarily
        return frozenset({AppliesTo.resident, AppliesTo.all})
    return None


def _passes_filters(
    rule: RegulatoryRule,
    allowed: frozenset[AppliesTo] | None,
    regulator: str | None,
    tags: frozenset[str] | None,
) -> bool:
    if allowed is not None and rule.applies_to not in allowed:
        return False
    if regulator is not None and rule.regulator.value != regulator:
        return False
    if tags is not None and not tags & {tag.lower() for tag in rule.tags}:
        return False
    return True


def _score(query_tokens: frozenset[str], rule: RegulatoryRule) -> float:
    text_tokens = _tokenize(f"{rule.title} {rule.summary} {rule.section}")
    tag_tokens = _tokenize(" ".join(rule.tags))
    return len(query_tokens & text_tokens) + _TAG_WEIGHT * len(query_tokens & tag_tokens)


def search_rules(
    query: str,
    taxpayer_type: str | None = None,
    regulator: str | None = None,
    tags: Sequence[str] | None = None,
    limit: int = 8,
) -> list[RegulatoryRule]:
    """Return the top-`limit` corpus rules matching the query and filters.

    - `taxpayer_type` maps resident-like values to {resident, all} and NRI-like
      values to {nri, all}; unrecognized values apply no filter.
    - `regulator` filters on the exact Regulator value (case-insensitive).
    - `tags` keeps rules sharing at least one tag (case-insensitive).
    - An empty query returns the filtered corpus in stable id order.
    """
    if limit <= 0:
        return []

    allowed = _allowed_applies_to(taxpayer_type)
    regulator_norm = regulator.strip().lower() if regulator else None
    tags_norm = frozenset(tag.strip().lower() for tag in tags if tag.strip()) if tags else None

    candidates = [
        rule for rule in RULES_CORPUS if _passes_filters(rule, allowed, regulator_norm, tags_norm)
    ]

    query_tokens = _tokenize(query)
    if not query_tokens:
        return sorted(candidates, key=lambda rule: rule.id)[:limit]

    scored = [(_score(query_tokens, rule), rule) for rule in candidates]
    matched = [(score, rule) for score, rule in scored if score > 0]
    matched.sort(key=lambda pair: (-pair[0], pair[1].id))
    return [rule for _, rule in matched[:limit]]
