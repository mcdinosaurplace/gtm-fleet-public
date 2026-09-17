"""Tests for scripts/pm/commitments.py — week math + scale/horizon classification."""
from scripts.pm.commitments import (
    build_resolution_update,
    build_row,
    cache_is_fresh,
    classify,
    end_of_week,
    evaluate_completion,
    match_open_commitment,
    project_entity_from_cache,
    refresh_project_from_live,
)

MON = "2026-06-08"   # Monday; Sun->Sat week ends Sat 2026-06-13


def test_end_of_week_from_each_day():
    assert end_of_week("2026-06-08") == "2026-06-13"  # Monday
    assert end_of_week("2026-06-07") == "2026-06-13"  # Sunday (start of the week)
    assert end_of_week("2026-06-13") == "2026-06-13"  # Saturday (the day itself)
    assert end_of_week("2026-06-10") == "2026-06-13"  # Wednesday


def test_classify_project():
    c = classify("project", "2026-07-01", MON)
    assert c == {"scale": "project", "horizon": "multi_week", "effective_due_date": "2026-07-01"}


def test_classify_issue_future_vs_none():
    fut = classify("issue", "2026-07-01", MON)
    assert fut["scale"] == "task" and fut["horizon"] == "multi_week" and fut["effective_due_date"] == "2026-07-01"
    none = classify("issue", None, MON)
    assert none["horizon"] == "this_week" and none["effective_due_date"] == "2026-06-13"


def test_classify_incidental():
    c = classify(None, None, MON)
    assert c == {"scale": "incidental", "horizon": "this_week", "effective_due_date": "2026-06-13"}


def test_build_row_project():
    row = build_row(MON, "Scott McKeighen", "ship MOPS Inbox and New Requests", "by_name",
                    entity_type="project", entity_due_date="2026-07-01",
                    linear_link="https://linear.app/orrery/project/x", project_id="proj-mops",
                    created_at="2026-06-08T00:00:00Z")
    assert row["scale"] == "project"
    assert row["horizon"] == "multi_week"
    assert row["effective_due_date"] == "2026-07-01"
    assert row["linear_ref_type"] == "project"
    assert row["resolution"] == "by_name"
    assert row["completion_status"] == "pending"
    assert row["acknowledged_untracked"] == 0


def test_build_row_incidental_acknowledged():
    row = build_row(MON, "Priya Natarajan", "tweak a headline", "unresolved", acknowledged_untracked=True,
                    created_at="2026-06-08T00:00:00Z")
    assert row["scale"] == "incidental"
    assert row["acknowledged_untracked"] == 1
    assert row["linear_ref_type"] is None
    assert row["effective_due_date"] == "2026-06-13"


def test_build_resolution_update_project():
    u = build_resolution_update(MON, "confirmed", entity_type="project", entity_due_date="2026-07-01",
                                linear_link="https://linear.app/orrery/project/x", project_id="proj-mops")
    assert u["resolution"] == "confirmed"
    assert u["linear_ref_type"] == "project" and u["project_id"] == "proj-mops"
    assert u["scale"] == "project" and u["horizon"] == "multi_week"
    assert u["effective_due_date"] == "2026-07-01"
    assert u["acknowledged_untracked"] == 0
    assert "completion_status" not in u and "created_at" not in u  # update-only subset


def test_build_resolution_update_incidental():
    u = build_resolution_update(MON, "unresolved", acknowledged_untracked=True)
    assert u["scale"] == "incidental" and u["acknowledged_untracked"] == 1
    assert u["linear_ref_type"] is None and u["issue_id"] is None


def test_resolution_update_agrees_with_build_row():
    """The update subset must match build_row's classify for the same inputs (drift guard)."""
    row = build_row(MON, "S", "c", "by_name", entity_type="issue", entity_due_date="2026-07-01",
                    linear_link="u", issue_id="i1", created_at="t")
    upd = build_resolution_update(MON, "by_name", entity_type="issue", entity_due_date="2026-07-01",
                                  linear_link="u", issue_id="i1")
    for k in ("resolution", "linear_link", "linear_ref_type", "project_id", "issue_id",
              "scale", "horizon", "effective_due_date", "acknowledged_untracked"):
        assert row[k] == upd[k]


EVAL = "2026-06-20T08:00:00Z"
LATER = "2026-06-20"


def _commit(**kw):
    base = {"project_id": "p1", "issue_id": None, "horizon": "multi_week", "effective_due_date": "2026-06-13"}
    base.update(kw)
    return base


def test_evaluate_linked_multi_week_in_flight_then_missed():
    c = _commit()
    assert evaluate_completion(c, {"closed": False, "canceled": False, "original_due_date": "2026-07-01"},
                               now=LATER, evaluated_at=EVAL)["completion_status"] == "in_flight"
    assert evaluate_completion(c, {"closed": False, "canceled": False, "original_due_date": "2026-06-15"},
                               now=LATER, evaluated_at=EVAL)["completion_status"] == "missed"


def test_evaluate_linked_completed_and_dropped():
    c = _commit()
    assert evaluate_completion(c, {"closed": True, "canceled": False}, now=LATER, evaluated_at=EVAL)["completion_status"] == "completed"
    assert evaluate_completion(c, {"closed": True, "canceled": True}, now=LATER, evaluated_at=EVAL)["completion_status"] == "dropped"


def test_evaluate_linked_vanished_is_carried():
    assert evaluate_completion(_commit(), None, now=LATER, evaluated_at=EVAL)["completion_status"] == "carried"


