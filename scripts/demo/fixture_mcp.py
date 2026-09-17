#!/usr/bin/env python3
"""
Fixture MCP server — DEMO_MODE connectors for the GTM Fleet (migration plan §4).

One process serves ONE connector over stdio FastMCP, same bootstrap as
scripts/luma_mcp.py:

    python3 scripts/demo/fixture_mcp.py hubspot

`mcp/demo.json` registers all seven (hubspot, linear, google-calendar, gmail,
slack, notion, grain) under the stable `mcp__<server>__<tool>` names the prompts
and `.claude/settings.json` already use, so an agent running with DEMO_MODE=1
calls exactly the tools it would call live — with no credentials anywhere.

**Reads** load `PLUGIN_ROOT/fixtures/<connector>/<tool>.json`. A missing file is
not an error: the tool returns a clearly-labeled empty result so a demo never
dies on a fixture gap. Every response carries a `_provenance` stamp naming its
fixture, mirroring the Luma server's envelope.

**Writes** never leave the machine. `slack_send_message` appends a block to
`FLEET_ROOT/state/demo-outbox/slack.md`; `notion-create-pages` /
`notion-update-page` write `FLEET_ROOT/state/demo-outbox/notion/<slug>.md`. Both
return a realistic success payload (deterministic fake ts / page id, plus a
`file://` path) so the agent can say where the write landed.

**Date tokens.** Fixture JSON may carry day offsets (`{{T+0d}}`, `{{T-3d}}`) and the
named forms TODAY, NOW, and MONDAY in the same double braces; they are substituted
in the raw text before it is parsed, so a fixture written months ago still reads as
"today". The shipped fixtures use the offset form only — the named forms collide
with scripts/profile_render.py's uppercase-token scan (fixtures/README.md).

**The derived surface.** HubSpot's funnel is not a static fixture: it is read
from the seeded database (latest `funnel_snapshots` row) plus one weekday's
deterministic increment, holding SAL→SQL below the 35% threshold. The planted dip
therefore continues into the demo day — revops-watchdog finds its MED anomaly on day N+1 —
and the numbers HubSpot reports can never drift out of agreement with the story
already in the journals. `fixtures/hubspot/funnel.json` is the fallback when
there is no database.

CLI:
    python3 scripts/demo/fixture_mcp.py <connector>   # run the MCP server (stdio)
    python3 scripts/demo/fixture_mcp.py --list        # print connector → tool names
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402
from scripts.demo.dates import render_tokens  # noqa: E402

from mcp.server.fastmcp import FastMCP  # noqa: E402

FIXTURES_DIR = fleet_paths.PLUGIN_ROOT / "fixtures"
PROV_TIER = "demo-fixture"

# Today's numbers = the last seeded snapshot + one weekday. SAL→SQL is then held
# under revops-watchdog's 35% absolute threshold so the planted dip reads as day N+1.
MQL_DAY_INCREMENT = 4
SAL_DAY_INCREMENT = 2
PIPELINE_DAY_INCREMENT = 11_000.0
SAL_TO_SQL_TARGET_PCT = 33.0
MQL_P1_SHARE, MQL_P2_SHARE = 0.22, 0.55       # inbound handraisers / auto-score; rest is outbound
MEL_PER_MQL = 5.8                             # MEL is upstream of MQL, never queried by cohort
AVG_OPEN_DEAL = 12_800.0                      # pipeline value → open-deal count


# ============================================================
# Roots, tokens, fixture loading
# ============================================================

def _fleet_root() -> Path:
    """FLEET_ROOT, re-resolved per call so an env override (tests, external state)
    wins over whatever was current when this module was imported."""
    return fleet_paths.fleet_root(strict=False)


def _db_path() -> Path:
    """fleet_paths.DB_PATH against the currently-resolved FLEET_ROOT."""
    return _fleet_root() / "state" / "working" / fleet_paths.DB_NAME


def outbox_dir() -> Path:
    """FLEET_ROOT/state/demo-outbox, created on demand. Every DEMO_MODE write lands here."""
    d = _fleet_root() / "state" / "demo-outbox"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fixture_path(connector: str, tool: str) -> Path:
    return FIXTURES_DIR / connector / f"{tool}.json"


def load_fixture(connector: str, tool: str):
    """Parsed fixture for <connector>/<tool>, or None when the file does not exist."""
    path = fixture_path(connector, tool)
    if not path.exists():
        return None
    return json.loads(render_tokens(path.read_text()))


def _provenance(connector: str, tool: str) -> dict:
    return {"tier": PROV_TIER, "source": f"fixtures/{connector}/{tool}.json"}


def _envelope(data, connector: str, tool: str) -> dict:
    """Fixture payload plus a `_provenance` stamp (a bare list is wrapped in `results`)."""
    prov = _provenance(connector, tool)
    if isinstance(data, dict):
        return {**data, "_provenance": prov}
    return {"results": data, "_provenance": prov}


def _derived(data: dict, source: str) -> dict:
    """Envelope for a response computed from the seeded database rather than read from a
    fixture file. Same tier; `source` names the derivation so provenance stays honest."""
    return {**data, "_provenance": {"tier": PROV_TIER, "source": source}}


def read(connector: str, tool: str, fixture: Optional[str] = None) -> dict:
    """Serve a read tool from its fixture file.

    `fixture` names a different file when several tools share one (e.g. Gmail's two
    search tools). A missing file yields an empty, explicitly-labeled result rather
    than an exception — a demo should degrade visibly, never crash.
    """
    name = fixture or tool
    data = load_fixture(connector, name)
    if data is None:
        return {
            "results": [], "total": 0,
            "_demo_note": (f"No fixture at fixtures/{connector}/{name}.json — returning an "
                           f"empty result. Add the file to give this tool demo data."),
            "_provenance": _provenance(connector, name),
        }
    return _envelope(data, connector, name)


# ============================================================
# HubSpot — funnel numbers derived from the seeded database
# ============================================================

def _latest_funnel_row() -> Optional[dict]:
    """The newest `funnel_snapshots` row, or None if there is no readable database."""
    db = _db_path()
    if not db.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT snapshot_date, mqls, sals, sqls, pipeline_value FROM funnel_snapshots "
            "ORDER BY snapshot_date DESC, id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error:
        return None
    finally:
        con.close()


def funnel_numbers() -> dict:
    """Today's MTD funnel figures — the one place HubSpot's demo numbers come from.

    Derived from the seeded database so the CRM can never contradict the journals:
    the latest `funnel_snapshots` row plus one weekday's deterministic increment,
    with SQL count pinned so SAL→SQL stays under the 35% threshold revops-watchdog watches.
    Falls back to fixtures/hubspot/funnel.json when no database is present.
    """
    row = _latest_funnel_row()
    if row is None:
        fx = load_fixture("hubspot", "funnel") or {}
        mtd = fx.get("month_to_date", {})
        mqls = int(mtd.get("mqls", 0))
        sals = int(mtd.get("sals", 0))
        sqls = int(mtd.get("sqls", 0))
        pipeline = float(mtd.get("pipeline_value", 0.0))
        source = "fixtures/hubspot/funnel.json"
    else:
        mqls = int(row["mqls"] or 0) + MQL_DAY_INCREMENT
        sals = min(int(row["sals"] or 0) + SAL_DAY_INCREMENT, mqls)
        prior_sqls = int(row["sqls"] or 0)
        # Monotone MTD (never below yesterday) but capped so the dip continues.
        sqls = max(prior_sqls, min(prior_sqls + 1, int(sals * SAL_TO_SQL_TARGET_PCT / 100)))
        while sals and 100.0 * sqls / sals >= 35.0:
            sqls -= 1
        pipeline = float(row["pipeline_value"] or 0.0) + PIPELINE_DAY_INCREMENT
        source = f"funnel_snapshots (snapshot_date={row['snapshot_date']}) + 1 weekday"

    p1 = round(mqls * MQL_P1_SHARE)
    p2 = round(mqls * MQL_P2_SHARE)
    return {
        "as_of": datetime.now(timezone.utc).date().isoformat(),
        "mels": round(mqls * MEL_PER_MQL),
        "mqls": mqls, "mql_p1": p1, "mql_p2": p2, "mql_out": max(0, mqls - p1 - p2),
        "sals": sals, "sqls": sqls,
        "mql_to_sal_rate": round(100.0 * sals / mqls, 1) if mqls else 0.0,
        "sal_to_sql_rate": round(100.0 * sqls / sals, 1) if sals else 0.0,
        "pipeline_value": round(pipeline, 2),
        "open_deals": max(1, round(pipeline / AVG_OPEN_DEAL)),
        "derived_from": source,
    }


_DEAL_ACCOUNTS = [
    "Northlake Fintech", "Calloway Robotics", "Harborlight Health", "Ridgeway Logistics",
    "Quillon Data", "Marchmont Retail", "Vellum Analytics", "Stonebridge Payments",
    "Aperture Grid", "Fernhill Media", "Cobalt Freight", "Tessellate Labs",
]
_DEAL_STAGES = ["900000101", "900000104", "900000105", "900000106"]


def open_deals(total: float, count: int) -> list[dict]:
    """`count` synthetic open deals whose `amount` values sum to exactly `total`.

    Seeded on the pipeline value, so the same funnel produces the same deal list on
    every call — a demo re-run shows the same board.
    """
    rng = random.Random(int(total))
    weights = [rng.uniform(0.55, 1.6) for _ in range(count)]
    scale = total / sum(weights) if weights else 0.0
    deals, running = [], 0.0
    for i, w in enumerate(weights):
        amount = round(w * scale, 2)
        if i == count - 1:
            amount = round(total - running, 2)   # absorb rounding drift in the last deal
        running = round(running + amount, 2)
        account = _DEAL_ACCOUNTS[i % len(_DEAL_ACCOUNTS)]
        deals.append({
            "id": f"9001{i:06d}",
            "properties": {
                "dealname": f"{account} — Orrery Platform",
                "amount": f"{amount:.2f}",
                "pipeline": "90000001",
                "dealstage": _DEAL_STAGES[i % len(_DEAL_STAGES)],
                "dealtype": "newbusiness",
            },
        })
    return deals


def _filter_props(filter_groups) -> dict:
    """{propertyName: [values]} flattened across every filter group.

    HubSpot's filterGroups are OR-of-ANDs; for routing a demo query we only care
    which properties were named, not how they were combined.
    """
    out: dict[str, list] = {}
    for group in filter_groups or []:
        if not isinstance(group, dict):
            continue
        for filt in group.get("filters") or []:
            if not isinstance(filt, dict):
                continue
            name = filt.get("propertyName")
            if not name:
                continue
            vals = out.setdefault(name, [])
            if filt.get("value") is not None:
                vals.append(filt["value"])
            vals.extend(filt.get("values") or [])
    return out


_CONTACT_SAMPLE_CAP = 25


def _contact_cohort(total: int, label: str) -> dict:
    """A `{total, results}` contact page: the exact count, a bounded sample of records.

    funnel-stats reads `total`; materializing all of a 400-contact cohort would only
    bloat the transcript, so the sample is capped and the truncation is stated.
    """
    n = min(total, _CONTACT_SAMPLE_CAP)
    today = datetime.now(timezone.utc).date()
    results = []
    for i in range(n):
        d = (today - timedelta(days=i % 20)).isoformat()
        results.append({
            "id": f"7010{i:06d}",
            "properties": {
                "email": f"{label.lower()}.contact{i + 1}@{_DEAL_ACCOUNTS[i % len(_DEAL_ACCOUNTS)].split()[0].lower()}.example",
                "createdate": d, "mel_date": d, "mql_date__latest_": d,
                "sal_date__latest_": d, "sql_date__latest_": d,
                "lifecyclestage": label.lower(),
            },
        })
    out = {"total": total, "results": results, "_demo_cohort": label}
    if total > n:
        out["_demo_note"] = (f"`total` is the full {label} cohort ({total}); `results` carries the "
                             f"first {n} records only. Read the count from `total`.")
    return out


# ============================================================
# HubSpot tools
# ============================================================

def search_crm_objects(objectType: str, query: str = "", filterGroups: Optional[list] = None,
                       properties: Optional[list] = None, limit: int = 100,
                       after: Optional[str] = None) -> dict:
    """Search CRM objects. `objectType` is 'contacts' or 'deals'; `filterGroups` follows
    HubSpot's OR-of-ANDs shape. Contact cohorts (MEL / MQL by type / SAL / SQL) and open
    pipeline are derived from the seeded funnel so every count agrees with revops-watchdog's
    snapshot; other contact queries serve fixtures/hubspot/contacts_recent.json."""
    f = funnel_numbers()
    props = _filter_props(filterGroups)

    if str(objectType).lower().startswith("deal"):
        deals = open_deals(f["pipeline_value"], f["open_deals"])
        start = int(after) if after and str(after).isdigit() else 0
        page = deals[start:start + max(1, int(limit or 100))]
        out = {"total": len(deals), "results": page, "_demo_pipeline_total": f["pipeline_value"]}
        if start + len(page) < len(deals):
            out["paging"] = {"next": {"after": str(start + len(page))}}
        return _derived(out, f["derived_from"])

    if "sql_date__latest_" in props:
        data = _contact_cohort(f["sqls"], "SQL")
    elif "sal_date__latest_" in props:
        data = _contact_cohort(f["sals"], "SAL")
    elif "mql_type_latest" in props:
        want = " ".join(str(v) for v in props["mql_type_latest"]).lower()
        if "handraiser" in want or "p1" in want:
            data = _contact_cohort(f["mql_p1"], "MQL Handraiser - P1")
        elif "threshold" in want or "p2" in want:
            data = _contact_cohort(f["mql_p2"], "MQL Score Threshold - P2")
        else:
            data = _contact_cohort(f["mql_out"], "Outbound")
    elif "mel_date" in props:
        data = _contact_cohort(f["mels"], "MEL")
    elif "mql_date__latest_" in props:
        data = _contact_cohort(f["mqls"], "MQL")
    else:
        # createdate / opsos__* sweeps and anything unrecognized: the 7-day new-contact
        # fixture, which carries the enrichment sentinel fields opsos-watch reads.
        return read("hubspot", "search_crm_objects", fixture="contacts_recent")
    return _derived(data, f["derived_from"])


def query_crm_data(query: str = "", objectType: Optional[str] = None,
                   limit: int = 100) -> dict:
    """Free-form CRM query. In demo mode the query text routes to a fixture: workflow
    questions serve fixtures/hubspot/workflows.json, lead-score questions
    fixtures/hubspot/scoring.json, enrichment/new-contact questions
    fixtures/hubspot/contacts_recent.json, anything else the funnel block."""
    q = f"{query} {objectType or ''}".lower()
    if "workflow" in q or "enrollment" in q:
        return read("hubspot", "query_crm_data", fixture="workflows")
    if "score" in q or "scoring" in q or "decile" in q:
        return read("hubspot", "query_crm_data", fixture="scoring")
    if "opsos__" in q or "enrich" in q or "createdate" in q or "new contact" in q:
        return read("hubspot", "query_crm_data", fixture="contacts_recent")
    f = funnel_numbers()
    return _derived({"funnel": f}, f["derived_from"])


def get_properties(objectType: str = "contacts", properties: Optional[list] = None) -> dict:
    """Property definitions for an object type (fixture-backed)."""
    return read("hubspot", "get_properties")


def search_properties(objectType: str = "contacts", query: str = "", limit: int = 100) -> dict:
    """Search property definitions by name or label (fixture-backed)."""
    return read("hubspot", "search_properties")


def get_user_details(include: Optional[list] = None) -> dict:
    """The authenticated CRM user, portal, and scopes — the preflight probe for ~~crm."""
    return read("hubspot", "get_user_details")


def get_campaign_analytics(campaignGuid: Optional[str] = None, startDate: Optional[str] = None,
                           endDate: Optional[str] = None) -> dict:
    """Marketing campaign analytics (fixture-backed; empty unless a fixture is added)."""
    return read("hubspot", "get_campaign_analytics")


# ============================================================
# Linear tools
# ============================================================

def list_issues(assignee: Optional[str] = None, team: Optional[str] = None,
                query: Optional[str] = None, project: Optional[str] = None,
                state: Optional[str] = None, updatedAt: Optional[str] = None,
                limit: int = 50, cursor: Optional[str] = None,
                includeArchived: bool = False) -> dict:
    """List issues. All filters are accepted and ignored in demo mode — the fixture is
    the open Marketing board (18 issues, urls under linear.app/orrery)."""
    return read("linear", "list_issues")


def list_projects(team: Optional[str] = None, query: Optional[str] = None,
                  updatedAt: Optional[str] = None, limit: int = 50,
                  cursor: Optional[str] = None) -> dict:
    """List projects with health, lead, and target date (fixture-backed)."""
    return read("linear", "list_projects")


def list_teams(query: Optional[str] = None, limit: int = 50) -> dict:
    """List teams (fixture-backed)."""
    return read("linear", "list_teams")


def get_issue(id: str = "", issueId: Optional[str] = None,
              includeRelations: bool = False) -> dict:
    """Fetch one issue by id or identifier. In demo mode the fixture issue is returned
    with the requested id echoed back so links stay consistent."""
    out = read("linear", "get_issue")
    wanted = issueId or id
    if wanted and isinstance(out.get("identifier"), str):
        out["_demo_requested_id"] = wanted
    return out


def list_comments(issueId: Optional[str] = None, projectId: Optional[str] = None,
                  limit: int = 50, cursor: Optional[str] = None) -> dict:
    """List comments on an issue or project (fixture-backed)."""
    return read("linear", "list_comments")


def get_status_updates(type: str = "project", project: Optional[str] = None,
                       team: Optional[str] = None, limit: int = 20) -> dict:
    """Latest project/team status updates with health (fixture-backed)."""
    return read("linear", "get_status_updates")


# ============================================================
# Google Calendar
# ============================================================

def list_events(calendarId: str = "primary", startTime: Optional[str] = None,
                endTime: Optional[str] = None, timeZone: Optional[str] = None,
                maxResults: int = 50, query: Optional[str] = None) -> dict:
    """Today's calendar events (fixture-backed): the window arguments are accepted and
    ignored — the fixture is already scoped to today."""
    return read("google-calendar", "list_events")


# ============================================================
# Gmail
# ============================================================

def search_threads(query: str = "", pageSize: int = 30,
                   pageToken: Optional[str] = None) -> dict:
    """Search inbox threads (Gmail query syntax, e.g. `is:unread in:inbox`)."""
    return read("gmail", "search_threads")


def gmail_search_messages(q: str = "", query: str = "", pageSize: int = 30,
                          pageToken: Optional[str] = None) -> dict:
    """Search inbox messages — the older tool name for the same search."""
    return read("gmail", "gmail_search_messages")


def gmail_read_message(messageId: str = "", id: Optional[str] = None,
                       threadId: Optional[str] = None) -> dict:
    """Read one message in full (fixture-backed: the customer ask chief-of-staff surfaces)."""
    return read("gmail", "gmail_read_message")


def gmail_get_profile() -> dict:
    """The authenticated mailbox — the preflight probe for ~~email."""
    return read("gmail", "gmail_get_profile")


# ============================================================
# Slack — one write tool
# ============================================================

def _slack_label(channel_id: str) -> str:
    """`#channel` / `@person` for a demo id, resolved from the Slack fixtures."""
    channels = (load_fixture("slack", "slack_search_channels") or {}).get("channels") or []
    for c in channels:
        if c.get("id") == channel_id:
            return f"#{c.get('name', channel_id)}"
    users = (load_fixture("slack", "slack_search_users") or {}).get("members") or []
    for u in users:
        if u.get("id") == channel_id:
            return f"@{u.get('real_name') or u.get('name') or channel_id}"
    return channel_id


def _fake_ts(*parts: str) -> str:
    """A Slack-shaped `ts` derived from the message itself — same send, same ts."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{1786000000 + int(digest[:6], 16) % 9_000_000}.{int(digest[6:12], 16) % 1_000_000:06d}"


