"""
sam/claude_analyst.py — uses Claude to analyze SAM.gov opportunities.

Sends the opportunity text to Claude and gets back a structured compliance
matrix: summary, requirements, eval criteria, compliance flags, and a
capability statement outline.

build_executive_summary() is a pure Python function (no API call) that maps
the Claude analysis dict to FAR/DFARS-cited executive summary flags.

Ported from sam_agent's claude_analyst.py: the direct anthropic.Anthropic()
client + inline try/except is replaced with shared.claude_client.call_claude(),
which enforces the broad-except pattern by construction.
"""

from __future__ import annotations

import json
import re

from shared.claude_client import call_claude, ClaudeCallError

CLAUDE_MAX_TOKENS = 2048

_PROMPT = """\
You are a defense acquisition analyst helping a small business understand a \
government contract opportunity. Analyze the solicitation below and return a \
JSON object — nothing else, no markdown, just raw JSON.

SOLICITATION:
{opportunity_text}

Return exactly this JSON structure:
{{
  "summary": "2-3 sentence plain-English description of what is being bought and why",
  "agency": "contracting agency name",
  "estimated_value": "dollar amount or range if stated, else null",
  "period_of_performance": "duration or date range if stated, else null",
  "place_of_performance": "city/state or remote, if stated, else null",
  "clearance_required": "security clearance level if required (e.g. Secret, TS/SCI), else null",
  "cmmc_level": "CMMC level if stated (e.g. Level 2), else null",
  "set_aside": "small business set-aside type if any, else null",
  "nist_800_171_required": "true if the solicitation explicitly requires NIST SP 800-171 compliance for handling Controlled Unclassified Information (CUI), false otherwise",
  "section_889_applies": "true if the contract involves telecommunications equipment, network hardware, surveillance systems, or IT infrastructure services where Section 889 NDAA prohibited-equipment restrictions (Huawei, ZTE, Hytera, Hikvision, Dahua) would be material, false otherwise",
  "buy_american_act_applies": "true if the solicitation explicitly references Buy American Act, Trade Agreements Act, or domestic sourcing mandates for supplies, false otherwise",
  "pricing_model": "cost-plus if this is a cost-reimbursement contract with audit requirements; commercial-item if FAR Part 12 commercial item procedures apply; fixed-price if firm-fixed-price or fixed-price incentive; other for hybrid types; null if not determinable from the solicitation",
  "key_requirements": [
    {{"requirement": "plain-language requirement text", "category": "Technical|Personnel|Compliance|Past Performance|Other"}}
  ],
  "evaluation_criteria": [
    {{"criterion": "evaluation criterion", "weight": "weight or relative importance if stated, else null"}}
  ],
  "compliance_flags": [
    {{"flag": "compliance concern or special requirement", "severity": "High|Medium|Low"}}
  ],
  "capability_statement_bullets": [
    "bullet point for a capability statement response to this specific opportunity"
  ],
  "bottom_line": "1-sentence go/no-go assessment for a small defense-focused company"
}}
"""

