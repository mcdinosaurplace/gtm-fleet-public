"""S1: end-to-end chain across the PM cores on synthetic data + a temp DB.

standup_post -> capture -> linear_resolve -> commitments.build_row -> pulse.compute_pulse
(write to DB) -> evaluate_completion. Validates the modules COMPOSE (the wiring M2 worried
about), not just their unit behavior.
"""
import sqlite3
from datetime import date

import pytest

from scripts.pm import capture, commitments, db, linear_resolve, pulse, standup_post
from scripts.pm.config import REPO_ROOT, _build_config

MIGR = REPO_ROOT / "state" / "working" / "migrations"
MONDAY = date(2026, 6, 8)

CONFIG = _build_config(
    {
        "team": {"monday_post_pt": "05:00", "monday_response_deadline_pt": "23:59",
                 "weekday_pulse_pt": "09:00", "thursday_agenda_pt": "06:30"},
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


@pytest.fixture
def pmdb(tmp_path):
    path = tmp_path / "e2e.db"
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


def test_pipeline_standup_to_pulse_to_completion(pmdb):
    # 1. B1 — render the Monday post + tags (wiring sanity)
    plan = standup_post.plan(CONFIG, MONDAY)
    assert "Weekly Marketing Standup" in plan["master_text"]
    assert plan["tag_text"] and "<@U0DEMO0001>" in plan["tag_text"]

    # 2. B2 — Scott replies in the template format; capture parses it
    scott = CONFIG.member("Scott McKeighen")
    reply = (
        ":ballot_box_with_check: Last Week:\nshipped the meta refresh\n"
        ":clipboard: This Week:\nMOPS Inbox and New Requests\n"
        ":warning: Blockers?:\nnone\n"
        ":grey_question: External Dependencies:\nJules / blog draft / 2026-06-12"
    )
    thread = [
        {"user_id": "UBOT", "text": plan["master_text"]},
        {"user_id": scott.slack_user_id, "text": reply},
    ]
    cap = capture.capture(thread, CONFIG)
    sc = next(m for m in cap["members"] if m["owner"] == "Scott McKeighen")
    assert "MOPS Inbox and New Requests" in sc["sections"]["this_week"]
    assert sc["external_deps_rule"][0]["external_party"] == "Jules"  # '/'-parsed deterministically

    # 3. B3 — resolve the this-week commitment by name against candidates
    cands = [{"id": "p1", "name": "MOPS Inbox and New Requests", "type": "project", "due_date": "2026-07-01"}]
    r = linear_resolve.resolve(sc["sections"]["this_week"], cands)
    assert r["resolution"] == "by_name" and r["match"]["id"] == "p1"

    # 4. B3 — build the pm_commitments row
    row = commitments.build_row(
        MONDAY.isoformat(), "Scott McKeighen", sc["sections"]["this_week"], "by_name",
        entity_type="project", entity_due_date="2026-07-01", linear_link="u",
        project_id="p1", created_at="2026-06-08T00:00:00Z")
    assert row["scale"] == "project" and row["horizon"] == "multi_week"

    # 5. C1 — pulse computes the same project, written to the temp DB
    proj = {"id": "p1", "name": "MOPS Inbox and New Requests", "status_type": "started",
            "lead_name": "Scott McKeighen", "member_names": ["Scott McKeighen"],
            "start_date": "2026-06-01", "target_date": "2026-07-01", "url": "u", "summary": "s"}
    res = pulse.compute_pulse(
        projects=[proj], issues=[], issue_blockers={}, status_health={},
        prior_projects={}, prior_issues={}, prior_blockers=[], prior_missed_ids=set(),
        config=CONFIG, now="2026-06-08", created_at="2026-06-08T00:00:00Z")
    for pr in res["project_rows"]:
        db.upsert(pmdb, "pm_projects", pr, key_cols=["id"])
    pmdb.commit()
    got = db.fetchone(pmdb, "SELECT * FROM pm_projects WHERE id=?", ("p1",))
    assert got["owner"] == "Scott McKeighen" and got["health"] == "on_track"
    assert row["project_id"] == got["id"]  # the commitment + the pulse'd project line up

    # 6. C3 — completion eval against the live entity state: open + future -> in_flight
    ev = commitments.evaluate_completion(
        row, {"closed": False, "canceled": False, "original_due_date": got["original_due_date"]},
        now="2026-06-09", evaluated_at="2026-06-09T00:00:00Z")
    assert ev["completion_status"] == "in_flight"
