"""Tests for scripts/pm/pulse.py — the linear-pulse-check compute core."""
import sqlite3

import pytest

from scripts.pm import db
from scripts.pm.config import REPO_ROOT, _build_config
from scripts.pm.pulse import (
    build_project_row,
    check_brake,
    compute_pulse,
    denormalize_issue,
    denormalize_project,
    detect_missed_deadlines,
    detect_state_changes,
    issues_to_fetch_blockers,
    map_owner,
    merge_issues,
    merge_projects,
    open_blockers_from_relations,
    original_date_capture,
    reconcile_health,
    select_safe_floor,
    select_working_set,
)

MIGR = REPO_ROOT / "state" / "working" / "migrations"


def test_issues_to_fetch_blockers_windows_open_recent():
    """Only open issues active within the window get a blocker fetch — bounds get_issue volume."""
    now = "2026-06-11"
    issues = [
        {"id": "recent-open", "status_type": "started", "updated_at": "2026-06-01"},      # 10d -> in
        {"id": "old-open", "status_type": "backlog", "updated_at": "2026-01-01"},          # ~161d -> out
        {"id": "edge-90", "status_type": "unstarted", "updated_at": "2026-03-13"},         # exactly 90d -> in
        {"id": "closed-recent", "status_type": "completed", "updated_at": "2026-06-10"},   # closed -> out
        {"id": "open-no-date", "status_type": "started", "updated_at": None},              # unknown -> in
    ]
    ids = [i["id"] for i in issues_to_fetch_blockers(issues, now=now)]
    assert ids == ["recent-open", "edge-90", "open-no-date"]
    # a tighter window drops the 90-day-edge issue
    ids30 = [i["id"] for i in issues_to_fetch_blockers(issues, now=now, window_days=30)]
    assert ids30 == ["recent-open", "open-no-date"]


# ---- delta-fetch cache reconstruction ----

def test_denormalize_project_reconstructs_normalized_shape():
    row = {"id": "p1", "name": "X", "status_type": "started", "lead_name": "Priya Natarajan",
           "start_date": "2026-04-01", "current_target_date": "2026-05-30",
           "linear_link": "https://linear.app/orrery/project/x", "short_description": "s"}
    assert denormalize_project(row) == {
        "id": "p1", "name": "X", "status_type": "started", "lead_name": "Priya Natarajan",
        "member_names": [], "start_date": "2026-04-01", "target_date": "2026-05-30",
        "url": "https://linear.app/orrery/project/x", "summary": "s",
    }


def test_denormalize_issue_reconstructs_normalized_shape():
    row = {"id": "i1", "title": "T", "status": "In Progress", "status_type": "started",
           "owner": "Priya Natarajan", "due_date": None, "project_id": "p2",
           "last_activity_at": "2026-06-09", "linear_link": "u/i1"}
    assert denormalize_issue(row) == {
        "id": "i1", "title": "T", "status": "In Progress", "status_type": "started",
        "assignee": "Priya Natarajan", "due_date": None, "project_id": "p2",
        "updated_at": "2026-06-09", "url": "u/i1",
    }


def test_merge_projects_prefers_delta_over_cache():
    prior = {"p1": {"id": "p1", "name": "stale name", "status_type": "started",
                    "lead_name": "Priya Natarajan", "start_date": "2026-04-01",
                    "current_target_date": "2026-05-30", "linear_link": "u/p1", "short_description": None},
             "p2": {"id": "p2", "name": "untouched", "status_type": "started", "lead_name": None,
                    "start_date": "2026-06-08", "current_target_date": "2026-09-01",
                    "linear_link": "u/p2", "short_description": None}}
    delta = [{"id": "p1", "name": "fresh name", "status_type": "started", "lead_name": "Priya Natarajan",
              "member_names": [], "start_date": "2026-04-01", "target_date": "2026-05-30",
              "url": "u/p1", "summary": None}]
    merged = {p["id"]: p for p in merge_projects(delta, prior)}
    assert merged["p1"]["name"] == "fresh name"   # delta wins over cache
    assert merged["p2"]["name"] == "untouched"    # unchanged project reconstructed from cache
    assert len(merged) == 2


