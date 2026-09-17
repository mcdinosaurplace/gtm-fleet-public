#!/usr/bin/env python3
"""
fleet_git.py — the fleet's git transport, with no branch or remote baked in.

    python3 scripts/fleet_git.py sync                  # Librarian step 0
    python3 scripts/fleet_git.py commit --agent revops-watchdog --action "Daily Tick"   # step 10a
    python3 scripts/fleet_git.py push                  # step 10b
    python3 scripts/fleet_git.py status

Configuration (environment, all optional):
    FLEET_ROOT     where state/ lives (see scripts/fleet_paths.py)
    FLEET_BRANCH   the branch agents must be on. Unset → whatever branch is checked out.
    FLEET_REMOTE   a remote name (e.g. origin). Unset → local-commit mode: no fetch, no push.

Semantics
  sync    With FLEET_REMOTE: `git fetch`, `git checkout $FLEET_BRANCH`, `git pull --ff-only`;
          any failure exits 2 — the caller treats that as a hard stop (never proceed on a
          fallback branch, never on a session-assigned branch). Without FLEET_REMOTE: verify the
          branch matches FLEET_BRANCH when set, otherwise just report it, exit 0.
  commit  Stages state/ (and wbr/ if present) and commits as the state-bot identity with the
          message `[state-bot] <Agent> | <action> | <ISO-8601Z>`. "Nothing to commit" is success.
  push    Only with FLEET_REMOTE; retries 4× with exponential backoff (2/4/8/16 s). Exit 3 on failure
          so the caller can log "committed locally but unpushed" with the SHA.

Single-machine kits never need a remote: commits are the audit trail. Multi-writer fleets
(two operators, a cloud routine) set FLEET_REMOTE + FLEET_BRANCH and inherit the original
"unpushed = never ran" contract. See docs/state-commit-convention.md.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import fleet_paths  # noqa: E402

STATE_BOT = "state-bot <state-bot@fleet.local>"


def git(root: Path, *args, check=False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def current_branch(root: Path) -> str:
    r = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else ""


def cmd_sync(root: Path, remote: str, branch: str) -> int:
    if not current_branch(root):
        print(f"sync: {root} is not a git repository — run `git init` (see docs/state-commit-convention.md)")
        return 2
    if remote:
        for step in (["fetch", remote], ["checkout", branch or current_branch(root)], ["pull", "--ff-only", remote, branch or current_branch(root)]):
            r = git(root, *step)
            if r.returncode != 0:
                print(f"sync: `git {' '.join(step)}` failed — hard stop:\n{r.stderr.strip()}")
                return 2
        print(f"sync: on {current_branch(root)}, up to date with {remote}")
        return 0
    br = current_branch(root)
    if branch and br != branch:
        r = git(root, "checkout", branch)
        if r.returncode != 0:
            print(f"sync: FLEET_BRANCH={branch} but on {br} and checkout failed — hard stop:\n{r.stderr.strip()}")
            return 2
        br = branch
    print(f"sync: FLEET_REMOTE unset — local mode; on branch {br}")
    return 0


def cmd_commit(root: Path, agent: str, action: str, paths: list[str]) -> int:
    ts = now_utc()
    for p in paths:
        if (root / p).exists():
            r = git(root, "add", "-A", "--", p)
            if r.returncode != 0:
                print(f"commit: git add {p} failed:\n{r.stderr.strip()}")
                return 1
    message = f"[state-bot] {agent} | {action} | {ts}"
    r = git(root, "-c", "user.name=state-bot", "-c", "user.email=state-bot@fleet.local",
            "commit", f"--author={STATE_BOT}", "-m", message)
    if r.returncode != 0:
        if "nothing to commit" in (r.stdout + r.stderr):
            print("commit: nothing to commit — state unchanged")
            return 0
        print(f"commit: failed:\n{r.stderr.strip() or r.stdout.strip()}")
        return 1
    sha = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"commit: {sha} {message}")
    return 0


def cmd_push(root: Path, remote: str, branch: str) -> int:
    if not remote:
        print("push: FLEET_REMOTE unset — local mode, nothing to push")
        return 0
    br = branch or current_branch(root)
    for attempt, delay in enumerate((2, 4, 8, 16), start=1):
        r = git(root, "push", "-u", remote, br)
        if r.returncode == 0:
            print(f"push: {remote}/{br} ok")
            return 0
        print(f"push: attempt {attempt} failed: {r.stderr.strip()[:200]}")
        if attempt < 4:
            time.sleep(delay)
    sha = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"push: FAILED after 4 attempts — committed locally as {sha} on {br} but unpushed")
    return 3


def cmd_status(root: Path, remote: str, branch: str) -> int:
    br = current_branch(root) or "(no git)"
    dirty = git(root, "status", "--porcelain", "--", "state").stdout.strip()
    print(f"branch={br} FLEET_BRANCH={branch or '(unset)'} FLEET_REMOTE={remote or '(unset: local mode)'} "
          f"state_dirty={'yes' if dirty else 'no'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    c = sub.add_parser("commit")
    c.add_argument("--agent", required=True)
    c.add_argument("--action", required=True)
    c.add_argument("--paths", nargs="*", default=["state", "wbr"])
    sub.add_parser("push")
    sub.add_parser("status")
    args = ap.parse_args()

    root = fleet_paths.fleet_root(strict=True)
    remote = os.environ.get("FLEET_REMOTE", "").strip()
    branch = os.environ.get("FLEET_BRANCH", "").strip()
    if args.cmd == "sync":
        return cmd_sync(root, remote, branch)
    if args.cmd == "commit":
        return cmd_commit(root, args.agent, args.action, args.paths)
    if args.cmd == "push":
        return cmd_push(root, remote, branch)
    return cmd_status(root, remote, branch)


if __name__ == "__main__":
    sys.exit(main())
