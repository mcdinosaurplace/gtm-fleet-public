---
name: performance-marketer:attribution-review
description: >
  Search-specific attribution analysis. Segments brand vs non-brand performance,
  tests paid/organic cannibalization, compares channel-level ROAS to incremental
  ROAS, and analyzes cross-channel conversion paths. Complements
  gtm-fleet:attribution-brief (which focuses on lifecycle/HubSpot attribution)
  with search-platform-specific depth.
---

# Attribution Review

## When This Runs

- **Standalone:** `/performance-marketer attribution-review`
- **Typical cadence:** Monthly, or when ROI claims look suspicious

## Inputs

- Google Ads conversion data (with brand/non-brand campaign segmentation)
- Google Analytics 4 data (channel groupings, conversion paths)
- Search Console data (organic CTR and traffic by query type)
- HubSpot source data (for lead-to-pipeline attribution)
- Optional: CRM closed-won data mapped back to marketing source

## Analysis Framework

### 1. Brand vs. Non-Brand Segmentation

This is the #1 blind spot in paid search reporting. Blended ROAS that mixes
brand and non-brand campaigns is almost always misleading because brand
campaigns convert at 5-10x the rate of non-brand.

**Required splits:**
- Brand campaigns (bidding on company name and variants)
- Non-brand campaigns (all other search campaigns)
- Competitor campaigns (conquesting — bidding on competitor names)

For each segment, calculate independently:
- Spend, conversions, CPA, ROAS
- Impression share, click share
- Conversion lag (time from click to conversion)

**Red flags:**
- If brand CPA is <$10 and non-brand CPA is >$100, a blended CPA of $40 is
  hiding a non-brand efficiency problem
- If brand campaigns account for >50% of reported conversions, the "search is
  our best channel" narrative needs qualification

### 2. Paid/Organic Cannibalization

Test whether paid search is genuinely incremental or cannibalizing organic:

**Signals of cannibalization:**
- Brand paid clicks go up → brand organic clicks go down by similar amount
- Pausing brand campaigns → organic traffic picks up most of the difference
- High impression share on terms where we rank #1 organically

**How to test:**
- Compare paid + organic total clicks for brand terms over time
- If available, review a historical pause test (period when brand ads were off)
- Calculate the "incremental click rate" = (total clicks with ads) / (organic
  clicks without ads) — values near 1.0 suggest heavy cannibalization

**When cannibalization is acceptable:**
- Competitors are actively bidding on your brand terms (brand defense)
- You need to control the messaging (new product launch, rebrand)
- Organic result is below fold due to SERP features

### 3. Channel-Level vs. Incremental ROAS

Three lenses on return:

| Metric | What It Measures | Risk of Misuse |
|--------|-----------------|---------------|
| **Channel ROAS** | Revenue / ad spend per channel | Over-credits last-touch channels; ignores assists |
| **Blended ROAS** | Total revenue / total ad spend | Hides underperformers behind brand performance |
| **Incremental ROAS** | Additional revenue attributable solely to the ad | Hardest to measure, closest to truth |

For each channel:
- Report all three where data allows
- Flag the gap between channel ROAS and estimated incremental ROAS
- Note which metric the team is currently using to make budget decisions

### 4. Multi-Touch Path Analysis

Using GA4 conversion paths (or HubSpot multi-touch reports):
- What are the most common paths to conversion?
- How often does paid search appear as first touch vs. last touch vs. assist?
- How does organic search participate in conversion paths?
- What's the average path length (number of touchpoints before conversion)?

**Common patterns to identify:**
- Paid search as introducer (first touch) → other channels close
- Organic search as researcher (mid-path) → paid search closes
- Direct/brand as closer (last touch) inflating brand attribution
- Social/content as silent assist (appears in path but never gets credit in
  last-touch models)

### 5. Attribution Model Comparison

Run the same conversion data through multiple models and compare:

| Model | Bias | Best For |
|-------|------|---------|
| Last-click | Over-credits closers | Quick-and-dirty reporting |
| First-click | Over-credits introducers | Understanding awareness channels |
| Linear | Dilutes across all touches | Fair-ish but unremarkable |
| Time-decay | Favors recent touches | B2B with long sales cycles |
| Position-based (U-shaped) | 40% first, 40% last, 20% middle | Balanced for most B2B |
| Data-driven (GA4) | Algorithmic, needs volume | Best if enough data |

Show how budget recommendations would differ under each model.

### 6. Data Quality Flags

Before presenting attribution findings, check:
- UTM coverage: what % of traffic has proper UTM tagging?
- Consent/cookie impact: what % of conversions may be unattributed due to
  cookie decline?
- CRM match rate: what % of marketing-sourced leads have source data in HubSpot?
- Cross-device tracking: are GA4 User-ID or Google Signals enabled?

Flag any data quality issue that could materially affect attribution conclusions.

## Output Format

```markdown
## Attribution Review — {Period} — {Date}

### Key Finding
{1-2 sentences: the most important attribution insight from this analysis}

### Brand vs. Non-Brand Split
| Segment | Spend | Conversions | CPA | ROAS | Share of Total |
|---------|-------|------------|-----|------|---------------|

### Cannibalization Assessment
- **Risk level:** {Low / Medium / High}
- **Evidence:** {specific data points}
- **Recommendation:** {continue brand bidding / test pause / reduce bids}

### ROAS Comparison
| Channel | Channel ROAS | Blended ROAS | Est. Incremental ROAS |
|---------|-------------|-------------|----------------------|

### Conversion Path Analysis
- **Average path length:** {N} touchpoints
- **Most common paths:** {top 3}
- **Paid search role:** {primarily introducer / closer / assist}

### Model Comparison
| Channel | Last-Click | First-Click | Position-Based | Data-Driven |
|---------|-----------|------------|---------------|-------------|

### Data Quality
| Check | Status | Impact on Findings |
|-------|--------|-------------------|

### Recommendations
1. {What to change in attribution approach}
2. {Budget implication}
3. {Tracking improvement needed}
```

## Relationship to gtm-fleet:attribution-brief

- **performance-marketer owns:** Search-specific attribution (brand/non-brand, paid/organic
  cannibalization, search path analysis)
- **GTM-ops owns:** Lifecycle attribution (MQL → SQL → Won), HubSpot source
  tracking, multi-channel marketing mix
- **Overlap zone:** Both care about "which channels actually drive pipeline."
  performance-marketer provides the search-depth view; GTM-ops provides the full-funnel view.
  Neither should contradict the other — if they disagree, flag it as a data
  quality issue to investigate.
