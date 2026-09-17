---
name: performance-marketer:competitor-scan
description: >
  Paid + organic competitive intelligence. Detects brand bidding, monitors
  competitor ad copy and landing pages, analyzes impression share and organic
  share of search, tracks SERP landscape changes. Produces a competitive
  position report with response recommendations.
---

# Competitor Scan

## When This Runs

- **Standalone:** `/performance-marketer competitor-scan`
- **Typical cadence:** Weekly (can also be triggered by ranking-watch flagging
  a new competitor or auction insights showing overlap increase)

## Inputs

- Google Ads auction insights data (via MCP, API, or CSV)
- Search terms report (for brand bidding detection)
- SERP data for tracked keywords (organic rankings of competitors)
- Optional: `~~SEO` competitor data (keyword, traffic, and paid-search history estimates)
- Optional: competitor landing page URLs for comparison

Reference `roster/performance-marketer/references/competitor-methodology.md` for tool-specific
interpretation guidance.

## Analysis Framework

### 1. Brand Bidding Detection

Scan the search terms report for:
- Queries containing competitor brand names that trigger our ads (we're bidding
  on them — expected for conquesting campaigns)
- Queries containing OUR brand name where competitor ads appear (they're bidding
  on us — this requires a response)

For brand defense:
- Check brand campaign impression share. If <90%, competitors are winning
  branded auctions.
- Identify which competitors appear on our brand terms (via auction insights)
- Recommend response: bid increases on brand terms, brand extensions refresh,
  or accept the loss if CPC is uneconomical

### 2. Paid Competitive Position

From auction insights, for each major competitor:

| Metric | What It Tells You |
|--------|------------------|
| Impression share | Their visibility vs. ours |
| Overlap rate | How often they appear alongside us |
| Position above rate | How often they outrank us |
| Top of page rate | Their prominence in results |
| Outranking share | Net competitive position |

Track these week-over-week. Flag:
- New competitors appearing (overlap rate was 0%, now >10%)
- Competitors gaining aggressively (outranking share up >15% WoW)
- Competitors disappearing (may indicate budget cuts or strategy shifts)

### 3. Competitor Ad Copy Analysis

For key competitors, analyze their active ads:
- What headlines are they running?
- What CTAs do they use?
- What value propositions do they lead with?
- Are they using price/discount language?
- Are they targeting our brand terms with specific conquesting copy?

Note patterns but do NOT copy competitor messaging. Use insights to
differentiate, not imitate.

### 4. Organic Share of Search

For tracked keywords, map the SERP landscape:
- Which competitors rank for which terms?
- Where do we rank vs. top 3 competitors?
- Which keywords have we lost position on where a specific competitor gained?
- Which keywords do competitors own that we have no presence on?

Calculate approximate "share of voice" if keyword volume data is available:
sum of (search volume * estimated CTR for position) across tracked terms.

### 5. SERP Landscape Changes

Detect structural changes:
- New domains entering the top 10 for tracked terms
- Domains dropping out of the top 10
- SERP feature changes (new featured snippets, PAA boxes, AI Overviews)
- New ad positions or ad format changes

### 6. Competitor Landing Page Assessment

If competitor landing page URLs are available:
- What's their headline/hero messaging?
- What social proof do they use?
- What's their primary CTA?
- Page speed / mobile experience (quick check only)

This is observation for positioning intelligence, not a full CRO audit.

## Output Format

```markdown
## Competitive Scan — {Date}

### Brand Defense Status
- **Brand IS:** {pct}% ({up/down from prior period})
- **Competitors on brand terms:** {list}
- **Action needed:** {Yes/No — if yes, specific recommendation}

### Paid Competitive Position
| Competitor | Overlap Rate | Outranking Share | Trend | Alert |
|-----------|-------------|-----------------|-------|-------|

### Key Movements
- {Competitor A}: {what changed and significance}
- {Competitor B}: {what changed and significance}

### Organic Share of Search
| Keyword | Our Position | Competitor A | Competitor B | Competitor C |
|---------|-------------|-------------|-------------|-------------|

### SERP Landscape Changes
- {New entrants, lost positions, feature changes}

### Ad Copy Intelligence
| Competitor | Sample Headline | Value Prop | Differentiator vs. Us |
|-----------|----------------|-----------|----------------------|

### Recommendations
1. {Priority response — what, why, expected impact}
2. ...

### Watch List
{Competitors or terms to monitor more closely next period}
```

## Brand Rules

- When reporting competitor findings, name competitors factually (this is
  competitive intelligence, not marketing copy)
- Do NOT generate ad copy that mentions competitor names unless the user
  explicitly requests conquesting creative
- Frame recommendations as positioning responses, not attacks