def slack_send_message(channel_id: str, message: str,
                       thread_ts: Optional[str] = None) -> dict:
    """WRITE — post a message. In demo mode nothing reaches Slack: the block is appended
    to `state/demo-outbox/slack.md` and a realistic send receipt is returned."""
    label = _slack_label(channel_id)
    ts = _fake_ts(channel_id, message, thread_ts or "")
    path = outbox_dir() / "slack.md"
    header = f"## {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} | {label} | ts={ts}"
    if thread_ts:
        header += f" | in thread {thread_ts}"
    with open(path, "a") as fh:
        fh.write(f"\n{header}\n\n{message.rstrip()}\n")
    return {
        "ok": True, "ts": ts, "channel": channel_id, "channel_label": label,
        "thread_ts": thread_ts,
        "permalink": f"file://{path}#{ts}",
        "outbox_path": f"file://{path}",
        "_demo_note": f"DEMO_MODE write — appended to state/demo-outbox/slack.md, not sent to {label}.",
        "_provenance": {"tier": PROV_TIER, "source": "state/demo-outbox/slack.md"},
    }


def slack_read_thread(channel_id: str = "", thread_ts: str = "", limit: int = 100) -> dict:
    """Read a thread's replies (fixture-backed: yesterday's AM-brief thread)."""
    return read("slack", "slack_read_thread")


