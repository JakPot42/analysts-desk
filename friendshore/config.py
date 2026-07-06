"""
friendshore/config.py — FriendShore Supply Chain De-Risking Engine, tool-local config.

Risk thresholds and country classifications carried over unchanged from the
standalone project. Not deduplicated against the near-identical lists that
GhostTrace/CFIUS/DIB/Debt Exposure Monitor each maintain in Arbor -- that
cross-cluster reconciliation is out of scope for this merge (Analyst's Desk
web merge is infrastructure-only, not a data/logic consolidation).
"""
from __future__ import annotations

APP_TITLE = "FriendShore Supply Chain De-Risking Engine"
DEMO_MODE = True
DEMO_BANNER = "DEMONSTRATION ONLY — SYNTHETIC DATA — NOT FOR OPERATIONAL USE"

# --- Graph rendering ---
GRAPH_OUTPUT_DIR = "static/friendshore/graphs"

# --- Risk scoring ---
# Countries considered high-risk per US policy (USMCA, Xinjiang concerns, etc.)
HIGH_RISK_COUNTRIES = {
    "China", "PRC", "People's Republic of China", "Russia", "Iran",
    "North Korea", "DPRK", "Belarus", "Venezuela",
}

# Countries considered friendly / low-risk for supply chain purposes
FRIENDLY_NATIONS = {
    "United States", "USA", "US",
    "Mexico", "Canada",
    "United Kingdom", "UK",
    "Germany", "France", "Italy", "Netherlands", "Poland", "Czech Republic",
    "Japan", "South Korea", "Australia", "Taiwan",
    "Vietnam", "India", "Thailand", "Malaysia",
    "Israel",
}

# Risk score weights
RISK_WEIGHTS = {
    "high_risk_country": 40,       # supplier is in a high-risk nation
    "single_point_of_failure": 30,  # only one supplier for a component
    "high_tier_concentration": 20,  # one node supplies 3+ customers
    "missing_country_data": 10,     # country unknown
}

# Maximum risk score (sum of all weights = 100)
MAX_RISK_SCORE = 100
