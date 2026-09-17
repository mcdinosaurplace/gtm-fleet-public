---
name: performance-marketer:keyword-research
description: >
  Keyword discovery and intent mapping. Expands seed terms, classifies search
  intent (informational/navigational/commercial/transactional), assigns topical
  clusters, scores paid vs organic opportunity, and cross-maps to existing pages.
  Produces a keyword-URL map, gap list, and SEO brief framework for content
  creation.
---

# Keyword Research

## When This Runs

- **Standalone:** `/performance-marketer keyword-research`
- **Typical cadence:** Campaign planning, content strategy, quarterly refresh

## Inputs

- Seed keywords or topics (user-provided)
- Optional: Google Search Console query data (shows what we already rank for)
- Optional: `~~SEO` keyword data (search volume, difficulty, SERP features)
- Optional: competitor domains for keyword gap analysis
- Target market/geography (defaults to US if not specified)

## Workflow

### 1. Seed Expansion

From the provided seeds, expand the keyword universe:
- Modifiers: add common head/tail modifiers (how, what, best, vs, for, cost,
  pricing, reviews, alternatives, free, tool, software, platform)
- Questions: generate question-form variants (how to, what is, why do, can you)
- Long-tail: combine seeds with category-specific qualifiers relevant to {{COMPANY}}'s
  market (on-call, incident response, alert noise, MTTR, escalation policy, rotation,
  postmortem, SRE, terraform, for startups, for small teams)
- Related terms: semantically related concepts that searchers might use

### 2. Intent Classification

Reference `roster/performance-marketer/references/search-intent-taxonomy.md`.

Classify each keyword into one of four intent categories:

| Intent | Signal | Funnel Stage | Channel Fit |
|--------|--------|-------------|-------------|
| **Informational** | "how to," "what is," "guide," "examples" | Top of funnel | Organic (blog, guides) |
| **Navigational** | Brand name, product name, "[brand] login" | Mid funnel | Brand search (paid + organic) |
| **Commercial** | "best," "vs," "reviews," "comparison," "alternatives" | Mid funnel | Both (comparison pages + paid) |
| **Transactional** | "pricing," "demo," "buy," "sign up," "get started" | Bottom funnel | Paid (high-intent) + organic (product pages) |

### 3. Topical Clustering

Group keywords into topical clusters. Each cluster has:
- A **pillar keyword** (highest volume, broadest intent)
- **Cluster keywords** (more specific variants and long-tail)
- A **suggested pillar page** (if one exists, link it; if not, flag as gap)
- **Supporting content** needed (blog posts, comparison pages, FAQ content)

### 4. Opportunity Scoring

For each keyword (where data is available), calculate an opportunity score:

```
Opportunity = (Search Volume * Estimated CTR at target position) / Keyword Difficulty
```

Adjust for:
- Current ranking (if we already rank 1-10, upside is limited vs. not ranking)
- SERP features present (featured snippets, PAA, AI Overviews reduce organic CTR)
- Commercial value (transactional intent > informational for direct pipeline impact)

### 5. Paid vs. Organic Recommendation

For each keyword or cluster, recommend the primary channel:

| Scenario | Recommendation |
|----------|---------------|
| Transactional + high CPC + we rank top 3 organically | Organic preferred (save ad spend) |
| Transactional + we don't rank organically | Paid now + build organic over time |
| Commercial/comparison | Both: paid for immediate visibility + organic comparison page |
| Informational + high volume | Organic (blog/guide content) |
| Brand + competitor bidding | Paid (brand defense) + organic (owned) |

### 6. Content Gap Cross-Map

Map every keyword to an existing URL on the site. For each:
- **Covered:** keyword maps to an existing, relevant page → note the URL
- **Weak coverage:** page exists but doesn't target the keyword well → flag for
  optimization (title/heading/content updates)
- **Gap:** no existing page targets this keyword → flag for content creation

### 7. SEO Brief Generation

> **Deprecated in place.** Full content briefs are now owned by
> `content-producer:brief-builder`, which absorbs and extends this framework (persona + tone,
> AEO question set, verbatim evidence bundle from `topic_evidence`, internal links
> from `content_inventory`). This section stays as performance-marketer's reference for the
> SEO-brief skeleton; route brief requests to `/content-producer brief-builder`.

For top-priority gap keywords, generate a brief framework:

```markdown
### SEO Brief: {Target Keyword}

- **Primary keyword:** {keyword}
- **Secondary keywords:** {2-5 related terms to include}
- **Intent:** {informational/commercial/transactional}
- **Suggested URL slug:** /{slug}
- **Target word count:** {range based on competitor top-ranking pages}
- **Content type:** {blog post / comparison page / landing page / guide}
- **H1 suggestion:** {headline that includes primary keyword}
- **Key sections to cover:** {outline of H2s based on SERP analysis}
- **SERP features to target:** {featured snippet, PAA, etc.}
- **Competitors ranking:** {top 3 URLs ranking for this term}
- **Internal links from:** {existing pages that should link to this}
- **Internal links to:** {existing pages this should link to}
```

These briefs are starting points for the content team. Route to
`/draft-content` or {{CONTENT_LEAD_FIRST}} for full content development.

## Output Format

```markdown
## Keyword Research — {Topic/Seed} — {Date}

### Summary
- **Total keywords identified:** {N}
- **Clusters formed:** {N}
- **Content gaps found:** {N}
- **Top opportunities:** {3-5 highest-opportunity keywords}

### Keyword Universe

#### Cluster: {Cluster Name}
| Keyword | Volume | Difficulty | Intent | Current Rank | URL | Status |
|---------|--------|-----------|--------|-------------|-----|--------|
| {pillar} | {vol} | {diff} | {intent} | {rank or —} | {url or —} | {covered/weak/gap} |

### Content Gaps (Priority Order)
| Keyword | Volume | Intent | Recommended Content Type | Effort |
|---------|--------|--------|------------------------|--------|

### SEO Briefs
{Briefs for top 3-5 gap keywords}

### Paid vs. Organic Map
| Keyword | Recommended Channel | Rationale |
|---------|-------------------|-----------|

### Cannibalization Warnings
| Keyword | Competing URLs | Recommended Resolution |
|---------|---------------|----------------------|
```

## Reference Files

- `roster/performance-marketer/references/search-intent-taxonomy.md`
