---
name: revops-watchdog:lifecycle-audit
description: >
  Monthly HubSpot lifecycle integrity audit. Finds contacts stuck in stages
  too long, skipped stages, orphaned lifecycle states (MQL date without
  MQL type), backward stage transitions, and contact/deal stage misalignment.
  Reads the most recent lifecycle-map-*.md artifact to get canonical stage
  definitions and transition criteria. Flags drift between designed
  architecture and live state.
---

# Lifecycle Audit

## When This Runs

- **Standalone:** `/revops-watchdog lifecycle-audit`
- **Typical cadence:** Monthly (first weekday of each month)

## Inputs

- HubSpot contacts with lifecycle stage, MQL date, MQL type, SAL date,
  SQL date, and associated deal data
- Deal records with deal stage, associated contact, and stage-entered
  timestamps

## Cross-Agent Input: lifecycle-map Artifact

Search for the most recent `lifecycle-map-*.md` artifact. Common paths:
- `docs/lifecycle-map-*.md`
- `outputs/lifecycle-map-*.md`
- `.claude/outputs/lifecycle-map-*.md`

**Canonical source:** the lead lifecycle model is the adopted single source of
truth in
[`docs/lead-lifecycle-model.md`](../../../docs/lead-lifecycle-model.md) (v1.0.0);
its frozen snapshot `docs/lifecycle-map-2026-06-30.md` is the current artifact
this audit consumes. It defines the real HubSpot stages (Prospect → Marketing
Engaged → Marketing Qualified Lead → Sales Accepted Lead → Sales Qualified Lead →
Sales Accepted Opportunity → Customer, plus Nurture/Unqualified detours) and the
Q2-2026 SAL/SQL meanings (SAL = Sales accepts and pursues a meeting; SQL = a
meeting is successfully booked).

Parse the document to extract:
- Canonical lifecycle stages (ordered list)
- Entry criteria per stage
- Exit criteria per stage
- Required HubSpot properties per stage (e.g., MQL stage requires
  mql_date__latest_ AND mql_type_latest)
- Expected time-in-stage benchmarks
- Allowed transitions (forward, backward, skip)

If no `lifecycle-map-*.md` exists, use a fallback set of universal rules
(stuck contacts, orphaned states, backward transitions) and note in the
output that no design spec was loaded.

## Audit Checks

### 1. Stuck Contacts

For each lifecycle stage, identify contacts that have been in the stage
longer than the expected time-in-stage benchmark (from lifecycle-map, or
a default of 60 days if no spec).

Output: list of contact IDs, names, current stage, days in stage, source.

### 2. Stage Skipping

Find contacts whose lifecycle history shows a stage jump that bypasses
intermediate stages (e.g., Marketing Engaged → SQL with no MQL or SAL date).

This requires either:
- HubSpot contact property history (if accessible)
- Comparison of stage-date properties (e.g., sql_date without mql_date)

Output: list of contacts with the skipped stage(s) and the transition.

### 3. Orphaned Lifecycle States

Identify property inconsistencies:

| Check | Orphan Condition |
|-------|-----------------|
| MQL without type | `mql_date__latest_` IS NOT NULL AND `mql_type_latest` IS NULL |
| MQL type without date | `mql_type_latest` IS NOT NULL AND `mql_date__latest_` IS NULL |
| SAL without MQL | lifecycle stage = SAL AND no `mql_date__latest_` |
| SQL without qualifying deal | lifecycle stage = SQL AND no associated open deal at Discovery Scheduled (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later |

Cross-reference lifecycle-map's "required properties per stage" section
to add any site-specific orphan checks.

### 4. Backward Transitions

Contacts whose lifecycle stage moved backward (e.g., SQL → MQL) without
an explicit reason (recycle workflow, manual reset).

Generally indicates a data error or workflow misconfiguration. Output:
list of contacts, previous stage, current stage, transition date.

### 5. Contact/Deal Stage Misalignment

For contacts marked as SQL, verify:
- At least one associated deal exists in the sales pipeline
- The deal is not in a closed-lost state (a closed-lost deal should
  trigger lifecycle regression to disqualified, not remain SQL)

For deals in Discovery Scheduled or later stages, verify:
- Associated contact is marked SAL or SQL
- No Subscriber or Lead stage contacts have active open deals

## Output Format

```markdown
## Lifecycle Audit — {Date}

### Design Spec Loaded
- File: {lifecycle-map-*.md or "No spec found — using defaults"}
- Date: {spec date}
- Stages defined: {count}

### Summary
- Total contacts audited: {N}
- Issues found: {N}
- Severity breakdown: {HIGH: X, MED: Y, LOW: Z}

### Stuck Contacts
| Contact | Stage | Days in Stage | Source | Severity |
|---------|-------|--------------|--------|----------|
| {name or email} | {stage} | {days} | {source} | {LOW/MED} |

### Stage Skipping
| Contact | From | To | Skipped | Date |
|---------|------|-----|---------|------|

### Orphaned Lifecycle States
| Contact | Orphan Condition | Fix Hint |
|---------|-----------------|----------|
| {id} | {description} | {suggested property update or workflow check} |

### Backward Transitions
| Contact | From | To | Date | Plausible Cause |
|---------|------|-----|------|----------------|

### Contact/Deal Misalignments
| Contact | Contact Stage | Deal Stage | Issue |
|---------|--------------|-----------|-------|

### Design Drift Findings
{Specific cases where live behavior contradicts lifecycle-map design}

### Recommended gtm-ops action
{If significant drift: "Run /lifecycle-map to document current state and
reconcile with designed architecture"}
{If data quality issue: "Consider workflow fix or bulk contact cleanup"}
```

## Anomaly Table Writes

For each MED or HIGH issue category, INSERT into `anomalies`:

```sql
INSERT INTO anomalies (
  agent, detected_at, surface, metric, value, baseline,
  deviation_pct, severity, description, status, created_at
) VALUES (
  'revops-watchdog', '{iso_now}', 'lifecycle', '{check_name}',
  {issue_count}, NULL, NULL, '{severity}',
  '{summary_description}', 'open', '{iso_now}'
);
```

Do not create per-contact anomaly rows (would be noisy). Create one anomaly
row per check category that exceeded a threshold:
- >50 stuck contacts in any single stage = MED
- >10 orphaned lifecycle states = MED
- Any backward transitions in the past 30 days = LOW (investigate; may be
  expected from recycle workflows)

## Handoff

Write one consolidated handoff to chief-of-staff summarizing the audit with a
link to the full output. Include top 3 issues and recommended follow-up
action.
