# Performance Report -- Team SOP

**Version:** 1.0
**Owner:** Marketing / Demand Gen
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 -> `/performance-report`

---

## What This Is

The Performance Report skill builds a structured marketing performance report from data you provide. It produces an executive summary, channel-level metrics table, top/bottom performer analysis, trend commentary, and ranked optimization recommendations. Use it for period-end reviews, campaign debriefs, or any time you need a fast, structured read on what is working and what needs attention.

**Time to complete:** ~10-20 minutes (data export + report generation + review)

---

## Section 1: Prerequisites

Before running the skill, confirm the following:

1. **Claude Co-Work** is open with the **{{COMPANY}} Marketing Plugin v1.5.0** active. The `/performance-report` command is only available through this plugin.
2. You have performance data ready to paste or summarize. The skill analyzes what you provide -- it does not pull data automatically.
3. If you need funnel metrics (MQLs, SALs, SQLs, pipeline), run `/funnel-stats` first and have the output ready to include in your prompt.

Primary data sources by channel:

| Channel | Source |
|---------|--------|
| Funnel metrics (MQLs, SALs, SQLs, pipeline) | HubSpot via `/funnel-stats` |
| Google Ads (clicks, impressions, spend, conversions) | Google Ads export |
| LinkedIn Sponsored Content (clicks, impressions, spend, leads) | LinkedIn Campaign Manager export |
| Email (sends, opens, clicks, conversions) | HubSpot email report |
| Content / organic (sessions, organic traffic, conversions) | GA4 |
| Social (LinkedIn, X) (impressions, engagements, clicks) | Native platform analytics or GA4 |

---

## Section 2: What Data to Bring

The quality of the report scales with the specificity of the data you provide. A well-structured input includes:

- **Reporting period** (e.g., "this month MTD" or "this quarter")
- **Prior period for comparison** (e.g., "last month" or "last quarter") -- without this, the skill cannot produce WoW or MoM comparisons
- **Channel-level metrics** for each channel you want analyzed -- provide what you have; the skill will note what is missing
- **Funnel metrics** (MQLs by type, SALs, SQLs, pipeline value) -- run `/funnel-stats` if you need current MTD numbers
- **Context** that raw data cannot capture: campaigns that launched mid-period, landing page changes, budget shifts, seasonality, or external events

The skill will note when data gaps limit the analysis. It will not invent numbers.

### Example: well-structured data input

```
Reporting period: this month MTD (days 1-21)
Prior period: last month, full month

Funnel:
  MQLs: 47 (P1: 18, P2: 22, Outbound: 7) | Feb: 39
  SALs: 31 | Feb: 27 | CVR: 66%
  SQLs: 19 | Feb: 16 | CVR: 61%
  Pipeline: $1.8M | Feb: $1.5M

Google Ads:
  Spend: $12,400 | Feb: $11,800
  Clicks: 3,210 | Feb: 2,980
  Conversions: 28 | Feb: 23
  CPA: $443 | Feb: $513

LinkedIn Sponsored Content:
  Spend: $8,600 | Feb: $9,200
  Clicks: 1,840 | Feb: 1,710
  Leads: 14 | Feb: 11
  CPL: $614 | Feb: $836

Email (HubSpot):
  Sends: 4,200 | Feb: 3,800
  Open rate: 31% | Feb: 28%
  CTR: 4.2% | Feb: 3.7%
  Conversions: 9 | Feb: 7

Organic / Content:
  Blog sessions: 8,400 | Feb: 7,900
  Organic sessions: 14,200 | Feb: 13,600
  Conversions: 6 | Feb: 5

Context: Launched new Google Ads landing page March 10. LinkedIn budget reduced $600 to shift toward Google.
```

---

## Section 3: Reading the Report

The report output has six sections. Here is what each contains and how to use it.

**Executive summary**
One paragraph covering overall period performance. It will state whether results are up or down, which channels drove the movement, and the headline finding. Read this first to orient leadership or a stakeholder who will not read the full report.

**Channel performance table**
A structured table comparing current-period metrics to the prior period for each channel, including percent-change columns. The table reflects only the channels you provided data for. Missing channels are noted but not fabricated.

