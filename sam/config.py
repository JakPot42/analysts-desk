"""sam/config.py — SAM.gov Acquisition Intelligence Agent, tool-local config."""
from __future__ import annotations

import os

SAM_API_KEY = os.environ.get("SAM_API_KEY", "")

APP_TITLE = "SAM.gov Acquisition Intelligence Agent"
DEMO_MODE = True
DEMO_BANNER = "DEMONSTRATION ONLY — SYNTHETIC ANALYSIS — NOT FOR PROPOSAL SUBMISSION"
