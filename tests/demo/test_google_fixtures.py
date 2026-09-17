"""Tests for the DEMO_MODE Google pull fixtures (fixtures/google/).

performance-marketer's Tick shells four Google pull commands. With DEMO_MODE=1 the same
commands must serve deterministic fixtures instead of calling an API, and the two
ETL-bound ones must still load cleanly into the seeded database.

The scripts are exercised as subprocesses, the way the Tick calls them: they import
`google_auth` by bare module name from `scripts/`, so they only resolve when run as
scripts. Every run is offline — the load-bearing property is that the demo branch
returns before any credential path is touched.
"""
import csv
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest


def utc_today() -> date:
    """The fixture renderer (scripts/demo/dates.py) and the fleet anchor run on UTC,
    not local time — asserting local date.today() fails every evening US-Pacific."""
    return datetime.now(timezone.utc).date()

ROOT = Path(__file__).resolve().parents[2]
KEYWORDS_FILE = ROOT / "roster" / "performance-marketer" / "references" / "tracked-keywords.txt"

# The four invocations from roster/performance-marketer/prompt.md, verbatim apart from
# --output. `fixture` is the relpath each one must report serving.
PULLS = {
    "ads-spend-watch": (
        ["scripts/google_ads_pull.py", "--mode", "spend-watch", "--range", "14d"],
        "fixtures/google/ads/spend-watch-14d.csv",
    ),
    "gsc-queries": (
        ["scripts/gsc_pull.py", "--range", "7d", "--dimensions", "query,page"],
        "fixtures/google/gsc/query-page-7d.csv",
    ),
    "ads-dmo": (
        ["scripts/google_ads_pull.py", "--mode", "dmo", "--range", "14d", "--by-day"],
        "fixtures/google/ads/dmo-14d-by-day.csv",
    ),
    "ga4-pages": (
        ["scripts/ga4_pull.py", "--range", "7d", "--by-day",
         "--metrics", "sessions,engagedSessions,conversions",
         "--dimensions", "pagePath,sessionSourceMedium"],
        "fixtures/google/ga4/date-pagepath-sessionsourcemedium-7d.csv",
    ),
}


def run(argv, env_extra=None):
    """Run a repo script as a subprocess with a pruned environment.

    Google credentials are stripped so a developer's real `.env` shell can never make a
    'live path' assertion pass for the wrong reason.
    """
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("GOOGLE_", "GA4_", "GSC_"))}
    env.pop("DEMO_MODE", None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(ROOT / argv[0]), *argv[1:]],
                          capture_output=True, text=True, cwd=ROOT, env=env)


def demo_run(name, output):
    argv, fixture = PULLS[name]
    r = run([*argv, "--output", str(output)], {"DEMO_MODE": "1"})
    return r, fixture


# ---- (a) every documented invocation serves its fixture ----

@pytest.mark.parametrize("name", sorted(PULLS))
def test_demo_mode_serves_the_mapped_fixture(name, tmp_path):
    out = tmp_path / "pull.csv"
    r, fixture = demo_run(name, out)

    assert r.returncode == 0, r.stdout + r.stderr
    assert f"[demo] served fixture {fixture}" in r.stderr, r.stderr
    assert (ROOT / fixture).is_file()

    source = (ROOT / fixture).read_text()
    body = out.read_text()
    assert "{{" not in body, "date tokens were not rendered"
    assert body.splitlines()[0] == source.splitlines()[0]
    # GSC's query,page report aggregates the whole window and has no date column —
    # google_to_sqlite.py stamps its snapshot date at load time. The other three carry
    # tokens, and test_dated_fixtures_end_today pins their windows.
    if "{{T" in source:
        assert utc_today().isoformat() in body, "the served window does not end today"


def test_dated_fixtures_end_today(tmp_path):
    """The three dated pulls cover their trailing window and end on today."""
    for name, days in (("ads-spend-watch", 14), ("ads-dmo", 14), ("ga4-pages", 7)):
        out = tmp_path / f"{name}.csv"
        r, _ = demo_run(name, out)
        assert r.returncode == 0, r.stderr
        dates = sorted({line.split(",")[0] for line in out.read_text().splitlines()[1:]})
        assert len(dates) == days, (name, dates)
        assert dates[-1] == utc_today().isoformat(), name


