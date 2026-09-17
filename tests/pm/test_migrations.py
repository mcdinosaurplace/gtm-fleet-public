"""G1: PM migrations apply in order, produce the right schema, and the runner is idempotent.

Previously this was only checked by hand on temp DBs; this puts it in the gate.
"""
import sqlite3

import pytest

from scripts.pm.config import REPO_ROOT

MIGR = REPO_ROOT / "state" / "working" / "migrations"


def test_pm_migrations_apply_in_order(tmp_path):
    path = tmp_path / "migr.db"
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    for m in ["003_pm_tables.sql", "004_pm_capture_provenance.sql", "005_pm_block_c.sql",
              "013_pm_g2_create_requested.sql"]:
        conn.executescript((MIGR / m).read_text())
    conn.commit()

    assert "owner_source" in {r[1] for r in conn.execute("PRAGMA table_info(pm_projects)")}
    assert {"raw_text", "parsed_by"} <= {r[1] for r in conn.execute("PRAGMA table_info(pm_standup_responses)")}
    assert "create_requested_at" in {r[1] for r in conn.execute("PRAGMA table_info(pm_commitments)")}
    # 'dropped' (migration 005) accepted; an unknown status still rejected by the CHECK
    conn.execute("INSERT INTO pm_commitments (week_starting,owner,commitment,completion_status,created_at) "
                 "VALUES ('2026-06-08','x','y','dropped','t')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO pm_commitments (week_starting,owner,commitment,completion_status,created_at) "
                     "VALUES ('2026-06-08','x','y','bogus','t')")
    assert {"003_pm_tables", "004_pm_capture_provenance", "005_pm_block_c"} <= {
        r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    conn.close()


def test_runner_skips_recorded_and_is_idempotent(tmp_path, monkeypatch):
    """The real run_pending_migrations applies pending PM migrations once, then no-ops."""
    import scripts.tick as tick

    path = tmp_path / "runner.db"
    conn = sqlite3.connect(str(path))
    # Bootstrap base schema via 001 (self-records '001_init'); pre-record 002 so the runner
    # skips its data-restore SQL (irrelevant to the PM chain) and only applies 003/004/005.
    conn.executescript((MIGR / "001_init.sql").read_text())
    conn.execute("INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES ('002_restore_data','t')")
    conn.commit()
    conn.close()

    monkeypatch.setattr(tick, "DB_PATH", path)
    applied1 = tick.run_pending_migrations()
    applied2 = tick.run_pending_migrations()

    assert any("003_pm_tables" in a for a in applied1)
    assert any("005_pm_block_c" in a for a in applied1)
    assert applied2 == []  # idempotent: nothing pending on the second run
