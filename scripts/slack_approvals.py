#!/usr/bin/env python3
"""
Slack draft-and-approve module — GTM Fleet Marketing Agent Fleet.

Handles Tier 2 approval flows via Slack thread replies. Agents post drafts,
Scott replies 'approve', 'reject', or pastes edits. This module posts, polls,
logs, and handles timeouts.

Approval keywords (case-insensitive):
    approve  → status=approved
    reject   → status=rejected
    anything else → status=needs_edit (edit text captured)

Usage (standalone smoke test):
    python3 scripts/slack_approvals.py \\
        --test-post \\
        --channel "#marketing-agent-approvals" \\
        --agent revops-watchdog \\
        --draft-type ops_summary

    python3 scripts/slack_approvals.py \\
        --test-poll \\
        --thread-ts 1713123456.000100 \\
        --channel "#marketing-agent-approvals"

    python3 scripts/slack_approvals.py \\
        --check-expired

Design:
    - Drafts are posted to Slack and tracked in the SQLite `approvals` table.
    - The module does NOT use a long-running process or webhook listener.
    - Polling happens on each chief-of-staff AM Tick (via check_expired() + poll_pending()).
    - The Slack MCP is called directly from Claude Code context; this module
      provides the logic and DB state management that wraps those calls.

Note on Slack MCP:
    This module is designed to be called from within a Claude Code / Cowork agent
    session that has the Slack MCP available. The _slack_send() and _slack_read_thread()
    functions below are stubs that describe the MCP calls to make. In a live agent
    session, replace them with direct MCP tool calls.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402
from typing import Optional


# ============================================================
# Config
# ============================================================

REPO_ROOT = fleet_paths.FLEET_ROOT
DB_PATH = fleet_paths.DB_PATH
OPS_INCIDENTS = fleet_paths.JOURNAL_DIR / "ops-incidents.md"

APPROVAL_EXPIRY_H = 48
DEFAULT_CHANNEL = "#marketing-agent-approvals"

APPROVE_KEYWORDS = ("approve", "approved", "lgtm", "yes", "ship it")
REJECT_KEYWORDS = ("reject", "rejected", "no", "don't", "stop")


# ============================================================
# Data structures
# ============================================================

class ApprovalResult:
    def __init__(
        self,
        approval_id: int,
        status: str,
        approver: Optional[str] = None,
        edit_notes: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        self.approval_id = approval_id
        self.status = status
        self.approver = approver
        self.edit_notes = edit_notes
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return (
            f"ApprovalResult(id={self.approval_id}, status={self.status}, "
            f"approver={self.approver}, timestamp={self.timestamp})"
        )


# ============================================================
# Utility
# ============================================================

def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str):
    print(f"[approvals] {msg}", flush=True)


def err(msg: str):
    print(f"[approvals][ERROR] {msg}", file=sys.stderr, flush=True)


def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# Slack MCP interface stubs
#
# In a live Claude Code / Cowork agent session, these are replaced
# by direct MCP tool calls:
#
#   _slack_send(channel, text)
#       → mcp__slack__send_message(channel_id=channel, text=text)
#
#   _slack_read_thread(channel, thread_ts)
#       → mcp__slack__read_thread(channel_id=channel, thread_ts=thread_ts)
#
# These stubs print the call so the agent knows what MCP tool to invoke.
# ============================================================

def _slack_send(channel: str, text: str) -> str:
    """
    Post a message to Slack. Returns a thread_ts string.

    In a live agent session, replace with:
        result = mcp__slack__send_message(channel_id=channel, text=text)
        return result["ts"]
    """
    log(f"[MCP CALL] slack_send_message(channel={channel})")
    log(f"[MCP CALL] Message preview: {text[:120]}...")
    # Stub: return a fake thread_ts for testing
    fake_ts = f"{int(datetime.now(timezone.utc).timestamp())}.000100"
    log(f"[MCP STUB] Fake thread_ts: {fake_ts}")
    return fake_ts


def _slack_read_thread(channel: str, thread_ts: str) -> list:
    """
    Read replies in a Slack thread. Returns list of message dicts.

    In a live agent session, replace with:
        result = mcp__slack__read_thread(channel_id=channel, thread_ts=thread_ts)
        return result["messages"]

    Each message dict should include:
        {
          "ts": "1713...",
          "user": "U12345",
          "text": "approve",
          "type": "message"
        }
    """
    log(f"[MCP CALL] slack_read_thread(channel={channel}, thread_ts={thread_ts})")
    # Stub: return empty replies
    return []


# ============================================================
# Draft posting
# ============================================================

def _format_draft_message(agent: str, draft_type: str, draft_content: str, draft_path: Optional[str]) -> str:
    ts = now_utc()
    path_note = f"\n*Draft file:* `{draft_path}`" if draft_path else ""
    return (
        f":robot_face: *{agent.capitalize()} Draft — {draft_type.replace('_', ' ').title()}*\n"
        f"_Submitted: {ts}_\n"
        f"{path_note}\n\n"
        f"```\n{draft_content[:2000]}\n```\n\n"
        f"_Reply with *approve*, *reject*, or paste your edits to update this draft._"
    )


def post_draft(
    agent: str,
    draft_type: str,
    draft_content: str,
    channel: str = DEFAULT_CHANNEL,
    draft_path: Optional[str] = None,
    tier: int = 2,
) -> ApprovalResult:
    """
    Post a draft to Slack and create a pending approval record in the DB.

    Returns an ApprovalResult with status='pending' and the new approval_id.
    """
    message = _format_draft_message(agent, draft_type, draft_content, draft_path)

    thread_ts = _slack_send(channel, message)
    ts = now_utc()

    conn = db_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO approvals
                (agent, tier, draft_type, draft_content, draft_path,
                 slack_channel, slack_thread_ts, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (agent, tier, draft_type, draft_content[:4000], draft_path,
             channel, thread_ts, ts),
        )
        conn.commit()
        approval_id = cursor.lastrowid
    finally:
        conn.close()

    log(f"Draft posted: approval #{approval_id} | {agent} {draft_type} | thread_ts={thread_ts}")
    return ApprovalResult(approval_id=approval_id, status="pending", timestamp=ts)


# ============================================================
# Thread-reply polling
# ============================================================

def _parse_reply(text: str, user: str) -> tuple:
    """
    Parse a Slack reply into (status, edit_notes).
    Returns ('approved', None), ('rejected', None), or ('needs_edit', text).
    """
    normalized = text.strip().lower()
    for kw in APPROVE_KEYWORDS:
        if normalized == kw or normalized.startswith(kw + " "):
            return "approved", None
    for kw in REJECT_KEYWORDS:
        if normalized == kw or normalized.startswith(kw + " ") or normalized.startswith(kw + ","):
            return "rejected", None
    # Anything else is treated as an edit
    return "needs_edit", text.strip()


def poll_approval(approval_id: int) -> Optional[ApprovalResult]:
    """
    Poll Slack thread for a reply on an existing pending approval.
    Returns an ApprovalResult if a reply was found, None if still pending.
    """
    conn = db_conn()
    try:
        row = conn.execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        err(f"Approval #{approval_id} not found in DB")
        return None

    if row["status"] != "pending":
        log(f"Approval #{approval_id} already resolved: {row['status']}")
        return ApprovalResult(
            approval_id=approval_id,
            status=row["status"],
            approver=row["approver"],
            edit_notes=row["edit_notes"],
            timestamp=row["approved_at"],
        )

    channel = row["slack_channel"]
    thread_ts = row["slack_thread_ts"]

    replies = _slack_read_thread(channel, thread_ts)
    if not replies:
        log(f"Approval #{approval_id}: no replies yet")
        return None

    # Process replies in chronological order; last one wins
    final_status = None
    final_user = None
    final_edit_notes = None
    final_ts = None

    for reply in replies:
        msg_ts = reply.get("ts", "")
        # Skip the original post (same ts as thread_ts)
        if msg_ts == thread_ts:
            continue
        text = reply.get("text", "")
        user = reply.get("user", "unknown")
        status, edit_notes = _parse_reply(text, user)
        final_status = status
        final_user = user
        final_edit_notes = edit_notes
        final_ts = now_utc()

    if final_status is None:
        log(f"Approval #{approval_id}: replies present but none are actionable yet")
        return None

    log(f"Approval #{approval_id}: {final_status} by {final_user}")
    return log_approval(
        ApprovalResult(
            approval_id=approval_id,
            status=final_status,
            approver=final_user,
            edit_notes=final_edit_notes,
            timestamp=final_ts,
        )
    )


# ============================================================
# Approval state tracker
# ============================================================

def log_approval(result: ApprovalResult) -> ApprovalResult:
    """
    Write a final (approved/rejected/needs_edit) result to the approvals table.
    """
    conn = db_conn()
    try:
        conn.execute(
            """
            UPDATE approvals
            SET status = ?, approver = ?, approved_at = ?, edit_notes = ?
            WHERE id = ?
            """,
            (result.status, result.approver, result.timestamp, result.edit_notes, result.approval_id),
        )
        conn.commit()
    finally:
        conn.close()
    log(f"Approval #{result.approval_id} logged: {result.status}")
    return result


def get_pending_approvals() -> list:
    """
    Return all approvals with status='pending', ordered by created_at ascending.
    """
    conn = db_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status = 'pending' ORDER BY created_at ASC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ============================================================
# Timeout handler
# ============================================================

def check_expired(hours: int = APPROVAL_EXPIRY_H) -> list:
    """
    Find pending approvals older than `hours` and mark them expired.
    Appends an entry to ops-incidents.md for each expired approval.
    Returns list of expired approval IDs.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = db_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status = 'pending' AND created_at < ?",
            (cutoff,),
        ).fetchall()
        expired = [dict(row) for row in rows]
        if not expired:
            log("No expired approvals")
            return []

        for row in expired:
            conn.execute(
                "UPDATE approvals SET status = 'expired' WHERE id = ?", (row["id"],)
            )
        conn.commit()
    finally:
        conn.close()

    incident_lines = []
    for row in expired:
        line = (
            f"## {now_utc()} | MED | chief-of-staff | "
            f"Approval #{row['id']} expired after {hours}h — "
            f"{row['agent']} {row['draft_type']} (created {row['created_at']})"
        )
        incident_lines.append(line)
        log(f"Expired: approval #{row['id']} ({row['agent']} {row['draft_type']})")

    if incident_lines:
        with open(OPS_INCIDENTS, "a") as f:
            for line in incident_lines:
                f.write("\n" + line + "\n")
        log(f"Wrote {len(incident_lines)} expiry incident(s) to ops-incidents.md")

    return [row["id"] for row in expired]


