"""Tests for shared/arxiv_client.py -- mocked requests, no real network calls."""
from unittest.mock import patch, MagicMock

from shared.arxiv_client import search, fetch_all, ArxivPaper

ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2501.99999</id>
    <title>Hypersonic Boundary Layer Control via Plasma Actuators</title>
    <summary>We demonstrate plasma-actuated boundary layer control at Mach 6 reducing drag by 22%.</summary>
    <published>2026-01-10T00:00:00Z</published>
    <author>
      <name>Jane Doe</name>
      <arxiv:affiliation>NASA Ames Research Center</arxiv:affiliation>
    </author>
    <author>
      <name>John Smith</name>
      <arxiv:affiliation>Caltech</arxiv:affiliation>
    </author>
  </entry>
  <entry>
    <id>https://arxiv.org/abs/2501.88888</id>
    <title>Quantum Gyroscope for Navigation in GPS-Denied Environments</title>
    <summary>Atom-interferometric gyroscope achieving 1e-10 rad/s/sqrt(Hz) sensitivity.</summary>
    <published>2026-01-08T00:00:00Z</published>
    <author>
      <name>Alice Brown</name>
    </author>
  </entry>
</feed>"""


def _mock_response():
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.text = ARXIV_ATOM
    return resp


class TestSearch:
    def test_returns_papers(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()):
            papers = search("ti:hypersonic", max_results=5)
        assert len(papers) == 2

    def test_paper_has_required_fields(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()):
            papers = search("ti:hypersonic")
        paper = papers[0]
        assert isinstance(paper, ArxivPaper)
        assert paper.external_id == "2501.99999"
        assert "Hypersonic" in paper.title
        assert paper.abstract
        assert paper.url.startswith("https://arxiv.org")
        assert paper.published_date == "2026-01-10"

    def test_extracts_affiliations(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()):
            papers = search("ti:hypersonic")
        assert "NASA Ames Research Center" in papers[0].affiliations
        assert "Caltech" in papers[0].affiliations

    def test_no_affiliation_is_empty_list(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()):
            papers = search("ti:quantum")
        assert papers[1].affiliations == []

    def test_network_error_returns_empty_list(self):
        with patch("shared.arxiv_client.requests.get", side_effect=Exception("timeout")):
            papers = search("ti:hypersonic")
        assert papers == []

    def test_default_sends_query_unprefixed(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()) as mock_get:
            search("ti:hypersonic")
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["search_query"] == "ti:hypersonic"

    def test_prefix_all_wraps_query(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()) as mock_get:
            search("hypersonic weapons", prefix_all=True)
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["search_query"] == "all:hypersonic weapons"

    def test_abstract_capped_at_max_chars(self):
        long_summary_atom = ARXIV_ATOM.replace(
            "We demonstrate plasma-actuated boundary layer control at Mach 6 reducing drag by 22%.",
            "x" * 2000,
        )
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.text = long_summary_atom
        with patch("shared.arxiv_client.requests.get", return_value=resp):
            papers = search("ti:hypersonic")
        assert len(papers[0].abstract) <= 1500


class TestFetchAll:
    def test_deduplicates_by_external_id(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()):
            papers = fetch_all([("ti:hypersonic", 5), ("ti:quantum", 5)])
        ids = [p.external_id for p in papers]
        assert len(ids) == len(set(ids))

    def test_runs_all_configured_searches(self):
        with patch("shared.arxiv_client.requests.get", return_value=_mock_response()) as mock_get:
            fetch_all([("ti:hypersonic", 5), ("ti:quantum", 3)])
        assert mock_get.call_count == 2