def test_demo_mode_writes_to_stdout_for_dash(tmp_path):
    argv, fixture = PULLS["gsc-queries"]
    r = run([*argv, "--output", "-"], {"DEMO_MODE": "1"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.splitlines()[0] == "query,page,clicks,impressions,ctr,position"
    assert "{{" not in r.stdout
    assert f"[demo] served fixture {fixture}" in r.stderr


def test_demo_mode_says_which_arguments_it_ignored(tmp_path):
    """--range variations serve the same canonical fixture, and the run says so."""
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    argv, _ = PULLS["ads-spend-watch"]
    r7 = run([*argv[:-1], "3d", "--output", str(a)], {"DEMO_MODE": "1"})
    r14 = run([*argv, "--output", str(b)], {"DEMO_MODE": "1"})
    assert (r7.returncode, r14.returncode) == (0, 0), r7.stderr + r14.stderr
    assert a.read_text() == b.read_text()
    assert "--range ignored" in r7.stderr


def test_missing_fixture_exits_non_zero_naming_the_path(tmp_path):
    """An un-fixtured shape fails loudly instead of serving the wrong columns."""
    r = run(["scripts/google_ads_pull.py", "--mode", "dmo", "--range", "14d",
             "--output", str(tmp_path / "x.csv")], {"DEMO_MODE": "1"})
    assert r.returncode != 0
    assert "fixtures/google/ads/dmo-14d.csv" in r.stderr
    assert not (tmp_path / "x.csv").exists()


@pytest.mark.parametrize("name", sorted(PULLS))
def test_demo_branch_never_imports_the_credential_path(name, tmp_path):
    """The whole point: DEMO_MODE returns before google_auth or any Google SDK loads.

    `-X importtime` names every module the process imported, so this fails the moment
    someone re-adds a top-level credential import to a pull script.
    """
    argv, _ = PULLS[name]
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("GOOGLE_", "GA4_", "GSC_"))}
    env["DEMO_MODE"] = "1"
    r = subprocess.run(
        [sys.executable, "-X", "importtime", str(ROOT / argv[0]), *argv[1:],
         "--output", str(tmp_path / "out.csv")],
        capture_output=True, text=True, cwd=ROOT, env=env)
    assert r.returncode == 0, r.stderr

    imported = [line.rsplit("|", 1)[-1].strip() for line in r.stderr.splitlines()
                if line.startswith("import time:")]
    assert imported, "-X importtime produced no module list"
    leaked = [m for m in imported
              if m == "google_auth" or m.startswith(("google.ads", "google.oauth2",
                                                     "google.analytics", "googleapiclient"))]
    assert leaked == [], leaked


# ---- (b) live mode is untouched ----

@pytest.mark.parametrize("name", sorted(PULLS))
def test_without_demo_mode_the_branch_does_not_hijack(name, tmp_path):
    """No DEMO_MODE: the scripts take their normal path and stop on missing creds.

    Offline — each fails while loading credentials, before any network call — but the
    point is that nothing was served and no output file appeared.
    """
    out = tmp_path / "live.csv"
    argv, _ = PULLS[name]
    r = run([*argv, "--output", str(out)])

    assert r.returncode != 0
    assert "[demo]" not in r.stderr and "[demo]" not in r.stdout
    assert not out.exists()
    combined = r.stdout + r.stderr
    assert "Missing required env vars" in combined or "credentials" in combined, combined


def test_live_argument_validation_still_runs():
    """A bad --range is still rejected by the live path, not swallowed by the branch."""
    r = run(["scripts/google_ads_pull.py", "--range", "fortnight", "--output", "-"])
    assert r.returncode == 2
    assert "--range must be like" in r.stderr


# ---- (c) ETL round-trip against a copy of the seeded database ----

@pytest.fixture
def seeded_copy(tmp_path):
    """A throwaway FLEET_ROOT seeded fresh (as of yesterday, like demo-reset).

    Never copies the workspace DB: after a live demo day the workspace already holds
    today's ETL rows and journal churn, and the insert/idempotency split below would
    have nothing to measure. A fresh seed is ~2s and independent of workspace state.
    """
    root = tmp_path / "fleet"
    (root / "state" / "identity").mkdir(parents=True)
    shutil.copy(ROOT / "state" / "identity" / "scribe-pm-cadence.yaml",
                root / "state" / "identity" / "scribe-pm-cadence.yaml")
    r = run(["scripts/seed_demo_state.py", "--profile", "orrery", "--as-of", "yesterday", "--force"],
            {"FLEET_ROOT": str(root)})
    assert r.returncode == 0, r.stdout + r.stderr
    return root


