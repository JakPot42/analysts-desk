# Analyst's Desk (Phase 6, Cluster 2)

Merger of 11 source projects: SAM.gov Acquisition Agent, FriendShore, SENTINEL,
FL OSINT Triage, OSINT Brief Generator, Emerging Tech Scanner, Defense Budget
Tracker, Volt Typhoon Assessor, IP Theft Pattern Database, Dragonbridge
Analyzer, ICS/SCADA Exposure Assessor.

Unlike Arbor (Phase 6, Cluster 1), this cluster has no single shared business
entity to converge on -- an acquisition opportunity isn't a narrative cluster
isn't a court case. So this is not one unified entity-centric app. It's two
things:

1. **`shared/`** -- a small, vendored (not pip-installed) reference library of
   the code that was genuinely duplicated across the 11 sources, copied out
   into each consuming repo the same way `entity_resolver.py` has already been
   copied four times across this portfolio (GhostTrace -> tech_scanner ->
   PatientFusion -> entity_graph).
2. **A web merge** (coming next) of the 3 FastAPI apps in the cluster
   (sam_agent, friendshore, sentinel) into one deployment -- shared
   infrastructure, not shared data.

## `shared/` contents

- **`claude_client.py`** -- one `call_claude()` wrapper pinning
  `claude-haiku-4-5-20251001` and enforcing the broad-`except Exception`
  pattern by construction. Built because two of the 11 source projects
  (`defense_budget_tracker`, `ip_theft`) had a live-mode Claude call with
  *no* exception handling at all -- both were fixed standalone before this
  library existed (see their own commit history), and this wrapper exists so
  that gap can't be reintroduced.
- **`entity_resolver.py`** -- promoted from `tech_scanner`'s copy (itself
  adapted from GhostTrace's). Institution/organization fuzzy-match and
  three-band merge (auto-merge >= 90, adjudicate >= 75, distinct below).
- **`sam_gov_client.py`** -- reconciles `sam_agent`'s general opportunity
  search and `tech_scanner`'s DARPA-filtered search (previously two
  independent clients hitting the same SAM.gov endpoint). **Disclosed
  behavior change:** the DARPA path used to swallow any request failure and
  return `[]`, indistinguishable from a real empty result. It now raises
  `SAMAPIError` on an actual failure while keeping the original "no API key
  -> `[]`" graceful skip for this optional source.
- **`arxiv_client.py`** -- reconciles `tech_scanner`'s (needs author
  affiliations) and `osint_brief`'s (doesn't) arXiv clients into one
  `search()` returning a superset `ArxivPaper` record. No behavior change.
- **`demo_mode.py`** -- one `is_demo_mode()` env-var convention. The 11
  sources used at least 5 different DEMO_MODE conventions; this doesn't force
  every tool onto the same UX, it just stops the parsing logic from
  drifting further.

## Status

Step 1 of the Phase 6 Cluster 2 plan: shared-core reference files, built and
tested standalone (83 tests, all mocked -- no real network/API calls). Not
yet distributed into the 8 CLI tool repos (that's Step 3) and the web merge
(Step 2) hasn't started yet.
