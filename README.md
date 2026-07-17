# Analyst's Desk

**Analyst's Desk is an intelligence and acquisition workbench that brings three analysis tools together in one web app.** Instead of running them as separate deployments, it puts federal opportunity-finding, supply-chain de-risking, and influence-operations detection behind a single landing page.

**Live demo:** https://analysts-desk.onrender.com

The demo runs on seeded example data — no login or API key needed.

## The three tools

| Tool | What it does |
|---|---|
| **SAM.gov Acquisition Agent** (`/sam`) | Searches SAM.gov for federal contract opportunities and uses AI to read an RFP, extract requirements, and draft a compliance matrix and capability statement |
| **FriendShore** (`/friendshore`) | Maps a supplier bill-of-materials into a tiered supply-chain graph, detects single points of failure in high-risk countries, and suggests allied alternatives |
| **SENTINEL** (`/sentinel`) | Monitors adversary media, clusters articles by narrative, classifies influence-operation techniques against the DISARM framework, and generates a finished intelligence assessment |

Each tool keeps its own data, prompts, and domain logic. Analyst's Desk shares the infrastructure underneath them — one web process, one database, a common AI client — not the data itself, because an acquisition opportunity, a supplier, and a media narrative aren't the same kind of object.

## Design principles

- **The AI extracts and drafts; deterministic rules decide.** Claude reads and summarizes unstructured sources; the scoring and classification are auditable code.
- **Demo mode by default.** Every tool works with no API key against seeded example data.
- **Hedged analytic language.** The threat-intelligence tools use non-attribution phrasing ("consistent with," "cannot be confirmed") rather than definitive claims.

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000. The database auto-seeds on startup. Set `ANTHROPIC_API_KEY` and turn off demo mode to enable live AI analysis.

## About

Analyst's Desk combines three independently-built tools — the SAM.gov Acquisition Agent, FriendShore, and SENTINEL — into one deployment, and shares a small common library with several related command-line tools in the same portfolio. It is part of a portfolio of national-security and defense-compliance software and is a demonstration of an integrated analyst workflow rather than a certified product.
