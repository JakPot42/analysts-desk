"""
sentinel/claude_analyst.py — narrative extraction, TTP classification, intel
report generation.

Ported from sentinel's claude_analyst.py: the lru_cache'd anthropic.Anthropic
client + inline try/except at all three call sites is replaced with
shared.claude_client.call_claude(). Note this project's DISARM TTP
classification is Claude-as-classifier (no deterministic rules-engine
backstop) -- an architectural outlier against the portfolio's dominant
"Claude extracts, rules decide" pattern, unchanged by this port since fixing
that is a design decision out of scope for a merge.
"""

from __future__ import annotations

import json
import re

from shared.claude_client import call_claude, ClaudeCallError
from sentinel.disarm_ttps import TTPS


class AnalystError(Exception):
    pass


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json(raw: str, context: str) -> dict:
    cleaned = _strip_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AnalystError(f"{context}: invalid JSON — {exc}") from exc


def _require(data: dict, fields: list[str], context: str) -> None:
    for f in fields:
        if f not in data:
            raise AnalystError(f"{context}: missing field '{f}'")


NARRATIVE_FIELDS = ["narrative_summary", "entities", "keywords", "sentiment", "is_divisive", "credibility_signals"]


def extract_narrative(title: str, body: str, source_name: str, outlet_type: str) -> dict:
    """Analyze a single article and extract the core narrative claim + signals."""
    prompt = f"""You are an intelligence analyst specializing in detecting foreign influence operations.
Analyze the following article and extract structured signals.

SOURCE: {source_name} (type: {outlet_type})
TITLE: {title}
BODY: {body[:1500]}

Respond ONLY with valid JSON (no markdown fences, no explanation):
{{
  "narrative_summary": "One sentence describing the core claim being made",
  "entities": ["list of named people, orgs, countries, weapons systems mentioned"],
  "keywords": ["5-8 keywords that define this narrative topic"],
  "sentiment": "negative|neutral|positive",
  "is_divisive": true|false,
  "credibility_signals": ["list of red flags: 'no sources cited', 'anonymous expert', 'emotional language', 'unverified claim', etc. Empty list if none."]
}}"""

    try:
        raw = call_claude([{"role": "user", "content": prompt}], max_tokens=600)
    except ClaudeCallError as exc:
        raise AnalystError(f"API error during narrative extraction: {exc}") from exc

    data = _parse_json(raw, "extract_narrative")
    _require(data, NARRATIVE_FIELDS, "extract_narrative")
    return data


TTP_LIST_TEXT = "\n".join(f"- {t['id']}: {t['name']} — {t['description']}" for t in TTPS)

CLUSTER_FIELDS = ["ttps", "coordination_indicators", "attribution", "confidence_level", "threat_level"]


def analyze_cluster_ttps(cluster_label: str, articles_summary: list[dict]) -> dict:
    """Analyze a narrative cluster and identify DISARM framework TTPs."""
    articles_text = "\n".join(
        f"[{a['source_name']} / {a['outlet_type']}] {a['title']} — {a.get('narrative_summary','')}"
        for a in articles_summary
    )

    prompt = f"""You are an IO (influence operations) analyst. A narrative cluster has been detected:

CLUSTER: {cluster_label}

ARTICLES IN CLUSTER:
{articles_text}

DISARM FRAMEWORK TTPs to assess:
{TTP_LIST_TEXT}

Respond ONLY with valid JSON:
{{
  "ttps": [
    {{
      "id": "T0019",
      "name": "Seed Distortions",
      "confidence": "high|medium|low",
      "rationale": "Brief explanation of why this TTP applies"
    }}
  ],
  "coordination_indicators": ["list of observable coordination signals, e.g. 'same narrative across 4 outlets in 90 min'"],
  "attribution": "One sentence — consistent with [actor] IO TTPs, or UNATTRIBUTED",
  "confidence_level": "HIGH|MODERATE|LOW|UNASSESSED",
  "threat_level": "HIGH|MEDIUM|LOW"
}}"""

    try:
        raw = call_claude([{"role": "user", "content": prompt}], max_tokens=800)
    except ClaudeCallError as exc:
        raise AnalystError(f"API error during TTP analysis: {exc}") from exc

    data = _parse_json(raw, "analyze_cluster_ttps")
    _require(data, CLUSTER_FIELDS, "analyze_cluster_ttps")
    return data


REPORT_FIELDS = ["title", "subject", "key_findings", "attribution", "confidence_level", "full_text"]


def generate_intel_report(clusters_data: list[dict]) -> dict:
    """Generate a formatted intelligence assessment across all active clusters."""
    clusters_text = "\n\n".join(
        f"CLUSTER {i+1}: {c['label']}\n"
        f"  Threat Level: {c['threat_level']} | Articles: {c['article_count']} | "
        f"Adversary sources: {c['adversary_count']} | Spread: {c['spread_hours']}h\n"
        f"  TTPs: {', '.join(c.get('ttps', [])) or 'none analyzed'}\n"
        f"  Summary: {c.get('summary', 'N/A')}"
        for i, c in enumerate(clusters_data)
    )

    prompt = f"""You are a senior intelligence analyst writing a finished intelligence product.

ACTIVE NARRATIVE CLUSTERS DETECTED:
{clusters_text}

Write a concise intelligence assessment. Respond ONLY with valid JSON:
{{
  "title": "Short title for the intelligence report",
  "subject": "SUBJECT line (one sentence)",
  "key_findings": [
    "Finding 1 — most significant",
    "Finding 2",
    "Finding 3"
  ],
  "attribution": "Attribution assessment sentence",
  "confidence_level": "HIGH|MODERATE|LOW|UNASSESSED",
  "full_text": "Full formatted intelligence assessment in plain text. Include: SUMMARY, KEY FINDINGS numbered list, THREAT ASSESSMENT, and RECOMMENDED ACTIONS. Use formal intelligence writing style. Mark as UNCLASSIFIED // FOR OFFICIAL USE ONLY (DEMO)."
}}"""

    try:
        raw = call_claude([{"role": "user", "content": prompt}], max_tokens=1500)
    except ClaudeCallError as exc:
        raise AnalystError(f"API error during report generation: {exc}") from exc

    data = _parse_json(raw, "generate_intel_report")
    _require(data, REPORT_FIELDS, "generate_intel_report")
    return data
