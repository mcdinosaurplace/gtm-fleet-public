#!/usr/bin/env python3
"""scripts/pm/pulse.py — the linear-pulse-check compute core (deterministic, no I/O).

The skill fetches Linear (projects, issues, blockedBy relations for open issues, the
latest project status-update health) and the prior pm_* rows, normalizes them to flat
dicts, and calls compute_pulse(). This core returns every row to write plus the
missed-deadline detections (C2) and the gated state-change DM events. No network, no DB.
"""

from datetime import date

from scripts.pm import health

_CLOSED = ("completed", "canceled")
_LINEAR_HEALTH = {"onTrack": "on_track", "atRisk": "at_risk", "offTrack": "off_track"}
_DECLINE = {("on_track", "at_risk"), ("at_risk", "off_track"), ("on_track", "off_track")}


def _to_date(v):
    if v is None:
        return None
    return v if isinstance(v, date) else date.fromisoformat(v[:10])


# ---------- normalization (MCP shape -> flat dict the core consumes) ----------

def normalize_project(p):
    status = p.get("status")
    status_type = (status.get("type") if isinstance(status, dict) else None) or p.get("statusType") or p.get("status_type")
    lead = p.get("lead")
    members = p.get("members") or []
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "status_type": status_type,
        "lead_name": (lead.get("name") if isinstance(lead, dict) else lead),
        "member_names": [m.get("name") if isinstance(m, dict) else m for m in members],
        "start_date": p.get("startDate") or p.get("start_date"),
        "target_date": p.get("targetDate") or p.get("target_date"),
        "url": p.get("url"),
        "summary": ((p.get("summary") or "")[:280] or None),
    }


def normalize_issue(i):
    assignee = i.get("assignee")
    return {
        "id": i.get("id"),
        "title": i.get("title"),
        "status": i.get("status"),
        "status_type": i.get("statusType") or i.get("status_type"),
        "assignee": (assignee.get("name") if isinstance(assignee, dict) else assignee),
        "due_date": i.get("dueDate") or i.get("due_date"),
        "project_id": i.get("projectId") or i.get("project_id"),
        "updated_at": i.get("updatedAt") or i.get("updated_at"),
        "url": i.get("url"),
    }


# ---------- delta-fetch cache reconstruction ----------
#
# The skill no longer re-pulls every Marketing project/issue from Linear on every run —
# it fetches only what changed since the last pulse (`updatedAt` >= last_synced_at) and
# reconstructs the full universe by denormalizing cached pm_projects/pm_issues rows for
# everything NOT in that delta. This still needs to happen every run because health and
# missed-deadline detection are date-driven (pace vs. today, original_due_date vs. today)
# and can flip with zero Linear activity — compute_pulse must see every active project's
# full issue set regardless of whether any of it changed today.

def denormalize_project(row):
    """Reconstruct a normalize_project()-shaped dict from a cached pm_projects row, for a
    project the delta fetch didn't return (i.e. unchanged since the last pulse)."""
    return {
        "id": row["id"],
        "name": row["name"],
        "status_type": row.get("status_type"),
        "lead_name": row.get("lead_name"),
        "member_names": [],
        "start_date": row.get("start_date"),
        "target_date": row.get("current_target_date"),
        "url": row.get("linear_link"),
        "summary": row.get("short_description"),
    }


def denormalize_issue(row):
    """Reconstruct a normalize_issue()-shaped dict from a cached pm_issues row, for an
    issue the delta fetch didn't return (i.e. unchanged since the last pulse)."""
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row.get("status"),
        "status_type": row.get("status_type"),
        "assignee": row.get("owner"),
        "due_date": row.get("due_date"),
        "project_id": row.get("project_id"),
        "updated_at": row.get("last_activity_at"),
        "url": row.get("linear_link"),
    }


def merge_projects(delta_projects, prior_projects):
    """Full normalized project universe = delta (fresh from Linear) + cached rows not in
    the delta. `prior_projects` is {id: pm_projects row}, as fetched by db.py."""
    delta_ids = {p["id"] for p in delta_projects}
    cached = [denormalize_project(r) for pid, r in prior_projects.items() if pid not in delta_ids]
    return cached + delta_projects


def merge_issues(delta_issues, prior_issues):
    """Full normalized issue universe = delta (fresh from Linear) + cached rows not in
    the delta. `prior_issues` is {id: pm_issues row}, as fetched by db.py."""
    delta_ids = {i["id"] for i in delta_issues}
    cached = [denormalize_issue(r) for iid, r in prior_issues.items() if iid not in delta_ids]
    return cached + delta_issues


