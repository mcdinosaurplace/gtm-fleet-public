# Competitor Intelligence Methodology

Reference document for the performance-marketer:competitor-scan skill. Covers how to
interpret data from common competitive intelligence tools, their limitations,
and triangulation rules.

## Tool-Specific Guidance

Third-party competitive tools are referenced here by the `~~SEO` connector
category (Ahrefs and Similarweb are the defaults this kit is built against) and
grouped by what class of estimate they produce. The limitations below are
properties of the *method*, not of any one vendor — swap the product and the
triangulation rules still hold.

### Google Ads Auction Insights (Primary — First-Party Data)

**What it is:** Google's own report showing who appears alongside you in
auctions. This is the most reliable competitive signal for paid search.

**Key metrics:**
- **Impression share:** % of auctions where your ad appeared
- **Overlap rate:** % of auctions where both you and the competitor appeared
- **Position above rate:** % of shared auctions where competitor was above you
- **Top of page rate:** % of their impressions at the top of the page
- **Abs. top of page rate:** % at the very top position
- **Outranking share:** % of auctions where you ranked higher OR appeared when
  they didn't

**Limitations:**
- Only shows data for auctions you participated in (not total market)
- Doesn't show competitor spend, bids, or keywords
- Data is aggregated — can't see specific query-level competition
- Competitors may appear under different display names

**Interpretation rules:**
- Rising overlap rate + rising position above rate = competitor is investing
  more aggressively
- Declining overlap rate = competitor may be cutting budget or narrowing targeting
- High outranking share + low impression share = you win when you show up, but
  you're not showing up enough (budget or bid issue)

### `~~SEO` — Keyword and Traffic Estimation Suites

**What it provides:**
- Estimated organic and paid keyword counts
- Traffic estimates (derived from rank + estimated CTR + search volume)
- Keyword overlap analysis (shared vs. unique keywords)
- Backlink profile
- Ad copy history

**Limitations:**
- Traffic estimates can be off by 30-70% — directional only
- Keyword data is sampled, not exhaustive
- Ad copy is scraped intermittently; may not reflect current live ads
- Organic position data can lag real-time GSC data by days/weeks

**When to trust:** Trends over time (is traffic going up or down), keyword
overlap (which terms they target that we don't), backlink quality signals.

**When to distrust:** Absolute traffic numbers, exact keyword positions,
estimated ad spend.

### `~~SEO` — Backlink and Content-Gap Indexes

**What it provides:**
- Backlink analysis (the strongest third-party signal available)
- Organic keyword rankings (from the vendor's own crawler)
- Content gap analysis
- A domain-authority score as a link-strength proxy

**Limitations:**
- The same traffic-estimation issues as the keyword suites above
- Crawler frequency varies — some pages updated monthly, others quarterly
- The authority score is a vendor metric, not a Google signal
- No paid search data

**When to trust:** Backlink data, content gap analysis, referring domain trends.

**When to distrust:** Absolute traffic estimates, exact rankings for volatile
SERPs — and the reliability SERPs are volatile, because the definition cluster
("what is MTTR," "error budget") reshuffles every core update.

### `~~SEO` — Paid-Search History Archives

**What it provides:**
- Historical paid search data (ad copy, keywords, estimated spend)
- Competitor PPC overlap
- Shared vs. unique keywords (paid)

**Limitations:**
- Spend estimates are very approximate
- Historical data may be stale
- Less reliable for smaller advertisers

**When to trust:** Directional competitor keyword strategy, ad copy patterns
over time, which competitors are consistently investing in paid search.

### `~~SEO` — Panel-Based Traffic and Channel Mix

**What it provides:**
- Total website traffic estimates (all channels)
- Traffic source breakdown (organic, paid, direct, referral, social)
- Geographic distribution
- Top referring sites

**Limitations:**
- Traffic estimates based on panel data — accuracy varies by site size
- Small sites (<50K monthly visits) have very unreliable data
- Channel breakdown is estimated, not measured
- Free tier data is limited

**When to trust:** Large competitor traffic trends, channel mix directionally,
top referral sources.

## Triangulation Rules

Never rely on a single tool for competitive conclusions. Rules:

1. **Use Google Ads Auction Insights as ground truth for paid competition.**
   It's first-party data from the actual ad platform.

2. **Triangulate organic data across GSC + two `~~SEO` sources.** If both
   third-party tools agree on a trend, it's likely real. If they disagree, trust
   GSC for your own site and treat third-party data as directional.

3. **Treat all traffic estimates as +/- 50%.** Never quote a competitor's traffic
   as fact. Use ranges: "`~~SEO` estimates ~50-100K monthly visits for
   {{COMPETITOR_A_DOMAIN}}."

4. **Look at trends, not snapshots.** A single data point is noise. Three months
   of directional movement is signal.

5. **Cross-reference ad copy claims with live SERPs.** Tool data may be stale.
   Before reporting that a competitor is running specific copy, verify by
   searching the target queries.

6. **Flag confidence levels.** When reporting findings:
   - **High confidence:** Based on first-party data (Auction Insights, GSC)
   - **Medium confidence:** Confirmed by 2+ third-party tools, directionally
   - **Low confidence:** Single third-party source, no corroboration
