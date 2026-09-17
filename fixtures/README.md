# Fixtures — the DEMO_MODE data set

Synthetic connector responses for `DEMO_MODE=1`. `scripts/demo/fixture_mcp.py` serves
one file per tool: `fixtures/<connector>/<tool>.json` is what
`mcp__<connector>__<tool>` returns. Every value here is Orrery-world — the fictional
incident-management company in `profiles/orrery/` — and nothing in this tree resolves
to a real system: emails end in `.example`, Slack ids are `U0DEMO*` / `C0DEMO*`, Notion
ids are zero-filled.

Nothing is a credential and nothing is a template: these are already-rendered demo
payloads, not tokenized kit files, so they carry no profile tokens.

## Date tokens

Fixtures would go stale the day after they were written, so date-shaped strings are
written as tokens and substituted at read time, over the raw text, before it is parsed.
Each name below is written wrapped in double braces, e.g. `{{T+0d}}`:

| Token | Becomes |
|---|---|
| `T+0d` | today, `YYYY-MM-DD` |
| `T-3d`, `T+2d` | that many days before / after today |
| `TODAY` | today (same as `T+0d`) |
| `MONDAY` | this week's Monday |
| `NOW` | an ISO-8601 UTC timestamp, `YYYY-MM-DDTHH:MM:SSZ` |

**Use the `T±Nd` form in fixture files.** `TODAY`, `MONDAY`, and `NOW` render correctly,
but their braced form also matches `scripts/profile_render.py`'s uppercase-token scan,
which then reports them as undefined profile tokens and fails `make render`. Pair an
offset with a literal clock time when you need a timestamp: `"{{T+0d}}T15:30:00Z"`.

## Adding a fixture

1. Find the tool name the prompt actually calls (`roster/**`, or
   `python3 scripts/demo/fixture_mcp.py --list`).
2. Write `fixtures/<connector>/<tool>.json` shaped like that connector's real
   response — the agent parses it as if it came from the live API.
3. Check it: `python3 scripts/demo/connector.py <connector> <tool>`.

A tool with no fixture file is not an error — it returns an empty result labeled
`_demo_note`, so a gap degrades visibly instead of crashing a demo.

## What is *not* a fixture

HubSpot's funnel numbers are derived, not stored. `search_crm_objects` reads the latest
`funnel_snapshots` row from `state/working/fleet.db` and reports it plus one weekday's
increment, keeping SAL→SQL under the 35% threshold so the seeded dip continues into the
demo day and revops-watchdog finds its MED anomaly. `hubspot/funnel.json` is only the fallback for
when there is no database. That is what keeps the CRM from contradicting the journals
`scripts/seed_demo_state.py` wrote.

## The hero-loop set

| Connector | Files | Carries |
|---|---|---|
| `hubspot/` | `funnel`, `workflows`, `contacts_recent`, `scoring`, `get_user_details` | the fallback funnel with the dip; 8 workflows with one 100%-first-step-exit HIGH; 7-day new contacts with the enrichment sentinel ids; the lead-score distribution; the portal probe |
| `linear/` | `list_issues`, `list_projects`, `list_teams`, `get_issue`, `list_comments`, `get_status_updates` | 18 open issues (2 High/Urgent due within a week), 10 projects with mixed health |
| `google-calendar/` | `list_events` | two events today — an all-hands with an agenda doc, a demo without one |
| `gmail/` | `search_threads`, `gmail_search_messages`, `gmail_read_message`, `gmail_get_profile` | 30 unread: vendor noise, a Linear digest, and one real customer ask |
| `slack/` | `slack_read_thread`, `slack_read_channel`, `slack_search_channels`, `slack_search_users` | yesterday's AM-brief thread with the operator's one reply; the team channel and the four cadence members |
| `notion/` | `notion-search`, `notion-fetch` | last week's WBR page, shaped like `templates/wbr-audit-artifact.md` |
| `grain/` | `list_meetings`, `fetch_meeting_transcript`, `fetch_meeting_notes`, `fetch_meeting_action_items` | one prospect call |

Writes have no fixtures: `slack_send_message`, `notion-create-pages`, and
`notion-update-page` append to `state/demo-outbox/` instead.

## The Google pulls — `fixtures/google/`

Not every demo surface is an MCP tool. performance-marketer's Tick shells four Google
pull commands, so `fixtures/google/` holds **CSVs**, not JSON, and they are served by
the pull scripts' own `DEMO_MODE` branch rather than by `fixture_mcp.py` — same
commands, same output paths, no credentials. Mapping, the planted spend / ranking /
landing-page anomalies, and the shape rules are in `fixtures/google/README.md`. The
date tokens above apply there unchanged.
