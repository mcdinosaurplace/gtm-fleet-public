#!/usr/bin/env python3
"""scripts/pm/commitments.py — classify a resolved commitment and build its row.

Pure + deterministic given the resolution outcome. Derives scale / horizon /
effective_due_date from the resolved Linear entity type (project | issue | none) and
the stand-up week, then assembles the pm_commitments row. The agent supplies the
resolution (ref lookup / name match / model / confirm) + the entity's due date; this
core does the classification and row assembly.

Week convention: a week runs Sunday -> Saturday. A 'this_week' commitment's effective
due date is that week's Saturday.
"""

from datetime import date, datetime, timedelta

from scripts.pm import linear_resolve


def end_of_week(standup_date):
    """Saturday of the Sun->Sat week containing standup_date. Accepts an ISO string or
    a date; returns an ISO string."""
    d = date.fromisoformat(standup_date) if isinstance(standup_date, str) else standup_date
    return (d + timedelta(days=(5 - d.weekday()) % 7)).isoformat()


def classify(entity_type, entity_due_date, standup_date):
    """Return {scale, horizon, effective_due_date} from the resolved entity.
    entity_type: 'project' | 'issue' | None (incidental / unresolved-but-acknowledged)."""
    sd = standup_date if isinstance(standup_date, str) else standup_date.isoformat()
    eow = end_of_week(sd)
    if entity_type == "project":
        return {"scale": "project", "horizon": "multi_week", "effective_due_date": entity_due_date}
    if entity_type == "issue":
        future = bool(entity_due_date) and entity_due_date > sd
        return {
            "scale": "task",
            "horizon": "multi_week" if future else "this_week",
            "effective_due_date": entity_due_date or eow,
        }
    return {"scale": "incidental", "horizon": "this_week", "effective_due_date": eow}


def build_row(week_starting, owner, commitment, resolution, *, entity_type=None,
              entity_due_date=None, linear_link=None, project_id=None, issue_id=None,
              acknowledged_untracked=False, created_at=None):
    """Assemble a pm_commitments row dict. `resolution` in by_ref|by_name|confirmed|unresolved."""
    cls = classify(entity_type, entity_due_date, week_starting)
    ref_type = "project" if entity_type == "project" else ("issue" if entity_type == "issue" else None)
    return {
        "week_starting": week_starting,
        "owner": owner,
        "commitment": commitment,
        "linear_link": linear_link,
        "linear_ref_type": ref_type,
        "project_id": project_id,
        "issue_id": issue_id,
        "resolution": resolution,
        "scale": cls["scale"],
        "acknowledged_untracked": 1 if acknowledged_untracked else 0,
        "horizon": cls["horizon"],
        "effective_due_date": cls["effective_due_date"],
        "completion_status": "pending",
        "created_at": created_at,
    }


def build_resolution_update(week_starting, resolution, *, entity_type=None,
                            entity_due_date=None, linear_link=None, project_id=None,
                            issue_id=None, acknowledged_untracked=False):
    """Column dict to UPDATE an EXISTING pm_commitments row when a resolution lands
    (by_ref / by_name / confirmed, or an acknowledged-incidental). The classification
    half of build_row, without the insert-only fields (week_starting/owner/commitment/
    created_at). Pure. Apply via `db.update(conn, 'pm_commitments', <this>, {'id': row_id})`.

    Mirrors build_row's classify so a linked resolution and a freshly-inserted one agree.
    """
    cls = classify(entity_type, entity_due_date, week_starting)
    ref_type = "project" if entity_type == "project" else ("issue" if entity_type == "issue" else None)
    return {
        "resolution": resolution,
        "linear_link": linear_link,
        "linear_ref_type": ref_type,
        "project_id": project_id,
        "issue_id": issue_id,
        "scale": cls["scale"],
        "horizon": cls["horizon"],
        "effective_due_date": cls["effective_due_date"],
        "acknowledged_untracked": 1 if acknowledged_untracked else 0,
    }


def evaluate_completion(commitment_row, entity, *, now, evaluated_at):
    """Week-over-week completion for ONE prior commitment. Pure.

    entity: for a LINKED commitment, a dict {closed: bool, canceled: bool,
    original_due_date: str|None} describing the linked pm_projects/pm_issues entity
    (the caller derives closed/canceled from its live Linear status); None if the
    linked entity has vanished from Linear. Ignored for unlinked commitments.

    Linked: canceled -> 'dropped'; completed -> 'completed'; vanished -> 'carried';
    multi_week open -> 'missed' once original_due_date passes else 'in_flight';
    this_week open -> 'missed' once effective_due_date passes else 'in_flight'.
    Unlinked/incidental -> 'pending' (the skill's close-the-loop / model-match sets these).
    """
    linked = commitment_row.get("project_id") or commitment_row.get("issue_id")
    if not linked:
        status = "pending"
    elif entity is None:
        status = "carried"
    elif entity.get("canceled"):
        status = "dropped"
    elif entity.get("closed"):
        status = "completed"
    else:
        n = date.fromisoformat(now[:10]) if isinstance(now, str) else now
        if commitment_row.get("horizon") == "multi_week":
            odd = entity.get("original_due_date")
            status = "missed" if (odd and n > date.fromisoformat(odd[:10])) else "in_flight"
        else:
            edd = commitment_row.get("effective_due_date")
            status = "missed" if (edd and n > date.fromisoformat(edd[:10])) else "in_flight"
    return {"completion_status": status, "evaluated_at": evaluated_at}


