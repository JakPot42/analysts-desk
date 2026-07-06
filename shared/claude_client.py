"""
Canonical Claude API call wrapper for the Analyst's Desk cluster.

Every consuming project should call `call_claude()` instead of constructing
its own anthropic.Anthropic client and its own try/except around
messages.create(). This exists because two real bugs were found across the
cluster's 11 source projects where the live-mode API call had no exception
handling at all (defense_budget_tracker's report_generator.py, ip_theft's
patterns.py) -- both crashed with an unhandled traceback on a live-mode
failure instead of degrading gracefully like every other Claude call site
in the portfolio. Routing every call through one wrapper makes that failure
mode structurally impossible to reintroduce.

The Anthropic SDK raises a bare TypeError (not anthropic.APIError) when
api_key is empty or malformed -- catching Exception broadly, not
anthropic.APIError specifically, is deliberate and matches the portfolio-
wide fix already applied elsewhere.
"""
from __future__ import annotations

import os

import anthropic

CLAUDE_MODEL = "claude-haiku-4-5-20251001"


class ClaudeCallError(Exception):
    """Raised for any Claude API failure -- missing key, network error,
    rate limit, malformed response, etc. Wraps the original exception."""


def call_claude(
    messages: list[dict],
    *,
    system: str | None = None,
    max_tokens: int = 1024,
    model: str = CLAUDE_MODEL,
    api_key: str | None = None,
) -> str:
    """
    Call Claude and return the response text (content[0].text, stripped).

    Raises ClaudeCallError -- never a bare SDK exception -- on any failure.
    Callers that need structured output (JSON, etc.) parse the returned
    string themselves; this wrapper only guarantees the call itself either
    succeeds or raises ClaudeCallError, nothing more.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ClaudeCallError(
            "ANTHROPIC_API_KEY not set. Set it in the environment or pass api_key= explicitly."
        )

    try:
        client = anthropic.Anthropic(api_key=key)
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system is not None:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
    except Exception as exc:
        raise ClaudeCallError(f"Claude API error: {exc}") from exc

    return response.content[0].text.strip()
