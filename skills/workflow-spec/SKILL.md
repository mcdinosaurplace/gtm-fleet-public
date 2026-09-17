---
name: workflow-spec
description: Spec a HubSpot workflow — enrollment triggers, action sequence, branching logic, exit criteria, property dependencies, and {{ENRICHMENT_VENDOR}}/Clay integration points.
allowed-tools: Read Write
disable-model-invocation: true
---

# /workflow-spec

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/stack.md` before proceeding. Pay particular attention to the {{ENRICHMENT_VENDOR}} section.

## What to Ask

Ask the user:
- **Workflow purpose**: What should this workflow accomplish? (e.g., "route MQLs to AEs", "trigger {{ENRICHMENT_VENDOR}} enrichment on new company record", "notify Sales when a contact hits the MQL threshold")
- **Object type**: Contact-based, Company-based, Deal-based, or Activity-based?
- **Trigger**: What event or property change fires enrollment?
- **{{ENRICHMENT_VENDOR}} involvement**: Does this workflow consume or produce a {{ENRICHMENT_VENDOR}} signal? (e.g., a marketing campaign conversion event should update HubSpot AND fire a {{ENRICHMENT_VENDOR}} signal)

## What to Produce

### 1. Workflow Overview

```
Workflow Name: [Name — use format: {Object} - {Action} - {Trigger}]
Object: [Contact / Company / Deal / Activity]
Purpose: [One sentence]
Owner: Scott McKeighen / Marketing Operations
Status: Draft — requires human review before activation
```

### 2. Enrollment Criteria

Describe the exact conditions that enroll a record:
- Property conditions (field name, operator, value)
- List membership conditions
- Form submission or activity triggers
- Re-enrollment: Yes / No — if yes, under what conditions?

### 3. Action Sequence

Number each action in order. For branching, use indented If/Else blocks:

```
1. [Delay: 0 minutes / immediate]
2. [Action: Set property "Lifecycle Stage" = "MQL"]
3. [Branch: If "AE Owner" is known]
   → YES: [Action: Create task for AE — "Follow up with MQL"]
   → NO:  [Action: Set property "Owner" = Round Robin pool]
            [Action: Send internal Slack notification via Zapier]
4. [Action: Send enrollment confirmation email]
5. [Delay: 3 days]
6. [Branch: If "SAL Date" is set]
   → YES: [Exit workflow]
   → NO:  [Action: Create task — "MQL not accepted after 3 days — review"]
```

### 4. {{ENRICHMENT_VENDOR}} Integration Points

For any step that involves {{ENRICHMENT_VENDOR}}, document:
- **Signal type**: Is this consuming a {{ENRICHMENT_VENDOR}} signal (i.e., {{ENRICHMENT_VENDOR}} fires → HubSpot updates) or producing one (HubSpot fires → {{ENRICHMENT_VENDOR}} acts)?
- **Signal name/category**: Marketing conversion signal / lifecycle signal / enrichment request
- **Expected behavior**: What does {{ENRICHMENT_VENDOR}} do with this signal? (e.g., trigger enrichment cascade, update cadence, initiate outreach sequence)
- **Fallback**: What happens if {{ENRICHMENT_VENDOR}} doesn't return enriched data? (Flag for manual review or use HubSpot default)

### 5. Property Dependencies

List every HubSpot property this workflow reads from or writes to:

| Property | Object | Read / Write | Notes |
|----------|--------|-------------|-------|
| Lifecycle Stage | Contact | R/W | Must be set before enrollment for some branches |
| AE Owner | Contact | R | Used in routing branch |
| MQL Date | Contact | W | Set on enrollment |

### 6. Exit Criteria

When does a record leave this workflow?
- Goal met (specific property set or action taken)
- Manual unenrollment
- Suppression list membership
- Timeout (after N days with no progression)

### 7. Testing Checklist

Before activating in production:
- [ ] Test with a sample contact in sandbox / test pipeline
- [ ] Verify all property writes are correct
- [ ] Confirm {{ENRICHMENT_VENDOR}} signal fires and returns expected result
- [ ] Confirm routing branch logic works for edge cases (missing enrichment)
- [ ] Get human sign-off before enabling on live contacts

### 8. Human Review Note

> ⚠️ This workflow spec is a draft. Do not activate in HubSpot production without review by Scott McKeighen. Any workflow touching lead routing, lifecycle transitions, or score thresholds requires explicit approval.

## Output

Save as `workflow-spec-{workflow-name}-{date}.md` in the user's outputs folder and present the file link. Display the Workflow Overview and Action Sequence inline in chat.
