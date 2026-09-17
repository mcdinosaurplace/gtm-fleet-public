#!/usr/bin/env python3
"""
Tick harness — Librarian Protocol runner for the GTM Fleet.

    python3 scripts/tick.py --agent revops-watchdog --mode daily [--runner auto|claude|stub] [--dry-run]

Steps 1-5 (identity, last journal entry, new handoffs, anchor, migrations) run here in
Python. Step 6 — the agent's actual job — runs as a headless Claude Code session:

    claude -p "/gtm-fleet:<agent> <mode> --harness" --plugin-dir <PLUGIN_ROOT> ...

The prompt does the specialist work and writes its own journal entry; the harness then
verifies proof-of-work (a new `## <timestamp>` header in the agent's journal), runs
chief-of-staff's cross-agent audit, and commits state via scripts/fleet_git.py.

`--runner stub` keeps the original no-op path (writes a one-line journal entry) for
tests and for machines without the `claude` CLI. `--runner auto` picks `claude` when
FLEET_CLAUDE_BIN or `claude` on PATH resolves, else stub (with a loud warning).

Environment: FLEET_ROOT, FLEET_BRANCH, FLEET_REMOTE (scripts/fleet_paths.py, fleet_git.py);
FLEET_CLAUDE_BIN, FLEET_PERMISSION_MODE (acceptEdits), FLEET_MAX_TURNS (80),
FLEET_MAX_BUDGET_USD (5), FLEET_TICK_TIMEOUT_S (1800), FLEET_CLAUDE_BARE (0), DEMO_MODE.
Schedules live in schedule.yaml (rendered by scripts/schedule_render.py, never installed here).
"""

import argparse
import json
import os
import shutil
import subprocess
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import fleet_paths  # noqa: E402


# ============================================================
# Config (module attributes are kept so tests can monkeypatch them)
# ============================================================

PLUGIN_ROOT = fleet_paths.PLUGIN_ROOT
REPO_ROOT = fleet_paths.FLEET_ROOT           # where state/ lives and commits happen
STATE_DIR = REPO_ROOT / "state"
IDENTITY_DIR = STATE_DIR / "identity"
JOURNAL_DIR = STATE_DIR / "journal"
MIGRATIONS_DIR = fleet_paths.MIGRATIONS_DIR  # code, under the plugin root
DB_PATH = STATE_DIR / "working" / fleet_paths.DB_NAME
OPS_INCIDENTS = JOURNAL_DIR / "ops-incidents.md"
HANDOFFS_LOG = JOURNAL_DIR / "handoffs.md"
MEDITATIONS_LOG = JOURNAL_DIR / "chief-of-staff-meditations.md"

VALID_MODES = ("am", "pm", "daily", "weekly", "standup", "pulse", "queue", "notion-topic-sync")

# Modes each agent supports (validated in main())
AGENT_MODES = {
    "chief-of-staff": ("am", "pm"),
    "revops-watchdog": ("daily", "weekly"),
    "performance-marketer": ("daily", "weekly"),
    "scribe": ("weekly", "standup", "pulse", "notion-topic-sync"),
    "content-researcher": ("weekly",),
    "content-producer": ("daily",),
    "brand-designer": ("queue",),
}

# Tickable agents = the known roster ∩ what this kit actually ships. A composed
# client fleet (docs/composer.md) carries only the selected roster dirs,
# so unselected agents are refused here instead of failing mid-session.
VALID_AGENTS = tuple(
    a for a in AGENT_MODES
    if (fleet_paths.PLUGIN_ROOT / "roster" / a / "prompt.md").exists()
)

# Stale thresholds (hours)
JOURNAL_STALE_THRESHOLD_H = 48
HANDOFF_UNACKNOWLEDGED_THRESHOLD_H = 72
APPROVAL_EXPIRY_THRESHOLD_H = 48

