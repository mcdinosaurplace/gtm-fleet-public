---
name: performance-marketer:spend-watch
description: >
  Daily spend anomaly detection across Google Ads and LinkedIn Campaign Manager.
  Compares yesterday's spend, CPL, and CTR against trailing 7-day baselines.
  Flags deviations using severity thresholds from performance-marketer's identity constitution.
  Writes to spend_alerts table; HIGH severity triggers immediate chief-of-staff handoff.
---

# Spend Watch

## When This Runs

- **Tick integration:** Every daily Tick (weekdays, 08:30 PT)
- **Standalone:** `/performance-marketer spend-watch`

## Inputs

One or more of:
- Google Ads campaign performance — preferred path: `scripts/google_ads_pull.py
  --mode spend-watch` (loaded into `paid_creative` via `scripts/google_to_sqlite.py
  ads-spend`). Falls back to MCP or CSV upload if env is unconfigured.
- LinkedIn Campaign Manager performance data (via CSV upload or LinkedIn API
  once live) — this is the only source of LinkedIn **spend**.
- LinkedIn **lead-side** data via HubSpot contact attribution — always
  available through the HubSpot MCP. See
  `references/hubspot-ads-bridge.md` for the verified query patterns.
  HubSpot provides lead counts by campaign/day (the numerator), never spend
  (the denominator).

Required metrics per campaign: spend, impressions, clicks, CTR, CPC/CPM,
conversions, CPL/CPA.

If no data source is available, state what's missing and skip that platform.
Do not fabricate baselines.

## LinkedIn Lead-Flow Check (HubSpot-only fallback)

When LinkedIn spend data is unavailable but HubSpot is reachable, still run
a lead-flow check — it catches the highest-severity failure mode (campaign
dead, zero leads) without cost data:

1. Count contacts with `hs_analytics_source = PAID_SOCIAL` created yesterday
   (and per-campaign via `hs_analytics_source_data_2` = lowercased campaign
   name).
2. Compare to the trailing 7-day daily average of the same count.
3. Zero leads on a weekday when the trailing average is >= 1/day → MED
   "linkedin_lead_flow_stopped" (cannot distinguish paused campaign from
   broken Lead Gen Form without spend data — say so in the description).
4. Lead flow >2x trailing average → LOW note in journal (possible viral
   creative or audience change; flag for Friday's creative-optimizer pass).

Record these in `spend_alerts` with `metric = 'leads'` and
`platform = 'linkedin'`.

## Workflow

### 1. Pull Yesterday's Data

For each platform available, collect campaign-level metrics for the prior
business day. Weekend data: on Monday, pull Friday + Saturday + Sunday and
analyze each day separately.

### 2. Calculate Baselines

Query `spend_alerts` and `paid_creative` tables for the trailing 7-day average
per campaign per metric. If fewer than 7 days of data exist, use whatever
history is available and note the limited baseline in the journal entry.

### 3. Apply Anomaly Thresholds

From `state/identity/performance-marketer.md`:

| Metric | Condition | Severity |
|--------|-----------|----------|
| Daily spend | >25% above 7-day avg | MED |
| Daily spend | >30% below 7-day avg | MED |
| CPL | >20% increase day-over-day | MED |
| CTR | >15% drop on top-spend campaign | MED |
| Spend | $0 on any active campaign for full day | HIGH |

### 4. Write Alerts

For each anomaly detected, INSERT into `spend_alerts`:

```sql
INSERT INTO spend_alerts (
  agent, detected_at, platform, campaign_name, metric,
  value, baseline, deviation_pct, severity, description, status, created_at
) VALUES (
  'performance-marketer', '{iso_now}', '{platform}', '{campaign}', '{metric}',
  {value}, {baseline}, {deviation_pct}, '{severity}', '{description}', 'open', '{iso_now}'
);
```

### 5. Escalate HIGH Severity

If any HIGH-severity alert was written, create a handoff entry in
`state/journal/handoffs.md`:

```
## YYYY-MM-DDTHH:MM:SSZ | performance-marketer → chief-of-staff | HIGH: {subject}

**Severity:** HIGH
**Surface:** spend_alerts
**Platform:** {platform}
**Campaign:** {campaign_name}
**Finding:** {description}
**Recommended action:** {action}
**Tier gate:** {0 for journal-only, 2 for creative draft, 3 for platform change}
```

Also INSERT into the `handoffs` database table.

### 6. Rollback Watch (applied 3a changes)

Watch every Tier-3a change performance-marketer applied in the last `config.ROLLBACK_WATCH_HOURS`
(72h) for its stated reversal condition:

```python
from scripts.paid import db, execute
from scripts import google_ads_mutate as gm
watched = execute.changes_under_watch(db.list_applied_changes(conn, active_only=True), now)
```

For each watched change, look up the originating proposal's `reversal_if` and
evaluate it against today's metrics already pulled above (e.g. "CTR drops >15%",
"CPL spike >20%"). If the condition has tripped:

1. Write a **HIGH** handoff to chief-of-staff naming the change, the tripped condition,
   and the one-command rollback — `gm.rollback(applied_change, conn, now)` — with
   the `applied_changes.id`.
2. **Default is to propose, not auto-revert.** Scott (or the owning human) confirms
   via the Decision Queue, then performance-marketer runs `gm.rollback` on the next Tick (shadow
   unless `PERFORMANCE_MARKETER_EXECUTE=live`). Auto-revert-on-trip applies only to changes the
   greenlight explicitly pre-authorized; otherwise hold.
3. When a rollback is applied, `gm.rollback` stamps `rolled_back_at`; report it
   under *Closed loops* in the next AM brief.

A change whose 72h window passes with no tripped condition needs no action — it
drops out of the watch set automatically.

## Output

- `spend_alerts` table rows (one per anomaly)
- Journal entry section (always, even if no anomalies — report "no anomalies detected")
- Handoff entry (HIGH severity only)

## No-Data Behavior

If no spend data is available for a platform:
- Log in journal: "Google Ads data unavailable — skipped spend check"
- Do NOT write a spend_alerts row for missing data
- Do NOT flag missing data as an anomaly
