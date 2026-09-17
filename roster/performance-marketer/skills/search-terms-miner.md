---
name: performance-marketer:search-terms-miner
description: >
  Analyzes Google Ads search terms reports to harvest negative keywords, identify
  match-type promotion opportunities, and flag high-spend/low-intent waste. Uses
  n-gram frequency analysis to surface recurring query patterns. Produces
  actionable negative keyword lists and match-type change recommendations.
---

# Search Terms Miner

## When This Runs

- **Tick integration:** Weekly Tick (Fridays, after creative-optimizer)
- **Standalone:** `/performance-marketer search-terms-miner`

## Inputs

- Google Ads search terms report (CSV export or API data)
  - Required columns: Search term, Campaign, Ad group, Impressions, Clicks,
    CTR, Avg. CPC, Cost, Conversions, Conv. rate, Match type
  - Date range: 14-30 days recommended for pattern detection
- Optional: existing negative keyword lists (for dedup)

If no data is provided, ask the user for a search terms CSV. This skill
cannot run without search terms data.

## Workflow

### 1. Parse and Categorize

Load the search terms data. For each query, classify into:

- **Converters** — queries with >= 1 conversion
- **Engaged non-converters** — queries with clicks but no conversions
  (further split by spend: high-spend vs. low-spend)
- **Impressions only** — queries with impressions but no clicks
- **Brand terms** — queries containing the brand name or close variants

### 2. N-Gram Analysis

Break all search terms into unigrams, bigrams, and trigrams. For each n-gram,
calculate:
- Total impressions
- Total clicks
- Total spend
- Total conversions
- Weighted CTR and conversion rate

Surface the top n-grams by spend that have zero conversions — these are the
highest-value negative keyword candidates.

### 3. Negative Keyword Harvesting

Flag queries for negative keyword addition when:

| Condition | Confidence |
|-----------|-----------|
| >$50 spend, 0 conversions, 14+ days | High — recommend adding |
| >$25 spend, 0 conversions, 14+ days | Medium — recommend reviewing |
| Clearly off-intent (e.g., "free," "jobs," "salary," competitor + "reviews") | High — pattern-based |
| Query matches known negative patterns (see references/negative-keyword-patterns.md) | Medium — verify relevance |

For each recommended negative:
- State the query or n-gram
- Recommended match type for the negative (phrase vs. exact)
- Total waste (spend on zero-conversion queries containing this term)
- Which campaigns/ad groups would be affected

### 4. Match-Type Promotion

Identify queries currently matching via broad or phrase that should be
promoted to exact match:

| Condition | Recommendation |
|-----------|---------------|
| CTR >2x ad group average + conversions >0 | Promote to exact match |
| Consistent converter over 3+ weeks | Promote to exact + increase bid |
| High-volume query matched to wrong ad group | Consider new ad group or RLSA |

### 5. Waste Report

Calculate total wasted spend:
- Sum of spend on queries with 0 conversions and no strategic value
  (excluding brand defense, awareness campaigns, and new-term testing)
- Express as % of total search spend for the period
- Compare to prior period waste % if historical data exists

### 6. Output

Produce a structured report:

```markdown
## Search Terms Analysis — {date range}

### Waste Summary
- **Total search spend:** ${total}
- **Wasted spend (0-conv, off-intent):** ${waste} ({pct}%)
- **Prior period waste:** {comparison if available}

### Negative Keyword Recommendations

#### High Confidence (add these)
| Term | Match Type | Campaigns Affected | Waste Avoided |
|------|------------|-------------------|---------------|
| {term} | Phrase | {campaigns} | ${amount} |

#### Medium Confidence (review these)
| Term | Match Type | Campaigns Affected | Waste Avoided |
|------|------------|-------------------|---------------|

### Match-Type Promotions
| Query | Current Match | Recommendation | CTR | Conv Rate |
|-------|--------------|----------------|-----|-----------|

### Top Waste N-Grams
| N-Gram | Total Spend | Conversions | Action |
|--------|------------|-------------|--------|

### Notes
[Patterns observed, seasonal terms, queries worth investigating further]
```

## Reference Files

- `roster/performance-marketer/references/negative-keyword-patterns.md` — common negative
  categories by vertical (informational queries, job searches, competitor
  reviews, free/cheap modifiers, location mismatches)

## Caveats

- Do not recommend negating terms that appear in awareness campaigns unless
  the user confirms those campaigns are conversion-focused
- Do not negate brand terms or brand + modifier queries
- Flag ambiguous queries (could be buyer intent OR off-intent) for human review
  rather than auto-recommending negation
- Search terms data has a natural lag (24-48h) — note the data freshness