def test_merge_issues_prefers_delta_over_cache():
    prior = {"i1": {"id": "i1", "title": "stale", "status": "Todo", "status_type": "unstarted",
                    "owner": None, "due_date": None, "project_id": None,
                    "last_activity_at": "2026-06-01", "linear_link": "u/i1"}}
    delta = [{"id": "i1", "title": "fresh", "status": "Done", "status_type": "completed",
              "assignee": None, "due_date": None, "project_id": None,
              "updated_at": "2026-06-09", "url": "u/i1"}]
    merged = {i["id"]: i for i in merge_issues(delta, prior)}
    assert merged["i1"]["title"] == "fresh" and merged["i1"]["status_type"] == "completed"


def test_merge_projects_recomputes_health_for_untouched_project_via_compute_pulse():
    """The whole point of merging cache + delta: an untouched project's health must still
    flip when today crosses its original_due_date, even with an empty delta."""
    prior_row = {"id": "p1", "name": "X", "status_type": "started", "lead_name": "Priya Natarajan",
                 "start_date": "2026-04-01", "current_target_date": "2026-05-30",
                 "linear_link": "u/p1", "short_description": None,
                 "original_due_date": "2026-05-30", "closed_at": None, "created_at": CREATED}
    merged_projects = merge_projects([], {"p1": prior_row})
    out = compute_pulse(
        projects=merged_projects, issues=[], issue_blockers={}, status_health={},
        prior_projects={"p1": prior_row}, prior_issues={}, prior_blockers=[], prior_missed_ids=set(),
        config=CONFIG, now="2026-06-09", created_at=CREATED,
    )
    row = out["project_rows"][0]
    assert row["health"] == "off_track"  # past original_due_date, purely from today's date


CONFIG = _build_config(
    {
        "team": {"monday_post_pt": "05:00", "monday_response_deadline_pt": "23:59",
                 "weekday_pulse_pt": "08:00", "thursday_agenda_pt": "06:30"},
        "accountability_mode": "state_only",
        "team_channel_id": "C0DEMO0001",
        "default_external_owner": "Maya Lindqvist",
        "members": [
            {"name": "Scott McKeighen", "slack_user_id": "U0DEMO0001", "slack_alias": "Scott McKeighen",
             "timezone": "America/Los_Angeles", "standup_tag_local": "08:00"},
            {"name": "Maya Lindqvist", "slack_user_id": "U0DEMO0002", "slack_alias": "Maya Lindqvist",
             "timezone": "America/Los_Angeles", "standup_tag_local": "08:00"},
            {"name": "Priya Natarajan", "slack_user_id": "U0DEMO0003", "slack_alias": "Priya Natarajan",
             "timezone": "America/Denver", "standup_tag_local": "10:00"},
            {"name": "Tomas Reyes", "slack_user_id": "U0DEMO0004", "slack_alias": "tomas",
             "timezone": "Europe/Athens", "standup_tag_local": "09:00"},
        ],
    }
)

NOW = "2026-06-09"
CREATED = "2026-06-09T08:00:00Z"


# ---- owner mapping ----

def test_map_owner_roster_lead():
    assert map_owner("Priya Natarajan", [], CONFIG) == {"owner": "Priya Natarajan", "owner_source": "lead"}


def test_map_owner_external_default_is_mark():
    out = map_owner("contact3@example.com", ["Priya Natarajan"], CONFIG)
    assert out == {"owner": "Maya Lindqvist", "owner_source": "external_default"}


def test_map_owner_external_declared():
    out = map_owner("contact3@example.com", [], CONFIG, declared_external=True)
    assert out["owner_source"] == "external_declared"


def test_map_owner_sole_member():
    assert map_owner(None, ["Tomas Reyes"], CONFIG) == {"owner": "Tomas Reyes", "owner_source": "member"}


def test_map_owner_unassigned():
    assert map_owner(None, ["Priya Natarajan", "Maya Lindqvist"], CONFIG)["owner_source"] == "unassigned"


# ---- original-date capture ----