# ---------- project-linked C3 entity resolution (cache-first, live-fallback) ----------
#
# get_project is not on every caller's Linear allowlist, so a project-linked commitment's
# entity is resolved cache-first: trust pm_projects.last_synced_at (the weekly pulse keeps
# it current) while it's fresh, and only fall back to a live list_projects search + name
# match (linear_resolve.resolve, already deterministic) when the cache is stale or the
# project_id has no cached row at all.

STALE_HOURS = 48


def cache_is_fresh(last_synced_at, now):
    """True if a cached pm_projects row's last_synced_at is within STALE_HOURS of `now`
    (both ISO 8601 timestamps). Missing last_synced_at is always stale."""
    if not last_synced_at:
        return False
    synced = datetime.fromisoformat(last_synced_at.replace("Z", "+00:00"))
    n = datetime.fromisoformat(now.replace("Z", "+00:00"))
    return (n - synced) <= timedelta(hours=STALE_HOURS)


def project_entity_from_cache(row):
    """C3 {closed, canceled, original_due_date} entity from a cached pm_projects row.
    Only valid when cache_is_fresh(row['last_synced_at'], now) is True."""
    return {
        "closed": row.get("status_type") == "completed",
        "canceled": row.get("status_type") == "canceled",
        "original_due_date": row.get("original_due_date"),
    }


def refresh_project_from_live(cached_row, live_project, *, now):
    """Build the pm_projects patch + C3 entity from a live Linear match for a project
    whose cache was stale or missing. `live_project` is pulse.normalize_project() output
    for the resolved match. `cached_row` may be None (no prior row).

    Honors the no-reschedule rule: original_due_date is set once (from the live project's
    target_date, on first capture) and never overwritten thereafter. Pure -- caller writes
    `patch` via db.update/db.upsert and passes `entity` to evaluate_completion."""
    status_type = live_project.get("status_type")
    closed = status_type == "completed"
    canceled = status_type == "canceled"
    original_due_date = (cached_row or {}).get("original_due_date") or live_project.get("target_date")
    prior_closed_at = (cached_row or {}).get("closed_at")
    patch = {
        "status_type": status_type,
        "original_due_date": original_due_date,
        "closed_at": prior_closed_at or (now if closed else None),
        "last_synced_at": now,
    }
    entity = {"closed": closed, "canceled": canceled, "original_due_date": original_due_date}
    return {"patch": patch, "entity": entity}


# ---------- matching a context reply to someone ELSE's existing commitment ----------
#
# A context (chatter) reply can be about the author's own new work -- that's just a
# this_week line for the author, resolved via the normal linear_resolve.resolve ->
# build_row path. But it can also be a resolution/approval of a DIFFERENT person's
# already-tracked commitment ("the head of marketing approves the copy the content lead raised"). That case needs a
# different match target: the subject person's own OPEN pm_commitments rows, not Linear
# entities. Reuses linear_resolve's ref-detection and name-scoring (same deterministic
# bar everywhere else) rather than a bespoke matcher.

def match_open_commitment(text, candidates):
    """Match `text` (e.g. an in-thread approval) against a person's OPEN pm_commitments
    rows. `candidates`: [{id, commitment, linear_link, project_id, issue_id}]. A canonical
    Linear ref in `text` that equals a candidate's own project_id/issue_id/linear_link
    wins outright; otherwise falls back to linear_resolve's name/content scoring against
    each candidate's `commitment` text. Returns {resolution: 'by_ref'|'by_name'|
    'needs_model', match: <candidate id> | None}. Ambiguous or no match -> needs_model --
    never guessed; the skill flags it in the journal rather than writing a link."""
    for ref in linear_resolve.detect_refs(text):
        key = ref.get("key") or ref.get("slug")
        if not key:
            continue
        for c in candidates:
            if key in (c.get("issue_id"), c.get("project_id")) or (c.get("linear_link") and key in c["linear_link"]):
                return {"resolution": "by_ref", "match": c["id"]}

    named = [{"id": c["id"], "name": c["commitment"]} for c in candidates]
    ranked = linear_resolve.score_candidates(text, named)
    strong = [r for r in ranked if r["exact"] or r["substring"]]
    if len(strong) == 1:
        return {"resolution": "by_name", "match": strong[0]["candidate"]["id"]}
    if len(strong) > 1:
        return {"resolution": "needs_model", "match": None}
    if ranked and ranked[0]["score"] >= linear_resolve.NAME_MATCH_THRESHOLD:
        if len(ranked) == 1 or ranked[0]["score"] - ranked[1]["score"] >= linear_resolve.MARGIN:
            return {"resolution": "by_name", "match": ranked[0]["candidate"]["id"]}
    return {"resolution": "needs_model", "match": None}
