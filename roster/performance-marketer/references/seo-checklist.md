# SEO Audit Checklist

Pass/fail checklist for the performance-marketer:seo-audit skill. Not every item applies to
every audit — use judgment on what's relevant for the site.

## Technical SEO

### Crawlability
- [ ] robots.txt exists and doesn't block critical paths
- [ ] XML sitemap exists and is submitted to GSC
- [ ] Sitemap includes all indexable pages
- [ ] Sitemap excludes noindex/canonicalized pages
- [ ] No redirect chains >2 hops
- [ ] No redirect loops
- [ ] 404 pages return proper 404 status (not soft 404s)
- [ ] Server responds with <500ms TTFB for key pages

### Indexability
- [ ] All priority pages are indexed in GSC
- [ ] "Discovered - not indexed" count is stable or declining
- [ ] Canonical tags are self-referencing on canonical pages
- [ ] No conflicting canonical signals (canonical vs. redirect vs. hreflang)
- [ ] No unintended noindex directives
- [ ] JavaScript-rendered content is accessible to crawlers

### HTTPS & Security
- [ ] Site fully on HTTPS (no mixed content)
- [ ] HTTP → HTTPS redirects in place
- [ ] HSTS header present
- [ ] SSL certificate valid and not expiring within 30 days

### Core Web Vitals
- [ ] LCP <2.5s on mobile for top 10 traffic pages
- [ ] INP <200ms on mobile
- [ ] CLS <0.1 on mobile
- [ ] No pages in "Poor" CWV bucket in GSC

## On-Page SEO

### Title Tags
- [ ] Every page has a unique title tag
- [ ] Titles are 50-60 characters
- [ ] Primary keyword appears in title
- [ ] Titles are compelling (not just keyword-stuffed)

### Meta Descriptions
- [ ] Every priority page has a meta description
- [ ] Descriptions are 150-160 characters
- [ ] Descriptions include a call to action
- [ ] Descriptions are unique per page

### Headings
- [ ] One H1 per page
- [ ] H1 includes primary keyword or close variant
- [ ] Heading hierarchy is logical (no H3 without H2)
- [ ] Headings describe content (not generic "Read more")

### Content
- [ ] No thin pages (<300 words on topics warranting depth)
- [ ] No duplicate content (>80% similarity between pages)
- [ ] No keyword cannibalization (multiple pages targeting same primary keyword)
- [ ] Key pages updated within last 12 months

### Internal Linking
- [ ] Priority pages have >= 5 internal links pointing to them
- [ ] No orphan pages (pages with zero internal links)
- [ ] All priority pages reachable within 3 clicks from homepage
- [ ] No broken internal links
- [ ] Anchor text is descriptive (not "click here")

### Schema Markup
- [ ] Organization schema on homepage
- [ ] Article/BlogPosting on blog content
- [ ] BreadcrumbList for navigation
- [ ] FAQ schema on FAQ pages (if applicable)
- [ ] Product schema on product pages (if applicable)
- [ ] Schema validates in Google Rich Results Test

## E-E-A-T Signals

- [ ] Author bios on blog/advice content
- [ ] About page with team, credentials, company info
- [ ] Contact information accessible
- [ ] Privacy policy and terms present
- [ ] External backlinks from authoritative sources
- [ ] Original data, research, or first-party insights published

## Off-Page (if data available)

- [ ] Referring domain count trending up or stable
- [ ] No toxic/spammy backlink pattern
- [ ] Anchor text distribution looks natural (majority branded/URL)
- [ ] No recent link penalties or manual actions in GSC
