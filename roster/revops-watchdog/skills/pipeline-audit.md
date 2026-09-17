---
name: revops-watchdog:pipeline-audit
description: >
  Weekly HubSpot deal pipeline integrity audit. Finds stuck deals, deals
  missing amounts, past-due close dates, deal-contact-company association
  gaps, and owner assignment issues. References {{company_slug}}-funnel.md stage
  definitions and HubSpot pipeline IDs from funnel-stats.
---

# Pipeline Audit

## When This Runs

- **Standalone:** `/revops-watchdog pipeline-audit`
- **Typical cadence:** Weekly (Monday)

## Inputs

- HubSpot deal records (from the main sales pipeline — ID `{{HUBSPOT_PIPELINE_ID}}` per
  funnel-stats reference)
- Associated contact and company records
- Deal stage history / stage-entered timestamps
- HubSpot user records (for owner assignment checks)

## Cross-Agent Input: Stage Definitions

Reference `skills/gtm-ops/references/funnel.md` (via gtm-fleet
plugin) for canonical stage definitions, transition criteria, and expected
time-in-stage benchmarks.

Key stage IDs from funnel-stats:
- Discovery Scheduled: `{{HUBSPOT_STAGE_DISCOVERY_ID}}` (SAL stage)
- Closed Won: `{{HUBSPOT_STAGE_CLOSED_WON_ID}}`
- Closed Lost: `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}`

## Audit Checks

### 1. Stuck Deals

For each active (non-closed) deal, calculate days in current stage.
Compare to expected time-in-stage from `{{company_slug}}-funnel.md` (or defaults if
unavailable).

Default stuck thresholds:
| Stage | Expected Max Days | Flag if Beyond |
|-------|------------------|---------------|
| Discovery Scheduled | 14 | 21 days → MED |
| Discovery Completed | 14 | 21 days → MED |
| Value Identified | 21 | 30 days → MED |
| Demo Completed | 30 | 45 days → MED |
| Proposal | 30 | 45 days → MED |
| Negotiation | 21 | 30 days → MED |

Output: list of stuck deals with stage, days in stage, owner, last activity.

### 2. Missing or Implausible Deal Amounts

For non-existing-business deals beyond Discovery Scheduled:
- `amount IS NULL` → flag (MED)
- `amount <= 0` → flag (MED; likely test deal or data error)
- `amount > threshold_implausible` (e.g., >$10M for {{COMPANY}}'s SMB focus) →
  flag as LOW for review (could be legitimate, but verify)

### 3. Past-Due Close Dates

Deals with `closedate` in the past but `dealstage` is not closed:
- Calculate days past due
- Flag all as MED (forecast integrity issue)
- Sort by days past due descending

### 4. Deal-Contact-Company Association Gaps

**Deals without contacts:**
- Any deal with zero associated contacts → HIGH (breaks attribution,
  breaks routing)

**Deals without companies:**
- For non-existing-business deals → MED (company context missing)
- For deals > $50K amount → HIGH (enterprise deals must have company)

**Contact/deal-stage consistency (cross-reference with lifecycle-audit):**
- Primary contact on an SQL-stage deal should be lifecycle = SAL or SQL
- Flag mismatches

### 5. Owner Assignment Integrity

- Deals with no owner assigned → HIGH
- Deals assigned to inactive / deactivated HubSpot users → MED
- Deal owner in a role inconsistent with stage (e.g., SDR owner on a
  Negotiation-stage deal) → LOW (informational; may be legitimate)

## Output Format

```markdown
## Pipeline Audit — {Week of Date}

### Stage Definitions Source
{{{company_slug}}-funnel.md path or "Using default time-in-stage thresholds"}

### Summary
| Check | Deals Flagged | Severity Split |
|-------|--------------|---------------|
| Stuck deals | {N} | {HIGH: X, MED: Y} |
| Missing amounts | {N} | MED |
| Past-due close dates | {N} | MED |
| Missing contact association | {N} | HIGH |
| Missing company association | {N} | {split} |
| Owner issues | {N} | {split} |

### Stuck Deals (Top 20 by Days Stuck)
| Deal | Stage | Days in Stage | Amount | Owner | Last Activity |
|------|-------|--------------|--------|-------|---------------|
| {name} | {stage} | {days} | ${amount} | {owner} | {date} |

### Missing or Implausible Amounts
| Deal | Stage | Amount | Issue |
|------|-------|--------|-------|

### Past-Due Close Dates
| Deal | Close Date | Days Past Due | Stage | Amount | Owner |
|------|-----------|---------------|-------|--------|-------|

### Association Gaps
**Deals without contacts:**
- {N} deals; top affected owners: {list}

**Deals without companies:**
- {N} total; {M} with amount >$50K (HIGH priority)

### Owner Assignment Issues
| Deal | Owner Issue | Stage |
|------|------------|-------|

### Recommended gtm-ops action
{If stuck deals concentrated in one stage: "Run /lifecycle-map to review
transition criteria for {stage}"}
{If association gaps systemic: "Run /workflow-spec to design a deal
association enforcement workflow"}
{If amounts missing at scale: "Consider mandatory amount field at deal
creation"}
```

## Anomaly Table Writes

INSERT into `anomalies` with `surface='pipeline'`. Aggregate per check
category (not per deal — avoid noise).

MED/HIGH thresholds:
- Stuck deals >20% of pipeline = MED
- Missing contact associations >5 = HIGH
- Missing company associations on deals >$50K >3 = HIGH
- Past-due close dates >10 = MED

## Handoff

Weekly handoff to chief-of-staff with:
- Top 3 issue categories
- Impact on pipeline forecast accuracy
- Recommended follow-up (clean-up workflow, data entry SOP, etc.)
