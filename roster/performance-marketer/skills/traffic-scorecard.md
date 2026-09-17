---
name: performance-marketer:traffic-scorecard
description: >
  Weekly (Wednesday) frozen snapshot of website traffic for the Weekly GTM
  Scorecard: dual-series organic search (first-touch users + sessions), full
  GA4 channel mix, GSC search visibility, with weekday-adjusted projections.
  Writes to the gtm_scorecard table, then assembles the combined scorecard
  (traffic + revops-watchdog's funnel rows) into the weekly draft for chief-of-staff and
  Scribe. Replaces the agency's manual scorecard.
---

# Traffic Scorecard

## When This Runs

- **Tick integration:** Wednesday scorecard pass (after revops-watchdog's funnel-scorecard
  handoff exists; must finish before Scribe's Wednesday WBR)
- **Standalone:** `/performance-marketer traffic-scorecard`

## Authority

All metric definitions, projection rules, and the restatement protocol live
in `docs/gtm-scorecard-definitions.md` (v1.5). Record `definition_version`
on every row.

## Workflow

### 1. Pull GA4 Monthly Series — rolling 6-month window (5 trailing closed + current MTD)

Inline Python via `scripts/google_auth.py` helpers
(BetaAnalyticsDataClient; `scripts/ga4_pull.py` lacks custom ranges):

- `organic_users`: `totalUsers`, filter `firstUserDefaultChannelGroup =
  "Organic Search"`, per calendar month
- `organic_sessions`: `sessions`, filter `sessionDefaultChannelGroup =
  "Organic Search"`, per calendar month
- **`channel_users:{Channel}` / `channel_sessions:{Channel}` full-month
  history (v1.4):** same shape as organic above but broken out by
  `firstUserDefaultChannelGroup` / `sessionDefaultChannelGroup` — one row
  per channel per calendar month. Covers ALL channel groups returned
  (Direct, Organic Search, Organic Social, Paid Search, Paid Social,
  Referral, Email, AI Assistant, Unassigned, …), not a fixed five.

Window: the 5 most recently CLOSED calendar months plus the current month
as MTD. Do not pull further back — nothing older is consumed downstream.
As months roll forward, the oldest closed month drops off naturally next
snapshot; no backfill of dropped months is needed.

### 2. Pull Channel Mix MTD Comparator (MTD vs prior-month same-day-count)

Separate from step 1's full-month history — this is the supplementary
same-day-count comparison used only in the standalone weekly scorecard
document's Monday-call framing (§7), not stored as its own history series.
All channel groups, both scopes: `totalUsers` by
`firstUserDefaultChannelGroup` and `sessions` by
`sessionDefaultChannelGroup`. Two date ranges: month-to-date, and the
first N days of the prior month (N = days elapsed). One row per channel
per metric. NOT frozen to `gtm_scorecard` — computed fresh each run and
used inline in the step-7 document only (step 1's full-month rows are the
persisted history).

### 3. Pull GSC Visibility (when access lands)

Trailing 28d vs prior 28d: clicks, impressions, average position —
site-wide and `/blog` segment. Until the service-account grant: render
"GSC pending access" and skip rows.

### 4. Project the Current Month (traffic)

Weekday-adjusted run rate per the definitions doc: daily series for the
month + trailing 8 full weeks → day-of-week weights → projection =
MTD × (full-month weighted capacity ÷ elapsed weighted capacity). Applies
to organic_users/organic_sessions AND to each current-month
channel_users:{Channel}/channel_sessions:{Channel} row (v1.4).

### 5. Freeze the Snapshot

INSERT rows into `gtm_scorecard` (`agent='performance-marketer'`, today's
`snapshot_date`):
- `organic_users` / `organic_sessions` per month (rolling 6-month window)
- `channel_users:{Channel}` / `channel_sessions:{Channel}` per channel per
  month, same rolling 6-month window, `is_complete`/`projected` set the
  same way as organic (v1.4)
- GSC metrics when available

Never UPDATE prior rows.

### 6. Compute Traffic Restatements

Compare closed-month values vs the prior snapshot (same query pattern as
revops-watchdog's funnel-scorecard step 4) — for organic_users/organic_sessions AND
for full-month channel_users:{Channel}/channel_sessions:{Channel} rows
(v1.4). Known cause: GA4 HyperLogLog reprocessing (±1-3% on user counts is
normal — note, don't alarm). Larger unexplained deltas → `spend_alerts`-style
entry in `anomalies` (surface='scorecard', MED).

### 7. Assemble the Combined Scorecard

Read revops-watchdog's rows for this week (`gtm_scorecard` WHERE `agent='revops-watchdog'`
AND `snapshot_date` = this week's — confirm the handoff exists; if absent,
assemble traffic-only and flag the gap in the draft and journal).

Supersede the prior pending scorecard, then write the new one:

```bash
python3 scripts/paid/publish.py gtm_scorecards
```

Write `docs/publications/pending/performance-marketer/gtm_scorecards/{YYYY-MM-DD}-gtm-scorecard.md`:

```markdown
# Weekly GTM Scorecard — data through {Thursday date}
performance-marketer (traffic) + revops-watchdog (funnel) | Snapshot {date} | Definitions v1.0

## Traffic
### Organic Search
| Month | Users (first-touch) | MoM | Sessions | MoM |
{Jan → current; MTD row; Projected row with ~ and % vs prior month}
{1-2 sentence narrative: pacing, cause attribution, holiday context}

### Channel Mix (MTD vs same period last month)
| Channel | Users | Δ | Sessions | Δ |

### Search Visibility (GSC, 28d vs prior 28d)
{clicks / impressions / avg position, site + blog — or "pending access"}

## Funnel
### Engaged Leads (MELs) | MQLs | SALs | SQLs | Meetings Held
{per metric: monthly series, MTD, ~projection, % vs prior, 1-line narrative}
SALs = sales accepted and pursued; SQLs = responded and scheduled a meeting.

### Conversion
MEL→MQL {%} | MQL→SAL {%} | SAL→SQL {%} (current + prior 2 months)

## Restatements Since Last Snapshot
| Metric | Month | Prior | Now | Δ | Cause |
{or "None."}

## Notes
{flags: import_polluted, low-sample, GSC pending, definition changes}
```

Narrative voice: performance-marketer's — number, baseline, delta, cause. No filler.
Keep the whole document scannable; it feeds a Monday call.

### 8. Hand Off

Handoff to chief-of-staff (Tier 2: surface for Monday-call use via Slack) and a
second handoff flagged for **Scribe**: the funnel block + projections are
WBR Summary inputs (`/scribe wbr-prep` consumes `gtm_scorecard` rows
directly — same frozen snapshot, no re-querying).

**Ad-hoc trigger from Scribe (v1.4):** Scribe's WBR Traffic section
consumes this skill's `channel_users`/`channel_sessions`/`organic_users`/
`organic_sessions` rows directly. If the most recent `performance-marketer` snapshot in
`gtm_scorecard` is more than 6 days old when Scribe runs its Wednesday
Tick, Scribe will spawn a standalone run of this skill ad hoc (outside the
normal Wednesday scorecard cadence) to get current data for the WBR. Treat
that as a normal invocation — same steps, same freeze — the only
difference is who asked and when.

### 9. Journal

Scorecard section in the Wednesday journal entry: rows written, projection,
restatements, assembly status.

## Output

- `gtm_scorecard` rows (traffic metrics: organic + full-month channel mix,
  rolling 6-month window, v1.4)
- `docs/publications/pending/performance-marketer/gtm_scorecards/{date}-gtm-scorecard.md` (combined document)
- Handoffs: chief-of-staff (Tier 2), Scribe (WBR input)
- `anomalies` rows for unexplained restatements
- Journal section

## On Approval: Publish

When the Tier 2 approval lands (thread-reply via chief-of-staff, or direct from
Scott), the scorecard publishes to the team-facing archive:

1. `git mv docs/publications/pending/performance-marketer/gtm_scorecards/{date}-gtm-scorecard.md
   reports/gtm-scorecard/{date}.md`
   (if a newer scorecard already superseded it, publish instead from
   `docs/publications/published/performance-marketer/gtm_scorecards/{date}-gtm-scorecard.md`)
2. Add the snapshot row to `reports/gtm-scorecard/README.md`'s index table
3. Record the approval in the `approvals` table (`status='approved'`)

Corrections to published cards are made **in-line at the canonical
section** — never as appended amendments (Scott). The
append-only, version-tagged `gtm_scorecard` rows carry the audit trail;
the card always reads clean.
