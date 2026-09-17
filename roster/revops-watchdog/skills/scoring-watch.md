---
name: revops-watchdog:scoring-watch
description: >
  Daily lead score distribution snapshot and drift detection. Pulls HubSpot
  lead score distribution, calculates median and top-decile counts, flags
  drift >10 points in 7 days or top-decile shrink >15% WoW. Reads
  lead-score-doc artifacts to know the designed model and expected
  distribution.
---

# Scoring Watch

## When This Runs

- **Tick integration:** Every daily Tick
- **Standalone:** `/revops-watchdog scoring-watch`

## Inputs

- HubSpot lead score data (via MCP or API)
  - Contact-level score values for all active contacts (or a representative
    sample — if full distribution is impractical, use score bucket counts)
  - Score thresholds in use (MQL, SAL trigger points)

## Cross-Agent Input: lead-score-doc Artifacts

Search for the most recent `lead-score-doc-*.md` or `lead-score-doc-v*.md`
artifact in common output locations. If found, extract:
- Designed MQL / SAL score thresholds
- Expected score distribution (if documented)
- Scoring rule categories (behavioral, firmographic, negative signals)
- Decay rules

Use this as the "should be" reference for interpreting observed distribution.
If no doc exists, audit live distribution alone and note in the journal.

## Workflow

### 1. Pull Score Distribution

Pull the current score distribution from HubSpot. Capture:
- Total contact count with a score value
- Score distribution in buckets: `0-9`, `10-19`, `20-29`, ..., `90-99`, `100+`
- Median score (50th percentile)
- Mean score
- Top decile count (contacts with score >= 80)

Store the bucket distribution as a JSON blob for the `scoring_drift` table.

### 2. Read Prior Snapshots

Query `scoring_drift` for entries from 7 days ago (for 7-day drift) and
from the prior Friday (for WoW top-decile comparison):

```sql
-- 7-day prior for median drift
SELECT median_score
FROM scoring_drift
WHERE snapshot_date = date('now', '-7 days')
  AND agent = 'revops-watchdog';

-- Prior week for top-decile comparison
SELECT top_decile_count
FROM scoring_drift
WHERE snapshot_date BETWEEN date('now', '-8 days') AND date('now', '-6 days')
  AND agent = 'revops-watchdog'
ORDER BY snapshot_date DESC
LIMIT 1;
```

### 3. Calculate Drift Metrics

- `median_drift_7d` = current_median - median_7_days_ago
- `top_decile_wow_pct` = (current_top_decile - prior_week_top_decile) /
  prior_week_top_decile * 100

### 4. Apply Anomaly Rules

From identity file:

| Condition | Severity | Flag |
|-----------|----------|------|
| `abs(median_drift_7d) > 10` | MED | "median_drift" |
| `top_decile_wow_pct < -15` (shrunk >15% WoW) | MED | "top_decile_shrink" |
| `top_decile_wow_pct > +50` (unusual growth) | LOW | "top_decile_surge" (monitor; may indicate scoring rule change) |

### 5. Write Scoring Drift Record

INSERT one row per day:

```sql
INSERT INTO scoring_drift (
  agent, snapshot_date, median_score, top_decile_count, top_decile_pct,
  distribution_json, drift_flag, drift_note, created_at
) VALUES (
  'revops-watchdog', '{today}', {median}, {top_decile_count}, {top_decile_pct},
  '{distribution_json}', {drift_flag_int}, '{drift_note}', '{iso_now}'
);
```

Set `drift_flag` to 1 if any anomaly rule fired, 0 otherwise.
`drift_note` includes a human-readable summary of what drifted.

### 6. Write Anomalies

For each MED flag, INSERT into `anomalies` with `surface='scoring'`:

```sql
INSERT INTO anomalies (
  agent, detected_at, surface, metric, value, baseline,
  deviation_pct, severity, description, status, created_at
) VALUES (
  'revops-watchdog', '{iso_now}', 'scoring', '{flag_name}', {current}, {baseline},
  {deviation_pct}, 'MED', '{description}', 'open', '{iso_now}'
);
```

### 7. Cross-Reference lead-score-doc

If a `lead-score-doc-*.md` artifact exists, note in each anomaly's
description whether the drift conflicts with the designed model. Examples:

> "Median score dropped 12 points in 7 days (65 → 53). Per the current
> lead-score-doc artifact, the designed median should be 55-75
> based on firmographic distribution. Current median below design range."

> "Top decile (80+) count dropped 22% WoW (340 → 265). Per the current
> lead-score-doc artifact, the 80+ threshold maps to MQL
> auto-qualification. Sharp decline may indicate scoring rule regression
> or decay rule acceleration."

### 8. Write Handoffs

For MED anomalies, append to handoffs for inclusion in chief-of-staff's next AM
brief.

## Output

- `scoring_drift` row (always, one per day)
- `anomalies` rows (zero or more)
- `handoffs` rows for MED (batched)
- Journal entry section summarizing median, top-decile, and any drift

## Phase 1 Grace

If fewer than 8 days of `scoring_drift` history exist:
- Write the snapshot normally
- Skip 7-day drift detection (note "baseline establishing" in journal)
- Skip WoW top-decile comparison
- Do not flag missing history as an anomaly
