#!/usr/bin/env python3
"""scripts/pm/health.py — deterministic project health (R/Y/G) + issue state.

Pure: no I/O, no clock (now is injected). The golden-gated heart of the pulse.
Health respects the no-reschedule rule: past the immutable original date and not
closed -> off_track, overriding every other signal. `thresholds` is duck-typed to
config.PulseThresholds (same field names); None uses the defaults below.
"""

from dataclasses import dataclass
from datetime import date, timedelta

PROJECT_HEALTH = ("on_track", "at_risk", "off_track")
ISSUE_STATE = ("active", "stale", "blocked", "closed")
CLOSED_STATUS_TYPES = ("completed", "canceled")


@dataclass(frozen=True)
class _Defaults:
    stale_days: int = 10
    behind_pace_pct: float = 0.20
    far_behind_pace_pct: float = 0.40
    blocker_age_business_days: int = 5
    due_soon_days: int = 7


DEFAULTS = _Defaults()


def _to_date(v):
    if v is None:
        return None
    return v if isinstance(v, date) else date.fromisoformat(v[:10])


def days_between(start, end):
    """Signed calendar days, end - start."""
    return (_to_date(end) - _to_date(start)).days


def business_days_between(start, end):
    """Count of Mon-Fri days in the half-open range (start, end]. 0 if end <= start."""
    s, e = _to_date(start), _to_date(end)
    n, d = 0, s + timedelta(days=1)
    while d <= e:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def percent_complete(issues):
    """completed / non-canceled issues. None if there are no non-canceled issues."""
    non_canceled = [i for i in issues if i.get("status_type") != "canceled"]
    if not non_canceled:
        return None
    done = sum(1 for i in non_canceled if i.get("status_type") == "completed")
    return done / len(non_canceled)


def expected_pace(start_date, target_date, now):
    """Linear interpolation clamp((now-start)/(target-start), 0, 1). None if a date is missing."""
    s, t, n = _to_date(start_date), _to_date(target_date), _to_date(now)
    if s is None or t is None:
        return None
    if t <= s:
        return 1.0 if n >= t else 0.0
    return max(0.0, min(1.0, (n - s).days / (t - s).days))


def pace_gap(issues, start_date, target_date, now):
    """expected - actual. Positive = behind. None if either input is None."""
    exp = expected_pace(start_date, target_date, now)
    act = percent_complete(issues)
    if exp is None or act is None:
        return None
    return exp - act


def suggest_project_health(project, issues, *, now, oldest_open_blocker_business_days=0, thresholds=None):
    """Agent-suggested R/Y/G from Linear signals. Returns {'health', 'reasons'}.

    project keys used: status_type, original_due_date, current_target_date, start_date.
    """
    t = thresholds or DEFAULTS
    n = _to_date(now)

    if project.get("status_type") in CLOSED_STATUS_TYPES:
        return {"health": "on_track", "reasons": ["closed/cancelled"]}

    original = _to_date(project.get("original_due_date"))
    if original is not None and n > original:
        return {"health": "off_track", "reasons": ["past original_due_date (no-reschedule rule)"]}

    target = _to_date(project.get("current_target_date"))
    if target is not None and n > target:
        return {"health": "off_track", "reasons": ["current_target_date passed"]}

    gap = pace_gap(issues, project.get("start_date"), project.get("current_target_date"), now)
    far_behind = gap is not None and gap >= t.far_behind_pace_pct
    stale_blocker = oldest_open_blocker_business_days > t.blocker_age_business_days
    if far_behind and stale_blocker:
        return {"health": "off_track",
                "reasons": ["far behind pace with a blocker open past the threshold"]}

    reasons = []
    if gap is not None and gap >= t.behind_pace_pct:
        reasons.append("behind expected pace")
    if stale_blocker:
        reasons.append(f"blocker open >{t.blocker_age_business_days} business days")
    if target is not None and 0 <= days_between(now, target) <= t.due_soon_days and percent_complete(issues) != 1.0:
        reasons.append(f"target within {t.due_soon_days}d and not complete")
    if reasons:
        return {"health": "at_risk", "reasons": reasons}
    return {"health": "on_track", "reasons": []}


def issue_state(issue, *, now, blocked_ids, thresholds=None):
    """Return closed | blocked | stale | active. Precedence: closed > blocked > stale > active."""
    t = thresholds or DEFAULTS
    if issue.get("status_type") in CLOSED_STATUS_TYPES:
        return "closed"
    if issue.get("id") in blocked_ids:
        return "blocked"
    last = issue.get("last_activity_at") or issue.get("updated_at")
    if last is not None and days_between(last, now) > t.stale_days:
        return "stale"
    return "active"
