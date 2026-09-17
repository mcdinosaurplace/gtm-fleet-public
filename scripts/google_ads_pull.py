#!/usr/bin/env python3
"""
Google Ads pull — GTM Fleet Marketing Agent Fleet.

Two modes:

    dmo (default)   — drop-in replacement for the manual Google Ads CSV
                      consumed by the weekly paid position pass. Schema
                      matches roster/performance-marketer/references/dmo/
                      google-ads-channel.md exactly.

    spend-watch     — daily campaign-level spend for performance-marketer's spend_alerts
                      table. Lighter query, simpler output.

Usage:
    # DMO replacement (14 days, daily granularity)
    python3 scripts/google_ads_pull.py \\
        --range 14d \\
        --output state/working/google/google-ads-14d.csv

    # performance-marketer spend-watch (7 days, daily campaign spend)
    python3 scripts/google_ads_pull.py \\
        --mode spend-watch \\
        --range 7d \\
        --output state/working/google/google-ads-spend-7d.csv

    # JSON output
    python3 scripts/google_ads_pull.py --format json --output -

Env vars (see docs/google-api-setup.md):
    GOOGLE_ADS_DEVELOPER_TOKEN
    GOOGLE_ADS_CLIENT_ID
    GOOGLE_ADS_CLIENT_SECRET
    GOOGLE_ADS_REFRESH_TOKEN
    GOOGLE_ADS_LOGIN_CUSTOMER_ID
    GOOGLE_ADS_CUSTOMER_ID

Caveats:
    - Search Impression Share is fetched at the ad_group level and joined
      onto ad rows by (date, campaign, ad_group). Not available at ad level.
    - Quality Score is a keyword-level attribute. It is fetched from
      keyword_view, aggregated to ad_group grain (impression-weighted
      average), and joined onto ad rows. Historical QS is not exposed by
      the API — the value reflects current score applied to all date rows.
    - Cost is reported in micros by the API and divided by 1e6 here.
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

# DMO CSV column order, matches references/google-ads-channel.md
DMO_BASE_COLUMNS = ["Campaign", "Ad group"]
DMO_HEADLINE_COLUMNS = [f"Headline {i}" for i in range(1, 16)]
DMO_DESCRIPTION_COLUMNS = [f"Description {i}" for i in range(1, 5)]
DMO_METRIC_COLUMNS = [
    "Final URL",
    "Impressions",
    "Clicks",
    "CTR",
    "Avg. CPC",
    "Cost",
    "Conversions",
    "Conv. rate",
    "Quality Score",
    "Search Impression Share",
]
DMO_COLUMNS = (
    DMO_BASE_COLUMNS
    + DMO_HEADLINE_COLUMNS
    + DMO_DESCRIPTION_COLUMNS
    + DMO_METRIC_COLUMNS
)

SPEND_WATCH_COLUMNS = [
    "date",
    "campaign_id",
    "Campaign",
    "Impressions",
    "Clicks",
    "Cost",
    "Conversions",
    "CTR",
    "Avg. CPC",
]


def _parse_range(range_str: str) -> tuple[str, str]:
    """Convert '14d' to (start, end) ISO strings. End is yesterday."""
    m = re.fullmatch(r"(\d+)d", range_str.strip())
    if not m:
        raise ValueError(f"--range must be like '7d' or '14d', got {range_str!r}")
    days = int(m.group(1))
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def _micros_to_currency(micros: int) -> float:
    return round(micros / 1_000_000, 2)


def _build_dmo_query(start: str, end: str, by_day: bool) -> str:
    """GAQL for the DMO CSV. Pulls RSAs primarily; ETAs handled gracefully.

    search_impression_share and quality_score are not available at the
    ad_group_ad resource level. They are fetched separately via
    _build_adgroup_sis_query and _build_keyword_qs_query and joined in.
    """
    fields = [
        "campaign.name",
        "ad_group.name",
        "ad_group_ad.ad.id",
        "ad_group_ad.ad.type",
        "ad_group_ad.ad.final_urls",
        "ad_group_ad.ad.responsive_search_ad.headlines",
        "ad_group_ad.ad.responsive_search_ad.descriptions",
        "ad_group_ad.ad.expanded_text_ad.headline_part1",
        "ad_group_ad.ad.expanded_text_ad.headline_part2",
        "ad_group_ad.ad.expanded_text_ad.headline_part3",
        "ad_group_ad.ad.expanded_text_ad.description",
        "ad_group_ad.ad.expanded_text_ad.description2",
        "metrics.impressions",
        "metrics.clicks",
        "metrics.ctr",
        "metrics.average_cpc",
        "metrics.cost_micros",
        "metrics.conversions",
        "metrics.conversions_from_interactions_rate",
    ]
    if by_day:
        fields.insert(0, "segments.date")

    return (
        "SELECT "
        + ", ".join(fields)
        + " FROM ad_group_ad "
        + f"WHERE segments.date BETWEEN '{start}' AND '{end}' "
        + "AND ad_group_ad.status != 'REMOVED' "
        + "AND campaign.status != 'REMOVED'"
    )


def _build_adgroup_sis_query(start: str, end: str, by_day: bool) -> str:
    """GAQL for search_impression_share at the ad_group resource level."""
    fields = [
        "campaign.name",
        "ad_group.name",
        "metrics.search_impression_share",
    ]
    if by_day:
        fields.insert(0, "segments.date")
    return (
        "SELECT " + ", ".join(fields)
        + f" FROM ad_group"
        + f" WHERE segments.date BETWEEN '{start}' AND '{end}'"
        + " AND ad_group.status != 'REMOVED'"
        + " AND campaign.status != 'REMOVED'"
    )


def _build_keyword_qs_query(start: str, end: str, by_day: bool) -> str:
    """GAQL for quality_score at the keyword level.

    quality_score is a keyword-level attribute. Results are aggregated to
    ad_group grain (impression-weighted average) before joining onto ad rows.
    """
    fields = [
        "campaign.name",
        "ad_group.name",
        "ad_group_criterion.quality_info.quality_score",
        "metrics.impressions",
    ]
    if by_day:
        fields.insert(0, "segments.date")
    return (
        "SELECT " + ", ".join(fields)
        + f" FROM keyword_view"
        + f" WHERE segments.date BETWEEN '{start}' AND '{end}'"
        + " AND ad_group_criterion.status != 'REMOVED'"
        + " AND campaign.status != 'REMOVED'"
    )


def _build_spend_watch_query(start: str, end: str) -> str:
    fields = [
        "segments.date",
        "campaign.id",
        "campaign.name",
        "metrics.impressions",
        "metrics.clicks",
        "metrics.cost_micros",
        "metrics.conversions",
        "metrics.ctr",
        "metrics.average_cpc",
    ]
    return (
        "SELECT "
        + ", ".join(fields)
        + " FROM campaign "
        + f"WHERE segments.date BETWEEN '{start}' AND '{end}' "
        + "AND campaign.status != 'REMOVED'"
    )


def _ad_text_assets(ad) -> tuple[list[str], list[str]]:
    """Return (headlines, descriptions) text lists from an ad row."""
    headlines: list[str] = []
    descriptions: list[str] = []
    ad_type = str(getattr(ad, "type_", "")).upper()

    if "RESPONSIVE_SEARCH_AD" in ad_type:
        rsa = ad.responsive_search_ad
        headlines = [a.text for a in (rsa.headlines or [])]
        descriptions = [a.text for a in (rsa.descriptions or [])]
    elif "EXPANDED_TEXT_AD" in ad_type:
        eta = ad.expanded_text_ad
        for part in (eta.headline_part1, eta.headline_part2, eta.headline_part3):
            if part:
                headlines.append(part)
        for desc in (eta.description, eta.description2):
            if desc:
                descriptions.append(desc)
    return headlines, descriptions


def _row_to_dmo_record(row, by_day: bool, sis_lookup: dict, qs_lookup: dict) -> dict:
    record: dict = {}
    if by_day:
        record["date"] = row.segments.date

    record["Campaign"] = row.campaign.name
    record["Ad group"] = row.ad_group.name

    headlines, descriptions = _ad_text_assets(row.ad_group_ad.ad)
    for i, col in enumerate(DMO_HEADLINE_COLUMNS, start=0):
        record[col] = headlines[i] if i < len(headlines) else ""
    for i, col in enumerate(DMO_DESCRIPTION_COLUMNS, start=0):
        record[col] = descriptions[i] if i < len(descriptions) else ""

    final_urls = list(row.ad_group_ad.ad.final_urls or [])
    record["Final URL"] = final_urls[0] if final_urls else ""

    m = row.metrics
    record["Impressions"] = int(m.impressions)
    record["Clicks"] = int(m.clicks)
    record["CTR"] = round(float(m.ctr), 6)
    record["Avg. CPC"] = _micros_to_currency(int(m.average_cpc))
    record["Cost"] = _micros_to_currency(int(m.cost_micros))
    record["Conversions"] = round(float(m.conversions), 4)
    record["Conv. rate"] = round(float(m.conversions_from_interactions_rate), 6)

    key = _lookup_key(row, by_day)
    record["Quality Score"] = qs_lookup.get(key, "")
    record["Search Impression Share"] = sis_lookup.get(key, "")
    return record


def _row_to_spend_record(row) -> dict:
    m = row.metrics
    return {
        "date": row.segments.date,
        "campaign_id": str(row.campaign.id),
        "Campaign": row.campaign.name,
        "Impressions": int(m.impressions),
        "Clicks": int(m.clicks),
        "Cost": _micros_to_currency(int(m.cost_micros)),
        "Conversions": round(float(m.conversions), 4),
        "CTR": round(float(m.ctr), 6),
        "Avg. CPC": _micros_to_currency(int(m.average_cpc)),
    }


def _stream_rows(client, customer_id: str, query: str):
    service = client.get_service("GoogleAdsService")
    return service.search_stream(customer_id=customer_id, query=query)


def _lookup_key(row, by_day: bool) -> tuple:
    if by_day:
        return (row.segments.date, row.campaign.name, row.ad_group.name)
    return (row.campaign.name, row.ad_group.name)


def _build_sis_lookup(client, customer_id: str, query: str, by_day: bool) -> dict:
    """Return {key: search_impression_share} from the ad_group sub-query."""
    lookup = {}
    for batch in _stream_rows(client, customer_id, query):
        for row in batch.results:
            sis = row.metrics.search_impression_share
            lookup[_lookup_key(row, by_day)] = round(float(sis), 6) if sis else ""
    return lookup


def _build_qs_lookup(client, customer_id: str, query: str, by_day: bool) -> dict:
    """Return {key: impression-weighted avg quality_score} from the keyword sub-query.

    quality_score is a keyword attribute; we aggregate to ad_group grain so it
    can be joined onto ad rows. When a group has no impressions (all keywords
    dormant), falls back to an unweighted average across keywords with a score.
    """
    raw: dict = {}
    for batch in _stream_rows(client, customer_id, query):
        for row in batch.results:
            qs = row.ad_group_criterion.quality_info.quality_score
            if not qs:
                continue
            key = _lookup_key(row, by_day)
            raw.setdefault(key, []).append((int(qs), int(row.metrics.impressions)))

    lookup = {}
    for key, pairs in raw.items():
        total_imp = sum(imp for _, imp in pairs)
        if total_imp > 0:
            lookup[key] = round(sum(qs * imp for qs, imp in pairs) / total_imp, 1)
        else:
            lookup[key] = round(sum(qs for qs, _ in pairs) / len(pairs), 1)
    return lookup


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

    Keyed on --mode, --by-day, and --format only: the window arguments do not
    select a fixture, so every --range serves the same canonical CSV.
    """
    if args.mode == "spend-watch":
        name = "spend-watch-14d"
    else:
        name = "dmo-14d-by-day" if args.by_day else "dmo-14d"
    return f"fixtures/google/ads/{name}.{args.format}"


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
    parser = argparse.ArgumentParser(description="Pull Google Ads data.")
    parser.add_argument("--mode", choices=("dmo", "spend-watch"), default="dmo",
                        help="dmo = DMO CSV replacement; spend-watch = daily campaign spend.")
    parser.add_argument("--range", default="14d",
                        help="Lookback like '7d' or '14d'. Default 14d (DMO convention).")
    parser.add_argument("--by-day", action="store_true",
                        help="In dmo mode, segment by day for granular WoW. Default off (matches manual export).")
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--output", default="-",
                        help="Output path or '-' for stdout. Default '-'.")
    args = parser.parse_args()

    if fleet_paths.demo_mode():
        return _serve_demo_fixture(_demo_fixture(args), args.output, "--range")

    try:
        start, end = _parse_range(args.range)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    from google_auth import get_ads_client, get_ads_customer_id

    client = get_ads_client()
    customer_id = get_ads_customer_id()

    if args.mode == "dmo":
        sis_lookup = _build_sis_lookup(
            client, customer_id,
            _build_adgroup_sis_query(start, end, by_day=args.by_day),
            args.by_day,
        )
        qs_lookup = _build_qs_lookup(
            client, customer_id,
            _build_keyword_qs_query(start, end, by_day=args.by_day),
            args.by_day,
        )
        query = _build_dmo_query(start, end, by_day=args.by_day)
        columns = (["date"] + DMO_COLUMNS) if args.by_day else DMO_COLUMNS
        rows: list[dict] = []
        for batch in _stream_rows(client, customer_id, query):
            for row in batch.results:
                rows.append(_row_to_dmo_record(row, by_day=args.by_day,
                                               sis_lookup=sis_lookup, qs_lookup=qs_lookup))
    else:
        query = _build_spend_watch_query(start, end)
        columns = SPEND_WATCH_COLUMNS
        rows = []
        for batch in _stream_rows(client, customer_id, query):
            for row in batch.results:
                rows.append(_row_to_spend_record(row))

    output_path = Path(args.output) if args.output != "-" else Path("-")
    if args.format == "csv":
        _write_csv(rows, columns, output_path)
    else:
        payload = {
            "customer_id": customer_id,
            "mode": args.mode,
            "date_range": {"start": start, "end": end},
            "by_day": bool(args.by_day) if args.mode == "dmo" else True,
            "row_count": len(rows),
            "rows": rows,
        }
        _write_json(payload, output_path)

    if str(output_path) != "-":
        print(f"Wrote {len(rows)} rows to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
