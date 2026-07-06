"""DISARM Framework TTP catalog — subset relevant to influence operations detection."""

from __future__ import annotations

TTPS: list[dict] = [
    {
        "id": "T0007",
        "name": "Create Inauthentic Accounts",
        "phase": "Plan",
        "description": "Create inauthentic personas, typically on social media, to carry out IO tasks.",
    },
    {
        "id": "T0008",
        "name": "Create Fake Experts",
        "phase": "Plan",
        "description": "Create fabricated subject-matter experts whose credentials cannot be verified.",
    },
    {
        "id": "T0019",
        "name": "Seed Distortions",
        "phase": "Prepare",
        "description": "Take a true event and introduce minor distortions that change its meaning or implication.",
    },
    {
        "id": "T0023",
        "name": "Distort Facts",
        "phase": "Prepare",
        "description": "Present factual information in a misleading or decontextualized way.",
    },
    {
        "id": "T0046",
        "name": "Search Engine Optimization (SEO)",
        "phase": "Execute",
        "description": "Manipulate SEO to increase reach of IO content in organic search results.",
    },
    {
        "id": "T0049",
        "name": "Flooding the Information Space",
        "phase": "Execute",
        "description": "Flood channels with high volumes of messaging to drown out legitimate content.",
    },
    {
        "id": "T0057",
        "name": "Amplify Divisive Content",
        "phase": "Execute",
        "description": "Amplify existing societal tensions and divisive narratives to increase polarization.",
    },
    {
        "id": "T0061",
        "name": "Sell Advertising around Content",
        "phase": "Monetise",
        "description": "Monetize IO content through advertising to sustain the operation.",
    },
    {
        "id": "T0081",
        "name": "Aggregate and Promote Existing Narratives",
        "phase": "Execute",
        "description": "Collect and re-broadcast existing divisive or false narratives to amplify reach.",
    },
    {
        "id": "T0085",
        "name": "Coordinate on Encrypted Platforms",
        "phase": "Plan",
        "description": "Use encrypted messaging platforms to coordinate IO activities while evading detection.",
    },
]

TTP_LOOKUP: dict[str, dict] = {t["id"]: t for t in TTPS}


def get_ttp(ttp_id: str) -> dict | None:
    return TTP_LOOKUP.get(ttp_id)


def all_ttp_ids() -> list[str]:
    return [t["id"] for t in TTPS]