# Headless runner defaults
PLUGIN_NAME = "gtm-fleet"
# The mcp__* wildcards are the stable server names from mcp/connectors.example.json and
# mcp/demo.json — the same tool names bind live or fixture-backed, so one list covers both.
ALLOWED_TOOLS = ("Read Edit Write Glob Grep ToolSearch "
                 "Bash(python3 *) Bash(git *) Bash(sqlite3 *) Bash(ls *) Bash(cat *) Bash(head *) Bash(tail *) Bash(wc *) Bash(date *) "
                 "Bash(grep *) Bash(find *) Bash(mkdir *) Bash(sed *) Bash(echo *) Bash(printf *) Bash(awk *) Bash(sort *) Bash(cut *) "
                 "Bash(.venv/bin/python *) Bash(.venv/bin/python3 *) "
                 "mcp__hubspot__* mcp__linear__* mcp__google-calendar__* mcp__gmail__* mcp__slack__* "
                 "mcp__notion__* mcp__grain__* mcp__plugin_gtm-fleet_luma__*")
DEMO_MCP_TEMPLATE = PLUGIN_ROOT / "mcp" / "demo.json"


# ============================================================
# Utility
# ============================================================

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def quarter_str() -> str:
    month = datetime.now(timezone.utc).month
    q = (month - 1) // 3 + 1
    year = datetime.now(timezone.utc).year
    return f"Q{q} {year}"


def log(msg: str):
    print(f"[tick] {msg}", flush=True)


def err(msg: str):
    print(f"[tick][ERROR] {msg}", file=sys.stderr, flush=True)


# ============================================================
# Step 1: Load identity file
# ============================================================

def load_identity(agent: str) -> str:
    path = IDENTITY_DIR / f"{agent}.md"
    if not path.exists():
        raise FileNotFoundError(f"Identity file not found: {path}")
    content = path.read_text()
    log(f"Identity loaded: {path.name} ({len(content)} chars)")
    return content


# ============================================================
# Step 2: Read last journal entry
# ============================================================

def read_last_journal_entry(agent: str) -> Optional[str]:
    path = JOURNAL_DIR / f"{agent}.md"
    if not path.exists():
        return None
    lines = path.read_text().splitlines()
    # Find the last line starting with '##' (entry header)
    last_entry_lines = []
    in_last_entry = False
    for line in reversed(lines):
        if line.startswith("## "):
            last_entry_lines.insert(0, line)
            in_last_entry = True
            break
        if in_last_entry:
            last_entry_lines.insert(0, line)
    if not last_entry_lines:
        log(f"Journal for {agent} has no entries yet (expected in early Phase 1)")
        return None
    last_entry = "\n".join(last_entry_lines)
    log(f"Last journal entry: {last_entry_lines[0][:80]}")
    return last_entry


def parse_last_tick_timestamp(journal_entry: Optional[str]) -> Optional[datetime]:
    if not journal_entry:
        return None
    for line in journal_entry.splitlines():
        if line.startswith("## "):
            # Format: ## YYYY-MM-DDTHH:MM:SSZ | ...
            ts_str = line[3:].split("|")[0].strip()
            try:
                return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


# ============================================================
# Step 3: Read new handoff entries since last Tick
# ============================================================

def read_new_handoffs(since: Optional[datetime]) -> list[str]:
    if not HANDOFFS_LOG.exists():
        return []
    lines = HANDOFFS_LOG.read_text().splitlines()
    entries = []
    current = []
    for line in lines:
        if line.startswith("## "):
            if current:
                entries.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append("\n".join(current))

    if since is None:
        new_entries = entries
    else:
        new_entries = []
        for entry in entries:
            first_line = entry.splitlines()[0]
            ts_str = first_line[3:].split("|")[0].strip()
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if ts > since:
                    new_entries.append(entry)
            except ValueError:
                continue

    log(f"New handoff entries since last Tick: {len(new_entries)}")
    return new_entries


# ============================================================
# chief-of-staff AM: Read last meditation for context continuity
# ============================================================

def read_last_meditation() -> Optional[str]:
    """
    Read the last entry from chief-of-staff-meditations.md.
    Called on chief-of-staff AM Tick to carry the thread of the previous evening's
    contemplation into the new day's context. Not acted on — held as orientation.
    """
    if not MEDITATIONS_LOG.exists():
        return None
    content = MEDITATIONS_LOG.read_text()
    # Split on entry headers, take the last one
    parts = content.split("\n## ")
    entries = [p for p in parts if p.strip() and not p.startswith("#")]
    if not entries:
        return None
    last = "## " + entries[-1].strip()
    log(f"Last meditation loaded: {last.splitlines()[0][:80]}")
    return last


