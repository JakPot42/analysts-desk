"""sentinel/config.py — SENTINEL Influence Operations Detection Engine, tool-local config."""
from __future__ import annotations

import os

APP_TITLE = "SENTINEL — Influence Operations Detection Engine"
# Preserved exactly from the standalone project: this is the one of the 3 web
# apps that actually reads DEMO_MODE from the environment (sam_agent and
# friendshore both hardcode True) -- not changed during the port.
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("1", "true", "yes")
DEMO_BANNER = "DEMO MODE — Operation STEEL ECHO synthetic dataset loaded. No real threat intelligence."

# RSS feed sources: (name, url, outlet_type)
# outlet_type: "adversary" | "baseline" | "social"
RSS_SOURCES = [
    ("RT English",       "https://www.rt.com/rss/news/",              "adversary"),
    ("Sputnik News",     "https://sputnikglobe.com/export/rss2/world/index.xml", "adversary"),
    ("TASS English",     "https://tass.com/rss/v2.xml",               "adversary"),
    ("Global Times",     "https://www.globaltimes.cn/rss/outbrain.xml", "adversary"),
    ("Reuters World",    "https://feeds.reuters.com/reuters/worldNews", "baseline"),
    ("BBC World",        "http://feeds.bbci.co.uk/news/world/rss.xml", "baseline"),
]

# Reddit subreddits to monitor for amplification
REDDIT_SUBREDDITS = ["worldnews", "news", "conspiracy", "military", "antiwar"]

# Clustering threshold: articles with ≥ this many shared keywords get grouped
CLUSTER_KEYWORD_OVERLAP = 2

# Velocity window in hours — articles in this window count toward velocity score
VELOCITY_WINDOW_HOURS = 6
