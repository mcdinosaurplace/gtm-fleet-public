---
name: revops-watchdog:property-dependency-map
description: >
  Maps which workflows, lists, reports, and scoring rules depend on each
  HubSpot custom property. Surfaces deprecation risk (don't delete this!),
  unused properties (dead weight), and over-loaded properties (single point
  of failure). Reads all workflow-spec-*.md and lifecycle-map-*.md artifacts
  to cross-reference designed dependencies.
---

# Property Dependency Map

## When This Runs

- **Standalone:** `/revops-watchdog property-dependency-map`
- **Typical cadence:** Quarterly, or triggered before any property
  deprecation decision

## Inputs

- HubSpot custom property list (all object types: contact, company, deal)
- HubSpot workflows and their enrollment criteria / action steps
- HubSpot lists and their membership criteria
- HubSpot reports / dashboards (if accessible)
- HubSpot scoring rules / score configuration

## Cross-Agent Input: Design Artifacts

Parse all available design artifacts to extract declared property dependencies:

**workflow-spec-*.md files:**
- Enrollment triggers (which properties gate enrollment)
- Action sequence property updates (which properties the workflow writes)
- Branching conditions (which properties are read in branches)
- Exit criteria (which properties trigger exit)

**lifecycle-map-*.md files:**
- Per-stage required properties
- Transition criteria properties
- Stage-date properties (e.g., `mql_date__latest_`)

**lead-score-doc-*.md files:**
- Properties used in scoring rules

**sop-*.md files:**
- Properties required by data entry rules

Create an aggregate map: property → [designed dependencies].

## Analysis

### 1. Build the Dependency Graph

For each property, collect all dependents:
- Workflows that read it (enrollment or branch condition)
- Workflows that write it (action step)
- Lists that filter on it
- Reports that group/filter by it
- Scoring rules that reference it
- Lifecycle stage transitions that require it

Classify dependents as:
- **Designed** (appears in a design artifact)
- **Runtime-only** (exists in HubSpot but no design artifact references it
  — this is drift)

### 2. Risk Classification

For each property, calculate:
- `dependent_count` = total dependents
- `criticality` = highest-tier dependent (workflow > list > report)
- `designed_coverage` = % of dependents that are documented

| Property Risk Tier | Condition |
|-------------------|-----------|
| **Critical** | >5 dependents OR any workflow that drives MQL/SAL/SQL transitions |
| **Important** | 2-5 dependents, at least one workflow |
| **Light** | 1 dependent, or only informational (list/report) |
| **Orphan** | 0 dependents — candidate for deprecation |
| **Undocumented-Critical** | Critical tier AND designed_coverage <50% — highest risk |

### 3. Deprecation Candidates

Orphan properties are safe to deprecate. Surface:
- Property name, type, created date
- When last populated on a contact (if accessible)
- Recommendation to archive or delete

### 4. Overloaded Properties

Properties with >10 dependents represent a single point of failure. Any
change to the property (label, type, allowed values) could cascade.
Flag these as "architectural risk" — not broken, but fragile.

### 5. Drift Detection

For each runtime-only dependency (HubSpot uses it, but no design spec
references it), flag as design drift. Recommend:
- Update the relevant spec (workflow-spec / lifecycle-map / etc.) to
  document the dependency
- OR remove the runtime dependency if it's not intentional

## Output Format

```markdown
## Property Dependency Map — {Date}

### Design Artifacts Loaded
- workflow-spec files: {N}
- lifecycle-map files: {N}
- lead-score-doc files: {N}
- SOP files: {N}

### Summary
| Tier | Property Count |
|------|---------------|
| Critical | {N} |
| Important | {N} |
| Light | {N} |
| Orphan (deprecation candidates) | {N} |
| Undocumented-Critical (risk) | {N} |

### Critical Properties
| Property | Object | Dependents | Designed Coverage | Notable |
|----------|--------|-----------|------------------|---------|
| {property_name} | Contact | {N} | {pct}% | {e.g., "drives MQL workflow"} |

### Undocumented-Critical (investigate)
| Property | Object | Undocumented Dependents | Risk |
|----------|--------|------------------------|------|

### Orphan Properties (deprecation candidates)
| Property | Object | Created | Last Populated | Safe to Remove? |
|----------|--------|---------|---------------|----------------|

### Overloaded Properties (architectural risk)
| Property | Dependents | Types of Dependents |
|----------|-----------|---------------------|
| {name} | {N} | workflows: X, lists: Y, reports: Z, scoring: W |

### Full Dependency Table
| Property | Workflows (R/W) | Lists | Reports | Scoring | SOPs |
|----------|----------------|-------|---------|---------|------|
| {name} | R: [...] W: [...] | [...] | [...] | [...] | [...] |

### Design Drift
- Properties with HubSpot dependencies not reflected in any spec: {N}
- Example: `{property}` is used in workflow "X" but workflow-spec "X"
  doesn't mention it

### Recommended gtm-ops action
**Deprecate:**
- {list of orphan properties safe to remove}

**Document (run /workflow-spec or /lifecycle-map):**
- {runtime-only dependencies that should be captured in spec}

**Architectural review:**
- {overloaded properties that may need refactoring}
```

## Anomaly Table Writes

INSERT into `anomalies` with `surface='property'`:
- Undocumented-Critical properties (one row per property) → MED
- Overloaded properties (single row if >3 exist) → LOW

Do not flag orphan properties as anomalies — they are informational
only.

## Handoff

One handoff to chief-of-staff with:
- Summary counts per tier
- Top 3 undocumented-critical properties to investigate
- Orphan property count + flag that they're safe to review for deletion
- Path to full dependency map
