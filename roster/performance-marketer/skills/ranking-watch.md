---
name: performance-marketer:ranking-watch
description: >
  Daily keyword position monitoring for tracked priority terms. Snapshots
  positions, compares to prior readings, flags movements exceeding thresholds.
  Detects SERP volatility patterns that may signal algorithm updates. Writes
  to keyword_rankings table; MED/HIGH severity triggers chief-of-staff handoff.
---

# Ranking Watch

## When This Runs

- **Tick integration:** Every daily Tick (weekdays, after spend-watch)
- **Standalone:** `/performance-marketer ranking-watch`

## Inputs

Keyword position data from one or more of:
- Google Search Console (via MCP or API)
- Third-party rank tracker (`~~SEO` tooling — via CSV or API)
- Manual input (user provides keyword + position list)

Required per keyword: keyword text, current position, URL ranking, date.
Optional: search volume, SERP features present.

## Priority Terms

Maintain a working list of tracked keywords. Sources:
- Keywords in the `keyword_rankings` table (historical tracking)
- Keywords from the latest `performance-marketer:keyword-research` output (if available)
- Keywords explicitly provided by the user

If no priority terms are established yet, ask the user for an initial list
or pull from existing `keyword_rankings` rows.

## Workflow

### 1. Snapshot Current Positions

For each tracked keyword, record the current position, ranking URL, and date.

### 2. Compare to Prior Snapshot

Query `keyword_rankings` for the most recent prior entry per keyword:

```sql
SELECT keyword, position AS prior_position, snapshot_date
FROM keyword_rankings
WHERE keyword = ?
ORDER BY snapshot_date DESC
LIMIT 1;
```

Calculate `position_delta` = prior_position - current_position
(positive = improvement, negative = decline).

### 3. Apply Anomaly Thresholds

From `state/identity/performance-marketer.md`:

| Condition | Severity | Action |
|-----------|----------|--------|
| Drop >5 positions | LOW | Journal entry only |
| Drop >10 positions | MED | Write handoff to chief-of-staff |
| Exits top 20 (was <=20, now >20) | HIGH | Immediate handoff |

### 4. Detect SERP Volatility

If 3+ tracked keywords moved >5 positions in the same direction on the
same day, flag a possible algorithm update or SERP volatility event.
Note this in the journal entry with the affected terms and direction.

### 5. Write to Database

INSERT one row per keyword per day:

```sql
INSERT INTO keyword_rankings (
  agent, snapshot_date, keyword, position, prior_position,
  position_delta, search_volume, url, flag, created_at
) VALUES (
  'performance-marketer', '{date}', '{keyword}', {position}, {prior_position},
  {delta}, {search_volume_or_null}, '{url}', '{flag_or_null}', '{iso_now}'
);
```

Set `flag` to the severity level if a threshold was triggered, NULL otherwise.

### 6. Escalate MED/HIGH

For MED and HIGH severity movements, write handoff to
`state/journal/handoffs.md` and INSERT into `handoffs` table:

```
## YYYY-MM-DDTHH:MM:SSZ | performance-marketer → chief-of-staff | {severity}: Keyword ranking drop

**Severity:** {MED|HIGH}
**Surface:** keyword_rankings
**Keyword:** {keyword}
**Movement:** Position {prior} → {current} (Δ {delta})
**URL:** {ranking_url}
**Possible cause:** {hypothesis if available, else "unknown — investigate"}
**Recommended action:** {action}
```

## Output

- `keyword_rankings` table rows (one per tracked keyword)
- Journal entry section (always — list top movers, flag anomalies)
- Handoff entries (MED/HIGH severity only)

## Ranking Correlation

When a keyword drops significantly, attempt to correlate with:
- Recent content changes (was the ranking page edited recently?)
- Technical changes (site speed, redirect changes, canonical updates)
- Competitor activity (new entrant ranking for this term?)
- Algorithm update signals (SERP volatility detected above)

Note correlations in the journal. If no correlation found, state "cause
unknown" — do not speculate without evidence.
