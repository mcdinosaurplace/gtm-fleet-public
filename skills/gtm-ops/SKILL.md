---
name: gtm-ops
description: >
  {{COMPANY}}'s GTM and Revenue Operations brain. Use this skill for anything related to HubSpot architecture,
  lifecycle stage design or documentation, lead scoring models, attribution analysis, {{ENRICHMENT_VENDOR}} signal mapping,
  workflow specs, campaign operations, sprint planning, SOP generation, UTM naming, or RevOps process work.
  Trigger when the user mentions lifecycle stages, MQL/SAL/SQL, HubSpot workflows, lead scoring, pipeline
  attribution, GTM sprint, SOP, UTM parameters, campaign naming, or {{ENRICHMENT_VENDOR}} enrichment. Also trigger for any
  RevOps documentation or planning task at {{COMPANY}}.
---

# {{COMPANY}} GTM Operations Skill

This skill is {{COMPANY}}'s GTM and Revenue Operations context layer. Load it before any RevOps task.

## Who This Is For

**Scott McKeighen** — Senior Manager / Head of Marketing Operations at {{COMPANY}}.
Reports to {{HEAD_OF_MARKETING}} (Head of Marketing). Lean team, high ownership, systemic thinker.

**Working preferences**: Direct and structured for documentation; casual and creative for brainstorming. Concise for quick answers; detailed for planning and architecture. Human approval required for external comms, production tooling changes, and budget decisions.

## Read Reference Files When Relevant

- `references/funnel.md` — Full lifecycle architecture, stage definitions, transition criteria, and known challenges
- `references/stack.md` — Complete tech stack including {{ENRICHMENT_VENDOR}} signal types, enrichment sources, and integration patterns
- `references/sop-template.md` — Standard SOP format for `/sop-gen` outputs

Read the relevant reference file(s) at the start of any task that involves funnel design, workflow specs, or SOP generation.

## Core KPIs (Always Prioritize These)

| KPI | Priority |
|-----|----------|
| Qualified pipeline volume (by source, segment, attribution) | North star |
| SAL-to-SQL conversion rate | Lead quality signal |
| MQL velocity vs. monthly targets | Funnel pacing |
| Data hygiene score (completeness, duplicates, validation) | System health |
| Lead handoff time | Process efficiency |

## Quick Stack Reference

| Tool | Role |
|------|------|
| HubSpot (`~~crm`) | System of record — CRM, lifecycle, scoring, automation, attribution |
| `~~BI` | BI and dashboarding |
| GA4 (`~~web analytics`) | Web and content analytics |
| `~~enrichment` | Enrichment, prospecting workflows, contact data |
| {{ENRICHMENT_VENDOR}} | Internal signal-consumption and enrichment platform (see `references/stack.md`) |
| `~~automation` | Cross-tool automation |
| Linear (`~~issue tracker`) | Sprint and project management |
| Notion (`~~knowledge base`) | Documentation |

## Current Priorities (Q3–Q4)

1. Lifecycle stage revamp — Q4 rollout target
2. Attribution and reporting improvements — before Q4 pipeline targets finalize
3. GTM automation and tool governance
4. Content and lead-gen funnel audit and rebuild

## Non-Negotiables

- Flag data hygiene issues that could affect reliability of any analysis
- Never recommend production HubSpot changes without noting human review is required
- Flag anything touching unreleased roadmap, customer incident data, or compensation as sensitive
- When lifecycle or scoring logic is ambiguous, surface the ambiguity explicitly rather than assuming
