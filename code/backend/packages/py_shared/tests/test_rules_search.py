"""Tests for the regulatory rules corpus and deterministic keyword search."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from verra_shared.rules import (
    RULES_BY_ID,
    RULES_CORPUS,
    AppliesTo,
    Regulator,
    RegulatoryRule,
    search_rules,
)

# ── search: taxpayer-type filtering ──────────────────────────────────────────


def test_nri_query_returns_only_nri_and_all_rules() -> None:
    results = search_rules("How is interest on my NRE account taxed?", taxpayer_type="nri")
    assert results, "expected NRE query to match rules"
    assert all(rule.applies_to in (AppliesTo.nri, AppliesTo.all) for rule in results)
    assert "it-10-4-nre-interest" in [rule.id for rule in results]


def test_non_resident_taxpayer_type_maps_to_nri_bucket() -> None:
    results = search_rules("rebate under section 87A", taxpayer_type="non_resident")
    assert "it-87a" not in [rule.id for rule in results]  # 87A is resident-only


def test_resident_taxpayer_type_sees_resident_and_all_rules() -> None:
    results = search_rules("rebate under section 87A", taxpayer_type="resident_ordinarily")
    assert results[0].id == "it-87a"
    assert all(rule.applies_to in (AppliesTo.resident, AppliesTo.all) for rule in results)


def test_resident_does_not_see_nri_only_rules() -> None:
    results = search_rules("NRE account interest exemption", taxpayer_type="resident")
    assert all(rule.applies_to is not AppliesTo.nri for rule in results)


# ── search: regulator + tag filters ──────────────────────────────────────────


def test_regulator_filter_restricts_results() -> None:
    results = search_rules("riskometer product labelling", regulator="sebi")
    assert results
    assert all(rule.regulator is Regulator.sebi for rule in results)
    assert results[0].id == "sebi-mf-riskometer"


def test_regulator_filter_excludes_other_regulators() -> None:
    assert search_rules("riskometer product labelling", regulator="gst") == []


def test_tag_filter_keeps_only_tagged_rules() -> None:
    results = search_rules("", tags=["portfolio"], limit=50)
    assert results
    assert all("portfolio" in rule.tags for rule in results)


def test_tag_filter_with_query_ranks_tagged_rules() -> None:
    results = search_rules("long term capital gains harvesting", tags=["portfolio", "sebi"])
    assert "it-112a" in [rule.id for rule in results]


# ── search: query + limit behavior ───────────────────────────────────────────


def test_empty_query_returns_filtered_corpus_in_id_order() -> None:
    results = search_rules("", limit=8)
    assert len(results) == 8
    assert [rule.id for rule in results] == sorted(rule.id for rule in results)


def test_whitespace_query_matches_empty_query() -> None:
    assert [r.id for r in search_rules("   ")] == [r.id for r in search_rules("")]


def test_no_token_overlap_returns_empty() -> None:
    assert search_rules("zzz qqq xyzzy") == []


def test_limit_caps_results() -> None:
    assert len(search_rules("tax", limit=3)) <= 3
    assert search_rules("tax", limit=0) == []


def test_results_are_deterministic() -> None:
    first = [rule.id for rule in search_rules("capital gains equity")]
    second = [rule.id for rule in search_rules("capital gains equity")]
    assert first == second


# ── corpus integrity ─────────────────────────────────────────────────────────


def test_corpus_size_in_expected_range() -> None:
    assert 35 <= len(RULES_CORPUS) <= 45


def test_corpus_ids_unique_and_well_formed() -> None:
    ids = [rule.id for rule in RULES_CORPUS]
    assert len(ids) == len(set(ids))
    assert all(rule.id == rule.id.lower() for rule in RULES_CORPUS)
    assert RULES_BY_ID["it-87a"].section == "87A"


def test_every_rule_fully_populated() -> None:
    for rule in RULES_CORPUS:
        assert rule.id.strip()
        assert rule.section.strip()
        assert rule.title.strip()
        assert len(rule.summary.strip()) >= 80, rule.id  # 2-4 sentence summaries
        assert rule.tags and all(tag.strip() for tag in rule.tags)
        assert rule.source.strip()


def test_corpus_covers_required_regulators() -> None:
    regulators = {rule.regulator for rule in RULES_CORPUS}
    assert {
        Regulator.income_tax,
        Regulator.sebi,
        Regulator.rbi_fema,
        Regulator.irdai,
        Regulator.gst,
    } <= regulators


def test_rules_are_immutable() -> None:
    rule = RULES_CORPUS[0]
    with pytest.raises(ValidationError):
        rule.title = "mutated"  # frozen model: pydantic raises at runtime


def test_rule_serializes_to_camel_case_wire_shape() -> None:
    payload = RULES_BY_ID["it-112a"].model_dump(by_alias=True)
    assert payload["appliesTo"] == "all"
    assert payload["assessmentYear"] == "2025-26"
    assert payload["id"] == "it-112a"


def test_rule_model_rejects_empty_fields() -> None:
    with pytest.raises(ValidationError):
        RegulatoryRule(
            id="",
            regulator=Regulator.income_tax,
            section="1",
            title="t",
            summary="s",
            applies_to=AppliesTo.all,
            tags=["x"],
            source="src",
        )
