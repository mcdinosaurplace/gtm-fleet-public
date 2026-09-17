#!/usr/bin/env python3
"""scripts/pm/linear_create.py — accountability-driven Linear creation (Block G2).

The deterministic core behind "track it / new ticket / new project" replies to an
accountability prompt. Pure: keyword intent detection, dedup matching, payload assembly,
and the idempotency decision. NO model and NO I/O here — the agent runs the fixed
intent/fields model prompt (only when `detect_intent` returns `needs_model`), issues the
Slack/Linear MCP calls, and writes the DB via `db.py`.

Determinism posture (matches capture.py / linear_resolve.py): explicit keywords resolve
in code; anything ambiguous is flagged `needs_model` for the rigid model fallback. The
core never invents a title or a parent.

Idempotency (no dupes): the agent stamps `pm_commitments.create_requested_at` BEFORE the
Linear write. `creation_action` reads that stamp + `linear_link` to decide skip / reconcile
/ create, and `dedup_match` catches a same-title entity so a re-run links instead of
duplicating.
"""

import re

from scripts.pm.linear_resolve import detect_refs, _normalize

INTENTS = ("link_existing", "roll_in", "create_issue", "create_project", "incidental", "needs_model")

# Keyword sets (matched on lowercased reply text). Order of the checks in detect_intent
# matters: stronger / more explicit signals win over the bare "track it" inference.
_INCIDENTAL = ("incidental", "untracked", "don't track", "do not track", "dont track",
               "won't track", "wont track", "not tracking", "no need", "not needed")
_ROLL_IN = ("roll in", "roll into", "roll it in", "roll them in", "fold in", "fold into",
            "merge into", "merge it into", "combine with", "consolidate into")
_PROJECT = ("new project", "as a project", "track as a project", "create a project",
            "make it a project", "spin up a project", "its own project", "it's own project")
_ISSUE = ("new ticket", "new issue", "new task", "create an issue", "create a ticket",
          "create a task", "open a ticket", "open an issue", "file a ticket", "file an issue",
          "make a ticket", "make an issue", "as a ticket", "as an issue", "track as an issue",
          "track as a ticket", "its own ticket", "it's own ticket")
# Bare affirmatives to a "track it or incidental?" prompt -> create_issue, but inferred.
_BARE_TRACK = ("track it", "track this", "track that", "track these", "yes track", "lets track",
               "let's track")
_BARE_AFFIRM = ("yes", "yep", "yeah", "yup", "sure", "ok", "okay", "do it", "please")


def _has(text, needles):
    return any(n in text for n in needles)


def detect_intent(reply_text):
    """Deterministic intent detection for one commitment's reply.

    Returns {intent, inferred, refs}:
      - intent in INTENTS. `needs_model` means no explicit keyword matched -> the agent
        runs the fixed intent/fields prompt.
      - inferred=True only for a create reached from a bare affirmative ("track it" / "yes")
        with no kind signal: the agent must confirm once (kind + title + parent) before
        writing, and must NEVER create a project on inference.
    """
    raw = (reply_text or "").strip()
    low = raw.lower()
    refs = detect_refs(raw)

    if refs or "link to" in low or "link it to" in low:
        return {"intent": "link_existing", "inferred": False, "refs": refs}
    if _has(low, _INCIDENTAL):
        return {"intent": "incidental", "inferred": False, "refs": []}
    if _has(low, _ROLL_IN):
        return {"intent": "roll_in", "inferred": False, "refs": []}
    if _has(low, _PROJECT):
        return {"intent": "create_project", "inferred": False, "refs": []}
    if _has(low, _ISSUE):
        return {"intent": "create_issue", "inferred": False, "refs": []}
    if _has(low, _BARE_TRACK) or low in _BARE_AFFIRM:
        return {"intent": "create_issue", "inferred": True, "refs": []}
    return {"intent": "needs_model", "inferred": False, "refs": []}


def dedup_match(title, candidates):
    """Conservative idempotency check: return the candidate whose name normalizes EXACTLY
    to `title`, else None. Exact-only (not containment) so a re-run with the same title
    links instead of creating a duplicate, without risking a wrong link. `candidates` are
    open entities shaped {id, name, type, ...}."""
    tnorm = _normalize(title or "")
    if not tnorm:
        return None
    for c in candidates:
        if _normalize(c.get("name", "")) == tnorm:
            return c
    return None


def _compose_description(commitment, notes, subscribers, provenance):
    parts = []
    if notes:
        parts.append(notes.strip())
    elif commitment:
        parts.append(commitment.strip())
    if subscribers:
        names = ", ".join(f"@{s}" for s in subscribers)
        parts.append(f"Looping in {names} as subscriber.")
    if provenance:
        parts.append(provenance.strip())
    return "\n\n".join(parts)


def build_payload(*, entity_kind, title, owner, team, commitment=None, notes=None,
                  parent_project=None, default_project=None, subscribers=None,
                  related_to=None, provenance=None, labels=None):
    """Map a validated extraction to a Linear MCP payload. Returns (tool_name, payload).

    Fixed defaults: assignee / lead = `owner`; an issue with no `parent_project` is filed
    under `default_project` (the orphan home, e.g. MOPS Inbox) — an issue is never left
    project-less. Subscribers and stated dependency/scope `notes` go into the description
    (save_issue has no subscriber field; relations are set only via a real issue ref in
    `related_to`). The agent passes the returned dict straight to save_issue/save_project.
    """
    if entity_kind not in ("issue", "project"):
        raise ValueError(f"entity_kind must be 'issue' or 'project', got {entity_kind!r}")
    if not (title and title.strip()):
        raise ValueError("title is required and must be non-empty")
    if not team:
        raise ValueError("team is required")

    description = _compose_description(commitment, notes, subscribers, provenance)

    if entity_kind == "issue":
        project = parent_project or default_project
        if not project:
            raise ValueError("an issue needs parent_project or default_project (never project-less)")
        payload = {"title": title.strip(), "team": team, "project": project,
                   "assignee": owner, "description": description}
        if labels:
            payload["labels"] = labels
        if related_to:
            payload["relatedTo"] = related_to
        return "save_issue", payload

    # project
    payload = {"name": title.strip(), "addTeams": [team], "lead": owner, "description": description}
    if labels:
        payload["labels"] = labels
    return "save_project", payload


def creation_action(commitment_row):
    """Idempotency decision for a create-intent commitment row. Pure.

      - 'skip'      : already linked (`linear_link` set) — nothing to do.
      - 'reconcile' : a create was already requested (`create_requested_at` set) but no
                      link landed — search Linear by title and link if found, else retry.
                      Never blind re-create.
      - 'create'    : no prior request and no link — proceed (after a dedup_match search).
    """
    if commitment_row.get("linear_link"):
        return "skip"
    if commitment_row.get("create_requested_at"):
        return "reconcile"
    return "create"
