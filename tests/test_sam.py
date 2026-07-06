"""
Tests for sam/claude_analyst.py, ported from sam_agent's tests/test_analyst.py.

Mocking target changed: the original patched claude_analyst._client.messages.create
directly; this ports to patching sam.claude_analyst.call_claude (the shared
wrapper), since that call itself is already covered by shared/tests/test_claude_client.py.
The SAMClient-specific tests (date range, 429/timeout handling, build_opportunity_text)
are NOT re-ported here -- that logic now lives in shared/sam_gov_client.py and is
already covered by shared/tests/test_sam_gov_client.py.
"""
import json
import pytest
from unittest.mock import patch

from sam.claude_analyst import AnalysisError, analyze_opportunity, build_executive_summary
from shared.claude_client import ClaudeCallError

VALID_ANALYSIS = {
    "summary": "Test summary.",
    "agency": "Test Agency",
    "estimated_value": "$1M",
    "period_of_performance": "1 year",
    "place_of_performance": "Remote",
    "clearance_required": "Secret",
    "cmmc_level": "Level 2",
    "set_aside": "Small Business",
    "key_requirements": [
        {"requirement": "Python experience", "category": "Technical"}
    ],
    "evaluation_criteria": [
        {"criterion": "Technical", "weight": "60%"}
    ],
    "compliance_flags": [
        {"flag": "Secret clearance required", "severity": "High"}
    ],
    "capability_statement_bullets": [
        "Proven Python development team"
    ],
    "bottom_line": "Good fit for a cleared small business.",
}


class TestAnalyzeOpportunity:

    def test_parses_clean_json(self):
        with patch("sam.claude_analyst.call_claude", return_value=json.dumps(VALID_ANALYSIS)):
            result = analyze_opportunity("some RFP text")
        assert result["summary"] == "Test summary."
        assert result["clearance_required"] == "Secret"
        assert len(result["key_requirements"]) == 1

    def test_strips_markdown_fences(self):
        wrapped = f"```json\n{json.dumps(VALID_ANALYSIS)}\n```"
        with patch("sam.claude_analyst.call_claude", return_value=wrapped):
            result = analyze_opportunity("some RFP text")
        assert result["agency"] == "Test Agency"

    def test_strips_plain_code_fences(self):
        wrapped = f"```\n{json.dumps(VALID_ANALYSIS)}\n```"
        with patch("sam.claude_analyst.call_claude", return_value=wrapped):
            result = analyze_opportunity("some RFP text")
        assert result["cmmc_level"] == "Level 2"

    def test_raises_on_invalid_json(self):
        with patch("sam.claude_analyst.call_claude", return_value="Sorry, I cannot analyze this."):
            with pytest.raises(AnalysisError, match="Could not parse"):
                analyze_opportunity("some RFP text")

    def test_raises_on_api_error(self):
        with patch("sam.claude_analyst.call_claude", side_effect=ClaudeCallError("Claude API error: boom")):
            with pytest.raises(AnalysisError, match="Claude API error"):
                analyze_opportunity("some RFP text")

    def test_null_fields_accepted(self):
        sparse = {**VALID_ANALYSIS, "clearance_required": None, "cmmc_level": None,
                  "estimated_value": None}
        with patch("sam.claude_analyst.call_claude", return_value=json.dumps(sparse)):
            result = analyze_opportunity("minimal RFP")
        assert result["clearance_required"] is None
        assert result["cmmc_level"] is None


class TestBuildExecutiveSummary:
    """Tests for build_executive_summary() — deterministic, no API calls."""

    def _make_analysis(self, **overrides):
        base = {
            "cmmc_level": None,
            "nist_800_171_required": False,
            "section_889_applies": False,
            "buy_american_act_applies": False,
            "pricing_model": None,
        }
        base.update(overrides)
        return base

    def test_empty_analysis_returns_no_flags(self):
        result = build_executive_summary(self._make_analysis())
        assert result == []

    def test_cmmc_level_2_cites_dfars_252_204_7021(self):
        result = build_executive_summary(self._make_analysis(cmmc_level="Level 2"))
        assert len(result) == 1
        assert "252.204-7021" in result[0]["clause"]
        assert result[0]["severity"] == "High"
        assert "Level 2" in result[0]["title"]

    def test_cmmc_level_3_cites_dfars_252_204_7021_level3(self):
        result = build_executive_summary(self._make_analysis(cmmc_level="Level 3"))
        assert len(result) == 1
        assert "252.204-7021" in result[0]["clause"]
        assert "Level 3" in result[0]["title"]

    def test_cmmc_level3_does_not_also_produce_level2_entry(self):
        result = build_executive_summary(self._make_analysis(cmmc_level="Level 3"))
        titles = [f["title"] for f in result]
        assert all("Level 2" not in t for t in titles)

    def test_nist_800_171_cites_dfars_252_204_7012(self):
        result = build_executive_summary(self._make_analysis(nist_800_171_required=True))
        clauses = [f["clause"] for f in result]
        assert any("252.204-7012" in c for c in clauses)
        assert result[0]["severity"] == "High"

    def test_nist_800_171_string_true_accepted(self):
        result = build_executive_summary(self._make_analysis(nist_800_171_required="true"))
        assert any("252.204-7012" in f["clause"] for f in result)

    def test_section_889_cites_far_52_204_25(self):
        result = build_executive_summary(self._make_analysis(section_889_applies=True))
        clauses = [f["clause"] for f in result]
        assert any("52.204-25" in c for c in clauses)
        assert any("252.204-7018" in c for c in clauses)

    def test_buy_american_cites_far_52_225(self):
        result = build_executive_summary(self._make_analysis(buy_american_act_applies=True))
        clauses = [f["clause"] for f in result]
        assert any("52.225" in c for c in clauses)
        assert result[0]["severity"] in ("High", "Medium")

    def test_cost_plus_cites_far_52_215_2(self):
        result = build_executive_summary(self._make_analysis(pricing_model="cost-plus"))
        clauses = [f["clause"] for f in result]
        assert any("52.215-2" in c for c in clauses)

    def test_commercial_item_cites_far_part_12(self):
        result = build_executive_summary(self._make_analysis(pricing_model="commercial-item"))
        clauses = [f["clause"] for f in result]
        assert any("52.212-1" in c for c in clauses)
        assert result[0]["severity"] == "Low"

    def test_multiple_signals_produce_multiple_flags(self):
        result = build_executive_summary(self._make_analysis(
            cmmc_level="Level 2",
            section_889_applies=True,
            buy_american_act_applies=True,
        ))
        assert len(result) == 3

    def test_missing_keys_handled_gracefully(self):
        result = build_executive_summary({"summary": "Minimal analysis."})
        assert result == []

    def test_all_flags_have_required_keys(self):
        result = build_executive_summary(self._make_analysis(
            cmmc_level="Level 2",
            nist_800_171_required=True,
            section_889_applies=True,
            buy_american_act_applies=True,
            pricing_model="cost-plus",
        ))
        for flag in result:
            assert "title" in flag
            assert "clause" in flag
            assert "description" in flag
            assert "severity" in flag
            assert flag["severity"] in ("High", "Medium", "Low")
