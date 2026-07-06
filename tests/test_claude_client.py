"""Tests for shared/claude_client.py -- mocked, no real API calls."""
import os
from unittest.mock import patch, MagicMock

import pytest

from shared.claude_client import call_claude, ClaudeCallError, CLAUDE_MODEL


def _mock_client_returning(text: str) -> MagicMock:
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=text)]
    mock_client.messages.create.return_value = mock_message
    return mock_client


class TestCallClaude:
    def test_returns_stripped_text(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_cls.return_value = _mock_client_returning("  hello world  \n")
            result = call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        assert result == "hello world"

    def test_uses_pinned_model_by_default(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["model"] == CLAUDE_MODEL

    def test_passes_system_prompt_when_given(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], system="be terse", api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["system"] == "be terse"

    def test_omits_system_kwarg_when_not_given(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert "system" not in kwargs

    def test_passes_max_tokens(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = _mock_client_returning("ok")
            mock_cls.return_value = mock_client
            call_claude([{"role": "user", "content": "hi"}], max_tokens=64, api_key="test-key")
        _, kwargs = mock_client.messages.create.call_args
        assert kwargs["max_tokens"] == 64

    def test_missing_api_key_raises_claude_call_error(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ClaudeCallError):
            call_claude([{"role": "user", "content": "hi"}], api_key="")

    def test_missing_api_key_env_fallback_raises(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ClaudeCallError):
            call_claude([{"role": "user", "content": "hi"}])

    def test_env_var_api_key_used_when_not_passed_explicitly(self):
        os.environ["ANTHROPIC_API_KEY"] = "from-env"
        try:
            with patch("anthropic.Anthropic") as mock_cls:
                mock_cls.return_value = _mock_client_returning("ok")
                call_claude([{"role": "user", "content": "hi"}])
            mock_cls.assert_called_once_with(api_key="from-env")
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_sdk_typeerror_wrapped_as_claude_call_error(self):
        # The Anthropic SDK raises a bare TypeError (not anthropic.APIError)
        # for a missing/malformed key -- this must be caught by the broad
        # except Exception, not slip through unguarded.
        with patch("anthropic.Anthropic", side_effect=TypeError("bad key")):
            with pytest.raises(ClaudeCallError):
                call_claude([{"role": "user", "content": "hi"}], api_key="test-key")

    def test_generic_exception_wrapped_as_claude_call_error(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = RuntimeError("network blip")
            mock_cls.return_value = mock_client
            with pytest.raises(ClaudeCallError):
                call_claude([{"role": "user", "content": "hi"}], api_key="test-key")

    def test_error_message_includes_original_exception_text(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = RuntimeError("network blip")
            mock_cls.return_value = mock_client
            with pytest.raises(ClaudeCallError, match="network blip"):
                call_claude([{"role": "user", "content": "hi"}], api_key="test-key")
