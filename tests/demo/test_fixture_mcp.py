"""Tests for the DEMO_MODE fixture layer (scripts/demo/).

No live MCP session and no credentials: the tools are plain functions, so these call
them directly and check tool registration the way tests/luma/test_luma_mcp.py does —
`anyio.run(server.list_tools)`.

The load-bearing properties are the ones a demo dies on: fixtures still parse after the
date tokens are rendered, a missing fixture degrades instead of raising, the HubSpot
funnel keeps agreeing with the seeded story (SAL→SQL under the 35% threshold, MTD counts
never going backwards), and every write lands in the outbox rather than on a live
surface.
"""
import json
import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import anyio
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.demo import fixture_mcp as F  # noqa: E402
from scripts.demo.render_config import render_config  # noqa: E402

CONNECTORS = {"hubspot", "linear", "google-calendar", "gmail", "slack", "notion", "grain"}


@pytest.fixture
def fleet_root(tmp_path, monkeypatch) -> Path:
    """A throwaway FLEET_ROOT with a state/ directory, exported to the environment.

    fixture_mcp re-resolves the root on every call, so this redirects both the outbox
    and the database lookup without touching the real workspace.
    """
    root = tmp_path / "fleet"
    (root / "state" / "working").mkdir(parents=True)
    root = root.resolve()          # fleet_paths resolves; match it so path equality holds
    monkeypatch.setenv("FLEET_ROOT", str(root))
    return root


def seed_funnel_row(root: Path, mqls: int, sals: int, sqls: int, pipeline: float,
                    snapshot_date: str = "2026-08-21") -> None:
    """One funnel_snapshots row — the minimum the funnel derivation reads."""
    db = root / "state" / "working" / "fleet.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE funnel_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "agent TEXT, snapshot_date TEXT, mqls INTEGER, sals INTEGER, sqls INTEGER, "
                "pipeline_value REAL, mql_to_sal_rate REAL, sal_to_sql_rate REAL, "
                "notes TEXT, created_at TEXT)")
    con.execute("INSERT INTO funnel_snapshots (agent, snapshot_date, mqls, sals, sqls, "
                "pipeline_value, created_at) VALUES ('revops-watchdog', ?, ?, ?, ?, ?, ?)",
                (snapshot_date, mqls, sals, sqls, pipeline, "2026-08-21T13:40:00Z"))
    con.commit()
    con.close()


# ---- (a) date-token rendering ----

def test_render_tokens_covers_every_documented_form():
    today = date(2026, 8, 26)                      # a Wednesday
    now = datetime(2026, 8, 26, 14, 5, 9, tzinfo=timezone.utc)
    out = F.render_tokens(
        '{"a":"{{TODAY}}","b":"{{T+0d}}","c":"{{T-3d}}","d":"{{T+2d}}",'
        '"e":"{{MONDAY}}","f":"{{NOW}}","g":"{{T+0d}}T15:30:00Z"}',
        today=today, now=now)
    got = json.loads(out)
    assert got["a"] == got["b"] == "2026-08-26"
    assert got["c"] == "2026-08-23" and got["d"] == "2026-08-28"
    assert got["e"] == "2026-08-24"                # Monday of that week
    assert got["f"] == "2026-08-26T14:05:09Z"
    assert got["g"] == "2026-08-26T15:30:00Z"      # offset + a literal clock time


def test_render_tokens_leaves_unknown_braces_alone():
    assert F.render_tokens("{{COMPANY}} {{T-1d}}", today=date(2026, 8, 26)) == "{{COMPANY}} 2026-08-25"


def test_render_tokens_defaults_to_now():
    assert datetime.now(timezone.utc).date().isoformat() in F.render_tokens("{{T+0d}}")


# ---- (b) the funnel stays consistent with the seeded story ----