# ---------- blocker-fetch windowing (bounds get_issue volume on a large backlog) ----------

_OPEN_STATUS_TYPES = ("backlog", "unstarted", "started")
BLOCKER_FETCH_WINDOW_DAYS = 90


def issues_to_fetch_blockers(issues, *, now, window_days=BLOCKER_FETCH_WINDOW_DAYS):
    """The open issues the skill should call get_issue(includeRelations) on for blockedBy
    relations — limited to those whose last activity is within `window_days` of `now`, to bound
    API call volume on a large backlog. Open = status_type in backlog/unstarted/started; closed
    issues are skipped; an open issue with no updated_at is included (unknown recency is not
    silently dropped). Operates on normalize_issue() output. Returns the issue dicts in order."""
    out = []
    for i in issues:
        if i.get("status_type") not in _OPEN_STATUS_TYPES:
            continue
        u = i.get("updated_at")
        if u is None or health.days_between(u, now) <= window_days:
            out.append(i)
    return out


# ---------- scoped working set (bounded fetch + freeze stale) + brake ----------
#
# The pulse no longer reconstructs the entire Marketing universe (thousands of
# terminal issues, dormant "zombie" projects) into compute_pulse every run — 85% of
# it is finished work that can never change health. Instead the skill fetches ONLY
# the active window from Linear (`list_*(updatedAt=-P{window}D)`) plus the explicit
# open-commitment refs, and this section assembles the compute universe from that:
#
#   compute universe = active-window delta  ∪  open-commitment-ref cache rows
#
# Everything else in the cache — terminal, OR non-terminal but stale beyond the
# window (a hygiene/backlog problem, not live work) — is FROZEN: not recomputed, not
# re-upserted. It stays in the DB as the historical record and is COUNTED into the
# hygiene tally for candid Thursday-agenda reporting rather than silently re-swept.
#
# `merge_projects`/`merge_issues` above remain the full-universe primitives (still
# golden-tested); `select_working_set` is the scoped entry the live skill uses.

# Terminal for SCOPE purposes includes `duplicate` (never reopens); note this is a
# superset of health's `_CLOSED`, which intentionally excludes duplicate from the
# closed-date / missed-deadline logic.
_TERMINAL_SCOPE = ("completed", "canceled", "duplicate")


def select_working_set(delta_projects, delta_issues, prior_projects, prior_issues, *,
                        commitment_project_ids=(), commitment_issue_ids=()):
    """Assemble the scoped compute universe + hygiene tally. Pure; no I/O.

    `delta_projects`/`delta_issues` are the normalized active-window fetch (Steps 2-3) —
    the window (activity recency) is already applied by that fetch, so anything
    non-terminal that is NOT in the delta is, by definition, stale beyond the window.
    `prior_projects`/`prior_issues` are the full cached mirror ({id: row}, cheap).
    `commitment_*_ids` force live-commitment referents into scope even if they fell
    outside the activity window (belt-and-suspenders: "is what we committed to still
    open?"). Returns projects/issues to feed compute_pulse, scope_counts (for the
    brake), and hygiene counts (frozen non-terminal-stale items).
    """
    cprojects, cissues = set(commitment_project_ids), set(commitment_issue_ids)
    delta_pids = {p["id"] for p in delta_projects}
    delta_iids = {i["id"] for i in delta_issues}
    in_scope_pids = delta_pids | cprojects

    # Commitment project referents not already in the delta -> reconstruct from cache.
    extra_projects = [denormalize_project(prior_projects[pid]) for pid in cprojects
                      if pid not in delta_pids and pid in prior_projects]
    projects = delta_projects + extra_projects

    # Issues in scope = active-window delta + commitment issue refs + the FULL cached child
    # set of every in-scope project. That last set is LOAD-BEARING: project health uses
    # percent_complete = done_children / non_canceled_children, so an in-scope project's
    # health is only correct when compute_pulse sees ALL its children — including completed
    # ones last touched beyond the window, which the activity-filtered delta omits. Feeding
    # only the in-window children collapses percent_complete and falsely degrades health.
    # This restores the guarantee the full-universe merge_issues used to provide, scoped to
    # in-scope projects; children of out-of-scope zombie/terminal projects stay frozen.
    extra_issues = [denormalize_issue(prior_issues[iid]) for iid in cissues
                    if iid not in delta_iids and iid in prior_issues]
    in_scope_children = [denormalize_issue(r) for iid, r in prior_issues.items()
                         if iid not in delta_iids and iid not in cissues
                         and r.get("project_id") in in_scope_pids]
    issues = delta_issues + extra_issues + in_scope_children

    compute_pids = {p["id"] for p in projects}
    compute_iids = {i["id"] for i in issues}

    child_counts = {}
    for r in prior_issues.values():
        pid = r.get("project_id")
        if pid is not None:
            child_counts[pid] = child_counts.get(pid, 0) + 1

    # Hygiene = non-terminal cache rows FROZEN out of the compute set (never re-fetched or
    # recomputed) — a backlog/hygiene signal, not live work. Membership is judged against
    # the FINAL compute set so an in-scope project's pulled-in children are not miscounted.
    zombie_project_ids, empty_zombie_ids = [], []
    for pid, r in prior_projects.items():
        if pid in compute_pids or r.get("status_type") in _TERMINAL_SCOPE:
            continue
        zombie_project_ids.append(pid)
        if child_counts.get(pid, 0) == 0:
            empty_zombie_ids.append(pid)

    stale_open_issue_ids = [
        iid for iid, r in prior_issues.items()
        if iid not in compute_iids and r.get("status_type") not in _TERMINAL_SCOPE
    ]

    active_open_issues = sum(1 for i in delta_issues if i.get("status_type") in _OPEN_STATUS_TYPES)
    active_projects = sum(1 for p in delta_projects if p.get("status_type") not in _TERMINAL_SCOPE)

    return {
        "projects": projects,
        "issues": issues,
        "scope_counts": {
            "compute_projects": len(projects),
            "compute_issues": len(issues),
            "active_open_issues": active_open_issues,
            "active_projects": active_projects,
            "commitment_projects": len(cprojects),
            "commitment_issues": len(cissues),
        },
        "hygiene": {
            "zombie_projects": len(zombie_project_ids),
            "empty_zombie_projects": len(empty_zombie_ids),
            "stale_open_issues": len(stale_open_issue_ids),
            "zombie_project_ids": zombie_project_ids,
            "empty_zombie_project_ids": empty_zombie_ids,
        },
    }


