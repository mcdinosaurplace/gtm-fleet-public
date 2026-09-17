---
name: attribution-brief
description: Build an attribution analysis for {{COMPANY}} — by source, segment, and channel. Multi-touch breakdown, funnel performance by source, data quality flags, and recommendations.
allowed-tools: Read Write
disable-model-invocation: true
---

# /attribution-brief

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/funnel.md` before proceeding.

## What to Ask

Ask the user:
- What **time period** should the analysis cover?
- Is this **pre-built from data they'll provide**, or should it be a **framework/template** they'll fill in with `~~crm` / `~~BI` (Metabase) data?
- Any specific question they're trying to answer (e.g., which source is driving the most qualified pipeline? Why is MQL volume down?)

If they're providing data, ask them to paste or describe the key figures. If building a template, generate a complete blank attribution brief they can fill in.

## What to Produce

### 1. Executive Summary (3–5 sentences)
What the data shows at a glance. If working from a template, provide a placeholder with guidance on what to write.

### 2. Attribution Model in Use
State which model is being applied and why:
- First-touch: awareness effectiveness
- Last-touch: conversion triggers
- Multi-touch linear: full-funnel view
- Note the gap: no product usage data in CRM yet, so self-reported or web-assisted attribution may undercount PLG signals

### 3. Source Performance Table

| Source | Contacts Created | MQLs | SALs | SQLs | Pipeline Created | Notes |
|--------|-----------------|------|------|------|-----------------|-------|
| Organic Search | | | | | | |
| Paid Search | | | | | | |
| LinkedIn Organic | | | | | | |
| LinkedIn Paid | | | | | | |
| Referral / Partner | | | | | | |
| Direct | | | | | | |
| Email / Newsletter | | | | | | |
| Event | | | | | | |
| Other | | | | | | |

### 4. Funnel Conversion by Source

For each material source, show conversion rates through the funnel:
`MQL → SAL → SQL → Pipeline`

Flag where a source is strong at one stage but drops off at another (e.g., high MQL volume from paid but low SAL conversion = quality issue).

### 5. Multi-Touch vs. Last-Touch Delta

Where do first-touch and last-touch attribution diverge? Which channels are "influencers" that don't get last-touch credit? Surface any channels that look undervalued in last-touch.

### 6. Data Quality Flags

Call out any attribution gaps:
- Source = "Direct" or "Other" that's likely mis-attributed
- Contacts with no source set
- Campaigns without UTM parameters (ties to the `/utm-builder` command)
- {{ENRICHMENT_VENDOR}}-sourced conversions that may not be flowing into HubSpot correctly

### 7. Recommendations

3–5 specific, actionable recommendations. Frame as: **Observation → Implication → Action**.

Example format:
> **Organic search drives the most MQLs but lowest SAL conversion.** This suggests content is attracting broad top-of-funnel traffic that doesn't match the ICP. **Action**: Audit top organic landing pages for persona fit and tighten CTAs toward Erin / Hannah audiences.

## Output

Save as `attribution-brief-{period}-{date}.md` in the user's outputs folder and present the file link. Display the Executive Summary and Source Performance Table inline.