def etl(root, *argv):
    return run(["scripts/google_to_sqlite.py", *argv], {"FLEET_ROOT": str(root)})


def rows(root, sql, params=()):
    con = sqlite3.connect(root / "state" / "working" / "fleet.db")
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params)]
    finally:
        con.close()


def test_ads_spend_etl_lands_today_and_is_idempotent(seeded_copy, tmp_path):
    out = tmp_path / "spend.csv"
    r, _ = demo_run("ads-spend-watch", out)
    assert r.returncode == 0, r.stderr

    first = etl(seeded_copy, "ads-spend", "--input", str(out))
    assert first.returncode == 0, first.stderr
    assert "inserted=42 skipped=0" in first.stderr

    today = utc_today().isoformat()
    landed = rows(seeded_copy,
                  "SELECT campaign_name, spend FROM paid_creative "
                  "WHERE snapshot_date = ? AND creative_id LIKE '__campaign_aggregate_%'",
                  (today,))
    assert {r["campaign_name"] for r in landed} == {
        "Brand — Core", "Nonbrand — Incident Mgmt", "Competitor — Conquest"}

    again = etl(seeded_copy, "ads-spend", "--input", str(out))
    assert again.returncode == 0, again.stderr
    assert "inserted=0 skipped=42" in again.stderr


def test_gsc_etl_lands_today_joins_history_and_is_idempotent(seeded_copy, tmp_path):
    out = tmp_path / "gsc.csv"
    r, _ = demo_run("gsc-queries", out)
    assert r.returncode == 0, r.stderr

    first = etl(seeded_copy, "gsc-rankings", "--input", str(out),
                "--keywords-file", str(KEYWORDS_FILE))
    assert first.returncode == 0, first.stderr
    # Every fixture keyword is a tracked keyword: nothing may be dropped as untracked.
    assert "inserted=15 skipped_existing=0 skipped_untracked=0" in first.stderr

    today = utc_today().isoformat()
    landed = rows(seeded_copy, "SELECT keyword, position, prior_position, position_delta "
                               "FROM keyword_rankings WHERE snapshot_date = ?", (today,))
    assert len(landed) == 15
    assert all(r["prior_position"] is not None for r in landed), \
        "fixture keywords must join to the seeded history"

    again = etl(seeded_copy, "gsc-rankings", "--input", str(out),
                "--keywords-file", str(KEYWORDS_FILE))
    assert again.returncode == 0, again.stderr
    assert "inserted=0 skipped_existing=15" in again.stderr


# ---- (d) the planted anomalies clear their thresholds ----

def spend_series(root, campaign):
    """(date, spend, conversions) for the fixture's campaign-aggregate rows, oldest first."""
    return rows(root, "SELECT snapshot_date, spend, conversions FROM paid_creative "
                      "WHERE campaign_name = ? AND creative_id LIKE '__campaign_aggregate_%' "
                      "ORDER BY snapshot_date", (campaign,))


def deviation_pct(value, baseline):
    """spend-watch's deviation: >25% above the trailing 7-day average is MED."""
    return 100.0 * (value - baseline) / baseline


def test_planted_spend_spike_clears_the_med_threshold(seeded_copy, tmp_path):
    out = tmp_path / "spend.csv"
    assert demo_run("ads-spend-watch", out)[0].returncode == 0
    assert etl(seeded_copy, "ads-spend", "--input", str(out)).returncode == 0
    today = utc_today().isoformat()

    series = spend_series(seeded_copy, "Nonbrand — Incident Mgmt")
    trailing = [r for r in series if r["snapshot_date"] < today][-7:]
    assert len(trailing) == 7
    baseline = sum(r["spend"] for r in trailing) / 7
    value = next(r["spend"] for r in series if r["snapshot_date"] == today)
    assert deviation_pct(value, baseline) > 25.0

    # CPL trips its own >20% day-over-day rule on the same campaign.
    cpl_base = sum(r["spend"] for r in trailing) / sum(r["conversions"] for r in trailing)
    row = next(r for r in series if r["snapshot_date"] == today)
    assert deviation_pct(row["spend"] / row["conversions"], cpl_base) > 20.0

    # ...and it is the ONLY campaign that moves: the rest stay inside the threshold.
    for campaign in ("Brand — Core", "Competitor — Conquest"):
        s = spend_series(seeded_copy, campaign)
        prior = [r for r in s if r["snapshot_date"] < today][-7:]
        base = sum(r["spend"] for r in prior) / 7
        v = next(r["spend"] for r in s if r["snapshot_date"] == today)
        assert abs(deviation_pct(v, base)) < 25.0, campaign


