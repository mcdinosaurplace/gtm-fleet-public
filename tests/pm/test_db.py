"""Tests for scripts/pm/db.py — the pm_* writer helpers.

Builds a temp DB from migration 003 (schema_migrations pre-created), then exercises
insert / upsert / fetch + the non-PM write guard + a CHECK constraint.
"""
import sqlite3

import pytest

from scripts.pm.config import REPO_ROOT
from scripts.pm.db import DBError, PM_TABLES, connect, fetchall, fetchone, insert, update, upsert

MIGRATION = REPO_ROOT / "state" / "working" / "migrations" / "003_pm_tables.sql"


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "pm_test.db"
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    conn.executescript(MIGRATION.read_text())
    conn.commit()
    conn.close()
    c = connect(path)
    yield c
    c.close()


def test_connect_missing_db_raises(tmp_path):
    with pytest.raises(DBError):
        connect(tmp_path / "nope.db")


def test_migration_creates_pm_tables(db):
    names = {r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(PM_TABLES).issubset(names)


def test_insert_and_fetch(db):
    rowid = insert(
        db,
        "pm_projects",
        {
            "id": "proj-1",
            "name": "MOPS Inbox and New Requests",
            "owner": "Scott McKeighen",
            "health": "on_track",
            "original_due_date": "2026-07-01",
            "linear_link": "https://linear.app/orrery/project/x",
            "created_at": "2026-06-08T00:00:00Z",
        },
    )
    assert rowid is not None
    got = fetchone(db, "SELECT * FROM pm_projects WHERE id=?", ("proj-1",))
    assert got["name"] == "MOPS Inbox and New Requests"
    assert got["health"] == "on_track"
    assert got["agent"] == "scribe"  # schema default applied


def test_guard_rejects_non_pm_table(db):
    with pytest.raises(DBError):
        insert(db, "funnel_snapshots", {"snapshot_date": "2026-06-08", "created_at": "x"})


def test_upsert_updates_on_conflict(db):
    base = {
        "week_starting": "2026-06-08",
        "channel_id": "C0DEMO0001",
        "master_ts": "111.0001",
        "master_posted_at": "2026-06-08T12:00:00Z",
        "created_at": "2026-06-08T12:00:00Z",
    }
    upsert(db, "pm_standup_threads", base, key_cols=["week_starting"])
    upsert(db, "pm_standup_threads", dict(base, master_ts="222.0002"), key_cols=["week_starting"])
    db.commit()
    rows = fetchall(db, "SELECT * FROM pm_standup_threads WHERE week_starting=?", ("2026-06-08",))
    assert len(rows) == 1                       # upsert, not a second row
    assert rows[0]["master_ts"] == "222.0002"   # updated in place


def test_check_constraint_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        insert(
            db,
            "pm_projects",
            {
                "id": "proj-2",
                "name": "X",
                "owner": "Y",
                "health": "amber",  # not in the CHECK set
                "linear_link": "z",
                "created_at": "2026-06-08T00:00:00Z",
            },
        )


def test_fetchone_none(db):
    assert fetchone(db, "SELECT * FROM pm_projects WHERE id=?", ("nope",)) is None


def test_update_sets_fields_and_returns_count(db):
    insert(db, "pm_commitments", {
        "week_starting": "2026-06-29", "owner": "Scott McKeighen", "commitment": "x",
        "resolution": "unresolved", "completion_status": "pending", "created_at": "t",
    })
    n = update(db, "pm_commitments",
               {"resolution": "confirmed", "linear_link": "https://linear.app/orrery/issue/MAR-7569"},
               {"week_starting": "2026-06-29", "owner": "Scott McKeighen"})
    db.commit()
    assert n == 1
    got = fetchone(db, "SELECT * FROM pm_commitments WHERE owner=?", ("Scott McKeighen",))
    assert got["resolution"] == "confirmed" and got["linear_link"].endswith("MAR-7569")


def test_update_requires_where(db):
    with pytest.raises(DBError):
        update(db, "pm_commitments", {"resolution": "confirmed"}, {})


def test_update_requires_set_fields(db):
    with pytest.raises(DBError):
        update(db, "pm_commitments", {}, {"id": 1})


def test_update_guard_rejects_non_pm_table(db):
    with pytest.raises(DBError):
        update(db, "funnel_snapshots", {"x": 1}, {"id": 1})