def check_brake(scope_counts, config, *, relation_fetch_count=None):
    """Emergency brake. Trips when the active scope blows past configured ceilings —
    a signal the pulse is about to do far more work than reality warrants (mass
    re-open, a filter regression, a genuine explosion). Pure; the SKILL decides what
    to do on a trip (headless -> auto-narrow via select_safe_floor + loud flag;
    interactive -> stop and ask). Pre-flight call passes scope_counts only; the runtime
    backstop passes relation_fetch_count before the get_issue relation loop."""
    p = config.pulse
    reasons = []
    if scope_counts.get("active_open_issues", 0) > p.brake_max_issues:
        reasons.append(f"active_open_issues={scope_counts.get('active_open_issues', 0)} > brake_max_issues={p.brake_max_issues}")
    if scope_counts.get("active_projects", 0) > p.brake_max_projects:
        reasons.append(f"active_projects={scope_counts.get('active_projects', 0)} > brake_max_projects={p.brake_max_projects}")
    if relation_fetch_count is not None and relation_fetch_count > p.brake_max_relation_fetches:
        reasons.append(f"relation_fetches={relation_fetch_count} > brake_max_relation_fetches={p.brake_max_relation_fetches}")
    return {"tripped": bool(reasons), "reasons": reasons}


def select_safe_floor(issues, *, now, config, commitment_issue_ids=(), blocked_ids=()):
    """The reduced issue set to keep when the brake trips on a headless run: in-progress
    work, anything due within `due_soon_days` (or overdue), currently-blocked issues, and
    live-commitment referents. Terminal issues are dropped. Operates on normalize_issue()
    output. Deterministic; order preserved."""
    c, b = set(commitment_issue_ids), set(blocked_ids)
    due_soon = config.pulse.due_soon_days
    out = []
    for i in issues:
        if i.get("status_type") in _TERMINAL_SCOPE:
            continue
        keep = i.get("status_type") == "started" or i["id"] in c or i["id"] in b
        if not keep and i.get("due_date"):
            keep = health.days_between(now, i["due_date"]) <= due_soon
        if keep:
            out.append(i)
    return out


# ---------- owner mapping (external lead -> default internal owner) ----------