def poll_all_pending() -> list:
    """
    Poll Slack for replies on all pending approvals.
    Called by chief-of-staff AM Tick.
    Returns list of ApprovalResults for resolved items.
    """
    pending = get_pending_approvals()
    if not pending:
        log("No pending approvals to poll")
        return []

    resolved = []
    for row in pending:
        result = poll_approval(row["id"])
        if result and result.status != "pending":
            resolved.append(result)

    log(f"Polled {len(pending)} pending approval(s); {len(resolved)} resolved")
    return resolved


# ============================================================
# Standalone smoke test entry points
# ============================================================

def cmd_test_post(channel: str, agent: str, draft_type: str):
    content = (
        f"This is a test draft from {agent} ({draft_type}).\n\n"
        "Reply 'approve' to approve, 'reject' to reject, or paste edits.\n\n"
        "Generated: " + now_utc()
    )
    result = post_draft(
        agent=agent,
        draft_type=draft_type,
        draft_content=content,
        channel=channel,
    )
    print(f"\nDraft posted. Approval ID: {result.approval_id}")
    print(f"Status: {result.status}")
    print(f"\nTo poll for a reply, run:")
    print(f"  python3 scripts/slack_approvals.py --test-poll --approval-id {result.approval_id}")


def cmd_test_poll(approval_id: int):
    result = poll_approval(approval_id)
    if result is None:
        print(f"Approval #{approval_id}: still pending (no actionable reply found)")
    else:
        print(f"\nApproval #{approval_id}: {result.status}")
        print(f"  Approver: {result.approver}")
        print(f"  Timestamp: {result.timestamp}")
        if result.edit_notes:
            print(f"  Edit notes: {result.edit_notes}")


