"""
entity_resolver.py — institution/organization name deduplication.

Canonical copy for the Analyst's Desk cluster, promoted from tech_scanner's
entity_resolver.py (itself adapted from GhostTrace's). This is the fourth
deployment of this pattern in the portfolio (GhostTrace -> tech_scanner ->
PatientFusion -> entity_graph), and the first time it's been pulled out as
a standalone shared file rather than copy-pasted+adapted per project.

Operates at INSTITUTION/ORGANIZATION level. If a consumer needs a
jurisdiction-conflict guard (the kind GhostTrace/CFIUS use for corporate
ownership resolution), that's a deliberately separate concern this module
does not add -- see NORMALIZE_SUFFIXES below, which mixes corporate and
academic/government-lab suffixes and has no jurisdiction field at all.

Same three-band design as every prior deployment:
  similarity >= FUZZY_AUTO_MERGE_THRESHOLD  -> merge automatically
  similarity >= FUZZY_ADJUDICATE_THRESHOLD  -> call adjudicator if provided
  below                                     -> distinct entities
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Callable

# Thresholds carried over unchanged from every prior deployment of this module.
FUZZY_AUTO_MERGE_THRESHOLD = 90.0
FUZZY_ADJUDICATE_THRESHOLD = 75.0

# Terms to strip when normalizing names -- corporate suffixes plus
# academic/government-lab vocabulary (tech_scanner's addition over
# GhostTrace's original corporate-only list).
NORMALIZE_SUFFIXES = [
    "inc", "llc", "ltd", "corp", "corporation", "co", "plc", "lp",
    "university", "univ",
    "institute", "inst",
    "laboratory", "lab", "labs", "national laboratory",
    "technologies", "tech",
    "systems", "group", "division", "dept", "department",
    "research", "center", "centre",
]

Adjudicator = Callable[[str, str], bool]

_SUFFIX_SET = {s.replace(".", "").replace(" ", "") for s in NORMALIZE_SUFFIXES}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, remove leading articles and suffixes."""
    cleaned = "".join(ch if ch.isalnum() or ch == " " else " " for ch in name.lower())
    tokens = cleaned.split()
    if tokens and tokens[0] in ("the", "a", "an"):
        tokens = tokens[1:]
    # Drop standard suffixes from the tail
    while tokens and tokens[-1] in _SUFFIX_SET:
        tokens = tokens[:-1]
    # Also check 2-3-token compound suffixes
    for n in (3, 2):
        if len(tokens) >= n and "".join(tokens[-n:]) in _SUFFIX_SET:
            tokens = tokens[:-n]
            break
    return " ".join(tokens)


def similarity(a: str, b: str) -> float:
    """0-100 similarity between two normalized names.

    Max of direct, token-sort, and token-set measures so word order and
    partial overlap (e.g. "MIT Lincoln Laboratory" vs "MIT") don't defeat
    the match.
    """
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 100.0
    direct = SequenceMatcher(None, na, nb).ratio()
    ta, tb = na.split(), nb.split()
    token_sort = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    sa, sb = set(ta), set(tb)
    token_set = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
    return max(direct, token_sort, token_set) * 100


def _merge_into(canonical: dict, raw: dict) -> None:
    """Fold a new sighting into an existing canonical entity."""
    if raw["name"] not in canonical["aliases"] and raw["name"] != canonical["canonical_name"]:
        canonical["aliases"].append(raw["name"])
    if not canonical.get("institution_type") and raw.get("institution_type"):
        canonical["institution_type"] = raw["institution_type"]
    for src in raw.get("sources") or []:
        if src and src not in canonical["sources"]:
            canonical["sources"].append(src)


def _new_canonical(raw: dict) -> dict:
    return {
        "canonical_name": raw["name"],
        "aliases": [],
        "institution_type": raw.get("institution_type"),
        "sources": list(raw.get("sources") or []),
    }


def resolve_entities(
    raw_entities: list[dict],
    adjudicator: Adjudicator | None = None,
) -> tuple[list[dict], dict[str, str]]:
    """Collapse name variants into canonical entities.

    Each entry in raw_entities must have at least: {"name": str}.
    Optional fields: institution_type, sources (list[str]).

    Returns (resolved_entities, alias_map) where alias_map maps every raw
    name to its canonical name.
    """
    resolved: list[dict] = []
    alias_map: dict[str, str] = {}
    verdict_cache: dict[frozenset[str], bool] = {}

    def _ask(name_a: str, name_b: str) -> bool:
        if adjudicator is None:
            return False
        key = frozenset((name_a, name_b))
        if key not in verdict_cache:
            verdict_cache[key] = adjudicator(name_a, name_b)
        return verdict_cache[key]

    for raw in raw_entities:
        name = (raw.get("name") or "").strip()
        if not name:
            continue
        raw = {**raw, "name": name}

        best: dict | None = None
        best_score = 0.0
        for canonical in resolved:
            for variant in [canonical["canonical_name"], *canonical["aliases"]]:
                score = similarity(name, variant)
                if score > best_score:
                    best_score = score
                    best = canonical

        merged = False
        if best is not None:
            if best_score >= FUZZY_AUTO_MERGE_THRESHOLD:
                merged = True
            elif best_score >= FUZZY_ADJUDICATE_THRESHOLD:
                merged = _ask(name, best["canonical_name"])

        if merged and best is not None:
            _merge_into(best, raw)
            alias_map[name] = best["canonical_name"]
        else:
            entity = _new_canonical(raw)
            resolved.append(entity)
            alias_map[name] = entity["canonical_name"]

    return resolved, alias_map


def resolve_institution_list(names: list[str]) -> list[str]:
    """Convenience wrapper: resolve a flat list of name strings.

    Returns a deduplicated list of canonical names, preserving first-seen order.
    """
    raw = [{"name": n} for n in names if n and n.strip()]
    _, alias_map = resolve_entities(raw)
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        canon = alias_map.get(n.strip(), n.strip())
        if canon and canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out