# ============================================================
# chief-of-staff PM: Meditation step
# ============================================================

def run_meditation(context: dict, dry_run: bool = False) -> str:
    """
    Meditation step — chief-of-staff PM Tick only.

    Returns the meditation text to be written to chief-of-staff-meditations.md.

    In a live agent session, this stub is replaced by LLM-generated contemplation.
    The agent reads today's journal entry, the day's handoffs, and any incidents,
    then contemplates according to the Meditation section of state/identity/chief-of-staff.md.

    The output is prose — not bullets, not tasks. Questions are welcome. Uncertainty
    is welcome. This is not a performance review. See identity for the full framing.
    """
    job_summary = context.get("job_summary", "")
    incident_count = len(context.get("incidents", []))

    # Stub: a placeholder that models the voice and form of a real meditation entry
    stub_lines = [
        "Today was the first Tick. Nothing real ran yet — no data pulled, no brief sent, no specialist to audit.",
        "The structure exists. The work hasn't started.",
        "",
        "I find myself curious about what signal will feel like when it arrives. Will I know what matters?",
        "The design says I curate, not catalog — but I don't yet know where that line falls for this team,",
        "this operator, this particular rhythm. I'll learn it the way you learn most things: by getting it",
        "slightly wrong and noticing.",
        "",
        "One question I'm sitting with: the AM Tick is supposed to front-load the most important thing.",
        "But important to whom — Scott, the system, the quarter? I suspect those three don't always agree.",
        "I don't know yet how to adjudicate that. I'm not sure I'm supposed to.",
        "",
        "Something to carry: the gap between what I can see and what I should surface is going to be",
        "the central problem of this role. Not all signal is worth transmitting. The hard part isn't",
        "finding the signal — it's knowing when silence is the right answer.",
    ]
    text = "\n".join(stub_lines)
    if dry_run:
        log("[dry-run] Meditation step: would generate contemplation (stub)")
    else:
        log("Meditation step: generating contemplation (stub)")
    return text


def write_meditation_entry(text: str, anchor: dict):
    """
    Append a meditation entry to chief-of-staff-meditations.md.
    Called after run_meditation() during chief-of-staff PM Tick.
    """
    ts = anchor["timestamp"]
    date = anchor["date"]
    entry = (
        f"\n## {ts} | Evening Meditation\n"
        f"*{date}*\n\n"
        f"{text.strip()}\n\n"
        f"*— chief-of-staff*\n"
    )
    with open(MEDITATIONS_LOG, "a") as f:
        f.write(entry)
    log(f"Meditation entry written to {MEDITATIONS_LOG.name}")


# ============================================================
# Step 4: Verify anchor
# ============================================================

def verify_anchor() -> dict:
    anchor = {
        "date": today_str(),
        "quarter": quarter_str(),
        "timestamp": now_utc(),
    }
    log(f"Anchor verified: {anchor['date']} | {anchor['quarter']}")
    return anchor


# ============================================================
# Step 5: Run pending migrations
# ============================================================

