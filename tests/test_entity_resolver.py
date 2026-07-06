"""Tests for shared/entity_resolver.py — no mocks needed, pure logic.

Carried over from tech_scanner's tests/test_entity_resolver.py, the source
this module was promoted from.
"""
from shared.entity_resolver import normalize_name, similarity, resolve_entities, resolve_institution_list


class TestNormalizeName:
    def test_strips_leading_the(self):
        assert normalize_name("The Massachusetts Institute of Technology") == normalize_name("Massachusetts Institute of Technology")

    def test_lowercases(self):
        assert normalize_name("MIT") == "mit"

    def test_strips_punctuation(self):
        assert "inc" not in normalize_name("Raytheon Technologies, Inc.")

    def test_strips_corporate_suffix_inc(self):
        result = normalize_name("Northrop Grumman Systems Corporation")
        assert "corporation" not in result

    def test_strips_university_suffix(self):
        result = normalize_name("Stanford University")
        assert result == "stanford"

    def test_strips_laboratory(self):
        result = normalize_name("MIT Lincoln Laboratory")
        assert "laboratory" not in result

    def test_handles_empty(self):
        assert normalize_name("") == ""

    def test_strips_lab_abbreviation(self):
        result = normalize_name("Lawrence Livermore National Lab")
        assert "lab" not in result

    def test_preserves_acronym(self):
        result = normalize_name("DARPA")
        assert result == "darpa"


class TestSimilarity:
    def test_identical_names(self):
        assert similarity("MIT", "MIT") == 100.0

    def test_mit_vs_full_name(self):
        score = similarity("MIT", "Massachusetts Institute of Technology")
        assert score > 0  # token-set may be low, direct low — just check it runs

    def test_same_after_normalization(self):
        score = similarity("Raytheon Technologies Inc.", "Raytheon Technologies")
        assert score >= 90.0

    def test_different_institutions(self):
        score = similarity("MIT", "Stanford University")
        assert score < 50.0

    def test_token_sort_insensitive(self):
        score = similarity("Lockheed Martin Corporation", "Martin Lockheed Corp")
        assert score >= 85.0

    def test_empty_names(self):
        assert similarity("", "MIT") == 0.0
        assert similarity("MIT", "") == 0.0

    def test_partial_overlap_apl(self):
        score = similarity(
            "Johns Hopkins University Applied Physics Laboratory",
            "Johns Hopkins APL",
        )
        assert score > 40.0

    def test_completely_different(self):
        score = similarity("Boeing", "Harvard University")
        assert score < 40.0


class TestResolveEntities:
    def test_auto_merges_suffix_variants(self):
        raw = [
            {"name": "Raytheon Technologies Inc."},
            {"name": "Raytheon Technologies"},
        ]
        resolved, alias_map = resolve_entities(raw)
        assert len(resolved) == 1
        assert alias_map["Raytheon Technologies Inc."] == alias_map["Raytheon Technologies"]

    def test_keeps_distinct_institutions(self):
        raw = [
            {"name": "MIT"},
            {"name": "Stanford University"},
            {"name": "Northrop Grumman"},
        ]
        resolved, alias_map = resolve_entities(raw)
        assert len(resolved) == 3

    def test_alias_map_completeness(self):
        raw = [{"name": "Lockheed Martin Corp"}, {"name": "Lockheed Martin"}]
        _, alias_map = resolve_entities(raw)
        assert "Lockheed Martin Corp" in alias_map
        assert "Lockheed Martin" in alias_map

    def test_skips_empty_names(self):
        raw = [{"name": ""}, {"name": "  "}, {"name": "DARPA"}]
        resolved, _ = resolve_entities(raw)
        assert len(resolved) == 1

    def test_merges_aliases(self):
        raw = [
            {"name": "Northrop Grumman Systems Corporation"},
            {"name": "Northrop Grumman Corp"},
        ]
        resolved, alias_map = resolve_entities(raw)
        assert len(resolved) == 1
        assert "Northrop Grumman Corp" in resolved[0]["aliases"] or \
               "Northrop Grumman Systems Corporation" in resolved[0]["aliases"]

    def test_with_adjudicator(self):
        raw = [{"name": "MIT Lincoln Laboratory"}, {"name": "MIT CSAIL"}]
        # Adjudicator that always says different — should keep distinct
        adj = lambda a, b: False
        resolved, _ = resolve_entities(raw, adjudicator=adj)
        assert len(resolved) >= 1  # may vary by threshold

    def test_institution_type_preserved(self):
        raw = [
            {"name": "Georgia Tech", "institution_type": "university"},
            {"name": "Georgia Institute of Technology", "institution_type": "university"},
        ]
        resolved, alias_map = resolve_entities(raw)
        # One or two entries depending on similarity score
        for r in resolved:
            if r["institution_type"]:
                assert r["institution_type"] == "university"

    def test_sources_merged(self):
        raw = [
            {"name": "DARPA", "sources": ["darpa_baa_001"]},
            {"name": "DARPA", "sources": ["darpa_baa_002"]},
        ]
        resolved, _ = resolve_entities(raw)
        assert len(resolved) == 1
        assert len(resolved[0]["sources"]) == 2

    def test_preserves_canonical_on_first_entry(self):
        raw = [{"name": "Lockheed Martin"}, {"name": "Lockheed Martin Corp"}]
        resolved, alias_map = resolve_entities(raw)
        assert resolved[0]["canonical_name"] == "Lockheed Martin"

    def test_no_self_merge(self):
        raw = [{"name": "MIT"}, {"name": "DARPA"}]
        resolved, alias_map = resolve_entities(raw)
        assert alias_map["MIT"] != alias_map["DARPA"]


class TestResolveInstitutionList:
    def test_deduplicates(self):
        result = resolve_institution_list(["MIT", "MIT"])
        assert result.count("MIT") == 1

    def test_returns_all_distinct(self):
        result = resolve_institution_list(["MIT", "Stanford", "DARPA"])
        assert len(result) == 3

    def test_handles_empty_list(self):
        result = resolve_institution_list([])
        assert result == []

    def test_suffix_variants_deduped(self):
        result = resolve_institution_list(["Raytheon Technologies", "Raytheon Technologies Inc."])
        assert len(result) == 1

    def test_preserves_order(self):
        names = ["DARPA", "MIT", "Stanford"]
        result = resolve_institution_list(names)
        assert result[0] == "DARPA"
