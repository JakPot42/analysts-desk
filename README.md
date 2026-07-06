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
2. **A web merge** of the 3 FastAPI apps in the cluster (sam_agent,
   friendshore, sentinel) into one deployment -- shared infrastructure, not
   shared data. Landing page (`templates/landing.html`) just links out to the
   three tools; there's no unifying entity view.

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

## Web merge (`/sam`, `/friendshore`, `/sentinel`)

One FastAPI process, one shared SQLite DB via `database.py`, one landing
page. Each tool keeps its own tables, own Claude prompts, own domain logic --
only infrastructure is shared (the DB engine, the static-mount discipline,
the `shared/claude_client.py` wrapper).

**Real table-name collision found and fixed during the port:** sam_agent's
`Analysis` model and friendshore's `SupplyChainAnalysis` model both used
`__tablename__ = "analyses"`. All three tools' tables are now prefixed
(`sam_*`, `friendshore_*`, `sentinel_*`) to remove that collision and any
future one, in one pass rather than fixing them as found.

**Route/static collisions resolved the same way Arbor's were:** all three
standalone apps mounted a bare `/static` and served routes off a bare `/`.
Routes are now under `/sam`, `/friendshore`, `/sentinel`; static assets under
`/static/sam`, `/static/friendshore`, `/static/sentinel`.

**Verified end-to-end over real HTTP before considering this done** (not
just unit tests): booted the merged server and hit every route for all
three tools, including FriendShore's actual matplotlib-rendered graph PNG
being served through the new static mount, SENTINEL's `/api/stats` and
cluster/report detail pages, idempotent re-seeding for all three (counts
unchanged on re-seed), and correct 404s for missing records.

Minor disclosed cleanup during the friendshore port: dropped a latent no-op
in `claude_agent.py` -- the original had an unreachable
`except json.JSONDecodeError` clause after a catch-all `except Exception`
at both Claude call sites (the broader clause already catches
`JSONDecodeError`, so the second one could never fire).

## Step 3 -- distributed into the 8 CLI tool repos

Each tool got only the files it actually needed, copied in (not pip-installed,
same vendoring pattern as `entity_resolver.py`), call sites swapped, existing
test suite re-run for regressions, committed and pushed individually:

| Repo | Files added | Notes |
|---|---|---|
| friendshore | (covered in Step 2) | entity_resolver.py upgrade flagged as optional, not done |
| tech_scanner | `claude_client.py` | consistency pass -- call site was already safe |
| osint_triage | `claude_client.py`, `demo_mode.py` | demo_mode.py added but deliberately NOT wired up -- this tool's `demo` command and live `triage` command stay as separate code paths, no forced DEMO_MODE flag |
| osint_brief | `claude_client.py`, `arxiv_client.py` | agent.py's `_decide_next`/`_synthesize` no longer take a client object; `sources/arxiv.py` is now a thin adapter over the shared client |
| volt_typhoon | `claude_client.py` | added 2 tests for a previously entirely-untested live-mode path |
| ics_assessor | `claude_client.py` | 2 call sites (advisory_parser.py, report_generator.py); added 6 tests, including a new test_report_generator.py that didn't exist before |
| dragonbridge_analyzer | `claude_client.py` | added 2 tests for a previously-untested live-mode path |

Every repo's full existing test suite was re-run after its swap with zero
regressions. Several tools (volt_typhoon, ics_assessor, dragonbridge_analyzer)
had genuinely zero test coverage of their live-mode Claude call before this
pass -- new tests were added alongside the refactor rather than left
uncovered.

One pre-existing, unrelated test failure was found and left alone during the
osint_brief port (`test_brief.py::test_source_log_shows_tool_and_query`,
confirmed via `git stash` to fail identically on unmodified master -- a
table-column-truncation display bug, out of scope for this distribution pass).

## Status

All three steps of the Phase 6 Cluster 2 plan are complete: the shared-core
reference library (Step 1), the web merge of sam_agent + friendshore +
sentinel (Step 2, live at analysts-desk.onrender.com), and distribution of
the shared-core files into the 8 CLI tool repos (Step 3). 146 tests passing
in this repo (83 shared-core + 63 ported/new web-app tests); each of the 6
CLI repos that received files re-ran its own full suite with zero
regressions.