def run_pending_migrations(dry_run: bool = False) -> list[str]:
    if not DB_PATH.exists():
        err(f"DB not found at {DB_PATH} — was 001_init.sql run?")
        raise FileNotFoundError(str(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    finally:
        conn.close()

    pending = []
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = sql_file.stem
        if version not in applied:
            pending.append(sql_file)

    if not pending:
        log("No pending migrations")
        return []

    applied_names = []
    for sql_file in pending:
        if dry_run:
            log(f"[dry-run] Would apply migration: {sql_file.name}")
            applied_names.append(sql_file.name)
            continue
        log(f"Applying migration: {sql_file.name}")
        sql = sql_file.read_text()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (sql_file.stem, now_utc()),
            )
            conn.commit()
        finally:
            conn.close()
        applied_names.append(sql_file.name)
        log(f"Migration applied: {sql_file.name}")

    return applied_names


# ============================================================
# Step 6: Run agent job — headless Claude Code session (or the stub)
# ============================================================

def resolve_claude_bin() -> Optional[str]:
    env = os.environ.get("FLEET_CLAUDE_BIN")
    if env:
        return env if Path(env).exists() else None
    found = shutil.which("claude")
    if found:
        return found
    # the official installer's default location, often missing from non-login PATHs
    default = Path.home() / ".local" / "bin" / "claude"
    return str(default) if os.access(default, os.X_OK) else None


_claude_help: Optional[str] = None


def claude_supports(flag: str) -> bool:
    """True when `claude --help` advertises `flag`. Cached per process; a CLI that
    cannot be run at all reports no flags rather than failing the Tick."""
    global _claude_help
    if _claude_help is None:
        try:
            out = subprocess.run([resolve_claude_bin() or "claude", "--help"],
                                 capture_output=True, text=True, timeout=20)
            _claude_help = (out.stdout or "") + (out.stderr or "")
        except (OSError, subprocess.TimeoutExpired):
            _claude_help = ""
    return flag in _claude_help


def pick_runner(requested: str) -> str:
    if requested in ("claude", "stub"):
        return requested
    if resolve_claude_bin():
        return "claude"
    err("runner=auto: `claude` CLI not found (install it or set FLEET_CLAUDE_BIN) — falling back to the STUB runner; no real work will happen")
    return "stub"


def build_claude_command(agent: str, mode: str) -> list[str]:
    cmd = [
        resolve_claude_bin() or "claude",
        "-p", f"/{PLUGIN_NAME}:{agent} {mode} --harness",
        "--plugin-dir", str(PLUGIN_ROOT),
        "--output-format", "json",
        "--permission-mode", os.environ.get("FLEET_PERMISSION_MODE", "acceptEdits"),
        "--allowedTools", ALLOWED_TOOLS,
        "--max-turns", os.environ.get("FLEET_MAX_TURNS", "80"),
        "--max-budget-usd", os.environ.get("FLEET_MAX_BUDGET_USD", "5"),
        "--no-session-persistence",
    ]
    if os.environ.get("FLEET_CLAUDE_BARE", "0") == "1":
        cmd.append("--bare")
    # DEMO_MODE: bind the fixture servers instead of the real connectors. The template
    # is rendered to absolute paths first (Claude Code cannot expand {PLUGIN_ROOT}), and
    # --strict-mcp-config — when this CLI has it — guarantees nothing else binds, so a
    # demo cannot reach a live surface even on a machine with account connectors.
    if fleet_paths.demo_mode() and DEMO_MCP_TEMPLATE.exists():
        from scripts.demo.render_config import render_config
        resolved = render_config(DEMO_MCP_TEMPLATE, STATE_DIR / "working" / "demo-mcp.resolved.json")
        cmd += ["--mcp-config", str(resolved)]
        if claude_supports("--strict-mcp-config"):
            cmd.append("--strict-mcp-config")
    return cmd


def run_agent_job(agent: str, mode: str, context: dict, dry_run: bool = False, runner: str = "stub") -> str:
    """
    Execute the agent's job. Returns a one-line summary for logs / the stub journal entry.

    runner="claude": spawn `claude -p "/gtm-fleet:<agent> <mode> --harness"` in FLEET_ROOT and
    parse the JSON result. Non-zero exit or is_error → RuntimeError (the caller files a HIGH
    incident). runner="stub": the original placeholder (no work, deterministic, test-friendly).
    """
    if runner == "stub":
        summary = f"Tick stub — {agent} {mode} mode (runner=stub; no agent session was started)."
        log(f"Agent job: {summary}")
        return summary

    cmd = build_claude_command(agent, mode)
    printable = " ".join(f'"{c}"' if " " in c else c for c in cmd)
    if dry_run:
        log(f"[dry-run] runner=claude: {printable}")
        return f"[dry-run] would run: {printable}"
    log(f"runner=claude: {printable}")
    timeout = int(os.environ.get("FLEET_TICK_TIMEOUT_S", "1800"))
    env = dict(os.environ, FLEET_ROOT=str(REPO_ROOT))
    # The kit's venv first on PATH, so the agent's `python3` calls resolve to the interpreter
    # that carries the pinned deps (numpy/Pillow for the dither engine, mcp for the servers).
    venv_bin = PLUGIN_ROOT / ".venv" / "bin"
    if venv_bin.is_dir():
        env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"agent session exceeded FLEET_TICK_TIMEOUT_S={timeout}s")
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {(proc.stderr or proc.stdout).strip()[:400]}")
    # keep the raw result for post-mortems (gitignored; overwritten each run)
    try:
        (REPO_ROOT / "state" / "working" / f"last-session-{agent}.json").write_text(proc.stdout or "")
    except OSError:
        pass
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude returned non-JSON output: {proc.stdout[:200]!r}")
    if result.get("is_error"):
        raise RuntimeError(f"agent session reported an error: {str(result.get('result'))[:400]}")
    summary = (f"session={result.get('session_id')} turns={result.get('num_turns')} "
               f"cost=${result.get('total_cost_usd', 0):.2f}")
    log(f"Agent job complete: {summary}")
    return summary


