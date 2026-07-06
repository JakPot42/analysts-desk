"""Tests for shared/demo_mode.py."""
import os
import pytest

from shared.demo_mode import is_demo_mode


@pytest.fixture(autouse=True)
def _clean_env():
    os.environ.pop("DEMO_MODE", None)
    yield
    os.environ.pop("DEMO_MODE", None)


class TestIsDemoMode:
    def test_defaults_to_true_when_unset(self):
        assert is_demo_mode() is True

    def test_respects_explicit_default_false(self):
        assert is_demo_mode(default=False) is False

    def test_env_true_string(self):
        os.environ["DEMO_MODE"] = "true"
        assert is_demo_mode() is True

    def test_env_1(self):
        os.environ["DEMO_MODE"] = "1"
        assert is_demo_mode() is True

    def test_env_yes(self):
        os.environ["DEMO_MODE"] = "yes"
        assert is_demo_mode() is True

    def test_env_case_insensitive(self):
        os.environ["DEMO_MODE"] = "TRUE"
        assert is_demo_mode() is True

    def test_env_false_string(self):
        os.environ["DEMO_MODE"] = "false"
        assert is_demo_mode() is False

    def test_env_0(self):
        os.environ["DEMO_MODE"] = "0"
        assert is_demo_mode() is False

    def test_env_arbitrary_string_is_false(self):
        os.environ["DEMO_MODE"] = "banana"
        assert is_demo_mode() is False

    def test_env_overrides_explicit_default(self):
        os.environ["DEMO_MODE"] = "false"
        assert is_demo_mode(default=True) is False
