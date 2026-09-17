"""scripts/seed_demo_state.py — synthetic state is complete, consistent, and leak-free."""
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import tick  # noqa: E402


def seed_into(tmp_path: Path) -> Path:
    root = tmp_path / "fleet"
    (root / "state/identity").mkdir(parents=True)
    shutil.copy(ROOT / "state/identity/scribe-pm-cadence.yaml", root / "state/identity/scribe-pm-cadence.yaml")
    env = dict(os.environ, FLEET_ROOT=str(root))
    r = subprocess.run([sys.executable, str(ROOT / "scripts/seed_demo_state.py"), "--profile", "orrery", "--as-of", "2026-08-21", "--seed", "7", "--force"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    return root


def test_every_table_is_seeded(tmp_path):
    root = seed_into(tmp_path)
    con = sqlite3.connect(root / "state/working/fleet.db")
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    assert len(tables) == 34
    empty = [t for t in tables if con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0]
    assert empty == []
    assert con.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 18
    assert con.execute("SELECT COUNT(*) FROM funnel_snapshots").fetchone()[0] == 22


def test_journals_parse_and_handoff_ids_match_db(tmp_path):
    root = seed_into(tmp_path)
    for agent in ("revops-watchdog", "chief-of-staff", "performance-marketer", "scribe", "content-researcher", "content-producer", "brand-designer"):
        text = (root / f"state/journal/{agent}.md").read_text()
        last = [l for l in text.splitlines() if l.startswith("## ")][-1]
        assert tick.parse_last_tick_timestamp(last) is not None, agent
    con = sqlite3.connect(root / "state/working/fleet.db")
    db_ids = {r[0] for r in con.execute("SELECT id FROM handoffs")}
    log = (root / "state/journal/handoffs.md").read_text()
    assert all(hid in log for hid in db_ids)


def test_seed_is_deterministic(tmp_path):
    a = seed_into(tmp_path / "a")
    b = seed_into(tmp_path / "b")
    dump = lambda p: [r for r in sqlite3.connect(p).iterdump() if "schema_migrations" not in r]  # noqa: E731
    assert dump(a / "state/working/fleet.db") == dump(b / "state/working/fleet.db")


def test_cadence_members_follow_the_profile(tmp_path):
    root = seed_into(tmp_path)
    cadence = (root / "state/identity/scribe-pm-cadence.yaml").read_text()
    assert "Maya Lindqvist" in cadence and "U0DEMO0002" in cadence


def test_seeded_keywords_carry_no_profile_tokens(tmp_path):
    # The base tracked-keywords file is tokenized; the seeder must render tokens
    # so keyword_rankings never shows raw {{company_slug}} strings in a demo.
    root = seed_into(tmp_path)
    db = sqlite3.connect(root / "state/working/fleet.db")
    tokened = [r[0] for r in db.execute("SELECT keyword FROM keyword_rankings WHERE keyword LIKE '%{{%'")]
    db.close()
    assert tokened == []