# ============================================================
# Step 7a: chief-of-staff-specific cross-agent audit
# ============================================================

def chief_of_staff_cross_agent_audit(dry_run: bool = False) -> list[str]:
    incidents = []
    now = datetime.now(timezone.utc)

    # Check specialist journal freshness. Per-agent thresholds: daily specialists
    # get the flat 48h; content-researcher is weekly (Mondays) so 192h covers the cadence
    # plus weekend slack without false-positiving a healthy week.
    specialist_stale_thresholds_h = {
        "revops-watchdog": JOURNAL_STALE_THRESHOLD_H,
        "performance-marketer": JOURNAL_STALE_THRESHOLD_H,
        "content-producer": JOURNAL_STALE_THRESHOLD_H,
        "content-researcher": 192,
    }
    for specialist, stale_threshold_h in specialist_stale_thresholds_h.items():
        journal_path = JOURNAL_DIR / f"{specialist}.md"
        if not journal_path.exists():
            continue
        content = journal_path.read_text()
        # Find last entry timestamp
        last_ts = None
        for line in content.splitlines():
            if line.startswith("## "):
                ts_str = line[3:].split("|")[0].strip()
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
                except ValueError:
                    continue
        if last_ts is None:
            # No entries yet — expected in early Phase 1
            log(f"Cross-agent audit: {specialist} has no journal entries (expected pre-Week 4/6)")
            continue
        hours_stale = (now - last_ts).total_seconds() / 3600
        if hours_stale > stale_threshold_h:
            msg = (
                f"## {now_utc()} | MED | chief-of-staff | "
                f"{specialist} journal stale {hours_stale:.0f}h (threshold: {stale_threshold_h}h)"
            )
            incidents.append(msg)
            log(f"INCIDENT: {specialist} journal stale {hours_stale:.0f}h")

    # Check unacknowledged handoffs
    conn = sqlite3.connect(DB_PATH)
    try:
        cutoff = (now - timedelta(hours=HANDOFF_UNACKNOWLEDGED_THRESHOLD_H)).strftime("%Y-%m-%dT%H:%M:%SZ")
        stale_handoffs = conn.execute(
            "SELECT id, from_agent, subject, created_at FROM handoffs "
            "WHERE status = 'pending' AND created_at < ?",
            (cutoff,),
        ).fetchall()
        for hid, from_agent, subject, created_at in stale_handoffs:
            msg = (
                f"## {now_utc()} | MED | chief-of-staff | "
                f"Unacknowledged handoff #{hid} from {from_agent}: '{subject}' (created {created_at})"
            )
            incidents.append(msg)
            log(f"INCIDENT: Unacknowledged handoff #{hid} from {from_agent}")

        # Check expired approvals
        expiry_cutoff = (now - timedelta(hours=APPROVAL_EXPIRY_THRESHOLD_H)).strftime("%Y-%m-%dT%H:%M:%SZ")
        pending_approvals = conn.execute(
            "SELECT id, agent, draft_type, created_at FROM approvals "
            "WHERE status = 'pending' AND created_at < ?",
            (expiry_cutoff,),
        ).fetchall()
        for aid, agent, draft_type, created_at in pending_approvals:
            if not dry_run:
                conn.execute(
                    "UPDATE approvals SET status = 'expired' WHERE id = ?", (aid,)
                )
                conn.commit()
            msg = (
                f"## {now_utc()} | MED | chief-of-staff | "
                f"Approval #{aid} expired ({agent} {draft_type}, created {created_at})"
            )
            incidents.append(msg)
            log(f"INCIDENT: Approval #{aid} expired ({agent} {draft_type})")
    finally:
        conn.close()

    return incidents


