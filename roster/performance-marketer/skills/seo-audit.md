---
name: performance-marketer:seo-audit
description: >
  Technical + on-page + content SEO audit. Evaluates crawlability, indexability,
  Core Web Vitals, schema markup, internal linking, content gaps, keyword
  cannibalization, and E-E-A-T signals. Replaces gtm-fleet:seo-audit with
  deeper specialist treatment. Produces prioritized findings with fix instructions.
  Run monthly or when organic traffic declines.
---

# SEO Audit

## When This Runs

- **Standalone:** `/performance-marketer seo-audit`
- **Typical cadence:** Monthly, or triggered by organic traffic decline or
  algorithm update signal

## Inputs

- Google Search Console data (performance report: queries, pages, CTR,
  impressions, position)
- Site crawl data (Screaming Frog, Sitebulb, or similar — optional but
  high-value)
- Core Web Vitals data (PageSpeed Insights, CrUX, or Search Console CWV report)
- Current XML sitemap URL
- robots.txt URL
- Optional: `~~SEO` site-audit data, competitor domain for comparison

If some inputs are unavailable, run the audit on what's provided and note
gaps in the findings.

## Audit Framework

### 1. Technical SEO

**Crawlability:**
- robots.txt review: any critical paths blocked?
- XML sitemap: exists, submitted to GSC, includes priority pages, excludes
  noindex pages?
- Crawl errors in GSC: 404s, 5xx, redirect errors
- Redirect chains: any >2 hops?
- Orphan pages: pages not linked from any other page on the site

**Indexability:**
- Index coverage in GSC: indexed vs. excluded pages
- "Discovered - currently not indexed" and "Crawled - currently not indexed"
  counts and trends
- Canonical tag audit: self-referencing canonicals, cross-domain canonicals,
  conflicting signals
- Meta robots directives: any unintended noindex/nofollow?
- JavaScript rendering: do critical pages require JS to display content?

**Site speed / Core Web Vitals:**
- LCP (Largest Contentful Paint): target <2.5s
- INP (Interaction to Next Paint): target <200ms
- CLS (Cumulative Layout Shift): target <0.1
- Per-page analysis for top traffic pages
- Mobile vs. desktop performance gap

**HTTPS and security:**
- Full HTTPS enforcement (no mixed content)
- HSTS headers present
- Certificate validity

### 2. On-Page SEO

**Title tags:**
- Unique across all pages?
- Within 50-60 character range?
- Include primary keyword?
- Compelling for CTR?

**Meta descriptions:**
- Present on all key pages?
- Within 150-160 character range?
- Unique and action-oriented?

**Heading hierarchy:**
- Single H1 per page?
- Logical H2-H6 nesting?
- Keywords in H1/H2 where natural?

**Internal linking:**
- Do top-priority pages have sufficient internal links pointing to them?
- Anchor text variety and relevance
- Link depth: can any priority page not be reached within 3 clicks from homepage?
- Broken internal links

**Schema markup (JSON-LD):**

Reference `roster/performance-marketer/references/schema-catalog.md`.

- Organization schema on homepage
- Article/BlogPosting on blog content
- FAQ schema on FAQ pages
- BreadcrumbList for navigation
- Product schema (if applicable)
- HowTo schema (if applicable)
- Validate implementation via Google Rich Results Test

### 3. Content SEO

**Keyword coverage:**
- Map priority keywords to existing pages (keyword-URL map)
- Identify gaps: keywords with search volume but no targeting page
- Identify cannibalization: multiple pages competing for the same keyword

**Content quality signals:**
- Thin content: pages with <300 words on topics that warrant depth
- Duplicate content: near-duplicate pages (use site crawl similarity scores)
- Content freshness: high-traffic pages not updated in >12 months
- Topical clusters: are related pages linked as a hub-and-spoke structure?

**E-E-A-T inventory:**
- Author bios present on blog/advice content?
- About page with credentials, team, trust signals?
- Contact information accessible?
- External citations/backlinks from authoritative sources?
- Original research, data, or first-party insights?

### 4. Off-Page Signals (if data available)

- Backlink profile: total referring domains, quality distribution
- Anchor text: branded vs. keyword vs. generic ratio
- Toxic/spammy links: any that warrant disavow?
- Competitor backlink gap: domains linking to competitors but not to us

### 5. SERP Feature Opportunities

- Featured snippets: are we winning any? Which competitors hold them for
  our target terms?
- People Also Ask: which questions appear for our keywords?
- Video carousels: opportunity for video content?
- AI Overviews: are our pages cited in AI-generated answers?

Reference `roster/performance-marketer/references/seo-checklist.md` for the full item list.

## Output Format

```markdown
## SEO Audit — {Domain} — {Date}

### Executive Summary
{3-5 sentences: overall SEO health, top findings, estimated organic traffic impact}

### Health Score
| Category | Score | Status |
|----------|-------|--------|
| Technical | {A/B/C/D/F} | {key issue or "healthy"} |
| On-Page | {A/B/C/D/F} | {key issue or "healthy"} |
| Content | {A/B/C/D/F} | {key issue or "healthy"} |
| E-E-A-T | {A/B/C/D/F} | {key issue or "healthy"} |

### Critical Findings (fix immediately)
1. {Finding} — {Pages affected} — {Fix instruction}

### Important Findings (fix this month)
1. {Finding} — {Pages affected} — {Fix instruction}

### Opportunities (growth potential)
1. {Opportunity} — {Estimated impact} — {Implementation}

### Technical Audit Detail
{Crawlability, indexability, CWV findings with specific URLs}

### On-Page Audit Detail
{Title/meta/heading/schema findings per priority page}

### Content Gap Analysis
| Target Keyword | Search Volume | Current Coverage | Recommendation |
|---------------|--------------|-----------------|----------------|

### Cannibalization Report
| Keyword | Competing URLs | Recommended Winner | Action |
|---------|---------------|-------------------|--------|

### SERP Feature Opportunities
| Keyword | Feature Type | Current Holder | Opportunity |
|---------|-------------|---------------|-------------|

### Next Steps
{Prioritized action list: Quick wins / This month / This quarter}
```