def test_funnel_is_derived_from_the_database_and_keeps_the_dip(fleet_root):
    seed_funnel_row(fleet_root, mqls=47, sals=31, sqls=9, pipeline=1_126_093.0)
    f = F.funnel_numbers()
    assert f["mqls"] >= 47 and f["sals"] >= 31          # MTD counts never go backwards
    assert f["sqls"] >= 9
    assert f["sal_to_sql_rate"] < 35.0                  # day N+1 of the planted dip
    assert f["pipeline_value"] > 1_126_093.0
    assert "funnel_snapshots" in f["derived_from"]
    assert f["mql_p1"] + f["mql_p2"] + f["mql_out"] == f["mqls"]


@pytest.mark.parametrize("mqls,sals,sqls", [(20, 12, 3), (47, 31, 9), (140, 96, 30), (5, 3, 1)])
def test_sal_to_sql_stays_under_the_threshold_for_any_seed(fleet_root, mqls, sals, sqls):
    seed_funnel_row(fleet_root, mqls=mqls, sals=sals, sqls=sqls, pipeline=900_000.0)
    assert F.funnel_numbers()["sal_to_sql_rate"] < 35.0


def test_funnel_falls_back_to_the_fixture_without_a_database(fleet_root):
    f = F.funnel_numbers()                              # no fleet.db written
    assert f["derived_from"] == "fixtures/hubspot/funnel.json"
    assert f["sal_to_sql_rate"] < 35.0


def test_contact_cohorts_and_pipeline_match_the_funnel(fleet_root):
    seed_funnel_row(fleet_root, mqls=47, sals=31, sqls=9, pipeline=1_126_093.0)
    f = F.funnel_numbers()
    sal = F.search_crm_objects("contacts", filterGroups=[{"filters": [
        {"propertyName": "mql_date__latest_", "operator": "GTE", "value": "2026-08-01"},
        {"propertyName": "sal_date__latest_", "operator": "GTE", "value": "2026-08-01"}]}])
    assert sal["total"] == f["sals"]
    sql = F.search_crm_objects("contacts", filterGroups=[{"filters": [
        {"propertyName": "mql_date__latest_", "operator": "GTE", "value": "2026-08-01"},
        {"propertyName": "sal_date__latest_", "operator": "GTE", "value": "2026-08-01"},
        {"propertyName": "sql_date__latest_", "operator": "GTE", "value": "2026-08-01"}]}])
    assert sql["total"] == f["sqls"]
    deals = F.search_crm_objects("deals", properties=["amount"], limit=200, filterGroups=[
        {"filters": [{"propertyName": "pipeline", "operator": "EQ", "value": "90000001"}]}])
    assert deals["total"] == f["open_deals"]
    assert round(sum(float(d["properties"]["amount"]) for d in deals["results"]), 2) == f["pipeline_value"]


def test_mql_type_filters_split_the_mql_total(fleet_root):
    seed_funnel_row(fleet_root, mqls=47, sals=31, sqls=9, pipeline=900_000.0)
    f = F.funnel_numbers()
    totals = []
    for value in ("MQL Handraiser - P1", "MQL Score Threshold - P2", "Outbound"):
        out = F.search_crm_objects("contacts", filterGroups=[{"filters": [
            {"propertyName": "mql_date__latest_", "operator": "GTE", "value": "2026-08-01"},
            {"propertyName": "mql_type_latest", "operator": "EQ", "value": value}]}])
        totals.append(out["total"])
    assert sum(totals) == f["mqls"]


# ---- (c) writes land in the outbox, never on a live surface ----

def test_slack_send_message_writes_to_the_outbox(fleet_root):
    out = F.slack_send_message(channel_id="C0DEMO0001", message="AM brief\n\nSAL to SQL still under threshold.")
    assert out["ok"] is True
    assert out["channel_label"] == "#team-marketing"
    assert "." in out["ts"] and out["ts"].replace(".", "").isdigit()
    path = fleet_root / "state" / "demo-outbox" / "slack.md"
    assert path.exists()
    body = path.read_text()
    assert f"ts={out['ts']}" in body and "#team-marketing" in body
    assert "SAL to SQL still under threshold." in body
    # deterministic: the same send produces the same ts, and appends rather than replaces
    again = F.slack_send_message(channel_id="C0DEMO0001", message="AM brief\n\nSAL to SQL still under threshold.")
    assert again["ts"] == out["ts"]
    assert path.read_text().count("ts=") == 2


