---
name: campaign-forecaster
description: Produce a lightweight, speculative campaign performance forecast for a {{COMPANY}} marketing campaign. Takes a campaign brief or key parameters and outputs channel-by-channel projections, lead funnel estimates (engaged → MQL → SAL → SQL → pipeline), ROI estimate, and confidence assessment benchmarked against industry norms.
allowed-tools: Read Write
disable-model-invocation: true
---

# /campaign-forecaster

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/funnel.md` before proceeding.

## Important Framing

This is a **speculative planning tool**, not a guarantee. Always state this clearly in the output. The value is directional — helping teams pressure-test campaign assumptions and set realistic expectations before committing budget.

## What to Ask

Ask the user to provide (or describe) a campaign brief with:

1. **Campaign goal**: Awareness / Lead gen / Event / Retention?
2. **Target audience**: Aaron (platform engineers at 50–500-engineer orgs), Erin (technical founders, pre-seed → Series A), or Hannah (VP Engineering, Series B–C)? Any combination?
3. **Channels in plan**: Which channels are being used? (LinkedIn paid, Google paid, email, content/SEO, event, partner, etc.)
4. **Campaign budget**: Total estimated spend (or per-channel if known)
5. **Campaign duration**: How many weeks/months?
6. **Key asset or offer**: What is the primary thing being promoted? (guide, demo, event, free trial)
7. **Historical context**: Any similar past campaigns they can reference? If not, use {{COMPANY}} funnel defaults + industry benchmarks.

If the user has a written campaign brief, ask them to paste it and extract the relevant inputs.

## What to Produce

### 1. Campaign Snapshot

```
Campaign:     {name or description}
Goal:         {Awareness / Lead gen / Event / etc.}
Audience:     {Aaron / Erin / Hannah / combination}
Duration:     {N weeks}
Total Budget: ${amount} (if provided)
Confidence:   Low / Medium / High (based on data quality)
```

### 2. Channel-by-Channel Projections

For each channel in the plan, produce estimated performance:

| Channel | Budget | Est. Reach / Impressions | Est. CTR | Est. Clicks | Est. Conversions | Est. CPL | Notes |
|---------|--------|--------------------------|----------|-------------|-----------------|---------|-------|
| LinkedIn Paid | $X | | | | | | Typically $80–$150 CPL B2B SaaS. Aaron is reached by Member Skills (Kubernetes, Terraform, SRE), not by title |
| Google Search | $X | | | | | | High-intent; category head terms run $8–$25 CPC, the on-call cluster $6–$15 |
| Email (existing list) | $0 | | | | | | Open rate 20–30% typical; CTR 2–5% |
| Content / Organic | $0 | | | | | | 30–90 day lag before traffic; long-tail |
| Event / Webinar | $X | | | | | | Registration → attendance ~40–50% |

Populate with estimates based on: provided budget, {{COMPANY}}'s known ICP, and B2B SaaS industry benchmarks. Flag each estimate as Low / Medium / High confidence based on whether there is historical data to support it.

### 3. Lead Funnel Projection

Build a funnel from campaign conversions through to potential pipeline:

| Stage | Volume | Conversion Rate | Notes |
|-------|--------|----------------|-------|
| Engaged leads (top-funnel) | | 100% baseline | Total campaign conversions |
| Marketing Qualified Leads (MQLs) | | ~10–20% of engaged | Based on {{COMPANY}}'s typical content-to-MQL rate |
| Sales Accepted Leads (SALs) | | ~40–60% of MQLs | Based on {{COMPANY}}'s SAL acceptance rate |
| Sales Qualified Leads (SQLs) | | ~30–50% of SALs | |
| Opportunities created | | ~70–85% of SQLs | |
| Estimated pipeline value | $X | ACV × opportunities | Use {{COMPANY}}'s known ACV or ask user to provide |

Apply {{COMPANY}}'s funnel conversion defaults from `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/funnel.md` unless the user provides actuals. Always show the assumed rates so they can be adjusted.

**Erin-led campaigns do not use this funnel.** A technical founder converts on a
free-tier signup in the same session, with no sales contact, so forecast the
self-serve path separately and do not double-count it into MQL volume:

| Stage | Volume | Conversion Rate | Notes |
|-------|--------|----------------|-------|
| Free-tier signups | | % of campaign conversions | The campaign's real conversion action |
| Activated workspaces | | % of signups | First routed page within 7 days |
| Crossed the 5-responder ceiling | | % of activated | The Detour path — enters at SAL, skipping MEL and MQL |
| Sales-assisted opportunities | | % of those crossing | Sales assistance starts around 75 responders |

Product telemetry does not reach the CRM yet, so treat every rate in this table
as an assumption and say so in Key Assumptions.

### 4. ROI Estimate

```
Total Campaign Cost:        ${budget + production costs}
Estimated Pipeline Created: ${pipeline value}
Pipeline-to-Spend Ratio:    {pipeline / cost}
Estimated Won Revenue:       ${pipeline × avg. win rate}
Estimated ROI:              {(won revenue - cost) / cost × 100}%
Payback Period:              ~{N months}
```

Flag if win rate is assumed vs. provided. Use 15–25% as the default win rate unless actuals are available.

### 5. Key Assumptions

List every assumption made in the forecast:
- ICP targeting match rate
- Channel conversion rates used and their source ({{COMPANY}} historical / industry benchmark / assumed)
- ACV used
- Win rate used
- Budget allocation across channels

### 6. Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LinkedIn audience too broad — high CPL, low quality | Medium | High | Narrow on Member Skills for Aaron and job title for Hannah; exclude adjacent "engineer" titles (Sales, Solutions, Support, Recruiter) |
| Low content engagement — weak MQL conversion | Medium | Medium | A/B test CTA; offer a higher-value lead magnet |
| Attribution gaps — pipeline undercounted | High | Medium | Ensure UTM parameters are in place for all channels |
| Budget insufficient for statistical significance | Low | High | Run for minimum 4 weeks before optimizing |

### 7. Benchmark Comparison

Compare projected performance against B2B SaaS industry benchmarks for the channels and campaign type:

| Metric | {{COMPANY}} Projection | Industry Benchmark | Delta |
|--------|-----------------|-------------------|-------|
| CPL (LinkedIn) | $X | $80–$150 | |
| Email CTR | X% | 2–5% | |
| MQL conversion from content | X% | 8–15% | |

## Output

Save as `campaign-forecast-{campaign-name}-{date}.md` in the user's outputs folder and present the file link. Display the Campaign Snapshot, Lead Funnel Projection, and ROI Estimate inline in chat.
