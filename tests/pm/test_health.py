"""Tests for scripts/pm/health.py — deterministic R/Y/G + issue state."""
from datetime import date

import pytest

from scripts.pm.health import (
    business_days_between,
    days_between,
    expected_pace,
    issue_state,
    pace_gap,
    percent_complete,
    suggest_project_health,
)

NOW = date(2026, 6, 9)


def _issues(done, total, canceled=0):
    out = [{"status_type": "completed"} for _ in range(done)]
    out += [{"status_type": "started"} for _ in range(total - done)]
    out += [{"status_type": "canceled"} for _ in range(canceled)]
    return out


# ---- date + pace helpers ----

def test_days_between():
    assert days_between("2026-06-01", "2026-06-09") == 8
    assert days_between("2026-06-09", "2026-06-01") == -8


def test_business_days_between():
    # Mon 2026-06-08 -> Mon 2026-06-15 = Tue..Mon weekdays = 5
    assert business_days_between("2026-06-08", "2026-06-15") == 5
    assert business_days_between("2026-06-15", "2026-06-08") == 0


def test_percent_complete():
    assert percent_complete(_issues(2, 4)) == 0.5
    assert percent_complete(_issues(0, 0, canceled=3)) is None   # only canceled
    assert percent_complete([]) is None
    assert percent_complete(_issues(1, 1, canceled=2)) == 1.0     # canceled excluded from denom


def test_expected_pace():
    assert expected_pace("2026-06-01", "2026-06-21", NOW) == pytest.approx(0.4)  # 8/20
    assert expected_pace("2026-07-01", "2026-07-31", NOW) == 0.0                  # before start
    assert expected_pace("2026-05-01", "2026-06-01", NOW) == 1.0                  # after target
    assert expected_pace(None, "2026-06-21", NOW) is None
    assert expected_pace("2026-06-09", "2026-06-09", NOW) == 1.0                  # degenerate, now>=target


def test_pace_gap_none_when_unmeasurable():
    assert pace_gap([], "2026-06-01", "2026-06-21", NOW) is None   # no issues -> % None


# ---- project health branches ----

def _proj(**kw):
    base = {"status_type": "started", "original_due_date": None,
            "current_target_date": None, "start_date": None}
    base.update(kw)
    return base


def test_closed_short_circuits_on_track():
    assert suggest_project_health(_proj(status_type="completed"), [], now=NOW)["health"] == "on_track"
    assert suggest_project_health(_proj(status_type="canceled"), [], now=NOW)["health"] == "on_track"


def test_past_original_is_off_track_override():
    # past the immutable original date -> off_track regardless of anything else
    h = suggest_project_health(
        _proj(original_due_date="2026-05-30", current_target_date="2026-08-01", start_date="2026-04-01"),
        _issues(5, 5), now=NOW,
    )
    assert h["health"] == "off_track"
    assert "original_due_date" in h["reasons"][0]


def test_current_target_passed_is_off_track():
    h = suggest_project_health(_proj(current_target_date="2026-06-01"), _issues(1, 2), now=NOW)
    assert h["health"] == "off_track"


def test_behind_pace_is_at_risk():
    # start 6/1, target 6/30 (29d), now 6/9 (8d) -> expected ~0.276; 0 done -> gap ~0.276 in [0.20, 0.40)
    h = suggest_project_health(
        _proj(start_date="2026-06-01", current_target_date="2026-06-30"), _issues(0, 5), now=NOW)
    assert h["health"] == "at_risk"
    assert "behind expected pace" in h["reasons"]


def test_stale_blocker_alone_is_at_risk():
    h = suggest_project_health(_proj(), [], now=NOW, oldest_open_blocker_business_days=6)
    assert h["health"] == "at_risk"
    assert any("blocker open" in r for r in h["reasons"])


def test_far_behind_with_stale_blocker_is_off_track():
    # start 6/1, target 6/15 (14d), now 6/9 (8d) -> expected ~0.571; 0 done -> gap >= 0.40
    h = suggest_project_health(
        _proj(start_date="2026-06-01", current_target_date="2026-06-15"), _issues(0, 5),
        now=NOW, oldest_open_blocker_business_days=6)
    assert h["health"] == "off_track"


def test_due_soon_not_complete_is_at_risk():
    # on pace (3/4 done, slightly ahead) but target within 7 days and not 100% -> at_risk
    h = suggest_project_health(
        _proj(start_date="2026-06-01", current_target_date="2026-06-12"), _issues(3, 4), now=NOW)
    assert h["health"] == "at_risk"
    assert any("within" in r for r in h["reasons"])


def test_clean_is_on_track():
    h = suggest_project_health(
        _proj(start_date="2026-06-01", current_target_date="2026-08-01"), _issues(2, 4), now=NOW)
    assert h["health"] == "on_track"
    assert h["reasons"] == []


# ---- issue state ----

def test_issue_state_precedence():
    assert issue_state({"status_type": "completed"}, now=NOW, blocked_ids=set()) == "closed"
    assert issue_state({"id": "i1", "status_type": "started"}, now=NOW, blocked_ids={"i1"}) == "blocked"
    # blocked beats stale
    assert issue_state({"id": "i1", "status_type": "started", "last_activity_at": "2026-05-01"},
                       now=NOW, blocked_ids={"i1"}) == "blocked"
    assert issue_state({"id": "i2", "status_type": "started", "last_activity_at": "2026-05-20"},
                       now=NOW, blocked_ids=set()) == "stale"   # >10 days
    assert issue_state({"id": "i3", "status_type": "started", "last_activity_at": "2026-06-07"},
                       now=NOW, blocked_ids=set()) == "active"
