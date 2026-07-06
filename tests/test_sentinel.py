"""
Tests for sentinel/cluster_engine.py and sentinel/claude_analyst.py, ported
from sentinel's tests/test_cluster_engine.py.

Mocking target changed: the original patched claude_analyst._get_client()
directly; this ports to patching sentinel.claude_analyst.call_claude (the
shared wrapper), which is itself already covered by
shared/tests/test_claude_client.py.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

from sentinel.cluster_engine import _keyword_overlap, _threat_level
from sentinel.claude_analyst import AnalystError, extract_narrative, analyze_cluster_ttps
from shared.claude_client import ClaudeCallError


# ---------------------------------------------------------------------------
# cluster_engine helpers
# ---------------------------------------------------------------------------

class TestKeywordOverlap:
    def test_identical_lists(self):
        assert _keyword_overlap(["a", "b", "c"], ["a", "b", "c"]) == 3

    def test_no_overlap(self):
        assert _keyword_overlap(["x", "y"], ["a", "b"]) == 0

    def test_partial_overlap(self):
        assert _keyword_overlap(["northgate", "f-35", "certifications"], ["f-35", "certifications", "senate"]) == 2

    def test_case_insensitive(self):
        assert _keyword_overlap(["Northgate", "F-35"], ["northgate", "f-35"]) == 2

    def test_empty_lists(self):
        assert _keyword_overlap([], []) == 0
        assert _keyword_overlap(["a"], []) == 0
        assert _keyword_overlap([], ["a"]) == 0

    def test_duplicates_counted_once(self):
        assert _keyword_overlap(["a", "a", "b"], ["a", "b", "b"]) == 2


class TestThreatLevel:
    def _make_cluster(self, adversary_count: int, velocity_score: float) -> MagicMock:
        c = MagicMock()
        c.adversary_count = adversary_count
        c.velocity_score = velocity_score
        return c

    def test_high_many_adversary_high_velocity(self):
        assert _threat_level(self._make_cluster(3, 0.5)) == "HIGH"

    def test_high_boundary(self):
        assert _threat_level(self._make_cluster(3, 0.4)) == "HIGH"

    def test_medium_two_adversary(self):
        assert _threat_level(self._make_cluster(2, 0.1)) == "MEDIUM"

    def test_medium_high_velocity_alone(self):
        assert _threat_level(self._make_cluster(1, 0.3)) == "MEDIUM"

    def test_low_few_adversary_low_velocity(self):
        assert _threat_level(self._make_cluster(1, 0.1)) == "LOW"

    def test_low_zero(self):
        assert _threat_level(self._make_cluster(0, 0.0)) == "LOW"


# ---------------------------------------------------------------------------
# claude_analyst — extract_narrative
# ---------------------------------------------------------------------------

class TestExtractNarrative:
    def _valid_payload(self) -> dict:
        return {
            "narrative_summary": "Test claim about defense contractor.",
            "entities": ["Northgate Defense", "F-35"],
            "keywords": ["northgate", "f-35", "certifications"],
            "sentiment": "negative",
            "is_divisive": True,
            "credibility_signals": ["anonymous sources"],
        }

    def test_returns_all_fields(self):
        with patch("sentinel.claude_analyst.call_claude", return_value=json.dumps(self._valid_payload())):
            result = extract_narrative("Title", "Body text", "RT English", "adversary")
        assert result["narrative_summary"] == "Test claim about defense contractor."
        assert result["sentiment"] == "negative"
        assert isinstance(result["keywords"], list)

    def test_strips_markdown_fences(self):
        wrapped = f"```json\n{json.dumps(self._valid_payload())}\n```"
        with patch("sentinel.claude_analyst.call_claude", return_value=wrapped):
            result = extract_narrative("Title", "Body", "Source", "adversary")
        assert result["sentiment"] == "negative"

    def test_raises_on_invalid_json(self):
        with patch("sentinel.claude_analyst.call_claude", return_value="not json"):
            with pytest.raises(AnalystError, match="invalid JSON"):
                extract_narrative("Title", "Body", "Source", "adversary")

    def test_raises_on_missing_field(self):
        with patch("sentinel.claude_analyst.call_claude", return_value=json.dumps({"narrative_summary": "x"})):
            with pytest.raises(AnalystError, match="missing field"):
                extract_narrative("Title", "Body", "Source", "adversary")

    def test_raises_on_claude_call_error(self):
        with patch("sentinel.claude_analyst.call_claude", side_effect=ClaudeCallError("boom")):
            with pytest.raises(AnalystError, match="API error"):
                extract_narrative("Title", "Body", "Source", "adversary")


# ---------------------------------------------------------------------------
# claude_analyst — analyze_cluster_ttps
# ---------------------------------------------------------------------------

class TestAnalyzeClusterTtps:
    def _valid_payload(self) -> dict:
        return {
            "ttps": [
                {"id": "T0019", "name": "Seed Distortions", "confidence": "high", "rationale": "Test rationale."},
                {"id": "T0057", "name": "Amplify Divisive Content", "confidence": "medium", "rationale": "Another rationale."},
            ],
            "coordination_indicators": ["Same narrative across 4 outlets in 90 min"],
            "attribution": "Consistent with Russian Federation IO TTPs",
            "confidence_level": "MODERATE",
            "threat_level": "HIGH",
        }

    def test_returns_all_fields(self):
        articles = [{"source_name": "RT", "outlet_type": "adversary", "title": "Test", "narrative_summary": "x"}]
        with patch("sentinel.claude_analyst.call_claude", return_value=json.dumps(self._valid_payload())):
            result = analyze_cluster_ttps("Test Cluster", articles)
        assert result["threat_level"] == "HIGH"
        assert result["confidence_level"] == "MODERATE"
        assert len(result["ttps"]) == 2

    def test_raises_on_api_error(self):
        with patch("sentinel.claude_analyst.call_claude", side_effect=ClaudeCallError("API error")):
            with pytest.raises(AnalystError):
                analyze_cluster_ttps("Test", [])

    def test_raises_on_missing_required_field(self):
        with patch("sentinel.claude_analyst.call_claude", return_value=json.dumps({"ttps": []})):
            with pytest.raises(AnalystError, match="missing field"):
                analyze_cluster_ttps("Test", [])
