#!/usr/bin/env python3
"""Handoff lifecycle CLI — the operator's ack signal.

Usage:
  python3 scripts/handoffs.py list
  python3 scripts/handoffs.py ack revops-watchdog_handoff_01j9x8k2p7_a3f2z9 [--note "reviewed"]
  python3 scripts/handoffs.py resolve 90 [--note "thresholds recalibrated"]

Handoff ids are text (minted via scripts/ids.py); legacy integer ids still work as
their string form (e.g. `resolve 90`).

Updates the handoffs table in state/working/fleet.db and appends a
matching entry to state/journal/handoffs.md so journal readers see the change.
Protocol: docs/conventions.md -> Handoff Lifecycle.
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402

ROOT = fleet_paths.FLEET_ROOT
DB = fleet_paths.DB_PATH
JOURNAL = fleet_paths.JOURNAL_DIR / "handoffs.md"


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_list(con, args):
    rows = con.execute(
        "SELECT id, severity, status, from_agent, to_agent, created_at, subject"
        " FROM handoffs WHERE status != 'resolved'"
        " ORDER BY CASE severity WHEN 'HIGH' THEN 0 WHEN 'MED' THEN 1 ELSE 2 END,"
        " created_at"
    ).fetchall()
    if not rows:
        print("No open handoffs.")
        return
    for hid, sev, status, src, dst, created, subject in rows:
        print(f"[{sev:<4}] id={hid:<4} {status:<12} {src}->{dst}  {created}  {subject}")


def cmd_update(con, args, status):
    ts = utcnow()
    stamp_col = "acknowledged_at" if status == "acknowledged" else "resolved_at"
    lines = []
    for hid in args.ids:
        row = con.execute(
            "SELECT severity, subject FROM handoffs WHERE id = ?", (hid,)
        ).fetchone()
        if row is None:
            sys.exit(f"handoff id={hid} not found")
        con.execute(
            f"UPDATE handoffs SET status = ?, {stamp_col} = ? WHERE id = ?",
            (status, ts, hid),
        )
        lines.append(f"- id={hid} [{row[0]}] -> {status}: {row[1]}")
    con.commit()

    ids = ",".join(str(i) for i in args.ids)
    entry = [f"\n## {ts} | {args.actor} → fleet | Handoff {status}: id={ids}", ""]
    entry.extend(lines)
    if args.note:
        entry.append(f"- Note: {args.note}")
    with open(JOURNAL, "a") as f:
        f.write("\n".join(entry) + "\n")
    print(f"{len(args.ids)} handoff(s) marked {status}; journal entry appended.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="show all non-resolved handoffs")
    for name, help_text in (
        ("ack", "mark handoffs acknowledged (seen, work may remain open)"),
        ("resolve", "mark handoffs resolved (underlying issue closed)"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("ids", nargs="+", type=str)
        p.add_argument("--note", help="appended to the journal entry")
        p.add_argument("--actor", default="Scott", help="who is signing the change")

    args = parser.parse_args()
    con = sqlite3.connect(DB)
    if args.command == "list":
        cmd_list(con, args)
    else:
        cmd_update(con, args, "acknowledged" if args.command == "ack" else "resolved")


if __name__ == "__main__":
    main()