def test_original_date_first_sight_and_immutable():
    first = original_date_capture(None, "2026-05-30")
    assert first == {"original_due_date": "2026-05-30", "current_target_date": "2026-05-30"}
    later = original_date_capture({"original_due_date": "2026-05-30"}, "2026-07-15")
    assert later == {"original_due_date": "2026-05-30", "current_target_date": "2026-07-15"}  # original frozen


def test_original_date_first_sight_null_stays_null():
    assert original_date_capture(None, None)["original_due_date"] is None
    later = original_date_capture({"original_due_date": None}, "2026-07-15")
    assert later["original_due_date"] is None and later["current_target_date"] == "2026-07-15"


# ---- health reconciliation ----

def test_reconcile_owner_wins():
    proj = {"status_type": "started", "original_due_date": "2026-08-01"}
    assert reconcile_health("atRisk", "on_track", proj, NOW) == {"health": "at_risk", "health_source": "owner"}


def test_reconcile_no_reschedule_beats_owner_ontrack():
    proj = {"status_type": "started", "original_due_date": "2026-05-30"}  # past
    assert reconcile_health("onTrack", "on_track", proj, NOW) == {"health": "off_track", "health_source": "agent_suggested"}


def test_reconcile_agent_fills_gap():
    proj = {"status_type": "started", "original_due_date": "2026-08-01"}
    assert reconcile_health(None, "at_risk", proj, NOW) == {"health": "at_risk", "health_source": "agent_suggested"}


# ---- blockers ----

def test_open_blockers_new_and_resolved():
    out = open_blockers_from_relations(
        {"i1": ["i9"]},
        [{"id": 7, "issue_id": "i2"}],  # i2 was blocked, no longer is
        created_at=CREATED,
    )
    assert len(out["opens"]) == 1 and out["opens"][0]["issue_id"] == "i1"
    assert out["resolves"] == [{"id": 7, "resolved_at": CREATED}]


def test_open_blockers_persistent_no_dup():
    out = open_blockers_from_relations({"i1": ["i9"]}, [{"id": 7, "issue_id": "i1"}], created_at=CREATED)
    assert out["opens"] == [] and out["resolves"] == []


# ---- missed deadlines ----

def test_detect_missed_one_row_ever():
    rows = [{"id": "p1", "closed_at": None, "original_due_date": "2026-05-30"}]
    assert len(detect_missed_deadlines(rows, set(), now=NOW, created_at=CREATED)) == 1
    assert detect_missed_deadlines(rows, {"p1"}, now=NOW, created_at=CREATED) == []     # already recorded
    closed = [{"id": "p2", "closed_at": CREATED, "original_due_date": "2026-05-30"}]
    assert detect_missed_deadlines(closed, set(), now=NOW, created_at=CREATED) == []     # closed


# ---- state changes ----

def test_state_changes_suppressed_when_state_only():
    proj = [{"id": "p1", "health": "off_track", "owner": "x"}]
    prior = {"p1": {"health": "on_track"}}
    assert detect_state_changes(proj, prior, [], {}, "state_only") == []


def test_state_changes_decline_emits_when_hybrid():
    proj = [{"id": "p1", "health": "at_risk", "owner": "x"}]
    prior = {"p1": {"health": "on_track"}}
    events = detect_state_changes(proj, prior, [], {}, "hybrid")
    assert events and events[0]["kind"] == "project_health_decline"


# ---- full compute_pulse ----

PROJECTS = [
    {"id": "p1", "name": "Repositioning: Content Marketing", "status_type": "started",
     "lead_name": "contact3@example.com", "member_names": ["Scott McKeighen"],
     "start_date": "2026-04-21", "target_date": "2026-05-30", "url": "https://linear.app/orrery/project/cm", "summary": "x"},
    {"id": "p2", "name": "Use Cases Database", "status_type": "started",
     "lead_name": "Priya Natarajan", "member_names": ["Priya Natarajan"],
     "start_date": "2026-06-08", "target_date": "2026-09-01", "url": "https://linear.app/orrery/project/ucd", "summary": "y"},
]
ISSUES = [
    {"id": "i1", "title": "Orphan task", "status": "Todo", "status_type": "unstarted",
     "assignee": "Scott McKeighen", "due_date": None, "project_id": None, "updated_at": "2026-06-07", "url": "u/i1"},
    {"id": "i2", "title": "done one", "status": "Done", "status_type": "completed",
     "assignee": "Priya Natarajan", "due_date": None, "project_id": "p2", "updated_at": "2026-06-08", "url": "u/i2"},
    {"id": "i3", "title": "active one", "status": "In Progress", "status_type": "started",
     "assignee": "Priya Natarajan", "due_date": None, "project_id": "p2", "updated_at": "2026-06-09", "url": "u/i3"},
]


