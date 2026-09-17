# Scribe — Journal

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.


## 2026-09-09T17:05:00Z | Weekly Tick — WBR posted

### Anchor
Wednesday 2026-09-09 · WBR covering the week of 2026-09-07.

### WBR
Draft posted to ~~knowledge base (Notion "Updates" database: `00000000-0000-4000-8000-000000000101`). Summary block auto-populated from revops-watchdog `funnel_snapshots`; traffic block from performance-marketer `gtm_scorecard` (v1.5).
Section owners pinged in #team-marketing: Summary — Scott McKeighen; Project Updates — Maya Lindqvist; Content — Priya Natarajan; Web & Design — Tomas Reyes; GTM Ops — Scott McKeighen. Deadline Thursday 07:00 PT.

### Notion topic sync
3 candidates mirrored to the review database; no rulings yet.

### Handoffs Written
- Scribe → chief-of-staff | LOW | WBR posted for 2026-09-09


## 2026-09-16T17:05:00Z | Weekly Tick — WBR posted

### Anchor
Wednesday 2026-09-16 · WBR covering the week of 2026-09-14.

### WBR
Draft posted to ~~knowledge base (Notion "Updates" database: `00000000-0000-4000-8000-000000000101`). Summary block auto-populated from revops-watchdog `funnel_snapshots`; traffic block from performance-marketer `gtm_scorecard` (v1.5).
Section owners pinged in #team-marketing: Summary — Scott McKeighen; Project Updates — Maya Lindqvist; Content — Priya Natarajan; Web & Design — Tomas Reyes; GTM Ops — Scott McKeighen. Deadline Thursday 07:00 PT.

### Notion topic sync
2 approved, 1 needs_edit harvested from the review database and applied via scripts/topic_review.py; 5 rows mirrored.

### Handoffs Written
- Scribe → chief-of-staff | LOW | WBR posted for 2026-09-16
- Scribe → content-researcher | MED | Topic backlog mirrored to Notion — 2 approved, 1 needs_edit


## 2026-09-17T15:49:55Z | Weekly Tick — WBR posted (off-cadence Thursday)

### Anchor
Thursday 2026-09-17 · September · Q3 2026. Off-cadence harness run (the WBR runs on Wednesdays). WBR page date: Friday 2026-09-18. turned_over = FALSE, so no recap block.

### MCP Preflight
DEMO_MODE=1, one probe each. ~~knowledge base (Notion), ~~chat (Slack), ~~crm (HubSpot), ~~issue tracker (Linear): all bound.

### WBR
- Page: `state/demo-outbox/notion/marketing-update-2026-09-18.md` (page id 00000000000000000000000000462968)
- Prior-week page: found (00000000000000000000000000000210, "Marketing Update - 2026-09-15"). Sections copied forward as written. Linear project names linked per the pre-send gate.
- Data source: revops-watchdog snapshot id=23 (2026-09-17T15:44:14Z). MEL 238 · MQL 41 (P1 9 · P2 23 · Outbound 9) · SAL 28 · SQL 8 · MQL→SAL 68.3% · SAL→SQL 28.6% · pipeline $1,137,093 / 89 open deals.
- Step 1c skipped: gtm_scorecard has no September rows, and funnel-scorecard was not run. MEL MTD came from the snapshot id=23 notes.
- Traffic: the scorecard lacks organic_users, channel_users and September MTD rows. Organic Search shows sessions for April to August only. Channel Mix was not refreshed.
- Audit artifact `wbr/2026-09-17.md` not saved: the write was denied by a permission prompt.

### Slack
#team-marketing (C0DEMO0001), outbox `state/demo-outbox/slack.md` ts=1788544721.391296. Owners prompted: Maya Lindqvist, Priya Natarajan, Tomas Reyes, Scott McKeighen. Callouts: 4. The Thursday 07:00 AM PT deadline had already passed, so the post asks for updates before Friday's review. The post footer says 15:55:00Z; the actual send was about 15:49Z.

### Notion topic sync
Skipped. The topic review data source could not be reached, and push was not run because pull must go first. Pulled 0 · Pushed 0 · Slack pointer suppressed. topic-0006, topic-0007 and topic-0008 are still unsynced. Retry next Tick.

### Handoffs Written
- `scribe_handoff_01m2r0yry6_sy73wt` | LOW | Scribe → chief-of-staff | WBR posted for 2026-09-18 (resolved)
- `scribe_handoff_01m2r0yry6_6cayp6` | MED | Scribe → chief-of-staff | WBR data gaps: prior page vs DB mismatch, missing scorecard rows, possible duplicate, topic sync skipped (pending)
- Ops incident `scribe_incident_01m2r0yry6_kfg0v3` | LOW
- Harness: session=2243accc-6083-47fb-acdd-0b603e3b071c turns=35 cost=$2.31


## 2026-09-17T15:58:31Z | Skill: notion-topic-sync — skipped (data source unreachable)

### Anchor
Thursday 2026-09-17 · September · Q3 2026. Standalone harness run of the topic sync; no mode work. Migration `018_topic_backlog_notion_sync` confirmed applied (2026-09-17 15:43:12).

### MCP Preflight
DEMO_MODE=1, one probe. ~~knowledge base (Notion) bound, but it is fixture-backed only for the Updates database: `notion-search` with `collection://00000000-0000-4000-8000-000000000104` and `notion-fetch` on the Topic Backlog page `00000000000000000000000000000204` both returned the "Marketing Update - 2026-09-15" WBR page. No Topic Backlog fixture exists under `fixtures/`.

### Notion topic sync
Pulled: 0 applied, 0 unchanged, 0 unmatched UID (pass 1 could not query the review data source)
Pushed: 0 created, 0 updated, 0 bodies refreshed (not attempted; pull must go first)
Slack pointer: suppressed, no news

Repo state unchanged: 9 `topic_backlog` rows. 5 carry `notion_page_id` (topic-0001 to topic-0005). 4 are still unsynced: topic-0006 (candidate), topic-0007 (briefed), topic-0008 (rejected), content-researcher_topic_01m2r1bg8c_q3ewne (candidate). All 5 synced rows share page id `00000000000000000000000000000501`, which looks like seed data and not 5 real pages. Check this before the first live sync.

### Handoffs Written
- None (no decisions applied, so no content-researcher handoff)
- Ops incident append to `state/journal/ops-incidents.md` was denied by a permission prompt; the incident is recorded here instead: LOW, second consecutive topic-sync skip, operator action is to add a Topic Backlog fixture or route data_source_url in `scripts/demo/fixture_mcp.py`.
- Harness: session=18836820-f512-41a1-ad02-1108fc432485 turns=17 cost=$0.79
