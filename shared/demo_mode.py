"""
Canonical DEMO_MODE boolean-parsing convention for the Analyst's Desk cluster.

The 11 source projects surveyed for this cluster used at least 5 different
DEMO_MODE conventions: hardcoded True with no branch (sam_agent,
friendshore, sentinel); no flag at all, a separate `demo` command instead
(osint_triage, osint_brief); an env-var-driven constant with a real
internal fallback (ip_theft, volt_typhoon); a hardcoded constant that's
actually ignored in favor of a --live CLI flag threaded through
ctx.obj (ics_assessor, dragonbridge_analyzer, defense_budget_tracker); and
no DEMO_MODE concept at all (tech_scanner).

is_demo_mode() does not force every tool onto the same UX -- a tool using
a separate `demo` command or a `--live` flag keeps that; this only
centralizes the parsing convention (env var, default True, same
string-to-bool coercion already used by ip_theft/volt_typhoon) so the
constant name and parsing logic stop drifting across the cluster.
"""
import os


def is_demo_mode(default: bool = True) -> bool:
    """Read DEMO_MODE from the environment, defaulting to `default` if unset."""
    return os.getenv("DEMO_MODE", str(default)).lower() in ("1", "true", "yes")
