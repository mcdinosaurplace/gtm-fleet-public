"""Tests for scripts/paid/db.py (proposal-persistence writer).

Exercises the REAL schema by building an in-memory DB from migration 008, so the
NOT NULL / CHECK constraints are enforced exactly as in production.

Runs under pytest AND standalone via `python3 tests/paid/test_db.py`.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid import db  # noqa: E402
from scripts.paid.classify import classify_move  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "state" / "working" / "migrations"
MIGRATION = MIGRATIONS_DIR / "008_paid_change_proposals.sql"
MIGRATION_009 = MIGRATIONS_DIR / "009_paid_applied_changes.sql"

TS = "2026-06-16T09:00:00Z"
DATE = "2026-06-16"


def _fresh_conn():
    conn = sqlite3.connect(":memory:")
    conn.executescript(MIGRATION.read_text())
    conn.executescript(MIGRATION_009.read_text())
    conn.row_factory = sqlite3.Row
    return conn


def _move(**over):
    m = {"platform": "google_ads", "op_type": "add_negative", "bucket": "auto_3a",
         "campaign_name": "Search - Generic", "summary": "Negate 'free crm'",
         "reason": "additive on Google Ads"}
    m.update(over)
    return m


def test_insert_and_list_roundtrip():
    conn = _fresh_conn()
    ids = db.insert_proposals(conn, [_move(), _move(op_type="set_bid", summary="Raise bid 10%")],
                              DATE, TS)
    assert len(ids) == 2
    rows = db.list_proposals(conn, dossier_date=DATE)
    assert len(rows) == 2
    assert rows[0]["summary"] == "Negate 'free crm'"
    assert rows[0]["agent"] == "performance-marketer"
    assert rows[0]["created_at"] == TS
    assert rows[0]["status"] == "proposed"  # default


def test_json_values_roundtrip():
    conn = _fresh_conn()
    db.insert_proposals(conn, [_move(op_type="set_bid", summary="bid",
                                     prior_value={"bid_micros": 1190000},
                                     target_value={"bid_micros": 1320000})], DATE, TS)
    row = db.list_proposals(conn)[0]
    import json
    assert json.loads(row["prior_value"]) == {"bid_micros": 1190000}
    assert json.loads(row["target_value"]) == {"bid_micros": 1320000}


def test_required_fields_raise():
    conn = _fresh_conn()
    bad = {"platform": "google_ads", "op_type": "add_negative", "summary": "x"}  # no bucket
    raised = False
    try:
        db.insert_proposals(conn, [bad], DATE, TS)
    except db.DBError:
        raised = True
    assert raised, "missing bucket should raise DBError"


def test_check_constraint_rejects_bad_bucket():
    conn = _fresh_conn()
    raised = False
    try:
        db.insert(conn, "paid_change_proposals", {
            "dossier_date": DATE, "platform": "google_ads", "bucket": "nonsense",
            "op_type": "add_negative", "summary": "x", "created_at": TS})
    except sqlite3.IntegrityError:
        raised = True
    assert raised, "bad bucket should hit the CHECK constraint"


def test_guard_refuses_non_paid_table():
    conn = _fresh_conn()
    raised = False
    try:
        db.insert(conn, "pm_projects", {"x": 1})
    except db.DBError:
        raised = True
    assert raised, "writing a non-paid table should raise DBError"


def test_list_filters_by_status():
    conn = _fresh_conn()
    db.insert_proposals(conn, [_move(), _move(status="rejected", summary="dropped")], DATE, TS)
    proposed = db.list_proposals(conn, status="proposed")
    rejected = db.list_proposals(conn, status="rejected")
    assert len(proposed) == 1 and len(rejected) == 1
    assert rejected[0]["summary"] == "dropped"


def test_set_proposal_status_transition():
    conn = _fresh_conn()
    [pid] = db.insert_proposals(conn, [_move()], DATE, TS)
    db.set_proposal_status(conn, pid, "greenlit", decided_at=TS, approval_id=42)
    row = db.list_proposals(conn)[0]
    assert row["status"] == "greenlit"
    assert row["decided_at"] == TS
    assert row["approval_id"] == 42


def test_set_awaiting_creative_with_linear_ref():
    conn = _fresh_conn()
    [pid] = db.insert_proposals(conn, [_move(op_type="creative", bucket="creative",
                                             summary="New RSA")], DATE, TS)
    db.set_proposal_status(conn, pid, "awaiting_creative", linear_ref="MAR-7076")
    row = db.list_proposals(conn)[0]
    assert row["status"] == "awaiting_creative"
    assert row["linear_ref"] == "MAR-7076"


def test_classify_then_persist_integration():
    """The real flow: classify full moves, merge the verdict, persist."""
    conn = _fresh_conn()
    full_moves = [
        {"platform": "google_ads", "op_type": "add_negative", "campaign_name": "Gen",
         "summary": "Negate 'free crm'"},
        {"platform": "google_ads", "op_type": "budget", "campaign_name": "Nonbrand — Incident Mgmt",
         "summary": "Shift $1.5k", "budget_delta_weekly": 1500.0},
        {"platform": "google_ads", "op_type": "creative", "campaign_name": "Comp",
         "summary": "Founder RSA"},
    ]
    for m in full_moves:
        v = classify_move(m)
        m["bucket"], m["reason"] = v["bucket"], v["reason"]
    db.insert_proposals(conn, full_moves, DATE, TS)
    rows = db.list_proposals(conn, dossier_date=DATE)
    buckets = sorted(r["bucket"] for r in rows)
    assert buckets == ["auto_3a", "creative", "human_3b"]
    # The classifier's reason is persisted alongside the bucket.
    assert all(r["reason"] for r in rows)


def test_applied_changes_list_and_rollback():
    conn = _fresh_conn()
    db.insert(conn, "applied_changes", {
        "proposal_id": 1, "platform": "google_ads", "entity": "x", "op_type": "set_bid",
        "prior_value": "{}", "new_value": "{}", "mode": "live",
        "applied_at": TS, "created_at": TS})
    active = db.list_applied_changes(conn, active_only=True)
    assert len(active) == 1
    db.mark_rolled_back(conn, active[0]["id"], TS)
    assert db.list_applied_changes(conn, active_only=True) == []      # no longer active
    assert len(db.list_applied_changes(conn)) == 1                    # still on the ledger


if __name__ == "__main__":
    failures = 0
    for name in sorted(k for k in dict(globals()) if k.startswith("test_")):
        fn = globals()[name]
        if not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}: {e}")
    print(f"\n{'PASS' if not failures else 'FAIL'} — "
          f"{0 if not failures else failures} failure(s)")
    sys.exit(1 if failures else 0)
