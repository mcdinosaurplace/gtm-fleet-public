#!/usr/bin/env python3
"""
Google Search Console pull — GTM Fleet Marketing Agent Fleet.

Pulls Search Analytics data via the Search Console API and writes CSV or
JSON. Used by performance-marketer for keyword tracking and by the SEO audit skill.

Usage:
    # Default 28-day query+page report
    python3 scripts/gsc_pull.py \\
        --range 28d \\
        --dimensions query,page \\
        --output state/working/google/gsc-28d.csv

    # By-day for trend lines
    python3 scripts/gsc_pull.py --range 7d --dimensions date,query --output -

    # JSON for programmatic consumers
    python3 scripts/gsc_pull.py --format json --output state/working/google/gsc.json

Env vars (see docs/google-api-setup.md):
    GOOGLE_SERVICE_ACCOUNT_JSON
    GSC_SITE_URL
"""

import argparse
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402
from scripts.demo.dates import render_tokens  # noqa: E402


REPO_ROOT = Path(__file__).parent.parent.resolve()

VALID_DIMENSIONS = {"date", "query", "page", "country", "device", "searchAppearance"}
DEFAULT_DIMENSIONS = "query,page"
PAGE_SIZE = 25000  # API max per call


def _parse_range(range_str: str) -> tuple[str, str]:
    """Convert '28d' to (start, end) ISO strings.

    GSC has a 2–3 day reporting lag, so end = today - 3d for safety.
    """
    m = re.fullmatch(r"(\d+)d", range_str.strip())
    if not m:
        raise ValueError(f"--range must be like '7d' or '28d', got {range_str!r}")
    days = int(m.group(1))
    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def _split_csv(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def _query_all(service, site_url: str, body: dict) -> list[dict]:
    """Page through searchanalytics.query, returning all rows."""
    rows: list[dict] = []
    start_row = 0
    while True:
        page_body = dict(body, startRow=start_row, rowLimit=PAGE_SIZE)
        resp = service.searchanalytics().query(siteUrl=site_url, body=page_body).execute()
        page_rows = resp.get("rows", [])
        rows.extend(page_rows)
        if len(page_rows) < PAGE_SIZE:
            return rows
        start_row += PAGE_SIZE


def _flatten(row: dict, dimensions: list[str]) -> dict:
    """Flatten a GSC row (keys: clicks, impressions, ctr, position, keys[])."""
    out = {}
    keys = row.get("keys", [])
    for i, d in enumerate(dimensions):
        out[d] = keys[i] if i < len(keys) else ""
    out["clicks"] = int(row.get("clicks", 0))
    out["impressions"] = int(row.get("impressions", 0))
    out["ctr"] = float(row.get("ctr", 0.0))
    out["position"] = float(row.get("position", 0.0))
    return out


def _write_csv(rows: list[dict], columns: list[str], path: Path) -> None:
    if str(path) == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(payload: dict, path: Path) -> None:
    body = json.dumps(payload, indent=2, default=str)
    if str(path) == "-":
        sys.stdout.write(body + "\n")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


# ============================================================
# DEMO_MODE
# ============================================================

def _demo_fixture(args) -> str:
    """Fixture relpath for this invocation.

    Keyed on --dimensions and --format only: the window and search-type arguments
    do not select a fixture, so every --range serves the same canonical CSV.
    """
    dimensions = _split_csv(args.dimensions)
    return f"fixtures/google/gsc/{'-'.join(d.lower() for d in dimensions)}-7d.{args.format}"


def _serve_demo_fixture(relpath: str, output: str, ignored: str) -> int:
    """DEMO_MODE: write the fixture to --output with its date tokens rendered.

    Runs before any credential import, so a demo needs no Google account. Exits
    non-zero naming the path when the mapped fixture does not exist.
    """
    path = fleet_paths.PLUGIN_ROOT / relpath
    if not path.is_file():
        print(f"ERROR: DEMO_MODE fixture not found: {path}", file=sys.stderr)
        return 2
    body = render_tokens(path.read_text())
    if output == "-":
        sys.stdout.write(body)
    else:
        dest = Path(output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body)
    print(f"[demo] served fixture {relpath} → {output}", file=sys.stderr)
    print(f"[demo] canonical demo data — {ignored} ignored", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull a Search Console report.")
    parser.add_argument("--range", default="28d",
                        help="Lookback like '7d', '28d'. Default 28d (matches GSC UI).")
    parser.add_argument("--dimensions", default=DEFAULT_DIMENSIONS,
                        help=f"Comma-separated GSC dimensions. Default: {DEFAULT_DIMENSIONS}. "
                             f"Valid: {sorted(VALID_DIMENSIONS)}")
    parser.add_argument("--search-type", default="web",
                        choices=("web", "image", "video", "news", "discover", "googleNews"))
    parser.add_argument("--row-limit", type=int, default=0,
                        help="Cap total rows. 0 = no cap (page through all). Default 0.")
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--output", default="-",
                        help="Output path or '-' for stdout. Default '-'.")
    args = parser.parse_args()

    if fleet_paths.demo_mode():
        return _serve_demo_fixture(_demo_fixture(args), args.output,
                                   "--range / --search-type / --row-limit")

    try:
        start, end = _parse_range(args.range)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    dimensions = _split_csv(args.dimensions)
    bad = [d for d in dimensions if d not in VALID_DIMENSIONS]
    if bad:
        print(f"ERROR: invalid dimensions {bad}. Valid: {sorted(VALID_DIMENSIONS)}", file=sys.stderr)
        return 2

    from google_auth import get_gsc_service, get_gsc_site_url

    service = get_gsc_service()
    site_url = get_gsc_site_url()

    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "type": args.search_type,
    }
    raw_rows = _query_all(service, site_url, body)
    if args.row_limit and len(raw_rows) > args.row_limit:
        raw_rows = raw_rows[: args.row_limit]

    rows = [_flatten(r, dimensions) for r in raw_rows]
    columns = dimensions + ["clicks", "impressions", "ctr", "position"]
    output_path = Path(args.output) if args.output != "-" else Path("-")

    if args.format == "csv":
        _write_csv(rows, columns, output_path)
    else:
        payload = {
            "site_url": site_url,
            "date_range": {"start": start, "end": end},
            "dimensions": dimensions,
            "search_type": args.search_type,
            "row_count": len(rows),
            "rows": rows,
        }
        _write_json(payload, output_path)

    if str(output_path) != "-":
        print(f"Wrote {len(rows)} rows to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