def map_owner(lead_name, project_member_names, config, *, declared_external=False):
    roster = {m.name for m in config.members}
    if lead_name and lead_name in roster:
        return {"owner": lead_name, "owner_source": "lead"}
    if lead_name:  # external lead
        if declared_external:
            return {"owner": lead_name, "owner_source": "external_declared"}
        return {"owner": config.default_external_owner, "owner_source": "external_default"}
    roster_in_project = [n for n in (project_member_names or []) if n in roster]
    if len(roster_in_project) == 1:
        return {"owner": roster_in_project[0], "owner_source": "member"}
    return {"owner": "Unassigned", "owner_source": "unassigned"}


# ---------- no-reschedule date capture ----------

def original_date_capture(prior_row, live_target):
    if prior_row is None:
        return {"original_due_date": live_target, "current_target_date": live_target}
    return {"original_due_date": prior_row.get("original_due_date"), "current_target_date": live_target}


# ---------- health reconciliation (owner wins; no-reschedule overrides) ----------

def reconcile_health(status_health_enum, suggested_health, project, now):
    n = _to_date(now)
    original = _to_date(project.get("original_due_date"))
    if project.get("status_type") not in _CLOSED and original is not None and n > original:
        return {"health": "off_track", "health_source": "agent_suggested"}
    mapped = _LINEAR_HEALTH.get(status_health_enum)
    if mapped:
        return {"health": mapped, "health_source": "owner"}
    return {"health": suggested_health, "health_source": "agent_suggested"}


# ---------- row builders ----------

def build_project_row(project, issues, prior_row, *, status_health_enum, oldest_blocker_biz_days,
                      config, now, created_at, declared_external=False):
    dates = original_date_capture(prior_row, project.get("target_date"))
    proj = {**project, **dates}
    suggested = health.suggest_project_health(
        proj, issues, now=now,
        oldest_open_blocker_business_days=oldest_blocker_biz_days, thresholds=config.pulse)
    hres = reconcile_health(status_health_enum, suggested["health"], proj, now)
    owner = map_owner(project.get("lead_name"), project.get("member_names"), config, declared_external=declared_external)
    closed = project.get("status_type") in _CLOSED
    return {
        "row": {
            "id": project["id"],
            "name": project["name"],
            "owner": owner["owner"],
            "owner_source": owner["owner_source"],
            "original_due_date": dates["original_due_date"],
            "current_target_date": dates["current_target_date"],
            "health": hres["health"],
            "health_source": hres["health_source"],
            "linear_link": project.get("url"),
            "short_description": project.get("summary"),
            "status_type": project.get("status_type"),
            "start_date": project.get("start_date"),
            "lead_name": project.get("lead_name"),
            "closed_at": (prior_row.get("closed_at") if prior_row else None) or (created_at if closed else None),
            "last_synced_at": created_at,
            "created_at": (prior_row.get("created_at") if prior_row else created_at),
        },
        "suggested": suggested,
        "owner_declared": _LINEAR_HEALTH.get(status_health_enum),
    }


def build_issue_row(issue, prior_row, *, blocked_ids, config, now, created_at):
    closed = issue.get("status_type") in _CLOSED
    return {
        "id": issue["id"],
        "project_id": issue.get("project_id"),
        "title": issue["title"],
        "owner": issue.get("assignee"),
        "status": issue.get("status"),
        "status_type": issue.get("status_type"),
        "state": health.issue_state(issue, now=now, blocked_ids=blocked_ids, thresholds=config.pulse),
        "due_date": issue.get("due_date"),
        "linear_link": issue.get("url"),
        "last_activity_at": issue.get("updated_at"),
        "closed_at": (prior_row.get("closed_at") if prior_row else None) or (created_at if closed else None),
        "last_synced_at": created_at,
        "created_at": (prior_row.get("created_at") if prior_row else created_at),
    }


# ---------- blockers from Linear relations ----------

def open_blockers_from_relations(issue_blockers, prior_blockers, *, created_at):
    """issue_blockers: {issue_id: [blocker target ids]} for currently-blocked issues.
    prior_blockers: list of OPEN pm_blockers rows (resolved_at IS NULL) keyed by issue_id.
    Returns {'opens': [new rows to insert], 'resolves': [{id, resolved_at} to update]}."""
    prior_by_issue = {b["issue_id"]: b for b in prior_blockers if b.get("issue_id")}
    opens = [
        {"issue_id": iid, "opened_at": created_at,
         "description": "blockedBy: " + ", ".join(targets), "created_at": created_at}
        for iid, targets in issue_blockers.items() if iid not in prior_by_issue
    ]
    resolves = [
        {"id": row["id"], "resolved_at": created_at}
        for iid, row in prior_by_issue.items() if iid not in issue_blockers
    ]
    return {"opens": opens, "resolves": resolves}


