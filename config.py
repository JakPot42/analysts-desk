"""
config.py — shared configuration for the merged Analyst's Desk web app.

Per-tool config (banners, DEMO_MODE, API-specific settings, risk weights,
RSS sources, etc.) stays in each tool's own package (sam/config.py,
friendshore/config.py, sentinel/config.py) exactly as before the merge --
this file only holds what's genuinely shared across all three: the overall
app title and the one database all three tools now share.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "Analyst's Desk"
DATABASE_URL = "sqlite:///./analysts_desk.db"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
