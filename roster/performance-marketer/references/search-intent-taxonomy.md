# Search Intent Taxonomy

Reference document for classifying keyword intent. Used by keyword-research,
seo-audit, and serp-analysis skills.

## Four Intent Categories

### Informational
The searcher wants to learn something. They're not ready to buy.

**Signals:** "how to," "what is," "why," "guide," "tutorial," "examples,"
"tips," "definition," "explained"

**Content fit:** Blog posts, guides, how-to articles, educational video
**Funnel stage:** Top of funnel (awareness)
**Channel:** Organic (rarely worth paid spend unless audience retargeting)

**Examples for {{COMPANY}}'s market:**
- "what is an error budget"
- "how to reduce alert noise"
- "blameless postmortem guide"
- "MTTA vs MTTR"

### Navigational
The searcher is looking for a specific brand, product, or page.

**Signals:** Brand name, product name, "[brand] login," "[brand] pricing,"
"[brand] vs [brand]"

**Content fit:** Homepage, product pages, branded landing pages
**Funnel stage:** Mid-funnel (consideration)
**Channel:** Brand paid (defense) + organic (owned ranking)

**Examples:**
- "{{COMPANY_DOMAIN}}"
- "{{company_slug}} incident management"
- "{{company_slug}} login"
- "{{company_slug}} status page"

**Caution for {{COMPANY}}:** the bare brand term is ambiguous with the
astronomical instrument, so it behaves like an informational query and is
excluded from the tracked set. Qualified brand terms are the real navigational
cluster — always pair the brand with a category or product modifier.

### Commercial Investigation
The searcher is comparing options before a purchase decision.

**Signals:** "best," "top," "vs," "comparison," "reviews," "alternatives,"
"[product] review," "[category] software"

**Content fit:** Comparison pages, "best X" listicles, review pages,
alternative pages
**Funnel stage:** Mid-funnel (evaluation)
**Channel:** Both — paid for immediate visibility, organic for long-term

**Examples:**
- "best on-call scheduling software"
- "best incident management tools"
- "{{COMPETITOR_A_LOWER}} vs {{company_slug}}"
- "{{COMPETITOR_B_LOWER}} alternative"
- "incident response tools comparison"

### Transactional
The searcher is ready to take action — buy, sign up, request a demo.

**Signals:** "pricing," "demo," "buy," "sign up," "get started," "free trial,"
"request quote," "schedule call," "[product] for [stack or team shape]"

**Content fit:** Product pages, pricing pages, demo request pages
**Funnel stage:** Bottom of funnel (decision)
**Channel:** Paid (high-intent, worth the CPC) + organic (product pages)

**Examples:**
- "{{company_slug}} pricing"
- "incident management platform pricing per user"
- "on call software free trial"
- "terraform on call rotation"

**Note on the technical long tail:** provider- and API-shaped queries
("terraform on call rotation," "incident management API") read informational but
convert like transactional ones, because Aaron evaluates by reading the provider
docs before he books anything. Classify them transactional and route them to the
docs, not the blog.

## Intent Ambiguity

Some queries are ambiguous. Classification rules:

1. If the SERP shows mostly informational results (blog posts, guides) → classify
   as informational even if the query could be transactional
2. If the SERP shows mostly product pages and ads → classify as transactional
3. If mixed → classify as commercial investigation
4. When in doubt, check the SERP — Google's ranking choices reveal the dominant
   intent

## Intent-to-Action Map

| Intent | Primary SEO Action | Primary Paid Action |
|--------|-------------------|-------------------|
| Informational | Create/optimize blog content | Skip (or use for remarketing audiences) |
| Navigational | Ensure brand pages rank #1 | Brand defense campaigns |
| Commercial | Create comparison/alternative pages | Bid on comparison terms |
| Transactional | Optimize product/pricing pages | High-bid, high-intent campaigns |
