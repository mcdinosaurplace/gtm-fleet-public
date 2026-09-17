#!/usr/bin/env python3
"""scripts/pm/linear_resolve.py — resolve a stand-up commitment to a Linear entity.

Deterministic-first (the rigid procedure): detect canonical refs in code; match the
commitment text against the owner's candidate projects/issues by normalized exact /
word-boundary substring / token overlap. Only a unique high-confidence match links
automatically. Everything else is flagged for the model-fallback (pick from the
shortlist) and, if still uncertain, a one-time human confirm. No model here — this
core does detection, scoring, and flagging; the agent runs the model + confirm.
"""

import re

_REF_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
_PROJECT_URL_RE = re.compile(r"linear\.app/[^/\s]+/project/([^/\s)]+)")
_ISSUE_URL_RE = re.compile(r"linear\.app/[^/\s]+/issue/([A-Z0-9]+-\d+)")
_WORD_RE = re.compile(r"[a-z0-9]+")

NAME_MATCH_THRESHOLD = 0.6   # token-overlap (Jaccard) floor for an auto link
MARGIN = 0.2                 # lead the top match needs over the next on token overlap


def detect_refs(text):
    """Canonical Linear references in the text: issue URLs, project URLs, and bare
    issue keys (e.g. MAR-7076). Returns [{raw, kind, key|slug}]."""
    refs = []
    for m in _ISSUE_URL_RE.finditer(text):
        refs.append({"raw": m.group(0), "kind": "issue_url", "key": m.group(1)})
    for m in _PROJECT_URL_RE.finditer(text):
        refs.append({"raw": m.group(0), "kind": "project_url", "slug": m.group(1)})
    in_urls = " ".join(r["raw"] for r in refs)
    for m in _REF_KEY_RE.finditer(text):
        if m.group(0) not in in_urls:
            refs.append({"raw": m.group(0), "kind": "issue_key", "key": m.group(0)})
    return refs


def _normalize(s):
    return " ".join(_WORD_RE.findall(s.lower()))


def _tokens(s):
    return set(_WORD_RE.findall(s.lower()))


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score_candidates(commitment, candidates):
    """Rank candidates ({id, name, type, due_date}) against the commitment text.
    Returns a list of {candidate, score, exact, substring} sorted by score desc."""
    cnorm = _normalize(commitment)
    cpad = f" {cnorm} "
    ctok = _tokens(commitment)
    ranked = []
    for c in candidates:
        nnorm = _normalize(c["name"])
        exact = bool(nnorm) and nnorm == cnorm
        substring = bool(nnorm) and f" {nnorm} " in cpad   # word-boundary containment
        score = 1.0 if (exact or substring) else _jaccard(ctok, _tokens(c["name"]))
        ranked.append({"candidate": c, "score": score, "exact": exact, "substring": substring})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def resolve(commitment, candidates):
    """Deterministic resolution attempt. Returns {resolution, refs, match, shortlist}:
      - 'by_ref'     : canonical refs found (the agent looks them up)
      - 'by_name'    : a single high-confidence candidate matched
      - 'needs_model': no clear match -> the agent runs the model over `shortlist`,
                       then a one-time human confirm if still uncertain
    """
    refs = detect_refs(commitment)
    if refs:
        return {"resolution": "by_ref", "refs": refs, "match": None, "shortlist": []}

    ranked = score_candidates(commitment, candidates)
    shortlist = [r["candidate"] for r in ranked[:5]]
    strong = [r for r in ranked if r["exact"] or r["substring"]]
    if len(strong) == 1:
        return {"resolution": "by_name", "refs": [], "match": strong[0]["candidate"], "shortlist": shortlist}
    if len(strong) > 1:
        return {"resolution": "needs_model", "refs": [], "match": None, "shortlist": shortlist}
    if ranked and ranked[0]["score"] >= NAME_MATCH_THRESHOLD:
        if len(ranked) == 1 or ranked[0]["score"] - ranked[1]["score"] >= MARGIN:
            return {"resolution": "by_name", "refs": [], "match": ranked[0]["candidate"], "shortlist": shortlist}
    return {"resolution": "needs_model", "refs": [], "match": None, "shortlist": shortlist}