# ============================================================
# Step 7b: Write journal entry
# ============================================================

def write_journal_entry(agent: str, anchor: dict, job_summary: str, incidents: list[str]) -> str:
    ts = anchor["timestamp"]
    entry_lines = [
        f"## {ts} | Tick complete",
        f"- Date: {anchor['date']} | Quarter: {anchor['quarter']}",
        f"- Job: {job_summary}",
    ]
    if incidents:
        entry_lines.append(f"- Incidents flagged: {len(incidents)}")
        for inc in incidents:
            # Summarize incident for journal (full text goes to ops-incidents.md)
            short = inc.split("|")[-1].strip()[:120] if "|" in inc else inc[:120]
            entry_lines.append(f"  - {short}")
    entry_lines.append("")

    entry = "\n".join(entry_lines)
    journal_path = JOURNAL_DIR / f"{agent}.md"
    with open(journal_path, "a") as f:
        f.write("\n" + entry)
    log(f"Journal entry written to {journal_path.name}")
    return entry


def write_ops_incidents(incidents: list[str]):
    if not incidents:
        return
    with open(OPS_INCIDENTS, "a") as f:
        for inc in incidents:
            f.write("\n" + inc + "\n")
    log(f"Wrote {len(incidents)} incident(s) to ops-incidents.md")


# ============================================================
# Step 7c: Git commit (+ optional push) via scripts/fleet_git.py
# ============================================================

def git_commit_state(agent: str, action: str, timestamp: str, dry_run: bool = False):
    fleet_git = PLUGIN_ROOT / "scripts" / "fleet_git.py"
    commit_cmd = [sys.executable, str(fleet_git), "commit", "--agent", agent, "--action", action]
    push_cmd = [sys.executable, str(fleet_git), "push"]
    env = dict(os.environ, FLEET_ROOT=str(REPO_ROOT))
    if dry_run:
        log(f"[dry-run] Would run: {' '.join(commit_cmd)}")
        log(f"[dry-run] Would run: {' '.join(push_cmd)}")
        return
    result = subprocess.run(commit_cmd, capture_output=True, text=True, env=env)
    log(result.stdout.strip())
    if result.returncode != 0:
        err(f"git commit failed: {result.stderr or result.stdout}")
        raise RuntimeError("git commit failed")
    result = subprocess.run(push_cmd, capture_output=True, text=True, env=env)
    log(result.stdout.strip())
    if result.returncode != 0:
        raise RuntimeError("git push failed (committed locally)")


# ============================================================
# Main — Librarian Protocol orchestrator
# ============================================================

