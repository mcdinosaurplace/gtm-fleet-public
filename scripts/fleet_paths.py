#!/usr/bin/env python3
"""
fleet_paths.py — the one place the fleet resolves where things live.

Two roots:
  PLUGIN_ROOT  where the code lives (skills/, roster/, scripts/, migrations, schema).
               Always this repository (the directory above scripts/).
  FLEET_ROOT   where mutable state lives and git commits happen (state/, wbr/).
               Resolved as: $FLEET_ROOT  →  PLUGIN_ROOT if it has state/  →
               $CLAUDE_PROJECT_DIR if it has state/  →  error.
               In "workspace mode" (you opened this repo) the two are identical.

Usage (CLI):
    python3 scripts/fleet_paths.py --root      # print FLEET_ROOT
    python3 scripts/fleet_paths.py --db        # print the SQLite path
    python3 scripts/fleet_paths.py --status    # one line: branch, profile, DEMO_MODE, db present
    python3 scripts/fleet_paths.py --check     # human-readable resolution report (exit 1 on error)
    python3 scripts/fleet_paths.py --json

Usage (import):
    from scripts.fleet_paths import FLEET_ROOT, DB_PATH, JOURNAL_DIR, profile, demo_mode
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DB_NAME = "fleet.db"


def _candidates():
    env = os.environ.get("FLEET_ROOT")
    if env:
        yield "FLEET_ROOT env", Path(env).expanduser()
    yield "plugin root", PLUGIN_ROOT
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        yield "CLAUDE_PROJECT_DIR", Path(proj).expanduser()


def fleet_root(strict: bool = True) -> Path:
    """Resolve FLEET_ROOT. With strict=False, fall back to PLUGIN_ROOT instead of exiting."""
    env = os.environ.get("FLEET_ROOT")
    if env:
        p = Path(env).expanduser()
        if (p / "state").is_dir():
            return p.resolve()
        if strict:
            sys.exit(f"[fleet_paths] FLEET_ROOT={env} has no state/ directory")
    for _, p in _candidates():
        if (p / "state").is_dir():
            return p.resolve()
    if strict:
        sys.exit(
            "[fleet_paths] cannot resolve FLEET_ROOT: set FLEET_ROOT=<dir containing state/>, "
            f"or run inside the fleet workspace (tried: {', '.join(f'{n}={p}' for n, p in _candidates())})"
        )
    return PLUGIN_ROOT


FLEET_ROOT = fleet_root(strict=False)
STATE_DIR = FLEET_ROOT / "state"
IDENTITY_DIR = STATE_DIR / "identity"
JOURNAL_DIR = STATE_DIR / "journal"
PENDING_DIR = STATE_DIR / "pending"
PUBLISHED_DIR = STATE_DIR / "published"
WORKING_DIR = STATE_DIR / "working"
DB_PATH = WORKING_DIR / DB_NAME
WBR_DIR = FLEET_ROOT / "wbr"
MIGRATIONS_DIR = PLUGIN_ROOT / "state" / "working" / "migrations"  # code, not state
SCHEMA_PATH = PLUGIN_ROOT / "state" / "working" / "schema.sql"
PROFILES_DIR = PLUGIN_ROOT / "profiles"


def profile() -> str:
    """Active profile name: $FLEET_PROFILE → fleet.yaml:profile → 'base'."""
    env = os.environ.get("FLEET_PROFILE")
    if env:
        return env
    fy = PLUGIN_ROOT / "fleet.yaml"
    if fy.exists():
        for line in fy.read_text().splitlines():
            if line.startswith("profile:"):
                return line.split(":", 1)[1].strip().strip('"\'') or "base"
    return "base"


def demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "").lower() in {"1", "true", "yes", "on"}


def git_branch(root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else "(no git)"
    except (OSError, subprocess.TimeoutExpired):
        return "(no git)"


def status_dict(strict: bool = False) -> dict:
    root = fleet_root(strict=strict)
    return {
        "plugin_root": str(PLUGIN_ROOT),
        "fleet_root": str(root),
        "db": str(root / "state" / "working" / DB_NAME),
        "db_present": (root / "state" / "working" / DB_NAME).exists(),
        "profile": profile(),
        "demo_mode": demo_mode(),
        "branch": git_branch(root),
        "fleet_remote": os.environ.get("FLEET_REMOTE", ""),
        "fleet_branch": os.environ.get("FLEET_BRANCH", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--root", action="store_true", help="print FLEET_ROOT")
    g.add_argument("--db", action="store_true", help="print the SQLite path")
    g.add_argument("--status", action="store_true", help="one-line status")
    g.add_argument("--check", action="store_true", help="resolution report; exit 1 on problems")
    g.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.root:
        print(fleet_root(strict=True))
        return 0
    if args.db:
        print(fleet_root(strict=True) / "state" / "working" / DB_NAME)
        return 0
    s = status_dict(strict=True)
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    if args.status:
        print(f"FLEET_ROOT={s['fleet_root']} profile={s['profile']} DEMO_MODE={int(s['demo_mode'])} "
              f"db={'present' if s['db_present'] else 'MISSING'} branch={s['branch']}"
              + (f" remote={s['fleet_remote']}" if s['fleet_remote'] else " remote=(local only)"))
        return 0
    # --check (default)
    problems = []
    print(f"PLUGIN_ROOT = {s['plugin_root']}")
    print(f"FLEET_ROOT  = {s['fleet_root']}  (mode: {'workspace' if s['fleet_root'] == s['plugin_root'] else 'external state'})")
    print(f"DB          = {s['db']}  ({'present' if s['db_present'] else 'MISSING — run: make seed'})")
    print(f"profile     = {s['profile']}    DEMO_MODE = {int(s['demo_mode'])}")
    print(f"git branch  = {s['branch']}    FLEET_REMOTE = {s['fleet_remote'] or '(unset — local commits only)'}")
    for sub in ("identity", "journal", "working/migrations"):
        if not (Path(s["fleet_root"]) / "state" / sub).is_dir() and not (PLUGIN_ROOT / "state" / sub).is_dir():
            problems.append(f"missing state/{sub}")
    if not s["db_present"]:
        problems.append("database missing (python3 scripts/seed_demo_state.py, or apply migrations)")
    for p in problems:
        print(f"PROBLEM: {p}")
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