def test_compute_pulse_end_to_end():
    out = compute_pulse(
        projects=PROJECTS, issues=ISSUES, issue_blockers={"i1": ["i9"]},
        status_health={"p1": "onTrack", "p2": "atRisk"},
        prior_projects={}, prior_issues={}, prior_blockers=[], prior_missed_ids=set(),
        config=CONFIG, now=NOW, created_at=CREATED,
    )
    proj = {r["id"]: r for r in out["project_rows"]}
    # p1: external lead -> Maya; past original -> off_track override (beats owner onTrack)
    assert proj["p1"]["owner"] == "Maya Lindqvist" and proj["p1"]["owner_source"] == "external_default"
    assert proj["p1"]["health"] == "off_track" and proj["p1"]["health_source"] == "agent_suggested"
    assert proj["p1"]["original_due_date"] == "2026-05-30"
    # p2: roster lead, owner-declared atRisk wins
    assert proj["p2"]["owner"] == "Priya Natarajan" and proj["p2"]["owner_source"] == "lead"
    assert proj["p2"]["health"] == "at_risk" and proj["p2"]["health_source"] == "owner"
    # issue states
    issues = {r["id"]: r for r in out["issue_rows"]}
    assert issues["i1"]["state"] == "blocked" and issues["i1"]["project_id"] is None
    assert issues["i2"]["state"] == "closed"
    assert issues["i3"]["state"] == "active"
    # detections
    assert out["orphans"] == ["i1"]
    assert len(out["missed"]) == 1 and out["missed"][0]["project_id"] == "p1"
    assert len(out["blocker_opens"]) == 1
    assert out["dm_events"] == []  # state_only
    # owner-vs-agent discrepancy surfaced for p2 (owner atRisk vs agent on_track)
    assert any(d["id"] == "p2" for d in out["summary"]["health_discrepancies"])


# ---- scoped working set + emergency brake ----

