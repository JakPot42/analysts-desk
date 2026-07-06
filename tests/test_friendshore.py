"""Tests for friendshore/graph_engine.py — no real APIs, no disk I/O (mocked).

Ported from friendshore's tests/test_graph_engine.py; only the import paths
and @patch targets changed (graph_engine -> friendshore.graph_engine).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import networkx as nx

from friendshore.graph_engine import (
    EdgeData,
    GraphAnalysisResult,
    SupplierData,
    _country_is_high_risk,
    _find_single_points_of_failure,
    _score_node,
    build_and_analyze,
)


# ---------------------------------------------------------------------------
# _country_is_high_risk
# ---------------------------------------------------------------------------

class TestCountryIsHighRisk:
    def test_china_is_high_risk(self):
        assert _country_is_high_risk("China") is True

    def test_prc_is_high_risk(self):
        assert _country_is_high_risk("PRC") is True

    def test_russia_is_high_risk(self):
        assert _country_is_high_risk("Russia") is True

    def test_usa_is_not_high_risk(self):
        assert _country_is_high_risk("USA") is False

    def test_none_is_not_high_risk(self):
        assert _country_is_high_risk(None) is False

    def test_case_insensitive(self):
        assert _country_is_high_risk("china") is True
        assert _country_is_high_risk("CHINA") is True


# ---------------------------------------------------------------------------
# _score_node
# ---------------------------------------------------------------------------

class TestScoreNode:
    def _make_graph(self, nodes, edges):
        G = nx.DiGraph()
        for n in nodes:
            G.add_node(n.name, data=n)
        for s, c in edges:
            G.add_edge(s, c)
        return G

    def test_high_risk_country_adds_40(self):
        node = SupplierData(name="Supplier A", country="China", tier=2)
        G = self._make_graph([node], [])
        score = _score_node("Supplier A", node, G, set())
        assert score == 40

    def test_spf_adds_30(self):
        node = SupplierData(name="Supplier A", country="USA", tier=2)
        G = self._make_graph([node], [])
        score = _score_node("Supplier A", node, G, {"Supplier A"})
        assert score == 30

    def test_missing_country_adds_10(self):
        node = SupplierData(name="Supplier A", country=None, tier=2)
        G = self._make_graph([node], [])
        score = _score_node("Supplier A", node, G, set())
        assert score == 10

    def test_combined_risk_capped_at_100(self):
        node = SupplierData(name="X", country="China", tier=2)
        # Make node have 3+ out-edges to trigger concentration penalty
        G = nx.DiGraph()
        G.add_node("X", data=node)
        for i in range(4):
            G.add_node(f"C{i}")
            G.add_edge("X", f"C{i}")
        score = _score_node("X", node, G, {"X"})
        assert score <= 100


# ---------------------------------------------------------------------------
# _find_single_points_of_failure
# ---------------------------------------------------------------------------

class TestFindSinglePointsOfFailure:
    def test_detects_high_risk_articulation_point(self):
        """
        Graph: MP_Materials → Longhua(China) → Raytheon → DefenseTech
        Longhua is the articulation point AND high-risk country → SPF.
        """
        focal = "DefenseTech"
        longhua = SupplierData(name="Longhua", country="China", tier=2)
        nodes = [
            SupplierData(name="MP_Materials", country="USA", tier=3),
            longhua,
            SupplierData(name="Raytheon", country="USA", tier=1),
            SupplierData(name=focal, country="USA", tier=0, is_focal_company=True),
        ]
        G = nx.DiGraph()
        for n in nodes:
            G.add_node(n.name, data=n)
        G.add_edge("MP_Materials", "Longhua")
        G.add_edge("Longhua", "Raytheon")
        G.add_edge("Raytheon", focal)

        spf = _find_single_points_of_failure(G, focal)
        assert "Longhua" in spf

    def test_friendly_nation_not_flagged_as_spf(self):
        """Even if a US supplier is an articulation point, it should not be flagged."""
        focal = "Primes Inc"
        us_supplier = SupplierData(name="US Supplier", country="USA", tier=1)
        tier3 = SupplierData(name="Raw Materials", country="Australia", tier=2)
        focal_node = SupplierData(name=focal, country="USA", tier=0, is_focal_company=True)

        G = nx.DiGraph()
        for n in [tier3, us_supplier, focal_node]:
            G.add_node(n.name, data=n)
        G.add_edge("Raw Materials", "US Supplier")
        G.add_edge("US Supplier", focal)

        # US Supplier is an articulation point but not high-risk
        spf = _find_single_points_of_failure(G, focal)
        assert "US Supplier" not in spf

    def test_empty_graph_returns_empty(self):
        G = nx.DiGraph()
        assert _find_single_points_of_failure(G, "NonExistent") == set()


# ---------------------------------------------------------------------------
# build_and_analyze (integration — mocks matplotlib and file I/O)
# ---------------------------------------------------------------------------

class TestBuildAndAnalyze:
    def _minimal_inputs(self):
        nodes = [
            SupplierData(name="Acme Defense", country="USA", tier=0, is_focal_company=True),
            SupplierData(name="GoodSupplier", country="UK", tier=1, component="widgets"),
            SupplierData(name="BadSupplier", country="China", tier=1, component="chips"),
        ]
        edges = [
            EdgeData(supplier="GoodSupplier", customer="Acme Defense", component="widgets"),
            EdgeData(supplier="BadSupplier", customer="Acme Defense", component="chips"),
        ]
        return nodes, edges

    @patch("friendshore.graph_engine.nx.draw_networkx_edge_labels")
    @patch("friendshore.graph_engine.nx.draw_networkx_labels")
    @patch("friendshore.graph_engine.nx.draw_networkx_nodes")
    @patch("friendshore.graph_engine.nx.draw_networkx_edges")
    @patch("friendshore.graph_engine.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("friendshore.graph_engine.plt")
    def test_returns_graph_analysis_result(
        self, mock_plt, mock_open, mock_makedirs,
        mock_edges, mock_nodes, mock_labels, mock_edge_labels,
    ):
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.savefig = lambda buf, **kw: buf.write(b"PNGDATA")

        nodes, edges = self._minimal_inputs()
        result = build_and_analyze(nodes, edges, "Acme Defense", 1)

        assert isinstance(result, GraphAnalysisResult)
        assert "BadSupplier" in result.risk_scores
        assert result.risk_scores["BadSupplier"] >= 40  # high-risk country

    @patch("friendshore.graph_engine.nx.draw_networkx_edge_labels")
    @patch("friendshore.graph_engine.nx.draw_networkx_labels")
    @patch("friendshore.graph_engine.nx.draw_networkx_nodes")
    @patch("friendshore.graph_engine.nx.draw_networkx_edges")
    @patch("friendshore.graph_engine.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("friendshore.graph_engine.plt")
    def test_graph_json_has_nodes_and_edges(
        self, mock_plt, mock_open, mock_makedirs,
        mock_edges, mock_nodes, mock_labels, mock_edge_labels,
    ):
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.savefig = lambda buf, **kw: buf.write(b"PNG")

        nodes, edges = self._minimal_inputs()
        result = build_and_analyze(nodes, edges, "Acme Defense", 1)

        assert "nodes" in result.graph_data_json
        assert "edges" in result.graph_data_json
        assert len(result.graph_data_json["nodes"]) == 3
        assert len(result.graph_data_json["edges"]) == 2


# ---------------------------------------------------------------------------
# claude_agent.py -- new coverage for the shared-client integration point.
# The original standalone friendshore project had no tests for this module
# at all; added here since the call_claude() wiring is new integration code.
# ---------------------------------------------------------------------------

import json
import pytest
from unittest.mock import patch

from friendshore.claude_agent import AgentError, parse_bom, suggest_alternatives
from shared.claude_client import ClaudeCallError


class TestParseBom:
    def test_parses_clean_json(self):
        payload = {"company_name": "Acme", "nodes": [{"name": "Acme", "tier": 0}], "edges": []}
        with patch("friendshore.claude_agent.call_claude", return_value=json.dumps(payload)):
            result = parse_bom("some BOM text")
        assert result["company_name"] == "Acme"

    def test_strips_markdown_fences(self):
        payload = {"company_name": "Acme", "nodes": [], "edges": []}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        with patch("friendshore.claude_agent.call_claude", return_value=wrapped):
            result = parse_bom("some BOM text")
        assert result["nodes"] == []

    def test_raises_on_invalid_json(self):
        with patch("friendshore.claude_agent.call_claude", return_value="not json"):
            with pytest.raises(AgentError):
                parse_bom("some BOM text")

    def test_raises_on_missing_keys(self):
        with patch("friendshore.claude_agent.call_claude", return_value=json.dumps({"company_name": "Acme"})):
            with pytest.raises(AgentError, match="nodes"):
                parse_bom("some BOM text")

    def test_raises_agent_error_on_claude_call_error(self):
        with patch("friendshore.claude_agent.call_claude", side_effect=ClaudeCallError("boom")):
            with pytest.raises(AgentError):
                parse_bom("some BOM text")


class TestSuggestAlternatives:
    def test_empty_suppliers_short_circuits_no_call(self):
        with patch("friendshore.claude_agent.call_claude") as mock_call:
            result = suggest_alternatives([], "Acme")
        assert result == []
        mock_call.assert_not_called()

    def test_parses_clean_json_array(self):
        payload = [{"original_supplier": "BadCo", "component": "chips", "alternatives": []}]
        with patch("friendshore.claude_agent.call_claude", return_value=json.dumps(payload)):
            result = suggest_alternatives([{"name": "BadCo", "country": "China"}], "Acme")
        assert result[0]["original_supplier"] == "BadCo"

    def test_raises_if_not_a_list(self):
        with patch("friendshore.claude_agent.call_claude", return_value=json.dumps({"not": "a list"})):
            with pytest.raises(AgentError, match="array"):
                suggest_alternatives([{"name": "BadCo", "country": "China"}], "Acme")

    def test_raises_agent_error_on_claude_call_error(self):
        with patch("friendshore.claude_agent.call_claude", side_effect=ClaudeCallError("boom")):
            with pytest.raises(AgentError):
                suggest_alternatives([{"name": "BadCo", "country": "China"}], "Acme")
