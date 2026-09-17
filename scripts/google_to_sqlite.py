#!/usr/bin/env python3
"""
Google pull → SQLite ETL — GTM Fleet Marketing Agent Fleet.

Loads outputs from `google_ads_pull.py` and `gsc_pull.py` into the canonical
`fleet.db` tables performance-marketer reads from. Idempotent on (date, key) —
re-running on the same input does not duplicate rows.

Subcommands:
    ads-spend     Load Google Ads spend-watch CSV → paid_creative table
                  (one row per campaign per day, creative_id sentinel).

    gsc-rankings  Load GSC query CSV → keyword_rankings table.
                  Auto-computes prior_position and position_delta from the
                  most recent prior snapshot.

Usage:
    # 1) Pull, then load
    python3 scripts/google_ads_pull.py --mode spend-watch --range 7d \\
        --output state/working/google/spend-7d.csv
    python3 scripts/google_to_sqlite.py ads-spend \\
        --input state/working/google/spend-7d.csv

    python3 scripts/gsc_pull.py --range 7d --dimensions query \\
        --output state/working/google/gsc-queries-7d.csv
    python3 scripts/google_to_sqlite.py gsc-rankings \\
        --input state/working/google/gsc-queries-7d.csv \\
        --keywords-file roster/performance-marketer/references/tracked-keywords.txt
"""

import argparse
import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402
from typing import Optional


REPO_ROOT = fleet_paths.FLEET_ROOT
DB_PATH = fleet_paths.DB_PATH

CAMPAIGN_AGGREGATE_PREFIX = "__campaign_aggregate_"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _safe_float(s: str) -> float:
    try:
        return float(s) if s not in ("", None) else 0.0
    except (ValueError, TypeError):
        return 0.0


def _safe_int(s: str) -> int:
    try:
        return int(float(s)) if s not in ("", None) else 0
    except (ValueError, TypeError):
        return 0


# ============================================================
# ads-spend
# ============================================================

def cmd_ads_spend(args) -> int:
    rows = _read_csv(Path(args.input))
    if not rows:
        print(f"No rows in {args.input}", file=sys.stderr)
        return 0

    required = {"date", "campaign_id", "Campaign", "Impressions", "Clicks", "Cost", "Conversions"}
    missing = required - set(rows[0].keys())
    if missing:
        print(f"ERROR: input missing columns: {sorted(missing)}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped = 0
    try:
        for r in rows:
            snapshot_date = r["date"]
            campaign_id = r["campaign_id"]
            creative_id = f"{CAMPAIGN_AGGREGATE_PREFIX}{campaign_id}__"

            # Idempotency: skip if a row with this (creative_id, snapshot_date) exists.
            cur = conn.execute(
                "SELECT 1 FROM paid_creative WHERE creative_id = ? AND snapshot_date = ?",
                (creative_id, snapshot_date),
            )
            if cur.fetchone():
                skipped += 1
                continue

            impressions = _safe_int(r["Impressions"])
            clicks = _safe_int(r["Clicks"])
            spend = _safe_float(r["Cost"])
            conversions = _safe_int(r["Conversions"])
            ctr = _safe_float(r.get("CTR", "0"))
            cpl = round(spend / conversions, 2) if conversions > 0 else None

            conn.execute(
                """
                INSERT INTO paid_creative (
                    agent, platform, campaign_name, ad_group, creative_id,
                    headline, description, impressions, clicks, ctr, spend,
                    conversions, cpl, status, snapshot_date, created_at
                ) VALUES (
                    'performance-marketer', 'google_ads', ?, NULL, ?,
                    NULL, NULL, ?, ?, ?, ?,
                    ?, ?, 'aggregate', ?, ?
                )
                """,
                (
                    r["Campaign"], creative_id, impressions, clicks, ctr, spend,
                    conversions, cpl, snapshot_date, _now_iso(),
                ),
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()

    print(f"paid_creative: inserted={inserted} skipped={skipped} (idempotent)", file=sys.stderr)
    return 0


# ============================================================
# gsc-rankings
# ============================================================

def cmd_gsc_rankings(args) -> int:
    rows = _read_csv(Path(args.input))
    if not rows:
        print(f"No rows in {args.input}", file=sys.stderr)
        return 0

    if "query" not in rows[0]:
        print("ERROR: input must include a 'query' dimension column", file=sys.stderr)
        return 2

    tracked: Optional[set[str]] = None
    if args.keywords_file:
        kw_path = Path(args.keywords_file)
        if kw_path.is_file():
            tracked = {
                line.strip().lower()
                for line in kw_path.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            }
        else:
            print(f"WARN: keywords file not found: {kw_path}", file=sys.stderr)

    snapshot_date = args.snapshot_date or datetime.now(timezone.utc).date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    inserted = 0
    skipped_existing = 0
    skipped_untracked = 0

    try:
        for r in rows:
            keyword = (r.get("query") or "").strip()
            if not keyword:
                continue
            if tracked is not None and keyword.lower() not in tracked:
                skipped_untracked += 1
                continue

            cur = conn.execute(
                "SELECT 1 FROM keyword_rankings WHERE keyword = ? AND snapshot_date = ?",
                (keyword, snapshot_date),
            )
            if cur.fetchone():
                skipped_existing += 1
                continue

            position = round(_safe_float(r.get("position", "0"))) or None

            cur = conn.execute(
                """
                SELECT position FROM keyword_rankings
                WHERE keyword = ? AND snapshot_date < ?
                ORDER BY snapshot_date DESC LIMIT 1
                """,
                (keyword, snapshot_date),
            )
            prior = cur.fetchone()
            prior_position = prior[0] if prior else None
            delta = (
                (prior_position - position)
                if prior_position is not None and position is not None
                else None
            )

            conn.execute(
                """
                INSERT INTO keyword_rankings (
                    agent, snapshot_date, keyword, position, prior_position,
                    position_delta, search_volume, url, flag, created_at
                ) VALUES ('performance-marketer', ?, ?, ?, ?, ?, NULL, ?, NULL, ?)
                """,
                (
                    snapshot_date, keyword, position, prior_position, delta,
                    r.get("page", None), _now_iso(),
                ),
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()

    print(
        f"keyword_rankings: inserted={inserted} "
        f"skipped_existing={skipped_existing} skipped_untracked={skipped_untracked}",
        file=sys.stderr,
    )
    return 0


# ============================================================
# Entry point
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Google pulls → fleet.db ETL.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ads = sub.add_parser("ads-spend", help="Load Google Ads spend-watch CSV.")
    p_ads.add_argument("--input", required=True, help="Path to spend-watch CSV.")
    p_ads.set_defaults(func=cmd_ads_spend)

    p_gsc = sub.add_parser("gsc-rankings", help="Load GSC CSV into keyword_rankings.")
    p_gsc.add_argument("--input", required=True, help="Path to GSC CSV (must include 'query').")
    p_gsc.add_argument("--keywords-file", help="Optional file of tracked keywords (one per line).")
    p_gsc.add_argument("--snapshot-date",
                       help="Override snapshot date (YYYY-MM-DD). Default: today UTC.")
    p_gsc.set_defaults(func=cmd_gsc_rankings)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