def test_select_working_set_freezes_stale_and_forces_commitments():
    """Compute universe = active-window delta ∪ open-commitment refs; terminal and
    non-terminal-stale (zombie) cache rows are frozen out and counted as hygiene."""
    delta_projects = [
        {"id": "pA", "name": "active", "status_type": "started", "lead_name": "Priya Natarajan",
         "member_names": [], "start_date": None, "target_date": None, "url": "u/pA", "summary": None},
    ]
    delta_issues = [
        {"id": "iA", "title": "active", "status": "In Progress", "status_type": "started",
         "assignee": "Priya Natarajan", "due_date": None, "project_id": "pA", "updated_at": "2026-07-17", "url": "u/iA"},
    ]
    prior_projects = {
        "pA": {"id": "pA", "name": "stale-cache", "status_type": "started", "lead_name": "Priya Natarajan",
               "start_date": None, "current_target_date": None, "linear_link": "u/pA", "short_description": None},
        "pZombie": {"id": "pZombie", "name": "zombie", "status_type": "backlog", "lead_name": None,
                    "start_date": None, "current_target_date": None, "linear_link": "u/pz", "short_description": None},
        "pEmpty": {"id": "pEmpty", "name": "empty-shell", "status_type": "backlog", "lead_name": None,
                   "start_date": None, "current_target_date": None, "linear_link": "u/pe", "short_description": None},
        "pDone": {"id": "pDone", "name": "done", "status_type": "completed", "lead_name": None,
                  "start_date": None, "current_target_date": None, "linear_link": "u/pd", "short_description": None},
        "pCommit": {"id": "pCommit", "name": "committed-old", "status_type": "started", "lead_name": "Maya Lindqvist",
                    "start_date": None, "current_target_date": None, "linear_link": "u/pc", "short_description": None},
    }
    prior_issues = {
        "iA": {"id": "iA", "title": "old-cache", "status": "x", "status_type": "started", "owner": None,
               "due_date": None, "project_id": "pA", "last_activity_at": "2026-01-01", "linear_link": "u/iA"},
        "iZombie": {"id": "iZombie", "title": "zombie", "status": "x", "status_type": "unstarted", "owner": None,
                    "due_date": None, "project_id": "pZombie", "last_activity_at": "2025-06-01", "linear_link": "u/iz"},
        "iDone": {"id": "iDone", "title": "done", "status": "x", "status_type": "completed", "owner": None,
                  "due_date": None, "project_id": "pA", "last_activity_at": "2025-06-01", "linear_link": "u/id"},
        "iCommit": {"id": "iCommit", "title": "committed-old", "status": "x", "status_type": "backlog", "owner": None,
                    "due_date": None, "project_id": "pCommit", "last_activity_at": "2025-01-01", "linear_link": "u/ic"},
    }
    out = select_working_set(
        delta_projects, delta_issues, prior_projects, prior_issues,
        commitment_project_ids=["pCommit"], commitment_issue_ids=["iCommit"],
    )
    assert {p["id"] for p in out["projects"]} == {"pA", "pCommit"}
    # iDone (completed child of in-scope pA) is pulled back in for accurate percent_complete;
    # iZombie/pDone stay frozen. iCommit forced in by the commitment ref.
    assert {i["id"] for i in out["issues"]} == {"iA", "iCommit", "iDone"}
    # delta wins over cache for pA; commitment ref reconstructed from cache
    assert next(p for p in out["projects"] if p["id"] == "pA")["name"] == "active"
    assert next(p for p in out["projects"] if p["id"] == "pCommit")["name"] == "committed-old"
    # hygiene: pZombie + pEmpty are frozen non-terminal (pDone terminal, pCommit forced in)
    assert out["hygiene"]["zombie_projects"] == 2
    assert out["hygiene"]["empty_zombie_projects"] == 1        # pEmpty has no child issue
    assert out["hygiene"]["empty_zombie_project_ids"] == ["pEmpty"]   # identity, not just count
    assert out["hygiene"]["stale_open_issues"] == 1            # iZombie only
    assert out["scope_counts"]["active_open_issues"] == 1
    assert out["scope_counts"]["active_projects"] == 1
    assert out["scope_counts"]["commitment_projects"] == 1


def test_select_working_set_pulls_full_child_set_of_in_scope_project():
    """Regression (review HIGH): an active in-window project's completed children that fell
    outside the activity window must still feed compute_pulse's percent_complete/pace — else
    health falsely degrades from on_track to at_risk. Routes through compute_pulse to prove it."""
    proj = {"id": "pMature", "name": "Mature", "status_type": "started", "lead_name": "Priya Natarajan",
            "member_names": [], "start_date": "2026-01-01", "target_date": "2026-09-01",
            "url": "u/pM", "summary": None}
    delta_issues = [
        {"id": f"open{k}", "title": "o", "status": "In Progress", "status_type": "started",
         "assignee": "Priya Natarajan", "due_date": None, "project_id": "pMature",
         "updated_at": "2026-07-16", "url": f"u/o{k}"} for k in range(2)
    ]
    # 8 completed children last touched >90d ago -> absent from the activity-window delta
    prior_issues = {
        f"done{k}": {"id": f"done{k}", "title": "d", "status": "Done", "status_type": "completed",
                     "owner": "Priya Natarajan", "due_date": None, "project_id": "pMature",
                     "last_activity_at": "2026-01-15", "linear_link": f"u/d{k}"} for k in range(8)
    }
    ws = select_working_set([proj], delta_issues, {}, prior_issues)
    assert sum(1 for i in ws["issues"] if i["status_type"] == "completed") == 8   # all pulled back
    out = compute_pulse(
        projects=ws["projects"], issues=ws["issues"], issue_blockers={}, status_health={},
        prior_projects={}, prior_issues=prior_issues, prior_blockers=[], prior_missed_ids=set(),
        config=CONFIG, now="2026-07-17", created_at="2026-07-17T00:00:00Z",
    )
    row = {r["id"]: r for r in out["project_rows"]}["pMature"]
    assert row["health"] == "on_track"          # 8/10 done ~= 0.81 expected pace -> on track
    assert row["health_source"] == "agent_suggested"