def test_evaluate_this_week_missed_vs_in_flight():
    past = _commit(project_id=None, issue_id="i1", horizon="this_week", effective_due_date="2026-06-13")
    assert evaluate_completion(past, {"closed": False, "canceled": False}, now=LATER, evaluated_at=EVAL)["completion_status"] == "missed"
    fut = _commit(project_id=None, issue_id="i1", horizon="this_week", effective_due_date="2026-06-25")
    assert evaluate_completion(fut, {"closed": False, "canceled": False}, now=LATER, evaluated_at=EVAL)["completion_status"] == "in_flight"


def test_evaluate_incidental_stays_pending():
    inc = _commit(project_id=None, issue_id=None, horizon="this_week")
    assert evaluate_completion(inc, None, now=LATER, evaluated_at=EVAL)["completion_status"] == "pending"


NOW = "2026-07-13T18:35:00Z"


def test_cache_is_fresh_within_48h():
    assert cache_is_fresh("2026-07-12T00:00:00Z", NOW) is True  # ~42.5h ago


def test_cache_is_fresh_stale_past_48h():
    assert cache_is_fresh("2026-07-10T18:24:23Z", NOW) is False  # ~72h ago (Friday pulse)


def test_cache_is_fresh_missing_is_stale():
    assert cache_is_fresh(None, NOW) is False


def test_project_entity_from_cache():
    row = {"status_type": "completed", "original_due_date": "2026-06-30"}
    assert project_entity_from_cache(row) == {
        "closed": True, "canceled": False, "original_due_date": "2026-06-30",
    }


def test_refresh_project_from_live_first_capture_sets_original_due_date():
    live = {"status_type": "started", "target_date": "2026-08-01"}
    result = refresh_project_from_live(None, live, now=NOW)
    assert result["patch"]["original_due_date"] == "2026-08-01"
    assert result["patch"]["closed_at"] is None
    assert result["patch"]["last_synced_at"] == NOW
    assert result["entity"] == {"closed": False, "canceled": False, "original_due_date": "2026-08-01"}


def test_refresh_project_from_live_never_overwrites_original_due_date():
    cached = {"original_due_date": "2026-07-10", "closed_at": None}
    live = {"status_type": "started", "target_date": "2026-09-01"}  # replanned in Linear
    result = refresh_project_from_live(cached, live, now=NOW)
    assert result["patch"]["original_due_date"] == "2026-07-10"  # immutable, no-reschedule rule
    assert result["entity"]["original_due_date"] == "2026-07-10"


def test_refresh_project_from_live_completed_stamps_closed_at_once():
    live = {"status_type": "completed", "target_date": "2026-07-10"}
    first = refresh_project_from_live(None, live, now=NOW)
    assert first["patch"]["closed_at"] == NOW
    assert first["entity"]["closed"] is True

    already_closed = {"original_due_date": "2026-07-10", "closed_at": "2026-07-08T00:00:00Z"}
    second = refresh_project_from_live(already_closed, live, now=NOW)
    assert second["patch"]["closed_at"] == "2026-07-08T00:00:00Z"  # not restamped


def test_refresh_project_from_live_canceled():
    live = {"status_type": "canceled", "target_date": None}
    result = refresh_project_from_live({"original_due_date": None, "closed_at": None}, live, now=NOW)
    assert result["entity"] == {"closed": False, "canceled": True, "original_due_date": None}


def test_chatter_new_commitment_falls_back_to_end_of_week():
    """A context (chatter) fragment stating a new commitment with no explicit due date
    ("yes, I'll do that list pull this week") must classify identically to a template
    this_week line with no date -- the existing end-of-week fallback, not a special
    case for chatter-sourced commitments."""
    text = "yes, I'll do that list pull this week"
    row = build_row("2026-07-13", "Scott McKeighen", text, "unresolved", created_at="2026-07-13T18:35:00Z")
    assert row["scale"] == "incidental"
    assert row["horizon"] == "this_week"
    assert row["effective_due_date"] == end_of_week("2026-07-13")


def test_match_open_commitment_by_ref():
    candidates = [
        {"id": 38, "commitment": "Review the demo video", "linear_link": None,
         "project_id": "00000000-0000-4000-8000-000000000199", "issue_id": None},
        {"id": 46, "commitment": "Draft blog post", "linear_link": None, "project_id": None, "issue_id": "MAR-7620"},
    ]
    assert match_open_commitment("approved, go ahead on MAR-7620", candidates) == {"resolution": "by_ref", "match": 46}


def test_match_open_commitment_by_name():
    candidates = [
        {"id": 46, "commitment": "founder nurture email copy from Jules", "linear_link": None,
         "project_id": None, "issue_id": None},
        {"id": 47, "commitment": "Create demo video draft in Navattic", "linear_link": None,
         "project_id": None, "issue_id": None},
    ]
    r = match_open_commitment("go ahead, the founder nurture email copy from Jules is approved", candidates)
    assert r == {"resolution": "by_name", "match": 46}


def test_match_open_commitment_ambiguous_or_none_needs_model():
    candidates = [
        {"id": 1, "commitment": "unrelated project work", "linear_link": None, "project_id": None, "issue_id": None},
    ]
    r = match_open_commitment("sounds good, approved", candidates)
    assert r == {"resolution": "needs_model", "match": None}
    assert match_open_commitment("sounds good, approved", []) == {"resolution": "needs_model", "match": None}
