"""Tests for the saved pm_* queries.

Each query parses and runs against a temp DB built from migration 003, and the
date-sensitive ones find their seeded rows. This keeps the saved queries inside
the regression gate, so a schema change that breaks one fails CI.
"""
import sqlite3

import pytest

from scripts.pm.config import REPO_ROOT

MIGRATION = REPO_ROOT / "state" / "working" / "migrations" / "003_pm_tables.sql"
QUERY_DIR = REPO_ROOT / "state" / "working" / "queries"
QUERIES = sorted(QUERY_DIR.glob("pm_*.sql"))


@pytest.fixture
def seeded(tmp_path):
    path = tmp_path / "q.db"
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    conn.executescript(MIGRATION.read_text())
    conn.executescript(
        """
        INSERT INTO pm_projects (id,name,owner,health,original_due_date,linear_link,created_at)
          VALUES ('p1','Past Due Proj','Scott McKeighen','off_track','2020-01-01','http://x','2026-06-08T00:00:00Z');
        INSERT INTO pm_issues (id,title,state,linear_link,created_at)
          VALUES ('i1','Orphan','blocked','http://y','2026-06-08T00:00:00Z');
        INSERT INTO pm_commitments (week_starting,owner,commitment,completion_status,created_at)
          VALUES ('2026-06-08','Scott McKeighen','do x','pending','2026-06-08T00:00:00Z');
        INSERT INTO pm_blockers (issue_id,description,opened_at,created_at)
          VALUES ('i1','waiting on design','2026-06-01T00:00:00Z','2026-06-08T00:00:00Z');
        INSERT INTO pm_external_dependencies (week_starting,internal_owner,external_party,expected_delivery,status,created_at)
          VALUES ('2026-06-08','Tomas Reyes','Jules','2020-01-01','pending','2026-06-08T00:00:00Z');
        """
    )
    conn.commit()
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_queries_exist():
    assert QUERIES, "no pm_*.sql saved queries found"


@pytest.mark.parametrize("qfile", QUERIES, ids=lambda p: p.name)
def test_query_executes(seeded, qfile):
    rows = seeded.execute(qfile.read_text()).fetchall()
    assert isinstance(rows, list)


def test_past_due_query_finds_seeded(seeded):
    sql = (QUERY_DIR / "pm_past_due_projects.sql").read_text()
    rows = [dict(r) for r in seeded.execute(sql).fetchall()]
    assert any(r["id"] == "p1" for r in rows)


def test_orphan_query_finds_seeded(seeded):
    sql = (QUERY_DIR / "pm_orphan_issues.sql").read_text()
    rows = [dict(r) for r in seeded.execute(sql).fetchall()]
    assert any(r["id"] == "i1" for r in rows)


def test_open_blockers_age(seeded):
    sql = (QUERY_DIR / "pm_open_blockers.sql").read_text()
    rows = [dict(r) for r in seeded.execute(sql).fetchall()]
    assert rows and rows[0]["age_days"] >= 1
