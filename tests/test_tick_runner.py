"""scripts/tick.py — the headless runner, exercised in stub mode against a throwaway FLEET_ROOT."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICK = ROOT / "scripts" / "tick.py"


def make_fleet(tmp_path: Path) -> Path:
    """A minimal FLEET_ROOT: identity + empty journals + an initialized DB, as a git repo."""
    root = tmp_path / "fleet"
    for sub in ("state/identity", "state/journal", "state/working"):
        (root / sub).mkdir(parents=True)
    shutil.copy(ROOT / "state/identity/revops-watchdog.md", root / "state/identity/revops-watchdog.md")
    shutil.copy(ROOT / "state/identity/chief-of-staff.md", root / "state/identity/chief-of-staff.md")
    (root / "state/journal/revops-watchdog.md").write_text("# revops-watchdog\n")
    (root / "state/journal/chief-of-staff.md").write_text("# chief-of-staff\n")
    (root / "state/journal/handoffs.md").write_text("# Handoffs\n")
    (root / "state/journal/ops-incidents.md").write_text("# Ops\n")
    (root / "state/journal/chief-of-staff-meditations.md").write_text("# Meditations\n")
    (root / "state/working/fleet.db").touch()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    return root


def run_tick(root: Path, *args, **env_extra):
    env = dict(os.environ, FLEET_ROOT=str(root), **env_extra)
    env.pop("FLEET_REMOTE", None)
    return subprocess.run([sys.executable, str(TICK), *args], capture_output=True, text=True, env=env)


def test_stub_runner_applies_migrations_journals_and_commits(tmp_path):
    root = make_fleet(tmp_path)
    r = run_tick(root, "--agent", "revops-watchdog", "--mode", "daily", "--runner", "stub")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Migration applied: 001_init.sql" in r.stdout
    journal = (root / "state/journal/revops-watchdog.md").read_text()
    assert "| Tick complete" in journal and "runner=stub" in journal
    log = subprocess.run(["git", "-C", str(root), "log", "--format=%an|%s", "-1"], capture_output=True, text=True).stdout.strip()
    assert log.startswith("state-bot|[state-bot] revops-watchdog | DAILY Tick complete")


def test_dry_run_prints_the_claude_command_without_writing(tmp_path):
    root = make_fleet(tmp_path)
    r = run_tick(root, "--agent", "revops-watchdog", "--mode", "daily", "--runner", "claude", "--dry-run", FLEET_CLAUDE_BIN=sys.executable)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '-p "/gtm-fleet:revops-watchdog daily --harness"' in r.stdout
    assert "--plugin-dir" in r.stdout and "--output-format json" in r.stdout
    assert (root / "state/journal/revops-watchdog.md").read_text() == "# revops-watchdog\n"


def test_claude_runner_requires_proof_of_work(tmp_path):
    """A fake `claude` that returns valid JSON but never journals must be treated as a failed Tick."""
    root = make_fleet(tmp_path)
    fake = tmp_path / "claude"
    fake.write_text("#!/bin/sh\necho '" + json.dumps({"result": "ok", "is_error": False, "session_id": "s", "num_turns": 1, "total_cost_usd": 0.0}) + "'\n")
    fake.chmod(0o755)
    r = run_tick(root, "--agent", "revops-watchdog", "--mode", "daily", "--runner", "claude", FLEET_CLAUDE_BIN=str(fake))
    assert r.returncode == 0  # the Tick completes, but records the failure
    incidents = (root / "state/journal/ops-incidents.md").read_text()
    assert "HIGH" in incidents and "without journaling" in incidents


def test_mode_validation():
    r = subprocess.run([sys.executable, str(TICK), "--agent", "brand-designer", "--mode", "am"], capture_output=True, text=True)
    assert r.returncode != 0 and "only supports" in r.stderr
