#!/usr/bin/env python3
"""
GA4 pull — GTM Fleet Marketing Agent Fleet.

Pulls a GA4 report via the Analytics Data API and writes CSV or JSON.
Designed for performance-marketer's daily tick (page performance, traffic trends) and
ad-hoc analysis.

Usage:
    python3 scripts/ga4_pull.py \\
        --range 7d \\
        --metrics sessions,engagedSessions,conversions \\
        --dimensions pagePath,sessionSourceMedium \\
        --output state/working/google/ga4-7d.csv

    # JSON output for programmatic consumers
    python3 scripts/ga4_pull.py --range 1d --format json --output -

    # Daily granularity (adds `date` dimension automatically when --by-day)
    python3 scripts/ga4_pull.py --range 14d --by-day --output state/working/google/ga4-14d.csv

Env vars (see docs/google-api-setup.md):
    GOOGLE_SERVICE_ACCOUNT_JSON
    GA4_PROPERTY_ID
"""

import argparse
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402
from scripts.demo.dates import render_tokens  # noqa: E402


REPO_ROOT = Path(__file__).parent.parent.resolve()

DEFAULT_METRICS = "sessions,engagedSessions,conversions,totalUsers"
DEFAULT_DIMENSIONS = "pagePath,sessionSourceMedium"


def _parse_range(range_str: str) -> tuple[str, str]:
    """Convert a range like '7d' or '28d' to (start_date, end_date) inclusive.

    Both dates are ISO strings (YYYY-MM-DD). End date is yesterday — GA4
    intraday data is incomplete, so today is excluded by default.
    """
    m = re.fullmatch(r"(\d+)d", range_str.strip())
    if not m:
        raise ValueError(f"--range must be like '7d' or '28d', got {range_str!r}")
    days = int(m.group(1))
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def _split_csv(s: str) -> list[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


def _run_report(
    property_id: str,
    start: str,
    end: str,
    metrics: list[str],
    dimensions: list[str],
    limit: int,
):
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    from google_auth import get_ga4_client

    client = get_ga4_client()
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        limit=limit,
    )
    return client.run_report(request)


def _rows_from_response(response, dimensions: list[str], metrics: list[str]):
    for row in response.rows:
        record = {}
        for i, d in enumerate(dimensions):
            record[d] = row.dimension_values[i].value
        for i, m in enumerate(metrics):
            raw = row.metric_values[i].value
            try:
                record[m] = float(raw) if "." in raw else int(raw)
            except ValueError:
                record[m] = raw
        yield record


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

    Keyed on --dimensions (after the --by-day `date` prepend) and --format only:
    the window and --metrics arguments do not select a fixture, so every --range
    serves the same canonical CSV with the metrics that CSV already carries.
    """
    dimensions = _split_csv(args.dimensions)
    if args.by_day and "date" not in dimensions:
        dimensions = ["date"] + dimensions
    return f"fixtures/google/ga4/{'-'.join(d.lower() for d in dimensions)}-7d.{args.format}"


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
    parser = argparse.ArgumentParser(description="Pull a GA4 report.")
    parser.add_argument("--range", default="7d", help="Lookback like '7d', '28d'. Default 7d.")
    parser.add_argument("--metrics", default=DEFAULT_METRICS,
                        help=f"Comma-separated GA4 metric names. Default: {DEFAULT_METRICS}")
    parser.add_argument("--dimensions", default=DEFAULT_DIMENSIONS,
                        help=f"Comma-separated GA4 dimension names. Default: {DEFAULT_DIMENSIONS}")
    parser.add_argument("--by-day", action="store_true",
                        help="Prepend `date` dimension for daily WoW analysis.")
    parser.add_argument("--limit", type=int, default=10000,
                        help="Max rows to return. GA4 caps at 100k. Default 10k.")
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--output", default="-",
                        help="Output path or '-' for stdout. Default '-'.")
    args = parser.parse_args()

    if fleet_paths.demo_mode():
        return _serve_demo_fixture(_demo_fixture(args), args.output,
                                   "--range / --metrics / --limit")

    try:
        start, end = _parse_range(args.range)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    metrics = _split_csv(args.metrics)
    dimensions = _split_csv(args.dimensions)
    if args.by_day and "date" not in dimensions:
        dimensions = ["date"] + dimensions

    if not metrics:
        print("ERROR: at least one metric required", file=sys.stderr)
        return 2

    from google_auth import get_ga4_property_id

    property_id = get_ga4_property_id()
    response = _run_report(property_id, start, end, metrics, dimensions, args.limit)
    rows = list(_rows_from_response(response, dimensions, metrics))

    columns = dimensions + metrics
    output_path = Path(args.output) if args.output != "-" else Path("-")

    if args.format == "csv":
        _write_csv(rows, columns, output_path)
    else:
        payload = {
            "property_id": property_id,
            "date_range": {"start": start, "end": end},
            "dimensions": dimensions,
            "metrics": metrics,
            "row_count": len(rows),
            "rows": rows,
        }
        _write_json(payload, output_path)

    if str(output_path) != "-":
        print(f"Wrote {len(rows)} rows to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