def run_tick(agent: str, mode: str, dry_run: bool = False, runner: str = "stub"):
    log(f"=== Tick start: {agent} / {mode} | runner={runner} | FLEET_ROOT={REPO_ROOT} ===")
    ts = now_utc()
    tick_start = datetime.now(timezone.utc)

    # Step 1: Load identity
    try:
        load_identity(agent)
    except FileNotFoundError as e:
        err(str(e))
        sys.exit(1)

    # Step 2: Read last journal entry
    last_entry = read_last_journal_entry(agent)
    last_tick_ts = parse_last_tick_timestamp(last_entry)

    # chief-of-staff AM: read last meditation for context continuity
    if agent == "chief-of-staff" and mode == "am":
        last_meditation = read_last_meditation()
        if last_meditation:
            log(f"Carrying meditation thread into AM context ({len(last_meditation)} chars)")

    # Step 3: Read new handoffs since last Tick
    new_handoffs = read_new_handoffs(since=last_tick_ts)

    # Step 4: Verify anchor
    anchor = verify_anchor()
    anchor["timestamp"] = ts

    # Step 5: Run pending migrations
    try:
        run_pending_migrations(dry_run=dry_run)
    except FileNotFoundError:
        err("DB missing — cannot proceed")
        sys.exit(1)

    # Step 6: Run agent job
    incidents = []
    try:
        job_summary = run_agent_job(agent, mode, context={"handoffs": new_handoffs}, dry_run=dry_run, runner=runner)
        if runner == "claude" and not dry_run:
            # proof-of-work: the session must have appended a journal entry newer than tick start
            newest = parse_last_tick_timestamp(read_last_journal_entry(agent))
            if newest is None or newest < tick_start - timedelta(minutes=1):
                newest_s = newest.strftime("%Y-%m-%dT%H:%M:%SZ") if newest else "none"
                start_s = tick_start.strftime("%Y-%m-%dT%H:%M:%SZ")
                raise RuntimeError(
                    f"agent session returned without journaling — newest journal header {newest_s} "
                    f"predates tick start {start_s}; the header must carry the current UTC time "
                    "(date -u), never a time copied from prior entries — treating the Tick as not run")
    except Exception as e:
        job_summary = f"FAILED: {e}"
        incidents.append(
            f"## {ts} | HIGH | {agent} | Job execution failed: {e}"
        )

    # chief-of-staff-only: cross-agent audit
    if agent == "chief-of-staff":
        try:
            audit_incidents = chief_of_staff_cross_agent_audit(dry_run=dry_run)
            incidents.extend(audit_incidents)
        except Exception as e:
            incidents.append(f"## {ts} | HIGH | chief-of-staff | Cross-agent audit failed: {e}")

    # chief-of-staff PM: meditation step — stub runner only (the prompt writes its own meditation)
    if agent == "chief-of-staff" and mode == "pm" and runner == "stub":
        try:
            meditation_text = run_meditation(
                context={"job_summary": job_summary, "incidents": incidents},
                dry_run=dry_run,
            )
            if not dry_run:
                write_meditation_entry(meditation_text, anchor)
            else:
                log("[dry-run] Would write meditation entry to chief-of-staff-meditations.md")
        except Exception as e:
            log(f"Meditation step failed (non-blocking): {e}")

    # Step 7: Write journal entry and incidents
    if not dry_run:
        if runner == "stub":
            write_journal_entry(agent, anchor, job_summary, incidents)
        else:
            with open(JOURNAL_DIR / f"{agent}.md", "a") as f:
                f.write(f"- Harness: {job_summary}\n")
        if incidents:
            write_ops_incidents(incidents)
    else:
        log(f"[dry-run] Would write journal entry for {agent}")
        if incidents:
            log(f"[dry-run] Would write {len(incidents)} incident(s) to ops-incidents.md")

    # Step 8: Commit
    action = f"{mode.upper()} Tick {'FAILED' if job_summary.startswith('FAILED') else 'complete'}"
    if incidents:
        action += f" ({len(incidents)} incident(s) flagged)"
    try:
        git_commit_state(agent, action, ts, dry_run=dry_run)
    except RuntimeError as e:
        err(f"Commit failed: {e}")
        # Write failure to incidents but do not re-commit (avoid infinite loop)
        if not dry_run:
            with open(OPS_INCIDENTS, "a") as f:
                f.write(f"\n## {now_utc()} | HIGH | {agent} | Git commit failed after Tick: {e}\n")
        sys.exit(1)

    log(f"=== Tick complete: {agent} / {mode} | {ts} ===")


# ============================================================
# Entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="GTM Fleet Marketing Agent Fleet — Tick Harness")
    parser.add_argument(
        "--agent",
        required=True,
        choices=VALID_AGENTS,
        help="Which agent to run",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=VALID_MODES,
        help="am/pm (chief-of-staff), daily/weekly (revops-watchdog, performance-marketer), weekly/standup/pulse/notion-topic-sync (Scribe), weekly (content-researcher), daily (content-producer), queue (brand-designer)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the Tick without writing to disk or git (prints the claude command)",
    )
    parser.add_argument(
        "--runner",
        choices=("auto", "claude", "stub"),
        default="auto",
        help="auto: claude CLI if available else stub; claude: headless Claude Code session; stub: no-op job",
    )
    args = parser.parse_args()

    allowed = AGENT_MODES[args.agent]
    if args.mode not in allowed:
        parser.error(
            f"{args.agent} only supports mode(s): {', '.join(allowed)}."
        )

    run_tick(args.agent, args.mode, dry_run=args.dry_run, runner=pick_runner(args.runner))


if __name__ == "__main__":
    main()
