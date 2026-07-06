"""
Canonical SAM.gov Opportunities API client for the Analyst's Desk cluster.

Reconciles two independently-built clients that both called
api.sam.gov/opportunities/v2/search: sam_agent's sam_client.py (general
keyword search across all opportunities) and tech_scanner's
sources/darpa_client.py (DARPA-filtered search, gated on SAM_API_KEY).

DISCLOSED BEHAVIOR CHANGE for the DARPA path only: tech_scanner's original
darpa_client.fetch() caught ANY exception -- a bad key, a network error, a
malformed response -- and silently returned [], indistinguishable from
"DARPA genuinely posted zero solicitations this window." That's a real
data-integrity gap: a broken key or a live outage would look identical to
an empty result, forever. search_darpa_solicitations() below keeps the
same "no key -> []" graceful skip (that's an intentional, expected
condition for this optional source, not a bug, and is unchanged), but now
raises SAMAPIError on an actual request/parse failure, matching
search_opportunities()'s existing (and more complete) error handling from
sam_agent, which already distinguishes 429 quota / 403 bad-key / timeout /
other failures with specific messages.

Also unifies the HTTP library: sam_agent used httpx, tech_scanner's
darpa_client used requests. This module standardizes on httpx. A consumer
adopting search_darpa_solicitations() that doesn't already depend on httpx
will need to add it.

Callers are responsible for reading their own SAM_API_KEY (or equivalent)
from the environment/their own config and passing it in explicitly -- this
module does not import any project's config.py, to stay decoupled.
"""
from __future__ import annotations

import datetime as _dt
import os

import httpx

SAM_BASE_URL = "https://api.sam.gov/opportunities/v2/search"


class SAMAPIError(Exception):
    pass


def _date_range(days_back: int = 90) -> tuple[str, str]:
    """Return (postedFrom, postedTo) in MM/dd/yyyy. Max span is 1 year."""
    today = _dt.date.today()
    start = today - _dt.timedelta(days=days_back)
    fmt = "%m/%d/%Y"
    return start.strftime(fmt), today.strftime(fmt)


def search_opportunities(
    query: str,
    api_key: str,
    limit: int = 10,
    offset: int = 0,
    active_only: bool = True,
    days_back: int = 90,
) -> dict:
    """Search SAM.gov for contract opportunities matching a keyword query."""
    posted_from, posted_to = _date_range(days_back)
    params: dict = {
        "api_key": api_key,
        "q": query,
        "limit": limit,
        "offset": offset,
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    if active_only:
        params["status"] = "active"

    try:
        response = httpx.get(SAM_BASE_URL, params=params, timeout=45)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429:
            raise SAMAPIError(
                "SAM.gov daily API quota reached. The free tier allows a limited number of "
                "requests per day. Quota resets at midnight UTC -- try again tomorrow, or "
                "use demo data in the meantime."
            ) from exc
        if status == 403:
            raise SAMAPIError(
                "SAM.gov API key rejected (403). Check that your API key matches the Public "
                "API Key from your SAM.gov Account Details page."
            ) from exc
        raise SAMAPIError(f"SAM.gov API error {status} -- try again in a moment.") from exc
    except httpx.TimeoutException as exc:
        raise SAMAPIError(
            "SAM.gov API timed out (the public API can be slow). Try your search again."
        ) from exc
    except httpx.RequestError as exc:
        raise SAMAPIError(f"Could not reach SAM.gov: {exc}") from exc


def get_opportunity(notice_id: str, api_key: str, days_back: int = 90) -> dict | None:
    """Fetch a single opportunity by its notice ID."""
    posted_from, posted_to = _date_range(days_back)
    params = {
        "api_key": api_key,
        "noticeid": notice_id,
        "limit": 1,
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    try:
        response = httpx.get(SAM_BASE_URL, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        hits = data.get("opportunitiesData", [])
        return hits[0] if hits else None
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise SAMAPIError(f"SAM.gov API error: {exc}") from exc


def build_opportunity_text(opp: dict) -> str:
    """Flatten a SAM.gov opportunity dict into a text block for Claude to analyze."""
    parts = [
        f"TITLE: {opp.get('title', 'N/A')}",
        f"SOLICITATION NUMBER: {opp.get('solicitationNumber', 'N/A')}",
        f"AGENCY: {opp.get('fullParentPathName', opp.get('organizationHierarchy', 'N/A'))}",
        f"NAICS CODE: {opp.get('naicsCode', 'N/A')}",
        f"SET-ASIDE TYPE: {opp.get('typeOfSetAside', 'N/A')}",
        f"POSTED DATE: {opp.get('postedDate', 'N/A')}",
        f"RESPONSE DEADLINE: {opp.get('responseDeadLine', 'N/A')}",
        f"PLACE OF PERFORMANCE: {opp.get('placeOfPerformance', {}).get('city', {}).get('name', 'N/A')}",
        "",
        "DESCRIPTION:",
        opp.get("description", "No description available."),
    ]
    return "\n".join(parts)


def search_darpa_solicitations(
    api_key: str | None = None,
    days_back: int = 90,
    limit: int = 10,
    dept_code: str = "9700",
    subtier_name: str = "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY",
) -> list[dict]:
    """
    Fetch recent DARPA solicitations from SAM.gov, filtered by subtier agency name.

    Returns [] (no exception) if api_key is not provided and SAM_API_KEY is
    not set in the environment -- an intentional graceful skip for this
    optional source, unchanged from tech_scanner's original behavior.
    Raises SAMAPIError on an actual request/parse failure -- see the module
    docstring for why this differs from the original silent-degrade-on-
    any-exception behavior.
    """
    key = api_key or os.environ.get("SAM_API_KEY", "")
    if not key:
        return []

    posted_from, posted_to = _date_range(days_back)
    try:
        resp = httpx.get(
            SAM_BASE_URL,
            params={
                "api_key": key,
                "limit": limit,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "organizationCode": dept_code,
                "typeOfSetAsideDescription": "",
                "ptype": "o,k",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
        raise SAMAPIError(f"SAM.gov DARPA search failed: {exc}") from exc

    items = []
    for opp in data.get("opportunitiesData") or []:
        # Filter to DARPA-issued solicitations by subtier name
        dept = (opp.get("subtierAgencyName") or "").upper()
        if subtier_name not in dept and "DARPA" not in dept:
            continue

        sol_id = (opp.get("solicitationNumber") or opp.get("noticeId") or "").strip()
        title = (opp.get("title") or "").strip()
        if not title:
            continue

        external_id = sol_id or title[:40]
        description = (opp.get("description") or "")[:1500]
        posted_date = (opp.get("postedDate") or "")[:10]
        url = opp.get("uiLink") or ""

        items.append({
            "source": "darpa",
            "external_id": external_id,
            "title": title,
            "abstract": description,
            "url": url,
            "published_date": posted_date,
            "raw_institutions": ["DARPA"],
        })
    return items
