---
name: lifecycle-map
description: Design or document {{COMPANY}}'s lifecycle stages. Use for designing stage changes, documenting transition criteria, specifying HubSpot property requirements, or mapping the full contact/company lifecycle.
allowed-tools: Read Write
disable-model-invocation: true
---

# /lifecycle-map

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/funnel.md` before proceeding.

## What to Ask

If the user hasn't specified, ask:
- Are they **designing a change** (new or modified stages) or **documenting the current state**?
- Which object: Contacts, Companies, or Deals?
- Is there a specific stage or transition they're focused on, or the full lifecycle?

## What to Produce

Generate a lifecycle map document with these sections:

### 1. Stage Overview Table

| Stage | Definition | Entry Criteria | Exit Criteria | Owner |
|-------|-----------|----------------|---------------|-------|

### 2. Transition Criteria (per transition)

For each stage-to-stage transition, document:
- **Trigger**: what event or condition fires the transition
- **Detection logic**: how HubSpot detects it (property value, workflow enrollment, form submission, manual update)
- **Required properties**: what must be set on the contact/company record for the transition to be valid
- **Blocking conditions**: what would prevent the transition from firing

### 3. HubSpot Implementation Notes

For each stage, list:
- HubSpot lifecycle stage value (exact property value)
- Any custom properties that gate this stage
- Workflow(s) that manage this transition
- Any {{ENRICHMENT_VENDOR}} signal inputs that affect this transition

### 4. Visual Flow (ASCII)

Produce a simple ASCII flow diagram of the stage path, marking decision branches and detour paths.

### 5. Known Issues / Open Questions

Flag any ambiguities, redundant states, or gaps in the current design that need resolution.

## Output

Save the lifecycle map as a Markdown file to the user's outputs folder: `lifecycle-map-{object}-{date}.md`. Present the file link when done. Also display the stage overview table inline in chat for a quick scan.
