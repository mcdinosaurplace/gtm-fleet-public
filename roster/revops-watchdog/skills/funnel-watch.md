---
name: revops-watchdog:funnel-watch
description: >
  Daily HubSpot funnel snapshot with anomaly detection. Wraps the funnel-stats
  skill to pull MTD MQL/SAL/SQL/pipeline metrics, compares against trailing
  4-week baselines, and flags deviations using thresholds from revops-watchdog's
  identity file. Writes funnel_snapshots and anomaly rows; triggers chief-of-staff
  handoff on MED/HIGH severity.
---

# Funnel Watch

## When This Runs

- **Tick integration:** Every daily Tick (weekdays, 08:00 PT)
- **Standalone:** `/revops-watchdog funnel-watch`

## Inputs

HubSpot data via MCP or HubSpot API. Uses the exact query set defined in
`roster/funnel-stats/prompt.md`:

- MQL counts by type (P1 Handraiser, P2 Auto, Outbound)
- SAL count (Sales Accepted — Sales accepts the lead and pursues a meeting)
- SQL count (Sales Qualified — a meeting is successfully booked after pursuit)
- Active open pipeline value

> **SAL/SQL definitions (Q2-2026):** the "Scheduled Demo Calls" / "Demos
> Completed" labels were the deprecated deal-based map. funnel-watch wraps
> funnel-stats, which counts the contact cohort. Canonical:
> [`docs/lead-lifecycle-model.md`](../../../docs/lead-lifecycle-model.md).

## Relationship to funnel-stats

This skill **wraps** `roster/funnel-stats/prompt.md`. The funnel-stats agent
handles the HubSpot query logic and produces the formatted MTD metrics block.
revops-watchdog's funnel-watch adds:

- State persistence (writes to `funnel_snapshots` table)
- Baseline calculation (trailing 4-week averages)
- Anomaly detection (applies identity-file thresholds)
- Handoff generation (notifies chief-of-staff on MED/HIGH)

`funnel-stats` stays independently invocable via `/funnel-stats` with no
change to its behavior.

## Workflow

### 1. Load Design Context (if available)

Load `docs/lead-lifecycle-model.md` — the canonical lead lifecycle model
(v1.0.0) — for the current stage definitions, the SAL/SQL meanings, and
conversion context when flagging anomalies.

### 2. Run funnel-stats

Invoke the funnel-stats workflow to produce today's MTD snapshot. Capture:

- `MQL_P1`, `MQL_P2`, `MQL_OUT`, `MQL_TOTAL`
- `SAL_COUNT`, `SQL_TOTAL`, `SQL_INMONTH`
- `MQL_SAL_CVR`, `SAL_SQL_CVR`
- `PIPELINE_TOTAL`

### 3. Persist Snapshot

INSERT one row into `funnel_snapshots`:

```sql
INSERT INTO funnel_snapshots (
  agent, snapshot_date, mqls, sals, sqls,
  pipeline_value, mql_to_sal_rate, sal_to_sql_rate,
  notes, created_at
) VALUES (
  'revops-watchdog', '{today}', {MQL_TOTAL}, {SAL_COUNT}, {SQL_TOTAL},
  {PIPELINE_TOTAL}, {MQL_SAL_CVR}, {SAL_SQL_CVR},
  '{notes}', '{iso_now}'
);
```

### 4. Calculate Baselines

Query `funnel_snapshots` for the trailing 28 days (excluding today) to
establish baselines:

```sql
SELECT
  AVG(mqls) AS mql_baseline,
  AVG(sals) AS sal_baseline,
  AVG(sqls) AS sql_baseline,
  AVG(mql_to_sal_rate) AS mql_sal_baseline,
  AVG(sal_to_sql_rate) AS sal_sql_baseline,
  AVG(pipeline_value) AS pipeline_baseline_avg,
  SUM(pipeline_value) AS pipeline_baseline_sum_7d
FROM funnel_snapshots
WHERE snapshot_date >= date('now', '-28 days')
  AND snapshot_date < date('now');
```

If fewer than 14 days of history exist, note "limited baseline" in the
journal entry and skip deviation-based anomaly flagging.

### 5. Apply Anomaly Thresholds

From `state/identity/revops-watchdog.md`:

| Metric | Condition | Severity |
|--------|-----------|----------|
| MQL count | >20% deviation from 4-week avg (up or down) | MED |
| MQL→SAL CVR (Contact-only cohort) | <55% OR trending down 3+ consecutive days | MED |
| SAL→SQL CVR (Contact-only cohort) | <35% | MED |
| Pipeline (7-day rolling sum) | >25% below trailing 4-week average | MED |

Low-N suppression: skip the absolute CVR thresholds while MTD MQL count <20
(early-month samples); the trend rule still applies. CVR thresholds are
calibrated to the Contact-only cohort method (standing since scorecard v1.1,
recalibrated at the definitions sign-off, handoff id=90); the Deal-based series
is deprecated reference only.

For each anomaly, INSERT into `anomalies`:

```sql
INSERT INTO anomalies (
  agent, detected_at, surface, metric, value, baseline,
  deviation_pct, severity, description, status, created_at
) VALUES (
  'revops-watchdog', '{iso_now}', 'funnel', '{metric_name}', {value}, {baseline},
  {deviation_pct}, '{severity}', '{description}', 'open', '{iso_now}'
);
```

### 6. Detect Trend-Based Anomalies

For MQL→SAL CVR "trending down 3+ consecutive days":

```sql
SELECT snapshot_date, mql_to_sal_rate
FROM funnel_snapshots
WHERE snapshot_date >= date('now', '-4 days')
ORDER BY snapshot_date DESC
LIMIT 4;
```

If the CVR has decreased on 3 consecutive days (excluding today), flag as
MED regardless of absolute value.

### 7. Write Handoffs

For each MED or HIGH anomaly, append to `state/journal/handoffs.md` and
INSERT into `handoffs` table:

```
## YYYY-MM-DDTHH:MM:SSZ | revops-watchdog → chief-of-staff | {severity}: Funnel anomaly — {metric}

**Severity:** {severity}
**Surface:** funnel
**Metric:** {metric}
**Value:** {value}
**Baseline (4-wk avg):** {baseline}
**Deviation:** {deviation_pct}%
**Recommended action:** {action or "Investigate; no action recommended yet"}
**Tier gate:** 1 (chief-of-staff curates for brief)
```

## Output

- `funnel_snapshots` row (always, one per day)
- `anomalies` rows (zero or more)
- `handoffs` rows for MED/HIGH (zero or more)
- Journal entry section with metric summary and any flags

## No-Data Behavior

If HubSpot query fails:
- Write to `state/journal/ops-incidents.md` with severity HIGH
- Do NOT write a partial `funnel_snapshots` row
- Do NOT commit partial state
- Write a handoff to chief-of-staff describing the failure

## Phase 1 Grace

If `funnel_snapshots` has <14 days of history:
- Write the snapshot normally
- Skip baseline-deviation anomaly detection
- Note "baseline establishing (N/14 days)" in the journal entry
- Do not treat missing baseline as an anomaly