def test_slack_send_message_resolves_a_user_dm(fleet_root):
    out = F.slack_send_message(channel_id="U0DEMO0001", message="hello")
    assert out["channel_label"] == "@Scott McKeighen"
    assert "@Scott McKeighen" in (fleet_root / "state" / "demo-outbox" / "slack.md").read_text()


def test_notion_create_pages_writes_a_slugged_file(fleet_root):
    out = F.notion_create_pages(
        parent={"database_id": "00000000-0000-4000-8000-000000000101"},
        pages=[{"properties": {"Name": "Marketing Update — 2026-08-28"},
                "content": "## Summary\n\n51 MQLs, 33 SALs, 10 SQLs."}])
    path = fleet_root / "state" / "demo-outbox" / "notion" / "marketing-update-2026-08-28.md"
    assert path.exists(), sorted(p.name for p in (fleet_root / "state/demo-outbox/notion").glob("*"))
    text = path.read_text()
    assert "51 MQLs, 33 SALs, 10 SQLs." in text
    assert "00000000-0000-4000-8000-000000000101" in text        # parent recorded
    assert out["url"].startswith("file://") and out["url"].endswith(path.name)
    assert out["id"].startswith("0" * 16) and len(out["id"]) == 32
    assert out["_provenance"]["tier"] == "demo-fixture"


def test_notion_update_page_appends_to_the_same_file(fleet_root):
    F.notion_create_pages(parent={}, pages=[{"properties": {"Name": "WBR draft"}, "content": "first"}])
    F.notion_update_page(page_id="00000000000000000000000000000210", title="WBR draft", content="second")
    text = (fleet_root / "state" / "demo-outbox" / "notion" / "wbr-draft.md").read_text()
    assert "first" in text and "second" in text and "## Update" in text


def test_no_write_escapes_the_outbox(fleet_root):
    F.slack_send_message(channel_id="C0DEMO0001", message="x")
    F.notion_create_pages(parent={}, pages=[{"properties": {"Name": "y"}, "content": "z"}])
    written = {p.relative_to(fleet_root).as_posix() for p in fleet_root.rglob("*") if p.is_file()}
    assert written == {"state/demo-outbox/slack.md", "state/demo-outbox/notion/y.md"}


# ---- (d) every fixture parses after rendering ----

def test_every_fixture_parses_after_token_rendering():
    files = sorted((ROOT / "fixtures").rglob("*.json"))
    assert files, "no fixtures found"
    for path in files:
        rendered = F.render_tokens(path.read_text())
        json.loads(rendered)                       # raises on malformed JSON
        assert "{{" not in rendered, f"{path} has an unrendered token"


def test_fixture_dates_render_to_real_dates():
    events = F.load_fixture("google-calendar", "list_events")
    today = datetime.now(timezone.utc).date().isoformat()
    assert events["events"][0]["start"]["dateTime"].startswith(today)


# ---- (e) a missing fixture degrades, it does not raise ----

def test_missing_fixture_returns_a_labeled_empty_result():
    out = F.read("hubspot", "get_campaign_analytics")
    assert out["results"] == [] and out["total"] == 0
    assert "No fixture at fixtures/hubspot/get_campaign_analytics.json" in out["_demo_note"]
    assert out["_provenance"] == {"tier": "demo-fixture",
                                  "source": "fixtures/hubspot/get_campaign_analytics.json"}


def test_every_registered_tool_answers_with_provenance(fleet_root):
    """No read tool may raise, whatever its fixture state — a demo degrades visibly."""
    for connector, tools in F.REGISTRY.items():
        for name, fn in tools.items():
            if name in ("slack_send_message", "notion-create-pages", "notion-update-page"):
                continue
            out = fn() if name not in ("search_crm_objects",) else fn("contacts")
            assert out["_provenance"]["tier"] == "demo-fixture", f"{connector}.{name}"


# ---- tool registration: the names the prompts call ----

