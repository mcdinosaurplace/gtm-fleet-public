---
name: revops-watchdog:workflow-watch
description: >
  Daily HubSpot workflow health monitoring. Tracks active workflow enrollment
  and exit rates, flags zero-enrollment workflows (paused/broken), 100%
  first-step exits (misconfigured triggers), new/deleted workflows, and
  action failures. Reads workflow-spec artifacts (if present) to compare
  live behavior against designed intent.
---

# Workflow Watch

## When This Runs

- **Tick integration:** Every daily Tick
- **Standalone:** `/revops-watchdog workflow-watch`

## Inputs

- HubSpot workflow list and per-workflow performance stats (via MCP or API)
  - Active workflows
  - 24h enrollment count per workflow
  - 24h exit count per workflow
  - First-step exit rate (contacts exiting on the first action)
  - Action failure counts (email bounces, property update failures, etc.)

## Cross-Agent Input: workflow-spec Artifacts

Search for the most recent `workflow-spec-*.md` artifacts. Common locations
to check:
- `docs/` (project docs)
- `outputs/` (generic outputs folder if configured)
- `.claude/outputs/` (skill-output directory pattern)

If found, parse each spec to extract:
- Workflow name or ID
- Designed enrollment trigger (what should enroll)
- Designed action sequence (what should happen)
- Designed exit criteria (when should it exit)

Use these as the "should be" baseline when interpreting live behavior.
If no spec exists for a workflow, audit against live state alone and note
"no design spec available" for that workflow.

## Workflow

### 1. Pull Active Workflows

Get the list of all active workflows from HubSpot. For each, capture:
- `workflow_id`
- `workflow_name`
- 24h enrollment count (`enrollments_24h`)
- 24h exit count (`exits_24h`)
- First-step exit rate (`first_step_exit_rate` — float, 0.0 to 1.0)
- Active status (`is_active`)

### 2. Read Prior Snapshot

Query `workflow_health` for the most recent entry per workflow to detect:
- Workflows that appeared today but not yesterday (new workflows)
- Workflows that disappeared (deleted or deactivated since last Tick)
- Workflows transitioning from active to inactive

### 3. Apply Anomaly Rules

From `state/identity/revops-watchdog.md`:

| Condition | Severity | Flag |
|-----------|----------|------|
| `enrollments_24h == 0` for 3+ consecutive days on an active workflow | MED | "stalled_enrollment" |
| `first_step_exit_rate >= 1.0` (100% first-step exit) | HIGH | "immediate_exit_anomaly" |
| New workflow detected (not in prior snapshot) | LOW | "new_workflow" |
| Deleted workflow detected (was active yesterday, gone today) | LOW | "deleted_workflow" |
| `first_step_exit_rate >= 0.80` (near-universal exit) | MED | "high_first_step_exit" |

Note: For "stalled 3+ days," query the trailing 3-day `workflow_health`
history for that workflow.

### 4. Write Workflow Health Records

INSERT one row per active workflow:

```sql
INSERT INTO workflow_health (
  agent, check_date, workflow_id, workflow_name,
  enrollments_24h, exits_24h, first_step_exit_rate,
  is_active, flag, created_at
) VALUES (
  'revops-watchdog', '{today}', '{workflow_id}', '{workflow_name}',
  {enrollments_24h}, {exits_24h}, {first_step_exit_rate},
  {is_active_int}, {flag_or_null}, '{iso_now}'
);
```

Set `flag` to the condition name (e.g., `'stalled_enrollment'`) if any rule
matched, otherwise NULL.

### 5. Write Anomalies

For each HIGH or MED flagged workflow, INSERT into `anomalies`:

```sql
INSERT INTO anomalies (
  agent, detected_at, surface, metric, value, baseline,
  deviation_pct, severity, description, status, created_at
) VALUES (
  'revops-watchdog', '{iso_now}', 'workflow_health', '{flag_name}',
  {observed_value}, {expected_value_or_null}, {deviation_or_null},
  '{severity}', '{description}', 'open', '{iso_now}'
);
```

Description should include workflow name, specific metric, and (if
workflow-spec is available) a note on whether behavior diverges from spec.

### 6. Cross-Reference Design Spec

For each flagged workflow, if a `workflow-spec-*.md` artifact exists:
- Note whether the flagged behavior contradicts the spec's designed
  enrollment or exit criteria
- Include spec filename and relevant section in the description

Example:
> "Workflow 'New Contact Nurture' has 100% first-step exit. Per the current
> new-contact-nurture workflow-spec artifact, the first action
> should be 'Send welcome email' with no designed exit branch."

### 7. Write Handoffs

For each HIGH anomaly, write an immediate handoff to chief-of-staff. For MED
anomalies, include in the next AM handoff batch.

## Output

- `workflow_health` rows (one per active workflow, always)
- `anomalies` rows (zero or more)
- `handoffs` rows for HIGH (immediate), MED (batched)
- Journal entry section summarizing counts and flagged workflows

## Phase 1 Grace

If HubSpot workflow API access is not yet configured:
- Log "workflow data unavailable — skipped" in journal
- Do NOT treat missing access as an anomaly (it's an infrastructure gap,
  not a HubSpot health issue)
- Flag the infrastructure gap as a LOW incident in `ops-incidents.md`
  once per week (not every Tick) to avoid noise