**Top performers and underperformers**
A ranked list of what is working (positive signals, efficiency gains, volume leaders) and what is not (declining metrics, efficiency drops, channels missing targets). This is based on the data provided -- if a channel is missing, it will not appear here.

**Trend analysis**
Commentary on directional movement: which metrics are accelerating or decelerating, and likely contributing factors given the context you provided. The skill will identify correlations (e.g., landing page change correlating with CPA drop) but will not assert causation unless the data makes it unambiguous. This section requires human review before presenting to stakeholders.

**Optimization recommendations**
Ranked by estimated impact. Each recommendation includes the channel, the specific action, and the rationale. These are starting points -- they do not account for constraints the skill does not know about (budget locks, creative cycles, team capacity). Add your constraints to the prompt to get more relevant recommendations (see Section 5).

**Next steps and focus areas**
Short list of concrete actions for the coming period. These are derived from the recommendations and are meant to feed directly into WBR planning or sprint tasking.

---

## Section 4: Using the Report

**In the WBR**
The executive summary and channel table map directly to the Summary and Paid Media sections of the WBR. If you ran `/wbr-prep`, paste the executive summary into the Summary section and the channel table into the relevant channel section. The next steps list can feed the Project Updates section.

**Campaign debrief**
Use the full report output as the working draft for a campaign debrief document. The top/bottom performer analysis and trend section are the most useful sections for this context. Add campaign-specific creative and audience notes manually before sharing.

**Board or leadership review prep**
Use the executive summary and recommendations sections. Strip the channel table for executive audiences who do not need row-level data. The trend analysis section may need editing to remove hedging language before presenting to non-technical stakeholders.

**Distribution options**
- Export to Notion: paste into a Notion page (follow `docs/notion-markdown-syntax.md` if formatting is needed)
- Slack: paste the executive summary and next steps into #marketing or a leadership channel
- Local: save in `localwork/` for working copies that do not need to be committed

---

## Section 5: Troubleshooting

| Problem | Fix |
|---------|-----|
| Report is too general or surface-level | Provide more specific data. If you gave summary-level numbers, add channel-level breakdowns. Include context about what changed during the period. |
| Prior period comparison is missing | The skill cannot generate WoW or MoM deltas without prior period numbers. Pull February (or prior quarter) actuals and include them in the prompt. |
| Recommendations do not match your actual priorities | Add a constraint statement to the prompt, e.g., "Our primary constraint this quarter is headcount -- recommendations requiring new creative production are not actionable." The skill will reprioritize accordingly. |
| Metrics in the report do not match your source data | The skill only analyzes what you give it. If numbers look off, verify what you pasted. Check for unit mismatches (e.g., providing leads vs. clicks in the wrong column). |
| A channel is missing from the output | Either the data was not included in the prompt or the skill could not parse it. Re-run with the channel data explicitly labeled by channel name. |
| Trend analysis contradicts what you know | The skill reasons from the data you provided. If it lacks context (e.g., a mid-period budget change), it will misread the trend. Add that context to the prompt and re-run. |

---

## Quick Reference

| Item | Value |
|------|-------|
| **Command** | `/performance-report` |
| **Plugin** | {{COMPANY}} Marketing Plugin v1.5.0 |
| **Environment** | Claude Co-Work (Path A) |
| **Required inputs** | Reporting period, channel metrics, prior period metrics |
| **Optional inputs** | Funnel metrics (run `/funnel-stats` first), contextual notes |
| **Output sections** | Executive summary, channel table, top/bottom performers, trend analysis, recommendations, next steps |
| **Primary data sources** | HubSpot (`/funnel-stats`), Google Ads export, LinkedIn Campaign Manager, GA4, HubSpot email reports |
| **Channels covered** | Google Ads, LinkedIn Sponsored Content, email (HubSpot), content/blog (organic), social (LinkedIn, X) |
| **Funnel metrics** | MQLs (P1/P2/Outbound), SALs, SQLs, pipeline |
| **Recommended cadence** | Monthly (period-end), or ad hoc for campaign debriefs and leadership prep |

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