# ---------- C2: missed deadlines ----------

def detect_missed_deadlines(project_rows, prior_missed_ids, *, now, created_at):
    n = _to_date(now)
    return [
        {"project_id": r["id"], "original_due_date": r["original_due_date"],
         "detected_at": created_at, "prompted_at": None, "acknowledged_at": None,
         "explanation": None, "linear_comment_link": None, "surfaced_in_thursday": 0,
         "created_at": created_at}
        for r in project_rows
        if (r.get("closed_at") is None and r.get("original_due_date")
            and n > _to_date(r["original_due_date"]) and r["id"] not in prior_missed_ids)
    ]


# ---------- state-change DM events (gated off under state_only) ----------

def detect_state_changes(project_rows, prior_projects, issue_rows, prior_issues, accountability_mode):
    if accountability_mode == "state_only":
        return []
    events = []
    for r in project_rows:
        prior = prior_projects.get(r["id"])
        if prior and (prior.get("health"), r["health"]) in _DECLINE:
            events.append({"kind": "project_health_decline", "id": r["id"], "owner": r["owner"],
                           "from": prior.get("health"), "to": r["health"]})
    for r in issue_rows:
        if r.get("project_id") is not None:
            continue
        prior = prior_issues.get(r["id"])
        if prior and prior.get("state") == "active" and r["state"] in ("stale", "blocked"):
            events.append({"kind": "orphan_degraded", "id": r["id"], "owner": r.get("owner"),
                           "from": prior.get("state"), "to": r["state"]})
    return events


# ---------- entry point ----------

def compute_pulse(*, projects, issues, issue_blockers, status_health,
                  prior_projects, prior_issues, prior_blockers, prior_missed_ids,
                  config, now, created_at):
    blocked_ids = set(issue_blockers.keys())
    issues_by_project = {}
    for i in issues:
        issues_by_project.setdefault(i.get("project_id"), []).append(i)

    # oldest open blocker (business days) per project, from blockers we've already been tracking
    prior_open_by_issue = {b["issue_id"]: b for b in prior_blockers if b.get("issue_id")}
    issue_to_project = {i["id"]: i.get("project_id") for i in issues}
    blocker_age_by_project = {}
    for iid in issue_blockers:
        pid = issue_to_project.get(iid)
        prior = prior_open_by_issue.get(iid)
        age = health.business_days_between(prior["opened_at"], now) if prior and prior.get("opened_at") else 0
        if pid is not None:
            blocker_age_by_project[pid] = max(blocker_age_by_project.get(pid, 0), age)

    project_rows, suggestions = [], []
    for p in projects:
        built = build_project_row(
            p, issues_by_project.get(p["id"], []), prior_projects.get(p["id"]),
            status_health_enum=status_health.get(p["id"]),
            oldest_blocker_biz_days=blocker_age_by_project.get(p["id"], 0),
            config=config, now=now, created_at=created_at)
        project_rows.append(built["row"])
        suggestions.append({"id": p["id"], "name": p["name"], "stored": built["row"]["health"],
                            "agent_suggested": built["suggested"]["health"],
                            "owner_declared": built["owner_declared"],
                            "reasons": built["suggested"]["reasons"]})

    issue_rows = [build_issue_row(i, prior_issues.get(i["id"]), blocked_ids=blocked_ids,
                                  config=config, now=now, created_at=created_at) for i in issues]
    blockers = open_blockers_from_relations(issue_blockers, prior_blockers, created_at=created_at)
    missed = detect_missed_deadlines(project_rows, prior_missed_ids, now=now, created_at=created_at)
    dm_events = detect_state_changes(project_rows, prior_projects, issue_rows, prior_issues, config.accountability_mode)
    orphans = [r["id"] for r in issue_rows if r.get("project_id") is None and r["state"] != "closed"]
    discrepancies = [s for s in suggestions if s["owner_declared"] and s["owner_declared"] != s["agent_suggested"]]

    return {
        "project_rows": project_rows,
        "issue_rows": issue_rows,
        "blocker_opens": blockers["opens"],
        "blocker_resolves": blockers["resolves"],
        "missed": missed,
        "dm_events": dm_events,
        "orphans": orphans,
        "summary": {
            "projects": len(project_rows), "issues": len(issue_rows), "orphans": len(orphans),
            "blocker_opens": len(blockers["opens"]), "blocker_resolves": len(blockers["resolves"]),
            "missed": len(missed), "dm_events": len(dm_events),
            "health_discrepancies": discrepancies, "suggestions": suggestions,
        },
    }
