---
name: revops-watchdog:funnel-scorecard
description: >
  Weekly (Friday) frozen snapshot of the GTM funnel for the Weekly GTM
  Scorecard: Engaged Leads (MELs), MQLs, SALs, SQLs, Meetings Held — monthly
  series with MTD + projection, written to the gtm_scorecard table and handed
  to performance-marketer for scorecard assembly. Replaces the funnel half of the agency's
  manual scorecard with locked definitions and restatement tracking.
---

# Funnel Scorecard

## When This Runs

- **WBR alignment (primary):** alongside Scribe's WBR funnel extraction —
  `/scribe wbr-prep` Step 1c triggers this skill if no same-day snapshot
  exists, so the WBR and the scorecard always cite the same frozen data
  (Scott)
- **Tick integration:** Friday weekly summary (after the daily watches),
  skipped if a same-day snapshot already exists from the WBR run
- **Standalone:** `/revops-watchdog funnel-scorecard`

## Authority

All metric definitions, queries, month boundaries, projection rules, and
restatement protocol live in `docs/gtm-scorecard-definitions.md` (v1.5).
Do not improvise queries — if a definition seems wrong, flag it; never
silently adjust.

## Workflow

### 1. Pull Monthly Series

For each month from January of the current year through the current month,
count via HubSpot `search_crm_objects` (UTC epoch-ms boundaries from the
definitions doc):

**MEL, MQL, SAL, and SQL: run the queries in `roster/funnel-stats/prompt.md`
verbatim** (Query MEL, Queries A-E) — the same canonical math Scribe uses for
the WBR Summary. `mel` moved here from a scorecard-only definition as of
definitions v1.5 (query unchanged, provenance-only fix — no restatement or
value impact). Do not re-derive or re-implement any of these here; if
funnel-stats changes, this skill follows automatically.

Scorecard-only addition (definitions v1.2):

| Metric | Query |
|--------|-------|
| `meetings_held` | deals, pipeline {{HUBSPOT_PIPELINE_ID}}, dealtype NEQ existingbusiness, `demo_done_date` GTE MONTH_START / LTE TODAY AND `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` >= MONTH_START |

**Window:** live MTD (`LTE TODAY`), exactly as funnel-stats specifies.
Label every funnel block "as of {ISO timestamp}". The scorecard and a
same-moment WBR refresh MUST produce identical numbers — divergence at
the same moment is a HIGH anomaly (trust breach). Across moments, compare
timestamps first: Latest-date re-stamping wobbles intraday counts in both
directions. Funnel projections divide by current day-of-month.

Use the `total` field from search results — never sample.

### 2. Project the Current Month

Simple run rate: `MTD ÷ days elapsed × days in month`. Tag `low-sample`
when MTD < 20. Render with "~" and % vs prior month.

### 3. Freeze the Snapshot

INSERT one row per metric per month into `gtm_scorecard`
(`agent='revops-watchdog'`, `snapshot_date` = today, `is_complete` = 1 for closed
months, `projected` set for the current month, `definition_version='v1.5'`).
Apply standing flags: any month whose `sal` cohort was inflated by a bulk list
import carries `import_polluted` and stays out of trend math (the seeded
snapshot is clean — the flag is for live runs). Never UPDATE prior rows.

### 4. Compute Restatements

For every closed month, compare this snapshot's value against the most
recent prior snapshot for the same metric+period:

```sql
SELECT value FROM gtm_scorecard
WHERE metric=? AND period=? AND snapshot_date < ?
ORDER BY snapshot_date DESC LIMIT 1;
```

For each delta, attribute the cause from the known mechanisms
(MEL backfill ↑, Latest-date re-stamp ↓, import pollution). A delta with
no known cause → INSERT into `anomalies` (surface='scorecard', MED).

First run: no prior snapshot exists — note "baseline snapshot" and skip.

### 5. Compute Conversion Rates

From THIS snapshot's rows only: `mel_to_mql_pct`, `mql_to_sal_pct`,
`sal_to_sql_pct` per month. Write as additional `gtm_scorecard` rows.

### 6. Hand Off to performance-marketer

Append to `state/journal/handoffs.md`:

```
## {ts} | revops-watchdog → performance-marketer | Funnel scorecard snapshot ready ({snapshot_date})

**Surface:** gtm_scorecard (agent='revops-watchdog', snapshot_date={date})
**Summary:** {1-line: current-month pacing headline + any restatements}
**Restatements:** {count, or "none"}
```

performance-marketer's traffic-scorecard assembles the combined document. Do not write
the scorecard document yourself — revops-watchdog produces data, not prose surfaces.

### 7. Journal

One section in the Friday journal entry: metrics written, projections,
restatements found, flags applied.

## Output

- `gtm_scorecard` rows (one per metric per month + conversion rates)
- `anomalies` rows for unexplained restatements
- Handoff to performance-marketer
- Journal section

## Human-Facing Definitions (for narratives)

- **Engaged Leads (MELs):** contacts entering the Marketing Engaged stage
- **MQLs:** marketing-qualified — hand-raisers, score-threshold, outbound
- **SALs:** MQLs / sales-ready leads that Sales accepts and pursues
- **SQLs:** leads that respond to pursuit and schedule a meeting
- **Meetings Held:** discovery meetings completed (in-month-scheduled deals)
