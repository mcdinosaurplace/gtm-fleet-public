# GTM Scorecard — Locked Metric Definitions

**Version: v1.5**

> **v1.5 changelog (per Scott):** `mel` is promoted into `roster/funnel-stats/prompt.md`
> as a canonical Query, alongside MQL/SAL/SQL — it is no longer a scorecard-only
> addition with its own definition here. The query itself is unchanged
> (`mel_date` GTE MONTH_START / LTE TODAY); this is a provenance fix, not a
> methodology change, so no historical `gtm_scorecard` rows are affected. Driven
> by Scribe now surfacing MELs in the WBR Summary every week (current MTD, plus
> the month that just closed when the month-turnover trigger fires), sourced
> from `gtm_scorecard`'s existing `mel` rows — no new table/column needed.

> **v1.4 changelog (per Scott):** Channel Mix (`channel_users:{Channel}` /
> `channel_sessions:{Channel}`) now ALSO freezes full-calendar-month history per
> channel, mirroring `organic_users`/`organic_sessions` — not just the MTD-vs-
> prior-month-same-day-count snapshot. Driven by the WBR Traffic section's rolling
> 6-month view (5 trailing closed months + current MTD), which needs real
> month-over-month channel comparisons (the month that just closed against the
> one before it), not same-day-count proxies. The MTD-vs-prior-MTD comparison
> is retained alongside the full-month series for the standalone weekly scorecard's
> Monday-call use. See Channel Mix section and Snapshot & Restatement Protocol.

> **v1.3 changelog (per Scott):** Snapshot cadence moved Friday → **Wednesday** so the
> frozen rows exist before the Wednesday WBR, which consumes them directly (Scribe
> does not re-query). See Snapshot & Restatement Protocol.

