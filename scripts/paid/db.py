#!/usr/bin/env python3
"""scripts/paid/db.py — the single writer to the paid execution tables.

Deterministic SQLite access for the paid cores. Maps classified moves (from
scripts/paid/classify.py, with the dossier's per-move detail merged in) into
paid_change_proposals rows, and exposes small read/transition helpers the
greenlight and execute steps build on.

No model in this path: pure SQL + parameter binding. Timestamps and ids are
supplied by the caller (kept out of here so the helpers stay deterministic).
Callers commit their own transactions.
"""

import json
import sqlite3
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402

REPO_ROOT = fleet_paths.FLEET_ROOT
DEFAULT_DB_PATH = fleet_paths.DB_PATH

PAID_TABLES = ("paid_change_proposals", "applied_changes")

# Move fields that must be present to build a proposal row.
_REQUIRED_MOVE_FIELDS = ("platform", "op_type", "bucket", "summary")


class DBError(Exception):
    """Raised on DB access problems or an attempted write to a non-paid table."""


def connect(path=DEFAULT_DB_PATH) -> sqlite3.Connection:
    p = Path(path)
    if not p.exists():
        raise DBError(f"DB not found: {p} (run pending migrations first)")
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def _guard(table: str):
    if table not in PAID_TABLES:
        raise DBError(f"refusing to write non-paid table {table!r}; paid/db.py writes paid tables only")


def insert(conn, table, row: dict) -> int:
    """Insert one row into a paid table. Returns lastrowid. Does not commit."""
    _guard(table)
    if not row:
        raise DBError("insert requires a non-empty row")
    cols = list(row.keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    return conn.execute(sql, [row[c] for c in cols]).lastrowid


def fetchall(conn, sql, params=()) -> list:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def fetchone(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def _as_json(value):
    """Encode a dict/list as deterministic JSON; pass strings/None through."""
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def _proposal_row(move: dict, dossier_date: str, created_at: str) -> dict:
    """Map one classified move (with detail merged in) to a proposal row."""
    missing = [f for f in _REQUIRED_MOVE_FIELDS if not move.get(f)]
    if missing:
        raise DBError(f"move missing required field(s) {missing}: {move.get('summary') or move}")
    return {
        "agent": "performance-marketer",
        "dossier_date": dossier_date,
        "platform": move["platform"],
        "campaign_name": move.get("campaign_name"),
        "bucket": move["bucket"],
        "op_type": move["op_type"],
        "summary": move["summary"],
        "reason": move.get("reason"),
        "prior_value": _as_json(move.get("prior_value")),
        "target_value": _as_json(move.get("target_value")),
        "reversal_if": move.get("reversal_if"),
        "linear_ref": move.get("linear_ref"),
        "approval_id": move.get("approval_id"),
        "status": move.get("status", "proposed"),
        "decided_at": move.get("decided_at"),
        "created_at": created_at,
    }


def insert_proposals(conn, moves, dossier_date: str, created_at: str) -> list:
    """Insert classified moves as paid_change_proposals rows.

    Each move must already carry its `bucket` (merge classify_move's verdict back
    onto the dossier move before calling). Returns the list of inserted ids.
    Does not commit — the caller owns the transaction.
    """
    return [insert(conn, "paid_change_proposals", _proposal_row(m, dossier_date, created_at))
            for m in moves]


def list_proposals(conn, dossier_date=None, status=None) -> list:
    """Return proposals, optionally filtered by dossier_date and/or status, ordered by id."""
    clauses, params = [], []
    if dossier_date:
        clauses.append("dossier_date = ?")
        params.append(dossier_date)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return fetchall(conn, f"SELECT * FROM paid_change_proposals{where} ORDER BY id", params)


def set_proposal_status(conn, proposal_id: int, status: str,
                        decided_at=None, approval_id=None, linear_ref=None) -> None:
    """Transition a proposal's status (+ optional decided_at/approval_id/linear_ref).

    Used by the greenlight step (-> 'greenlit'/'rejected'), the copy-delegation
    step (-> 'awaiting_creative' with a linear_ref), and execute (-> 'applied'/
    'rolled_back'). Does not commit.
    """
    sets, params = ["status = ?"], [status]
    if decided_at is not None:
        sets.append("decided_at = ?")
        params.append(decided_at)
    if approval_id is not None:
        sets.append("approval_id = ?")
        params.append(approval_id)
    if linear_ref is not None:
        sets.append("linear_ref = ?")
        params.append(linear_ref)
    params.append(proposal_id)
    conn.execute(f"UPDATE paid_change_proposals SET {', '.join(sets)} WHERE id = ?", params)


def list_applied_changes(conn, active_only=False):
    """Return applied_changes rows, optionally only those still active (applied
    live and not yet rolled back), ordered by id."""
    sql = "SELECT * FROM applied_changes"
    if active_only:
        sql += " WHERE rolled_back_at IS NULL AND mode = 'live'"
    sql += " ORDER BY id"
    return fetchall(conn, sql)


def mark_rolled_back(conn, change_id, rolled_back_at):
    """Stamp an applied_changes row as reversed. Does not commit."""
    conn.execute("UPDATE applied_changes SET rolled_back_at = ? WHERE id = ?",
                 (rolled_back_at, change_id))