def slack_read_channel(channel_id: str = "", limit: int = 50,
                       oldest: Optional[str] = None) -> dict:
    """Read recent channel messages (fixture-backed)."""
    return read("slack", "slack_read_channel")


def slack_search_channels(query: str = "", limit: int = 20) -> dict:
    """Resolve a channel name to its id — the preflight probe for ~~chat."""
    return read("slack", "slack_search_channels")


def slack_search_users(query: str = "", limit: int = 20) -> dict:
    """Resolve a person's name to their Slack user id (the four cadence members)."""
    return read("slack", "slack_search_users")


# ============================================================
# Notion — two write tools
# ============================================================

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Filesystem-safe slug for an outbox page name."""
    return _SLUG_STRIP.sub("-", (title or "untitled").lower()).strip("-")[:80] or "untitled"


def _fake_page_id(slug: str) -> str:
    """A 32-char Notion-shaped id that is unmistakably fake: 26 zeros then 6 digits."""
    digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return "0" * 26 + f"{int(digest[:8], 16) % 1_000_000:06d}"


def _page_title(pages, properties, title) -> str:
    if title:
        return str(title)
    for src in (properties, (pages or [{}])[0] if pages else None):
        if isinstance(src, dict):
            for key in ("title", "Name", "name", "Title"):
                if src.get(key):
                    return str(src[key])
            nested = src.get("properties")
            if isinstance(nested, dict):
                for key in ("title", "Name", "name", "Title"):
                    if nested.get(key):
                        return str(nested[key])
    return "Untitled page"


def _page_content(pages, content) -> str:
    if content:
        return str(content)
    if pages:
        first = pages[0]
        if isinstance(first, dict):
            for key in ("content", "children", "body", "markdown"):
                if first.get(key):
                    return first[key] if isinstance(first[key], str) else json.dumps(first[key], indent=2)
    return "_(no page body supplied)_"


def notion_create_pages(parent: Optional[dict] = None, pages: Optional[list] = None,
                        properties: Optional[dict] = None, content: Optional[str] = None,
                        title: Optional[str] = None) -> dict:
    """WRITE — create a page. In demo mode the page is written to
    `state/demo-outbox/notion/<slug>.md` (front matter records the parent ids) and a
    fake page id plus a `file://` url is returned; Notion is never contacted."""
    parent = parent or {}
    name = _page_title(pages, properties, title)
    slug = slugify(name)
    page_id = _fake_page_id(slug)
    path = outbox_dir() / "notion" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    props = properties or ((pages or [{}])[0].get("properties") if pages else None) or {}
    front = [
        f"# {name}",
        "",
        f"- **DEMO_MODE Notion write** — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- **page id:** `{page_id}` (synthetic)",
        f"- **parent database id:** `{parent.get('database_id') or parent.get('data_source_id') or '—'}`",
        f"- **parent page id:** `{parent.get('page_id') or '—'}`",
        f"- **properties:** `{json.dumps(props, sort_keys=True)}`",
        "",
        "---",
        "",
    ]
    path.write_text("\n".join(front) + _page_content(pages, content).rstrip() + "\n")
    return {
        "ok": True, "id": page_id, "title": name,
        "url": f"file://{path}",
        "outbox_path": f"file://{path}",
        "_demo_note": f"DEMO_MODE write — page saved to state/demo-outbox/notion/{slug}.md, not created in Notion.",
        "_provenance": {"tier": PROV_TIER, "source": f"state/demo-outbox/notion/{slug}.md"},
    }


def notion_update_page(page_id: str = "", data: Optional[dict] = None,
                       command: Optional[str] = None, content: Optional[str] = None,
                       properties: Optional[dict] = None, title: Optional[str] = None) -> dict:
    """WRITE — update a page. In demo mode the update is appended to the page's outbox
    file (created if this demo never made it) and a success payload is returned."""
    data = data or {}
    name = title or data.get("title") or page_id or "untitled"
    slug = slugify(str(name))
    path = outbox_dir() / "notion" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = content or data.get("content") or data.get("new_str") or json.dumps(
        {k: v for k, v in {**data, "properties": properties}.items() if v is not None},
        indent=2, sort_keys=True)
    block = (f"\n\n---\n\n## Update — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} "
             f"(command: {command or data.get('command') or 'replace_content'})\n\n{str(body).rstrip()}\n")
    with open(path, "a") as fh:
        fh.write(block)
    return {
        "ok": True, "id": page_id or _fake_page_id(slug), "title": str(name),
        "url": f"file://{path}",
        "outbox_path": f"file://{path}",
        "_demo_note": f"DEMO_MODE write — update appended to state/demo-outbox/notion/{slug}.md.",
        "_provenance": {"tier": PROV_TIER, "source": f"state/demo-outbox/notion/{slug}.md"},
    }


def notion_search(query: str = "", data_source_url: Optional[str] = None,
                  query_type: Optional[str] = None, limit: int = 20) -> dict:
    """Search pages and databases (fixture-backed: the prior week's WBR page)."""
    return read("notion", "notion-search")


def notion_fetch(id: str = "", url: Optional[str] = None) -> dict:
    """Fetch a page's full content by id or url (fixture-backed: the prior WBR page)."""
    return read("notion", "notion-fetch")


# ============================================================
# Grain
# ============================================================

def list_meetings(filters: Optional[dict] = None, cursor: Optional[str] = None,
                  limit: int = 50) -> dict:
    """List recorded meetings — the preflight probe for ~~meeting notes."""
    return read("grain", "list_meetings")


def fetch_meeting_transcript(meeting_id: str = "", id: Optional[str] = None) -> dict:
    """Full verbatim transcript for a meeting (fixture-backed)."""
    return read("grain", "fetch_meeting_transcript")


def fetch_meeting_notes(meeting_id: str = "", id: Optional[str] = None) -> dict:
    """Structured notes / summary for a meeting (fixture-backed)."""
    return read("grain", "fetch_meeting_notes")


def fetch_meeting_action_items(meeting_id: str = "", id: Optional[str] = None) -> dict:
    """Action items captured on a meeting (fixture-backed)."""
    return read("grain", "fetch_meeting_action_items")


# ============================================================
# Connector → tool registry
# ============================================================
# The exact tool names the prompts call and .claude/settings.json allows. Hyphenated
# Notion names cannot be Python identifiers, so every tool is registered by explicit
# name rather than by function name.

REGISTRY: dict[str, dict] = {
    "hubspot": {
        "search_crm_objects": search_crm_objects,
        "query_crm_data": query_crm_data,
        "get_properties": get_properties,
        "search_properties": search_properties,
        "get_user_details": get_user_details,
        "get_campaign_analytics": get_campaign_analytics,
    },
    "linear": {
        "list_issues": list_issues,
        "list_projects": list_projects,
        "list_teams": list_teams,
        "get_issue": get_issue,
        "list_comments": list_comments,
        "get_status_updates": get_status_updates,
    },
    "google-calendar": {
        "list_events": list_events,
    },
    "gmail": {
        "search_threads": search_threads,
        "gmail_search_messages": gmail_search_messages,
        "gmail_read_message": gmail_read_message,
        "gmail_get_profile": gmail_get_profile,
    },
    "slack": {
        "slack_send_message": slack_send_message,
        "slack_read_thread": slack_read_thread,
        "slack_read_channel": slack_read_channel,
        "slack_search_channels": slack_search_channels,
        "slack_search_users": slack_search_users,
    },
    "notion": {
        "notion-search": notion_search,
        "notion-fetch": notion_fetch,
        "notion-create-pages": notion_create_pages,
        "notion-update-page": notion_update_page,
    },
    "grain": {
        "list_meetings": list_meetings,
        "fetch_meeting_transcript": fetch_meeting_transcript,
        "fetch_meeting_notes": fetch_meeting_notes,
        "fetch_meeting_action_items": fetch_meeting_action_items,
    },
}


def build_server(connector: str) -> FastMCP:
    """A FastMCP server exposing exactly one connector's tools, named for that connector
    so its tools appear as `mcp__<connector>__<tool>`."""
    if connector not in REGISTRY:
        raise SystemExit(f"unknown connector {connector!r} — one of: {', '.join(sorted(REGISTRY))}")
    server = FastMCP(connector)
    for name, fn in REGISTRY[connector].items():
        server.tool(name=name)(fn)
    return server


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--list":
        for connector, tools in REGISTRY.items():
            print(f"{connector}: {' '.join(tools)}")
        return 0
    build_server(args[0]).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