# FAR/DFARS citation library for the executive summary
_EXEC_SUMMARY_MAP = {
    "cmmc_l3": {
        "title": "CMMC Level 3 Certification Required",
        "clause": "DFARS 252.204-7021",
        "description": (
            "Contractor must hold a valid CMMC Level 3 certification (110 NIST SP 800-171 "
            "practices + 24 NIST SP 800-172 practices). Assessments are conducted by DCSA "
            "and required for contracts involving programs critical to national security."
        ),
        "severity": "High",
    },
    "cmmc_l2": {
        "title": "CMMC Level 2 Certification Required",
        "clause": "DFARS 252.204-7021",
        "description": (
            "Contractor must hold a valid CMMC Level 2 certification (110 NIST SP 800-171 "
            "practices) issued by a DoD-authorized C3PAO prior to award. Self-assessments "
            "are not accepted for Level 2 contracts that involve CUI."
        ),
        "severity": "High",
    },
    "nist_800_171": {
        "title": "NIST SP 800-171 CUI Safeguarding Required",
        "clause": "DFARS 252.204-7012",
        "description": (
            "Contractor must implement all 110 security practices in NIST SP 800-171 Rev 2 "
            "to protect Covered Defense Information (CDI) / CUI. A current System Security "
            "Plan (SSP) and Plan of Action & Milestones (POA&M) must be maintained and made "
            "available to the government upon request."
        ),
        "severity": "High",
    },
    "section_889": {
        "title": "Section 889 Covered Telecom Equipment Prohibition",
        "clause": "FAR 52.204-25 / DFARS 252.204-7018",
        "description": (
            "Contractor must not provide or use telecommunications equipment or services from "
            "Huawei, ZTE, Hytera, Hikvision, or Dahua (or their subsidiaries/affiliates) in "
            "contract performance. A Section 889 representation is required at offer submission "
            "and recertified annually under FAR 52.204-24."
        ),
        "severity": "High",
    },
    "buy_american": {
        "title": "Buy American Act — Domestic Sourcing Required",
        "clause": "FAR 52.225-1 / FAR 52.225-3",
        "description": (
            "Supplies delivered under this contract must meet Buy American Act domestic "
            "end-product requirements. Products must be manufactured in the U.S. with domestic "
            "components exceeding 55% of cost. Exceptions require contracting officer approval. "
            "Trade Agreements Act (TAA) exceptions may apply for designated-country end products."
        ),
        "severity": "Medium",
    },
    "cost_plus": {
        "title": "Cost-Plus Contract — DCAA Audit Rights Apply",
        "clause": "FAR 52.215-2 / FAR 15.408",
        "description": (
            "This is a cost-reimbursement contract. Contractor must maintain a DCAA-approved "
            "cost accounting system. Certified cost or pricing data is required if the "
            "negotiated price exceeds the FAR threshold ($2M). The government retains full "
            "audit rights over incurred costs, subcontract costs, and indirect rates for the "
            "period of performance plus three years."
        ),
        "severity": "Medium",
    },
    "commercial_item": {
        "title": "Commercial Item Procurement — FAR Part 12 Applies",
        "clause": "FAR 52.212-1 / FAR Part 12",
        "description": (
            "FAR Part 12 commercial item procedures govern this acquisition. Standard commercial "
            "terms apply; certified cost or pricing data is not required. Verify the offered "
            "product or service qualifies as a 'commercial product' or 'commercial service' "
            "under FAR 2.101 before submitting an offer."
        ),
        "severity": "Low",
    },
}


def _is_truthy(val: object) -> bool:
    """Accept both JSON boolean true and the string 'true' from Claude."""
    if val is True:
        return True
    if isinstance(val, str) and val.strip().lower() in ("true", "yes"):
        return True
    return False


def build_executive_summary(analysis: dict) -> list[dict]:
    """
    Derive FAR/DFARS-cited executive summary flags from a Claude analysis dict.

    Pure Python — no API call. Returns a list of dicts, each with:
      title, clause, description, severity
    """
    flags: list[dict] = []

    # CMMC (highest level first so Level 3 doesn't also produce a Level 2 entry)
    cmmc_raw = (analysis.get("cmmc_level") or "").lower()
    if "level 3" in cmmc_raw:
        flags.append(_EXEC_SUMMARY_MAP["cmmc_l3"])
    elif cmmc_raw:
        flags.append(_EXEC_SUMMARY_MAP["cmmc_l2"])

    # NIST SP 800-171 (distinct FAR clause from CMMC; may appear without CMMC on older awards)
    if _is_truthy(analysis.get("nist_800_171_required")):
        flags.append(_EXEC_SUMMARY_MAP["nist_800_171"])

    # Section 889 Chinese telecom prohibition
    if _is_truthy(analysis.get("section_889_applies")):
        flags.append(_EXEC_SUMMARY_MAP["section_889"])

    # Buy American Act
    if _is_truthy(analysis.get("buy_american_act_applies")):
        flags.append(_EXEC_SUMMARY_MAP["buy_american"])

    # Pricing model
    pricing = (analysis.get("pricing_model") or "").lower()
    if "cost" in pricing and "plus" in pricing:
        flags.append(_EXEC_SUMMARY_MAP["cost_plus"])
    elif "commercial" in pricing:
        flags.append(_EXEC_SUMMARY_MAP["commercial_item"])

    return flags


class AnalysisError(Exception):
    pass


def analyze_opportunity(opportunity_text: str) -> dict:
    """Send opportunity text to Claude and return structured analysis dict."""
    try:
        raw = call_claude(
            [{"role": "user", "content": _PROMPT.format(opportunity_text=opportunity_text)}],
            max_tokens=CLAUDE_MAX_TOKENS,
        )
    except ClaudeCallError as exc:
        raise AnalysisError(str(exc)) from exc

    # Strip markdown code fences if the model wrapped the JSON anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"Could not parse Claude response as JSON: {exc}\n\nRaw: {raw}") from exc
