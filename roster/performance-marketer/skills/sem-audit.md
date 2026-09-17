---
name: performance-marketer:sem-audit
description: >
  Full paid search account health check. Reviews campaign structure, budget
  allocation, match type hygiene, Quality Score diagnostics, auction insights,
  bidding strategy evaluation, ad extensions completeness, and PMax asset group
  coverage. Produces a prioritized findings report with specific fix recommendations.
  Run quarterly or when account performance deteriorates.
---

# SEM Audit

## When This Runs

- **Standalone:** `/performance-marketer sem-audit`
- **Typical cadence:** Quarterly, or triggered by persistent performance decline

## Inputs

- Google Ads account data (via MCP, API, or CSV exports):
  - Campaign report (spend, conversions, CPA, ROAS, impression share)
  - Ad group report (keywords, match types, QS, ads)
  - Search terms report (for match type hygiene)
  - Auction insights (for competitive position)
  - Ad extensions report
- LinkedIn Campaign Manager data (optional, for cross-channel context)
- Account goals: target CPA, target ROAS, budget constraints

## Audit Framework

### 1. Account Structure

- **Campaign organization:** Are campaigns logically grouped by theme, intent
  tier, or audience? Flag overlapping targeting.
- **Ad group granularity:** Are ad groups thematically tight (5-20 keywords)
  or bloated catch-alls?
- **Naming conventions:** Do campaign/ad group names follow a parseable pattern?
  Flag inconsistencies.
- **PMax assessment:** If Performance Max campaigns exist, evaluate asset group
  coverage, signal inputs, and cannibalization with standard search campaigns.

### 2. Budget Allocation

- **Spend distribution:** What % of total spend goes to each campaign? Does
  allocation match strategic priority?
- **Budget-capped winners:** Identify campaigns with strong CPA/ROAS that are
  losing impression share to budget. These are the #1 reallocation opportunity.
- **Overspend on underperformers:** Flag campaigns spending >15% of total budget
  with CPA >2x the account average.
- **Day-of-week patterns:** Does performance vary significantly by day? Are
  budgets adjusted accordingly?

### 3. Match Type Hygiene

- **Match type distribution:** What % of keywords are exact, phrase, broad?
  Flag accounts that are >80% broad with no negative keyword lists.
- **Negative keyword coverage:** Are negative lists in place? When were they
  last updated? Cross-reference with search-terms-miner output.
- **Close variant bleed:** Check if exact match keywords are triggering for
  unintended close variants.

### 4. Quality Score Diagnostics

For each ad group, decompose Quality Score into its three components:

| Component | What It Measures | Fix If Below Average |
|-----------|-----------------|---------------------|
| Expected CTR | Historical CTR vs. competitors | Improve ad relevance, test new headlines |
| Ad Relevance | Keyword-to-ad copy alignment | Tighten ad group themes, add keyword in headlines |
| LP Experience | Landing page quality signals | Page speed, mobile UX, content relevance |

Flag any ad group where QS < 5. Prioritize high-spend, low-QS ad groups
as these are paying a premium for poor relevance.

### 5. Bidding Strategy Evaluation

Reference `roster/performance-marketer/references/dmo/bid-strategy.md`.

- **Strategy fit:** Is the current bid strategy appropriate for the campaign's
  goal and conversion volume?
- **Conversion thresholds:** Does the campaign have enough conversions for Smart
  Bidding? (Google recommends 30+ conversions in 30 days for tCPA/tROAS)
- **Target aggressiveness:** Are tCPA/tROAS targets set realistically relative
  to historical performance? Overly aggressive targets throttle delivery.
- **Manual holdouts:** Are any campaigns still on Manual CPC that should be
  transitioned?

### 6. Auction Insights

- **Impression share:** Total IS, top IS, abs top IS by campaign
- **Lost IS (budget):** Where are budget constraints costing visibility?
- **Lost IS (rank):** Where are quality/bid issues losing impressions?
- **Competitive overlap:** Which competitors appear most? Rising or falling?
- **Brand defense:** Is brand IS >90%? If not, who's bidding on your terms?

### 7. Ad Extensions

Check completeness across:
- Sitelinks (min 4 per campaign)
- Callouts (min 4)
- Structured snippets (min 1 relevant header)
- Call extensions (if applicable)
- Location extensions (if applicable)
- Price extensions (if applicable)
- Lead form extensions (if using lead gen)

Flag campaigns missing high-impact extensions.

### 8. Conversion Tracking

- **Conversion actions:** Are the right actions being tracked? Are there
  duplicate or redundant conversion actions?
- **Attribution window:** Is the conversion window appropriate (default 30-day
  click, 1-day view)?
- **Enhanced conversions:** Enabled? If not, flag as a priority improvement.
- **Offline conversion import:** If lead gen, is CRM data being fed back to
  Google Ads for smarter bidding?

## Output Format

```markdown
## SEM Audit — {Account Name} — {Date}

### Executive Summary
{3-5 sentences: overall account health, top 3 findings, estimated impact}

### Findings

#### Critical (fix immediately)
1. {Finding} — {Impact} — {Recommended action}

#### Important (fix this quarter)
1. {Finding} — {Impact} — {Recommended action}

#### Improvement (when bandwidth allows)
1. {Finding} — {Impact} — {Recommended action}

### Structure Review
{Campaign/ad group structure assessment}

### Budget Allocation
| Campaign | Monthly Spend | % of Total | CPA | IS Lost (Budget) | Recommendation |
|----------|-------------|-----------|-----|-----------------|----------------|

### Quality Score Heatmap
| Ad Group | QS | Exp CTR | Ad Rel | LP Exp | Priority |
|----------|-----|---------|--------|--------|----------|

### Bid Strategy Assessment
| Campaign | Current Strategy | Conversions/30d | Recommendation |
|----------|----------------|----------------|----------------|

### Competitive Position
| Metric | You | Top Competitor | Gap |
|--------|-----|---------------|-----|

### Extensions Audit
| Campaign | Sitelinks | Callouts | Snippets | Other | Status |
|----------|-----------|----------|----------|-------|--------|

### Next Steps
{Prioritized action list with estimated effort: Quick / Medium / Involved}
```
