---
name: sprint-plan
description: Create a GTM Ops sprint plan — objectives, backlog items with priorities and effort, dependencies, and acceptance criteria formatted for Linear.
allowed-tools: Read Write
disable-model-invocation: true
---

# /sprint-plan

Load the `gtm-ops` skill before proceeding.

## What to Ask

Ask the user:
- **Sprint goal**: What is the one-sentence outcome this sprint should deliver?
- **Duration**: How long is the sprint? ({{COMPANY}} standard: 1–2 weeks)
- **Backlog items**: What are the known tasks? (They can list rough items — you'll structure them.)
- **Current priorities context**: Reference Q3/Q4 priorities (lifecycle revamp, attribution, content/lead-gen rebuild, tool governance) and ask if this sprint is aligned to one of these or separate.

If they say "just figure it out from what we've been working on," generate a suggested sprint based on known current priorities from the gtm-ops skill context.

## What to Produce

### 1. Sprint Header

```
Sprint: [Sprint Name or Number]
Goal: [One-sentence sprint objective]
Duration: [Start date] → [End date]
Owner: Scott McKeighen
Team: Marketing & Revenue Operations
```

### 2. Sprint Backlog

Format as a Linear-ready issue list. For each item:

| # | Issue Title | Priority | Effort | Owner | Dependencies | Acceptance Criteria |
|---|-------------|----------|--------|-------|--------------|-------------------|
| 1 | | P0/P1/P2 | S/M/L/XL | | | |

**Priority scale**: P0 = blocking / urgent, P1 = high value, P2 = standard, P3 = nice to have
**Effort scale**: S = <2h, M = 2–4h, L = 4–8h, XL = >1 day

### 3. Dependencies Map

List inter-issue dependencies and any cross-functional blockers:
- Issue N depends on Issue M
- External dependency: [what's needed from Sales / Marketing / Product]

### 4. Risks and Open Questions

Flag anything that could block sprint completion. Format as:
> **Risk**: [Description] → **Mitigation**: [What to do if it occurs]

### 5. Definition of Done

Sprint-level acceptance criteria — what does "done" look like for this sprint as a whole?

### 6. Linear Import Block

Produce a clean, copy-paste-ready list of issues in Linear format:

```
[P0] Issue title — Acceptance criteria: ... | Estimate: M
[P1] Issue title — Acceptance criteria: ... | Estimate: L
```

## Output

Save as `sprint-plan-{sprint-name}-{date}.md` in the user's outputs folder and present the file link. Display the Sprint Header and Backlog table inline in chat.