> **v1.2 changelog (same-day, per Scott):** Funnel math is now defined by
> **deference, not duplication** — the scorecard runs the queries in
> `roster/funnel-stats/prompt.md` verbatim (the WBR's canonical source).
> Funnel MTD window is **live through run time** (`LTE TODAY`), matching
> the WBR, with a mandatory as-of timestamp; the complete-days freeze
> applies to traffic only. Corrections to published scorecards are made
> in-line at their canonical places, never as addenda.
>
> **v1.1 changelog (superseded same-day):** moved SAL/SQL to the cohort
> method; introduced a complete-days funnel window (reverted in v1.2).

This document is the single source of truth for every metric in the Weekly
GTM Scorecard. Skills (`performance-marketer:traffic-scorecard`, `revops-watchdog:funnel-scorecard`)
reference these definitions and record `definition_version` with every
snapshot row. **Any change to a definition requires a version bump here and
a note in the next scorecard** — this is what prevents the silent metric
drift that made the predecessor process (prompt-driven, unversioned,
unlogged) unreliable.

Every definition here is checked against the seeded `gtm_scorecard` series
(8 metrics × 8 closed months, all tagged `v1.5`) before a version bump ships.
A definition change that restates no historical row is a provenance or naming
fix, not a methodology change, and its changelog must say so — that distinction
is what keeps `definition_version` meaningful as a comparison key.

---

## Traffic Metrics (owner: performance-marketer, source: GA4 + GSC)

### organic_users — "Organic Search Users (first-touch)"

- **GA4 Data API:** metric `totalUsers`, dimension filter
  `firstUserDefaultChannelGroup = "Organic Search"`, full-calendar-month
  date range (UTC).
- **Semantics:** users whose *first acquisition* was organic search. This is
  the continuity series: once a month closes it must match digit-for-digit
  across every later snapshot. The seeded `gtm_scorecard` carries
  `organic_sessions` but not `organic_users` — read the users series from GA4
  and expect it to land roughly 19k–28k a month against the seeded organic
  sessions of 29.0k–39.8k.
- **Caution:** this is a USERS count, not visits. GA4 user counts are
  HyperLogLog estimates and can shift ±1-3% on reprocessing — restatements
  of recent months are expected and tracked, not errors.

### organic_sessions — "Organic Search Sessions"

- **GA4 Data API:** metric `sessions`, dimension filter
  `sessionDefaultChannelGroup = "Organic Search"`, full-calendar-month range.
- **Semantics:** true visit volume from organic search (any-touch).
  Runs ~40-55% above `organic_users`. Reported alongside it so "traffic"
  is never ambiguous again. Seeded range: 29.0k–39.8k a month, against
  all-channel `sessions` of 47.5k–61.5k.

### channel_users:{Channel} / channel_sessions:{Channel} — "Channel Mix"

- **GA4 Data API:** metrics `totalUsers` (dimension
  `firstUserDefaultChannelGroup`) and `sessions` (dimension
  `sessionDefaultChannelGroup`), one row per channel group.
- Covers ALL default channel groups returned (Direct, Organic Search,
  Organic Social, Paid Search, Paid Social, Referral, Email, AI Assistant,
  Unassigned, …) — not a fixed five.
- **Two parallel series, both frozen every snapshot (as of v1.4):**
  1. **Full-calendar-month history** — same shape as `organic_users`/
     `organic_sessions`: one row per channel per closed month (`period` =
     `YYYY-MM`, `is_complete=1`, digit-exact across snapshots once closed),
     plus the current month as MTD (`is_complete=0`, `projected` = weekday-
     adjusted run rate per the Projection Methodology below). This is the
     series the WBR Traffic section's rolling 6-month view consumes.
  2. **MTD vs same-day-count prior-month** — the original v1.0 comparison
     (MTD range vs the first N days of the prior month, N = days elapsed).
     Retained for the standalone weekly scorecard document's Monday-call
     framing, where "are we pacing ahead of last month at this point" is
     the more useful question than a full-month comparison mid-month.
- Full-month channel rows are subject to the same GA4 HyperLogLog
  reprocessing drift as `organic_users` (±1-3% restatement on recent closed
  months, expected and tracked — not an error).

### gsc_clicks / gsc_impressions / gsc_avg_position — "Search Visibility"

- **GSC API:** site `https://{{COMPANY_DOMAIN}}/` (or `sc-domain:` once confirmed),
  trailing 28 days vs prior 28 days, site-wide plus `/blog` page filter.
- Pending the service-account grant; the block renders "GSC pending access"
  until then.

---

## Funnel Metrics (owner: revops-watchdog, source: HubSpot)

**Canonical source: `roster/funnel-stats/prompt.md` — the scorecard runs
those queries verbatim.** This is the same math Scribe uses for the WBR
Summary; if funnel-stats changes, the scorecard follows automatically.
Divergence between the scorecard and the WBR pulled at the same moment is
a trust breach — investigate immediately, never reinterpret.

**Window:** live MTD — `GTE MONTH_START` / `LTE TODAY` — exactly as
funnel-stats specifies. Every funnel block carries an as-of timestamp.
Note: "Latest"-date re-stamping means intraday counts can move in BOTH
directions (observed: SAL 65 → 67 → 65 across one afternoon); the timestamp,
not the number alone, is the comparison key.

Human-facing definitions per Scott. The date properties are
the canonical contact-funnel fields; positions in the funnel are unchanged
from the contact-based method.

### mel — "Engaged Leads (MELs)"

**As of v1.5, runs via `roster/funnel-stats/prompt.md` Query MEL verbatim** —
the same canonical query Scribe now uses for the WBR Summary. If funnel-stats
changes, this metric follows automatically, same as mql/sal/sql below.

- **Definition:** contacts that first entered the **Marketing Engaged**
  lifecycle stage (id `{{HUBSPOT_WORKFLOW_ID_1}}`) during the month.
- **Query:** contacts, `mel_date` >= month-start AND < next-month-start
  (UTC; date-typed property, timezone-safe).
- **Known restatement mechanism:** retroactive MEL backfill
  (`stage_backfill_logs`) keeps adding stamps to historical months for
  ~4-8 weeks after close. Expect upward restatements; the Restatements
  table makes them visible.
- Do NOT use `mel_date__latest_` (diverges on re-engagements; a
  re-engagement-heavy month read 235 against 177).

### mql — "MQLs"

- **Definition:** contacts becoming Marketing Qualified in the month —
  hand-raisers, score-threshold, and outbound-sourced.
- **Query:** contacts, `mql_date__latest_` in month,
  `mql_type_latest` IN ("MQL Handraiser - P1", "MQL Score Threshold - P2",
  "Outbound"). Outbound is mandatory — omitting it turns a seeded 110-MQL
  month into 62. Watch for the "PQL" type appearing (zero records in every
  month seeded so far).

### sal — "SALs (Sales Accepted)"

- **Definition (human):** MQLs / sales-ready leads that **Sales accepts
  and pursues**.
- **Query:** funnel-stats **Query D verbatim** — contacts with
  `mql_date__latest_` AND `sal_date__latest_` both in `GTE MONTH_START` /
  `LTE TODAY` (the funnel-consistent cohort, standing since v1.1).
- **Known data caveats:**
  - "Latest"-date re-stamping pulls re-qualified contacts out of
    historical months — a closed month can lose SALs to a later one — and
    wobbles intraday counts in both directions. Past-month downward
    restatements are expected.
  - A bulk list import inflates MEL and MQL on the import day and can
    inflate that month's SAL cohort well above its organic run rate. Flag
    the affected row `import_polluted` and hold it out of trend math. (The
    seeded `gtm_scorecard` is a single clean snapshot, so nothing is
    flagged there — the flag exists for live runs.)

### sql — "SQLs (Meeting Scheduled)"

- **Definition (human):** leads that **respond to pursuit and schedule a
  meeting** after being pursued.
- **Query:** funnel-stats **Query E verbatim** — contacts with all three
  dates (`mql_date__latest_`, `sal_date__latest_`, `sql_date__latest_`)
  in `GTE MONTH_START` / `LTE TODAY`.
- Subject to the same Latest-date re-stamping and import-pollution caveats.

### meetings_held — "Meetings Held"

- **Definition:** discovery meetings actually completed in the month for
  in-month-scheduled deals.
- **Query:** deals, `pipeline = {{HUBSPOT_PIPELINE_ID}}`, `dealtype NEQ existingbusiness`,
  `demo_done_date` in month AND `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` >= month
  start. (The funnel-stats "SQL In-Month" query.)

### Conversion rates

- `mel_to_mql_pct` = mql / mel (same month)
- `mql_to_sal_pct` = sal / mql
- `sal_to_sql_pct` = sql / sal
- Computed per month from the SAME snapshot's rows — never across
  snapshots.

### Month boundaries (UTC epoch-ms)

HubSpot date filters take epoch milliseconds, so **never** hand-type a boundary.
The rule: a month's start is the first of that month at `00:00:00Z`, expressed
in milliseconds; its end-exclusive bound is the next month's start. Compute both,
never transcribe them:

```python
from datetime import datetime, timezone
ms = lambda y, m: int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp() * 1000)
```

A boundary off by one timezone hour silently moves records between months and
shows up as an unexplained restatement — treat any hand-entered epoch value in a
query as a defect.

---

## Projection Methodology

### Traffic metrics (daily data available)

**Weekday-adjusted run rate.** Pull the month's daily series; compute
day-of-week weights from the trailing 8 full weeks of the same metric;
project = MTD × (full-month weighted capacity ÷ elapsed weighted capacity).
This corrects the predecessor's naive run-rate, which over-projects when a
month starts weekday-heavy.

### Funnel metrics (low counts)

**Simple run rate** (MTD ÷ days elapsed × days in month) — weekday
adjustment is noise at <50 events/month. When MTD count < 20, the
projection carries a `low-sample` tag and the narrative must hedge.

Projections always render with "~" and the % vs prior month, matching the
established readout style.

---

## MTD Windows

- **Funnel:** live MTD — `GTE MONTH_START` / `LTE TODAY` per funnel-stats,
  labeled "as of {ISO timestamp}". Matches the WBR exactly when pulled at
  the same moment. Funnel projections divide by the current day-of-month.
- **Traffic:** complete days — month start through yesterday 23:59 UTC,
  labeled "data through {date}". GA4 intraday data is incomplete (24-48h
  processing lag), so a live traffic window would systematically
  undercount.

## Scorecard vs. WBR Reconciliation

The scorecard's funnel block and the WBR Summary run the SAME queries
(funnel-stats verbatim) on the SAME window definition. The trust standard:

- **Same moment → identical numbers.** Any divergence between a scorecard
  and a WBR refreshed at the same time is a method breach — investigate
  immediately (`anomalies`, severity HIGH).
- **Different moments → compare timestamps first.** Latest-date
  re-stamping moves intraday counts in both directions; a 65 → 67 → 65
  SAL drift across an afternoon is data motion, not error. Closed months
  must match exactly across surfaces.

## Published-Card Correction Policy

Corrections to a published scorecard are made **in-line at the canonical
section** (table cells, narratives, notes updated in place) — never as
appended amendments. The `gtm_scorecard` table keeps the audit trail:
rows are append-only and version-tagged, so every published number's
history is reconstructable even though the card reads clean.

## Snapshot & Restatement Protocol

- Every **Wednesday** run (moved from Friday in v1.3) INSERTs one row per metric
  per month into `gtm_scorecard` keyed by `snapshot_date`, and must finish before
  Scribe's Wednesday WBR (which consumes these rows). **Rows are never updated** —
  history is append-only.
- The scorecard's Restatements section compares this snapshot's values for
  prior months against last snapshot's values and lists every delta with
  its known cause (MEL backfill, Latest-date re-stamp, GA4 reprocessing,
  import pollution). This applies to full-month channel_users/
  channel_sessions rows exactly as it does to organic_users/organic_sessions
  (v1.4) — both are GA4 monthly series subject to the same reprocessing drift.
- A restatement with NO known cause is an anomaly — revops-watchdog/performance-marketer write it
  to the `anomalies` table (severity MED) for investigation.

## Known Quirks

Quirks of the seeded demo dataset, so nobody reads them as definition defects:

- **One snapshot, no restatement history.** The seed carries a single
  `snapshot_date`, every row `is_complete=1` with no `projected` value. The
  Restatements section therefore renders empty against a fresh seed — that is
  correct, not a missing pull. Restatements only appear from the second
  Wednesday run onward.
- **The seeded metric set is a subset.** `organic_sessions`, `paid_sessions`,
  `sessions`, `demo_requests`, `mel`, `mql`, `sal`, `sql` have rows.
  `organic_users`, the `channel_users:{Channel}` / `channel_sessions:{Channel}`
  family, `gsc_clicks` / `gsc_impressions` / `gsc_avg_position`,
  `meetings_held`, and the conversion rates do not — compute them from source,
  never look them up in the seed and report a zero.
- **The series stops at the last closed month.** There is no MTD row in the
  seed, so a scorecard run against it must pull the current month live (or from
  fixtures under `DEMO_MODE=1`). A card that shows only closed months has not
  finished its run.
- **The seeded `funnel_snapshots` dip is deliberate.** SAL→SQL sits under the
  35% threshold across the last several MTD days — the demo's planted anomaly,
  not a definition error. Do not "fix" it by changing a definition.