def test_select_working_set_dedupes_commitment_ref_also_in_delta():
    """A commitment referent that is ALSO in the active-window delta must not duplicate; delta wins."""
    delta_projects = [{"id": "pA", "name": "fresh", "status_type": "started", "lead_name": "Priya Natarajan",
                       "member_names": [], "start_date": None, "target_date": None, "url": "u/pA", "summary": None}]
    delta_issues = [{"id": "iA", "title": "fresh", "status": "x", "status_type": "started", "assignee": None,
                     "due_date": None, "project_id": "pA", "updated_at": "2026-07-17", "url": "u/iA"}]
    prior_projects = {"pA": {"id": "pA", "name": "stale", "status_type": "started", "lead_name": "Priya Natarajan",
                             "start_date": None, "current_target_date": None, "linear_link": "u/pA", "short_description": None}}
    prior_issues = {"iA": {"id": "iA", "title": "stale", "status": "x", "status_type": "started", "owner": None,
                           "due_date": None, "project_id": "pA", "last_activity_at": "2026-07-17", "linear_link": "u/iA"}}
    out = select_working_set(delta_projects, delta_issues, prior_projects, prior_issues,
                             commitment_project_ids=["pA"], commitment_issue_ids=["iA"])
    assert [p["id"] for p in out["projects"]] == ["pA"]      # single row, no dup
    assert [i["id"] for i in out["issues"]] == ["iA"]        # single row, no dup
    assert out["projects"][0]["name"] == "fresh" and out["issues"][0]["title"] == "fresh"  # delta wins


def test_select_working_set_active_counts_exclude_terminal():
    """Terminal delta rows (recently-closed, so within the window) must not inflate the
    active_open_issues / active_projects brake counts, but still flow into the compute set."""
    delta_projects = [
        {"id": "pOpen", "name": "o", "status_type": "started", "lead_name": None, "member_names": [],
         "start_date": None, "target_date": None, "url": "u/po", "summary": None},
        {"id": "pDone", "name": "d", "status_type": "completed", "lead_name": None, "member_names": [],
         "start_date": None, "target_date": None, "url": "u/pd", "summary": None},
    ]
    delta_issues = [
        {"id": "iOpen", "title": "o", "status": "x", "status_type": "started", "assignee": None,
         "due_date": None, "project_id": "pOpen", "updated_at": "2026-07-17", "url": "u/io"},
        {"id": "iDone", "title": "d", "status": "x", "status_type": "completed", "assignee": None,
         "due_date": None, "project_id": "pOpen", "updated_at": "2026-07-16", "url": "u/id"},
        {"id": "iCanceled", "title": "c", "status": "x", "status_type": "canceled", "assignee": None,
         "due_date": None, "project_id": "pOpen", "updated_at": "2026-07-15", "url": "u/ic"},
    ]
    out = select_working_set(delta_projects, delta_issues, {}, {})
    assert out["scope_counts"]["active_open_issues"] == 1   # iOpen only
    assert out["scope_counts"]["active_projects"] == 1      # pOpen only
    assert {i["id"] for i in out["issues"]} == {"iOpen", "iDone", "iCanceled"}  # terminal still computed


def test_check_brake_ok_under_ceilings():
    assert check_brake({"active_open_issues": 188, "active_projects": 23}, CONFIG)["tripped"] is False


def test_check_brake_trips_over_issue_ceiling():
    res = check_brake({"active_open_issues": 500, "active_projects": 23}, CONFIG)
    assert res["tripped"] and any("active_open_issues" in r for r in res["reasons"])


def test_check_brake_trips_over_project_ceiling():
    res = check_brake({"active_open_issues": 10, "active_projects": 61}, CONFIG)
    assert res["tripped"] and any("active_projects" in r for r in res["reasons"])


