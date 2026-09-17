#!/usr/bin/env python3
"""scripts/pm/db.py — the single writer to the pm_* tables.

Deterministic SQLite access for the PM cores. Opens fleet.db, guards
writes to the pm_* tables only, and exposes small typed helpers (insert, upsert,
fetchall, fetchone) that the capture / resolve / pulse / commitments cores build
on — they do not open the DB themselves.

No model in this path: pure SQL + parameter binding. Timestamps and ids are
supplied by the caller (kept out of here so the helpers stay deterministic).
Callers commit their own transactions.
"""

import sqlite3
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402

REPO_ROOT = fleet_paths.FLEET_ROOT
DEFAULT_DB_PATH = fleet_paths.DB_PATH

PM_TABLES = (
    "pm_projects",
    "pm_issues",
    "pm_blockers",
    "pm_standup_threads",
    "pm_standup_responses",
    "pm_commitments",
    "pm_external_dependencies",
    "pm_missed_deadlines",
    "pm_rca_log",
)


class DBError(Exception):
    """Raised on DB access problems or an attempted write to a non-PM table."""


def connect(path=DEFAULT_DB_PATH) -> sqlite3.Connection:
    p = Path(path)
    if not p.exists():
        raise DBError(f"DB not found: {p} (run pending migrations first)")
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def _guard(table: str):
    if table not in PM_TABLES:
        raise DBError(f"refusing to write non-PM table {table!r}; pm/db.py writes pm_* only")


def insert(conn, table, row: dict) -> int:
    """Insert one row into a pm_* table. Returns lastrowid. Does not commit."""
    _guard(table)
    if not row:
        raise DBError("insert requires a non-empty row")
    cols = list(row.keys())
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    return conn.execute(sql, [row[c] for c in cols]).lastrowid


def upsert(conn, table, row: dict, key_cols) -> None:
    """Insert, or update non-key columns on conflict of key_cols. Does not commit.

    key_cols must be a UNIQUE or PRIMARY KEY in the table.
    """
    _guard(table)
    if not row:
        raise DBError("upsert requires a non-empty row")
    cols = list(row.keys())
    values = [row[c] for c in cols]
    insert_sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
    update_cols = [c for c in cols if c not in key_cols]
    if update_cols:
        set_clause = ", ".join(f"{c}=excluded.{c}" for c in update_cols)
        sql = f"{insert_sql} ON CONFLICT({', '.join(key_cols)}) DO UPDATE SET {set_clause}"
    else:
        sql = f"{insert_sql} ON CONFLICT({', '.join(key_cols)}) DO NOTHING"
    conn.execute(sql, values)


def update(conn, table, set_fields: dict, where: dict) -> int:
    """Update rows in a pm_* table. Returns the affected row count. Does not commit.

    `where` is required and must be non-empty (no blanket updates). Used for resolution
    write-backs, the G2 create-requested stamp, and C3 completion updates.
    """
    _guard(table)
    if not set_fields:
        raise DBError("update requires non-empty set_fields")
    if not where:
        raise DBError("update requires a non-empty where clause (no blanket updates)")
    set_clause = ", ".join(f"{c}=?" for c in set_fields)
    where_clause = " AND ".join(f"{c}=?" for c in where)
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    return conn.execute(sql, [*set_fields.values(), *where.values()]).rowcount


def fetchall(conn, sql, params=()) -> list:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def fetchone(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None
