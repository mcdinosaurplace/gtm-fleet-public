---
name: revops-watchdog:scoring-calibration
description: >
  Deep lead scoring model accuracy analysis. Compares predicted conversion
  (based on score bucket) to actual conversion over historical windows.
  Rule-level signal-vs-noise analysis. Reads lead-score-doc-*.md as designed
  model spec; output is designed to feed the next lead-score-doc revision.
---

# Scoring Calibration

## When This Runs

- **Standalone:** `/revops-watchdog scoring-calibration`
- **Typical cadence:** Quarterly, or triggered when `scoring-watch` flags
  significant drift, or before a lead-score-doc revision

## Inputs

- Historical contact records (HubSpot): score at MQL creation, final
  lifecycle stage reached, deal outcome (if closed)
- Active scoring rules (HubSpot Score configuration)
- Time window: default trailing 90 days for short-cycle analysis;
  extend to 180 days if conversion volume is low

## Cross-Agent Input: lead-score-doc

Read the most recent `lead-score-doc-v*.md` artifact. Extract:
- Behavioral signal rules and point values
- Firmographic signal rules and weights
- Negative signals
- Decay rules (score aging, inactivity penalties)
- MQL / SAL threshold values (80+, etc.)
- Expected conversion rate per score bucket (if documented)

**This skill's output is explicitly designed to feed the next
lead-score-doc revision.** Frame findings in terms of "what should change
in the scoring model."

## Analysis Framework

### 1. Build the Calibration Dataset

For each contact with a score and a final outcome in the analysis window:
- `score_at_mql` (score value at the moment of MQL qualification)
- `final_stage` (most advanced stage reached: MQL, SAL, SQL, Won, Lost)
- `converted_to_sal` (boolean)
- `converted_to_sql` (boolean)
- `won` (boolean)
- `days_to_first_conversion` (time from MQL to SAL)

### 2. Score Bucket Conversion Analysis

Segment contacts into score buckets (e.g., 60-69, 70-79, 80-89, 90-99, 100+)
and calculate actual conversion rates per bucket:

| Score Bucket | MQL Count | Actual MQL→SAL | Actual MQL→SQL | Actual MQL→Won |
|-------------|-----------|---------------|----------------|---------------|
| 60-69 | N | X% | Y% | Z% |
| 70-79 | N | X% | Y% | Z% |
| 80-89 | N | X% | Y% | Z% |
| 90-99 | N | X% | Y% | Z% |
| 100+ | N | X% | Y% | Z% |

**Calibration check:** Conversion rate should monotonically increase with
score bucket. Any bucket that converts worse than a lower bucket is a
signal that the scoring model has a ranking flaw in that region.

### 3. Threshold Fit Analysis

Evaluate the designed MQL threshold (typically 80+):

- How many contacts below the threshold actually converted to SAL/SQL?
  (False negatives — rejected by scoring, but turned out to be qualified)
- How many contacts above the threshold converted vs. did not?
  (Precision above threshold)

Recommend:
- Raise threshold if precision is low (too many MQLs not converting)
- Lower threshold if false negative rate is high
- Keep current if both sides balanced

### 4. Rule-Level Signal Analysis

For each behavioral or firmographic rule in the model:
- How often does it fire?
- Among contacts where it fires, what's the conversion rate?
- Among contacts where it does NOT fire, what's the conversion rate?
- `signal_lift` = conversion_if_fired - conversion_if_not_fired

Rank rules by lift. Flag:
- Rules with negligible lift (< 2 percentage points) — candidates for
  removal
- Rules that never fire — dead rules to remove
- Rules with inverse lift (conversion lower when fired) — broken
  hypothesis

### 5. Decay Rule Check

If decay rules exist (score decreases after inactivity):
- How many contacts have been decayed in the window?
- Do decayed contacts genuinely have worse conversion than
  non-decayed contacts at the same current score?
- If yes, decay is working; if no, decay may be too aggressive or too lenient

### 6. Designed vs. Actual Distribution Comparison

From lead-score-doc (if documented), compare the expected score
distribution to observed. Document material deviations.

## Output Format

```markdown
## Scoring Calibration Analysis — {Date}

### Model Version Analyzed
- Source: {lead-score-doc-vN-YYYY-MM-DD.md}
- Analysis window: {start date} to {end date} ({N} days)
- Contacts analyzed: {N} (with score and outcome)

### Summary
| Finding | Direction | Magnitude |
|---------|-----------|-----------|
| Score-to-conversion monotonicity | {Pass/Fail} | {details} |
| MQL threshold precision | {pct} | {vs. target} |
| MQL threshold recall (false negatives) | {pct} | {vs. target} |
| Low-lift rules identified | {count} | — |
| Dead rules identified | {count} | — |

### Score Bucket Performance
| Bucket | N | MQL→SAL | MQL→SQL | MQL→Won | Avg Days to SAL |
|--------|---|---------|---------|---------|-----------------|

### Threshold Analysis
- Current MQL threshold: {N} (from lead-score-doc)
- Precision at threshold: {pct}% of ≥{N} convert to SAL
- False negative rate: {pct}% of <{N} converted anyway
- Recommendation: {raise to N2 / lower to N3 / keep}

### Rule-Level Lift
| Rule | Fires/N | Conversion If Fired | If Not | Lift | Recommendation |
|------|---------|--------------------|--------|------|----------------|
| {rule name} | {N}/{total} | {pct}% | {pct}% | {+/-pp} | {keep/modify/remove} |

### Decay Check
- Decayed contacts in window: {N}
- Conversion of decayed vs. non-decayed at same current score: {details}
- Assessment: {decay working / too aggressive / too lenient / no decay rules}

### Distribution Drift
- Expected (per lead-score-doc): {summary}
- Observed: {summary}
- Notable deviations: {list}

### Recommended gtm-ops action
**Run `/lead-score-doc` to revise the model with these changes:**
1. {specific rule change with rationale}
2. {threshold adjustment if warranted}
3. {rule removals}
4. {new rules to consider based on observed signals}

### Raw Data for Reference
{Link or embed to CSV / JSON of full calibration dataset if saved}
```

## Anomaly Table Writes

INSERT a summary anomaly row per calibration run with `surface='scoring'`,
`metric='calibration'`. Use severity MED by default (this is analysis, not
a live alert).

## Handoff

One handoff to chief-of-staff summarizing:
- Overall calibration verdict (pass / needs revision)
- Top 3 recommended model changes
- Link to full output
- Suggested owner: Scott (RevOps Admin), to run lead-score-doc next
