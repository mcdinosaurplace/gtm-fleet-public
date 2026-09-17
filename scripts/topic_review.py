#!/usr/bin/env python3
"""Apply a human review decision on a content topic to local state.

the head of marketing reviews content-researcher's topic backlog in Notion (Marketing -> Content Engine ->
Topic Backlog). Scribe owns the Notion I/O; this script owns what a decision
*means* for local state, so the semantics live in one place instead of being
re-derived by whichever agent happens to be holding the Notion connector.

Why a shared script rather than Scribe writing the table directly:
`topic_backlog` is content-researcher's, and the fleet takes that boundary seriously
(content-producer:brief-builder is explicitly forbidden from writing it). But routing
decisions through content-researcher's weekly Monday tick would mean a Tuesday approval
waits until the following Monday before content-producer could build against it. This script
is the compromise the repo already uses elsewhere (scripts/pm/ cores,
scripts/handoffs.py): a deterministic mutator that encodes the owning agent's
rules, invoked by whoever has the connector. content-researcher still reads the outcomes
on its own tick for scoring calibration and needs_edit re-synthesis.

Status mapping (Notion -> topic_backlog.status):
    Approved        -> approved      (also stamps approved_at)
    Needs revision  -> needs_edit    (Comments land in review_notes as instruction)
    Rejected        -> rejected      (Comments land in review_notes for calibration)

Anything else in Notion's Status (Pending review, Candidate, Briefed, Published,
Refresh) is not a human review decision and is rejected by this script — those
transitions are agent-owned and flow repo -> Notion, not the other way.

Idempotency: re-applying the same decision is a no-op that reports "unchanged",
so a sync that runs on every Scribe tick will not churn state or stack duplicate
approvals rows.

Usage:
  python3 scripts/topic_review.py apply --uid <topic_uid> --status "Approved" \
      [--comments "..."] [--approver mark] [--notion-page-id <id>]

  python3 scripts/topic_review.py apply --json '[{"uid": "...", "status": "Approved",
      "comments": "...", "notion_page_id": "..."}, ...]'

  python3 scripts/topic_review.py pending      # topics awaiting a decision

Exit codes: 0 success (including no-op), 1 nothing matched, 2 bad input.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402

DB_PATH = str(fleet_paths.DB_PATH)

# Notion Status value -> (topic_backlog.status, approvals.status)
DECISION_MAP = {
    "Approved": ("approved", "approved"),
    "Needs revision": ("needs_edit", "needs_edit"),
    "Rejected": ("rejected", "rejected"),
}

# Statuses that are agent-owned and must never be pulled back from Notion.
AGENT_OWNED = {"Pending review", "Candidate", "Briefed", "Published", "Refresh"}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def apply_decision(conn, uid, notion_status, comments=None, approver="mark",
                   notion_page_id=None):
    """Apply one decision. Returns a result dict; never partially commits."""
    if notion_status in AGENT_OWNED:
        return {"uid": uid, "result": "skipped_agent_owned", "status": notion_status}
    if notion_status not in DECISION_MAP:
        raise ValueError(
            f"{notion_status!r} is not a review decision. "
            f"Expected one of {sorted(DECISION_MAP)}"
        )

    repo_status, approval_status = DECISION_MAP[notion_status]
    comments = (comments or "").strip() or None

    cur = conn.cursor()
    cur.execute(
        "SELECT id, topic, status, review_notes FROM topic_backlog WHERE topic_uid = ?",
        (uid,),
    )
    row = cur.fetchone()
    if row is None:
        return {"uid": uid, "result": "no_match"}

    # Already in this exact state -> no-op. Keeps a per-tick sync from churning.
    if row["status"] == repo_status and (row["review_notes"] or None) == comments:
        return {"uid": uid, "result": "unchanged", "topic": row["topic"],
                "status": repo_status}

    now = _now()
    approved_at = now if repo_status == "approved" else None

    cur.execute(
        """UPDATE topic_backlog
              SET status = ?, review_notes = ?, approved_at = COALESCE(?, approved_at),
                  notion_page_id = COALESCE(?, notion_page_id)
            WHERE topic_uid = ?""",
        (repo_status, comments, approved_at, notion_page_id, uid),
    )

    # One approvals row per decision, as the Tier 2 gate record.
    cur.execute(
        """INSERT INTO approvals (agent, tier, draft_type, draft_content, draft_path,
                                  approver, approved_at, status, edit_notes, created_at)
           VALUES ('content-researcher', 2, 'topic_backlog', ?, ?, ?, ?, ?, ?, ?)""",
        (
            row["topic"],
            f"notion://{notion_page_id}" if notion_page_id else None,
            approver,
            now,
            approval_status,
            comments,
            now,
        ),
    )
    conn.commit()
    return {
        "uid": uid,
        "result": "applied",
        "topic": row["topic"],
        "from_status": row["status"],
        "status": repo_status,
        "approvals_id": cur.lastrowid,
        "has_notes": bool(comments),
    }


def list_pending(conn):
    """Topics that are synced to Notion and still awaiting a human decision."""
    cur = conn.cursor()
    cur.execute(
        """SELECT topic_uid, topic, score_total, evidence_sources, status, notion_page_id
             FROM topic_backlog
            WHERE status IN ('submitted', 'candidate', 'refresh')
            ORDER BY score_total DESC"""
    )
    return [dict(r) for r in cur.fetchall()]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["apply", "pending"])
    parser.add_argument("--uid", help="topic_backlog.topic_uid")
    parser.add_argument("--status", help='Notion Status value, e.g. "Approved"')
    parser.add_argument("--comments", default=None, help="the head of marketing's Comments text")
    parser.add_argument("--approver", default="mark")
    parser.add_argument("--notion-page-id", default=None)
    parser.add_argument("--json", dest="json_payload", default=None,
                        help="JSON array of decisions for batch apply")
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args()

    conn = _connect(args.db)
    try:
        if args.command == "pending":
            rows = list_pending(conn)
            print(json.dumps(rows, indent=2))
            return 0

        if args.json_payload:
            try:
                decisions = json.loads(args.json_payload)
            except json.JSONDecodeError as e:
                print(f"error: --json is not valid JSON: {e}", file=sys.stderr)
                return 2
            if not isinstance(decisions, list):
                print("error: --json must be an array of decision objects", file=sys.stderr)
                return 2
        elif args.uid and args.status:
            decisions = [{
                "uid": args.uid,
                "status": args.status,
                "comments": args.comments,
                "notion_page_id": args.notion_page_id,
            }]
        else:
            print("error: apply needs either --json or both --uid and --status",
                  file=sys.stderr)
            return 2

        results = []
        for d in decisions:
            if not d.get("uid") or not d.get("status"):
                print(f"error: decision missing uid or status: {d!r}", file=sys.stderr)
                return 2
            try:
                results.append(apply_decision(
                    conn,
                    d["uid"],
                    d["status"],
                    comments=d.get("comments"),
                    approver=d.get("approver", args.approver),
                    notion_page_id=d.get("notion_page_id"),
                ))
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 2

        print(json.dumps(results, indent=2))
        return 0 if any(r["result"] != "no_match" for r in results) else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