def test_check_brake_relation_fetch_backstop():
    counts = {"active_open_issues": 10, "active_projects": 2}
    assert check_brake(counts, CONFIG, relation_fetch_count=301)["tripped"] is True
    assert check_brake(counts, CONFIG, relation_fetch_count=300)["tripped"] is False


def test_select_safe_floor_keeps_active_floor_only():
    now = "2026-07-17"
    issues = [
        {"id": "started", "status_type": "started", "due_date": None},
        {"id": "backlog-far", "status_type": "backlog", "due_date": "2026-12-01"},       # far -> drop
        {"id": "backlog-due-soon", "status_type": "unstarted", "due_date": "2026-07-20"},  # 3d -> keep
        {"id": "backlog-overdue", "status_type": "backlog", "due_date": "2026-07-01"},    # overdue -> keep
        {"id": "committed", "status_type": "backlog", "due_date": None},                  # commitment -> keep
        {"id": "blocked", "status_type": "backlog", "due_date": None},                    # blocked -> keep
        {"id": "done", "status_type": "completed", "due_date": None},                     # terminal -> drop
    ]
    kept = {i["id"] for i in select_safe_floor(
        issues, now=now, config=CONFIG, commitment_issue_ids=["committed"], blocked_ids=["blocked"])}
    assert kept == {"started", "backlog-due-soon", "backlog-overdue", "committed", "blocked"}


# ---- M1: the no-reschedule rule survives a real round-trip through db.upsert ----

@pytest.fixture
def pmdb(tmp_path):
    """Temp DB with migrations 003+004+005 applied (pm_projects has owner_source, etc.)."""
    path = tmp_path / "pm.db"
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    for m in ["003_pm_tables.sql", "004_pm_capture_provenance.sql", "005_pm_block_c.sql",
              "014_pm_pulse_delta_cache.sql"]:
        conn.executescript((MIGR / m).read_text())
    conn.commit()
    conn.close()
    c = db.connect(path)
    yield c
    c.close()


def test_pulse_upsert_preserves_immutable_dates(pmdb):
    """A second pulse must NOT clobber original_due_date or created_at via the upsert,
    and must flip health to off_track once the (immutable) original date has passed."""
    proj = {"id": "p1", "name": "X", "status_type": "started", "lead_name": "Priya Natarajan",
            "member_names": ["Priya Natarajan"], "start_date": "2026-04-01", "target_date": "2026-05-30",
            "url": "https://linear.app/orrery/project/x", "summary": "s"}

    # First sight (target not yet passed): original captured = 2026-05-30.
    r1 = build_project_row(proj, [], None, status_health_enum=None, oldest_blocker_biz_days=0,
                           config=CONFIG, now="2026-05-01", created_at="2026-05-01T00:00:00Z")["row"]
    db.upsert(pmdb, "pm_projects", r1, key_cols=["id"])
    pmdb.commit()

    # Second sight weeks later: target moved out to 2026-07-15; re-upsert with prior row read back.
    prior = db.fetchone(pmdb, "SELECT * FROM pm_projects WHERE id=?", ("p1",))
    proj2 = {**proj, "target_date": "2026-07-15"}
    r2 = build_project_row(proj2, [], prior, status_health_enum="onTrack", oldest_blocker_biz_days=0,
                           config=CONFIG, now="2026-06-09", created_at="2026-06-09T08:00:00Z")["row"]
    db.upsert(pmdb, "pm_projects", r2, key_cols=["id"])
    pmdb.commit()

    got = db.fetchone(pmdb, "SELECT * FROM pm_projects WHERE id=?", ("p1",))
    assert got["original_due_date"] == "2026-05-30"        # immutable — NOT moved to 07-15
    assert got["current_target_date"] == "2026-07-15"      # refreshed from live Linear
    assert got["created_at"] == "2026-05-01T00:00:00Z"     # preserved — re-upsert did not reset it
    assert got["last_synced_at"] == "2026-06-09T08:00:00Z" # refreshed
    assert got["health"] == "off_track"                    # past the original date (override beats owner onTrack)
    assert got["health_source"] == "agent_suggested"