def test_servers_register_exactly_the_expected_tool_names():
    assert set(F.REGISTRY) == CONNECTORS
    for connector, tools in F.REGISTRY.items():
        names = {t.name for t in anyio.run(F.build_server(connector).list_tools)}
        assert names == set(tools), f"{connector}: {names} != {set(tools)}"
    notion = {t.name for t in anyio.run(F.build_server("notion").list_tools)}
    assert "notion-create-pages" in notion and "notion-search" in notion   # hyphens survive


def test_unknown_connector_is_refused():
    with pytest.raises(SystemExit):
        F.build_server("salesforce")


# ---- (f) the MCP config template renders ----

def test_render_config_substitutes_both_roots(fleet_root, tmp_path):
    out = render_config(out=tmp_path / "demo-mcp.resolved.json")
    cfg = json.loads(out.read_text())
    assert set(cfg["mcpServers"]) == CONNECTORS
    for name, server in cfg["mcpServers"].items():
        assert "{PLUGIN_ROOT}" not in json.dumps(server) and "{FLEET_ROOT}" not in json.dumps(server)
        assert Path(server["args"][0]).is_absolute() and Path(server["args"][0]).exists()
        assert server["args"][1] == name
        assert server["env"]["FLEET_ROOT"] == str(fleet_root)


def test_render_config_defaults_into_state_working(fleet_root):
    out = render_config()
    assert out == fleet_root / "state" / "working" / "demo-mcp.resolved.json"
    assert len(json.loads(out.read_text())["mcpServers"]) == 7


# ---- (g) the no-MCP CLI fallback ----

def test_connector_cli_round_trip(fleet_root):
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/demo/connector.py"), "hubspot", "search_crm_objects",
         '{"objectType":"contacts"}'],
        capture_output=True, text=True, env={**os.environ, "FLEET_ROOT": str(fleet_root)})
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["_provenance"]["tier"] == "demo-fixture"
    assert out["total"] == 20 and out["results"][0]["properties"]["email"].endswith(".example")


def test_connector_cli_write_reaches_the_outbox(fleet_root):
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/demo/connector.py"), "slack", "slack_send_message",
         '{"channel_id":"C0DEMO0001","message":"from the cli"}'],
        capture_output=True, text=True, env={**os.environ, "FLEET_ROOT": str(fleet_root)})
    assert r.returncode == 0, r.stderr
    assert "from the cli" in (fleet_root / "state" / "demo-outbox" / "slack.md").read_text()


def test_connector_cli_rejects_an_unknown_tool(fleet_root):
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/demo/connector.py"), "slack", "delete_everything"],
        capture_output=True, text=True, env={**os.environ, "FLEET_ROOT": str(fleet_root)})
    assert r.returncode == 2 and "unknown tool" in r.stderr


# ---- the demo data set says what the story needs it to say ----

def test_fixture_story_invariants():
    workflows = F.load_fixture("hubspot", "workflows")["results"]
    assert [w for w in workflows if w["first_step_exit_rate"] >= 1.0], "the HIGH workflow anomaly is missing"
    contacts = F.load_fixture("hubspot", "contacts_recent")["results"]
    both = [c for c in contacts if c["properties"]["opsos__person_id"] and c["properties"]["opsos__company_id"]]
    assert len(both) / len(contacts) >= 0.9, "enrichment coverage should read CLEAR"
    issues = F.load_fixture("linear", "list_issues")["issues"]
    assert len(issues) == 18
    soon = date.today() + timedelta(days=7)
    urgent = [i for i in issues
              if i["priorityLabel"] in ("Urgent", "High") and date.fromisoformat(i["dueDate"]) <= soon]
    assert len(urgent) == 2, f"expected 2 High/Urgent issues due within a week, got {len(urgent)}"
    events = F.load_fixture("google-calendar", "list_events")["events"]
    assert len(events) == 2 and bool(events[0]["attachments"]) and not events[1]["attachments"]
    threads = F.load_fixture("gmail", "search_threads")["threads"]
    assert len(threads) == 30
    assert len([t for t in threads if t["_demo_class"] == "customer"]) == 1
    replies = F.load_fixture("slack", "slack_read_thread")["messages"]
    assert len([m for m in replies if not m["is_bot"]]) == 1
