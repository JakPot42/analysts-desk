"""Tests for shared/sam_gov_client.py -- mocked httpx, no real network calls."""
import httpx
import pytest
from unittest.mock import patch, MagicMock

from shared.sam_gov_client import (
    search_opportunities,
    get_opportunity,
    build_opportunity_text,
    search_darpa_solicitations,
    SAMAPIError,
    _date_range,
)


class TestDateRange:
    def test_returns_two_strings(self):
        start, end = _date_range(90)
        assert isinstance(start, str)
        assert isinstance(end, str)

    def test_format_is_mm_dd_yyyy(self):
        start, end = _date_range(90)
        assert len(start.split("/")) == 3
        assert len(end.split("/")) == 3


class TestSearchOpportunities:
    def test_success_returns_json(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"opportunitiesData": [{"title": "Test"}]}
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = search_opportunities("radar", api_key="test-key")
        assert result == {"opportunitiesData": [{"title": "Test"}]}

    def test_429_raises_quota_message(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=MagicMock(status_code=429)
            )
            with pytest.raises(SAMAPIError, match="quota"):
                search_opportunities("radar", api_key="test-key")

    def test_403_raises_key_rejected_message(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "403", request=MagicMock(), response=MagicMock(status_code=403)
            )
            with pytest.raises(SAMAPIError, match="rejected"):
                search_opportunities("radar", api_key="bad-key")

    def test_other_status_raises_generic_message(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "500", request=MagicMock(), response=MagicMock(status_code=500)
            )
            with pytest.raises(SAMAPIError, match="500"):
                search_opportunities("radar", api_key="test-key")

    def test_timeout_raises_samapierror(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(SAMAPIError, match="timed out"):
                search_opportunities("radar", api_key="test-key")

    def test_request_error_raises_samapierror(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("dns failure")
            with pytest.raises(SAMAPIError, match="Could not reach"):
                search_opportunities("radar", api_key="test-key")


class TestGetOpportunity:
    def test_returns_first_hit(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"opportunitiesData": [{"noticeId": "abc123"}]}
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = get_opportunity("abc123", api_key="test-key")
        assert result == {"noticeId": "abc123"}

    def test_returns_none_when_no_hits(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"opportunitiesData": []}
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = get_opportunity("missing-id", api_key="test-key")
        assert result is None

    def test_request_error_raises_samapierror(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("dns failure")
            with pytest.raises(SAMAPIError):
                get_opportunity("abc123", api_key="test-key")


class TestBuildOpportunityText:
    def test_includes_title(self):
        text = build_opportunity_text({"title": "Radar Systems Upgrade"})
        assert "Radar Systems Upgrade" in text

    def test_handles_missing_fields_gracefully(self):
        text = build_opportunity_text({})
        assert "N/A" in text


class TestSearchDarpaSolicitations:
    def test_no_key_returns_empty_list_gracefully(self, monkeypatch):
        monkeypatch.delenv("SAM_API_KEY", raising=False)
        result = search_darpa_solicitations(api_key=None)
        assert result == []

    def test_env_var_key_used_when_not_passed(self, monkeypatch):
        monkeypatch.setenv("SAM_API_KEY", "env-key")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"opportunitiesData": []}
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp) as mock_get:
            search_darpa_solicitations()
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["api_key"] == "env-key"

    def test_filters_to_darpa_subtier_only(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "opportunitiesData": [
                {"subtierAgencyName": "Defense Advanced Research Projects Agency",
                 "title": "AI Research BAA", "solicitationNumber": "HR001", "postedDate": "2026-01-01"},
                {"subtierAgencyName": "Defense Logistics Agency",
                 "title": "Fuel Contract", "solicitationNumber": "SP001", "postedDate": "2026-01-01"},
            ]
        }
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = search_darpa_solicitations(api_key="test-key")
        assert len(result) == 1
        assert result[0]["title"] == "AI Research BAA"

    def test_skips_items_without_title(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "opportunitiesData": [
                {"subtierAgencyName": "DARPA", "title": "", "solicitationNumber": "HR001"},
            ]
        }
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = search_darpa_solicitations(api_key="test-key")
        assert result == []

    def test_request_failure_now_raises_instead_of_silently_returning_empty(self):
        # Disclosed behavior change from tech_scanner's original darpa_client.fetch():
        # a real request failure must be visible, not indistinguishable from
        # "zero solicitations this window."
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("dns failure")
            with pytest.raises(SAMAPIError):
                search_darpa_solicitations(api_key="test-key")

    def test_timeout_raises_samapierror(self):
        with patch("shared.sam_gov_client.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(SAMAPIError):
                search_darpa_solicitations(api_key="test-key")

    def test_result_shape_matches_items_table_schema(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "opportunitiesData": [
                {"subtierAgencyName": "DARPA", "title": "Quantum Sensing BAA",
                 "solicitationNumber": "HR002", "postedDate": "2026-02-01",
                 "description": "desc", "uiLink": "https://sam.gov/x"},
            ]
        }
        mock_resp.raise_for_status.return_value = None
        with patch("shared.sam_gov_client.httpx.get", return_value=mock_resp):
            result = search_darpa_solicitations(api_key="test-key")
        item = result[0]
        assert item["source"] == "darpa"
        assert item["external_id"] == "HR002"
        assert item["raw_institutions"] == ["DARPA"]