def cmd_check_expired():
    expired_ids = check_expired()
    if expired_ids:
        print(f"Marked {len(expired_ids)} approval(s) as expired: {expired_ids}")
    else:
        print("No expired approvals found")


# ============================================================
# Entry point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Slack draft-and-approve module — GTM Fleet Marketing Agent Fleet"
    )
    subparsers = parser.add_subparsers(dest="command")

    # --test-post
    post_parser = subparsers.add_parser("post", help="Post a test draft to Slack")
    post_parser.add_argument("--channel", default=DEFAULT_CHANNEL)
    post_parser.add_argument("--agent", default="revops-watchdog")
    post_parser.add_argument("--draft-type", default="ops_summary")

    # --test-poll
    poll_parser = subparsers.add_parser("poll", help="Poll Slack thread for a reply")
    poll_parser.add_argument("--approval-id", type=int, required=True)

    # --check-expired
    subparsers.add_parser("expired", help="Check for and mark expired approvals")

    # --list-pending
    subparsers.add_parser("pending", help="List all pending approvals")

    # Legacy CLI flags (for backward compat with plan doc examples)
    parser.add_argument("--test-post", action="store_true")
    parser.add_argument("--test-poll", action="store_true")
    parser.add_argument("--check-expired", action="store_true")
    parser.add_argument("--channel", default=DEFAULT_CHANNEL)
    parser.add_argument("--agent", default="revops-watchdog")
    parser.add_argument("--draft-type", default="ops_summary")
    parser.add_argument("--approval-id", type=int)
    parser.add_argument("--thread-ts", help="(legacy) use --approval-id instead")

    args = parser.parse_args()

    # Subcommand routing
    if args.command == "post" or getattr(args, "test_post", False):
        cmd_test_post(
            channel=args.channel,
            agent=args.agent,
            draft_type=args.draft_type.replace("-", "_"),
        )
    elif args.command == "poll" or getattr(args, "test_poll", False):
        aid = args.approval_id
        if aid is None:
            err("--approval-id required for poll")
            sys.exit(1)
        cmd_test_poll(aid)
    elif args.command == "expired" or getattr(args, "check_expired", False):
        cmd_check_expired()
    elif args.command == "pending":
        rows = get_pending_approvals()
        if not rows:
            print("No pending approvals")
        else:
            for row in rows:
                print(f"  #{row['id']} | {row['agent']} {row['draft_type']} | created {row['created_at']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
