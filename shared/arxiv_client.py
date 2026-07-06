"""
Canonical arXiv Atom-feed client for the Analyst's Desk cluster.

Reconciles two independently-built clients that both called
export.arxiv.org/api/query: tech_scanner's sources/arxiv_client.py (needs
author affiliations, for institution-level entity resolution) and
osint_brief's sources/arxiv.py (doesn't need affiliations -- just wants
raw hits for its bounded agentic loop).

Returns one superset record (ArxivPaper) per paper; consumers that don't
need `affiliations` just ignore the field. No behavior change for either
original consumer beyond that shape unification -- both source clients
already had the identical "return [] on any request/parse failure, never
raise" behavior, which is preserved here unchanged (unlike the SAM.gov
reconciliation, this is not a disclosed behavior change).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests

_BASE = "https://export.arxiv.org/api/query"
_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"
_TIMEOUT = 20
_MAX_ABSTRACT_CHARS = 1500


@dataclass
class ArxivPaper:
    external_id: str
    title: str
    abstract: str
    url: str
    published_date: str
    affiliations: list[str] = field(default_factory=list)


def _extract_affiliations(entry: ET.Element) -> list[str]:
    """Extract author affiliations from an arXiv Atom entry."""
    affiliations: list[str] = []
    for author in entry.findall(f"{{{_ATOM_NS}}}author"):
        aff_el = author.find(f"{{{_ARXIV_NS}}}affiliation")
        if aff_el is not None and aff_el.text:
            aff = aff_el.text.strip()
            if aff and aff not in affiliations:
                affiliations.append(aff)
    return affiliations


def search(query: str, max_results: int = 5, *, prefix_all: bool = False) -> list[ArxivPaper]:
    """
    Search arXiv for papers matching `query`.

    prefix_all=True sends the query as `all:{query}` (osint_brief's
    free-text style); prefix_all=False (the default) sends it as-is,
    matching tech_scanner's own pre-built field-prefixed queries (e.g.
    "ti:hypersonic").

    Returns [] on any request/parse failure -- never raises.
    """
    search_query = f"all:{query}" if prefix_all else query
    try:
        resp = requests.get(
            _BASE,
            params={
                "search_query": search_query,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    papers: list[ArxivPaper] = []
    for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
        title_el = entry.find(f"{{{_ATOM_NS}}}title")
        summary_el = entry.find(f"{{{_ATOM_NS}}}summary")
        id_el = entry.find(f"{{{_ATOM_NS}}}id")
        published_el = entry.find(f"{{{_ATOM_NS}}}published")

        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        abstract = (summary_el.text or "").strip() if summary_el is not None else ""
        url = (id_el.text or "").strip() if id_el is not None else ""
        date = (published_el.text or "")[:10] if published_el is not None else ""

        if not title or not url:
            continue

        # Use the arxiv ID (last segment of URL) as external_id
        external_id = url.rstrip("/").rsplit("/", 1)[-1]

        papers.append(ArxivPaper(
            external_id=external_id,
            title=title,
            abstract=abstract[:_MAX_ABSTRACT_CHARS],
            url=url,
            published_date=date,
            affiliations=_extract_affiliations(entry),
        ))
    return papers


def fetch_all(searches: list[tuple[str, int]]) -> list[ArxivPaper]:
    """Run multiple (query, max_results) searches and dedupe by external_id."""
    seen: set[str] = set()
    results: list[ArxivPaper] = []
    for query, max_r in searches:
        for paper in search(query, max_results=max_r):
            if paper.external_id not in seen:
                seen.add(paper.external_id)
                results.append(paper)
    return results