def test_planted_spend_spike_also_clears_the_seeded_ad_level_baseline(seeded_copy, tmp_path):
    """The spike is sized against the seeded story, not just against its own fixture."""
    out = tmp_path / "spend.csv"
    assert demo_run("ads-spend-watch", out)[0].returncode == 0
    assert etl(seeded_copy, "ads-spend", "--input", str(out)).returncode == 0
    today = utc_today().isoformat()

    seeded = rows(seeded_copy,
                  "SELECT SUM(spend) AS spend FROM paid_creative "
                  "WHERE campaign_name = 'Nonbrand — Incident Mgmt' "
                  "AND creative_id NOT LIKE '__campaign_aggregate_%' "
                  "GROUP BY snapshot_date ORDER BY snapshot_date DESC LIMIT 7")
    assert len(seeded) == 7, "the seeded campaign history is missing"
    baseline = sum(r["spend"] for r in seeded) / 7
    value = next(r["spend"] for r in spend_series(seeded_copy, "Nonbrand — Incident Mgmt")
                 if r["snapshot_date"] == today)
    assert deviation_pct(value, baseline) > 25.0


def test_planted_ranking_drop_exits_the_top_20(seeded_copy, tmp_path):
    out = tmp_path / "gsc.csv"
    assert demo_run("gsc-queries", out)[0].returncode == 0
    assert etl(seeded_copy, "gsc-rankings", "--input", str(out),
               "--keywords-file", str(KEYWORDS_FILE)).returncode == 0

    row = rows(seeded_copy, "SELECT position, prior_position, position_delta FROM "
                            "keyword_rankings WHERE snapshot_date = ? AND keyword = ?",
               (utc_today().isoformat(), "sidereal on call"))[0]
    assert row["prior_position"] <= 20 and row["position"] > 20, row   # HIGH: exits top 20
    assert row["position_delta"] <= -10, row                           # MED: drop >10


def test_planted_landing_page_sag_is_sessions_up_conversions_down(tmp_path):
    """The GA4 fixture carries one page worth a dossier bullet; the rest are flat."""
    out = tmp_path / "ga4.csv"
    assert demo_run("ga4-pages", out)[0].returncode == 0
    with out.open(newline="") as f:
        data = list(csv.DictReader(f))

    sag = [r for r in data if r["pagePath"] == "/product/incident-response"
           and r["sessionSourceMedium"] == "google / cpc"]
    assert len(sag) == 7
    first, last = sag[0], sag[-1]
    assert int(last["sessions"]) > 2 * int(first["sessions"])
    assert int(last["conversions"]) <= int(first["conversions"]) / 2
    assert last["date"] == utc_today().isoformat()

    # Nothing else in the file tells the same story.
    others = {(r["pagePath"], r["sessionSourceMedium"]) for r in data} - {
        ("/product/incident-response", "google / cpc")}
    for page, medium in others:
        series = [r for r in data if r["pagePath"] == page
                  and r["sessionSourceMedium"] == medium]
        lo, hi = series[0], series[-1]
        assert int(hi["sessions"]) < 2 * int(lo["sessions"]), (page, medium)


# ---- (e) fixture hygiene ----

def test_fixtures_are_rendered_orrery_payloads():
    """No profile tokens, no real domains: fixtures are payloads, not kit files."""
    profile_token = re.compile(r"\{\{([A-Z][A-Z0-9_]+|company_slug)\}\}")
    for path in sorted((ROOT / "fixtures" / "google").rglob("*.csv")):
        text = path.read_text()
        assert not profile_token.search(text), f"{path.name} carries a profile token"
        for url in re.findall(r"https?://([^/,\s\"]+)", text):
            assert url.endswith(".example"), f"{path.name}: {url}"
