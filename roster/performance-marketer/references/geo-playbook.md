# Generative Engine Optimization (GEO) Playbook

Reference document for optimizing brand presence in AI-powered search surfaces:
Google AI Overviews, ChatGPT, Perplexity, Claude, Gemini.

This is an emerging field. Treat recommendations as hypotheses to test, not
established best practices.

## Why GEO Matters

AI-powered search is changing how users find and evaluate products:
- Google AI Overviews appear for an increasing share of queries, reducing
  traditional organic clicks
- ChatGPT, Perplexity, and Claude are becoming research tools for B2B buyers
- Buyers may form opinions about your product from AI responses before ever
  visiting your site
- If your brand isn't mentioned (or is mentioned inaccurately), you've lost
  influence over the narrative

## Current State of AI Citation

### What Gets Cited

Based on observed patterns (subject to change as models evolve):

**Commonly cited content types:**
- Authoritative blog posts with clear, structured information
- Pages with FAQ sections (Q&A format is highly parseable)
- Comparison/review pages with structured data
- Official documentation and pricing pages
- Content with statistics, data points, and specific claims

**Rarely cited:**
- Gated content (AI can't read it)
- Heavy JavaScript-rendered pages
- Pages behind login walls
- Content with no clear structure (walls of text)

### How AI Overviews Select Sources

Google's AIO appears to favor:
1. Content that directly answers the query in the first 1-2 paragraphs
2. Pages that already rank well organically (positions 1-10)
3. Structured content (tables, lists, clear headers)
4. Pages with strong E-E-A-T signals
5. Content that provides specific, factual answers (not vague marketing copy)

## Optimization Levers

### 1. Structured Data / Schema

JSON-LD schema makes your content machine-readable. Priority types:

| Schema Type | Where to Use | Why It Helps |
|------------|-------------|-------------|
| Organization | Homepage | Establishes entity identity |
| Product | Product pages | Price, features, availability |
| FAQ | FAQ pages, blog posts with Q&A | Directly answers questions AI extracts |
| HowTo | Tutorial/guide content | Step-by-step structure AI can parse |
| Article | Blog posts | Authorship, publish date, topic |
| BreadcrumbList | All pages | Site structure signal |

### 2. llms.txt

A proposed standard (inspired by robots.txt) that provides AI systems with a
structured description of your site, product, and key information.

**What to include in llms.txt:**
- Company name and one-line description
- Product name(s) and what they do
- Key differentiators (what makes you different from competitors)
- Target audience
- Pricing model (if public)
- Links to key pages (product, pricing, documentation, about)

**Placement:** Root domain (e.g., {{COMPANY_DOMAIN}}/llms.txt)

**Status:** Not yet a formal standard. Adoption is early. Worth implementing
as a low-effort, high-optionality move.

### 3. Content Structure for AI Parsability

Structure content so AI can extract clean answers:

- **Lead with the answer.** First 40-60 words of any section should directly
  answer the likely query. Don't bury the lead under preamble.
- **Use definition format.** "An error budget is [definition]." "Ownership as
  code means [definition]." AI systems love pulling clean definitions, and the
  category terms {{COMPANY}} is trying to own are exactly the ones worth
  defining in this shape.
- **Include comparison tables.** "[Product] vs [Alternative]" tables are
  highly extractable.
- **Add FAQ sections.** Explicit Q&A format with schema markup.
- **Use specific numbers.** "Free for up to 5 responders" is more citable than
  "affordable for small teams," and "MTTA under two minutes across {{COMPANY}}
  customers" is more citable than "fast acknowledgement." Aggregate benchmarks
  must say "across {{COMPANY}} customers"; availability figures cite the SLA
  they came from.

### 4. Entity Establishment

AI systems build entity graphs. Strengthen your entity by:
- Consistent NAP (Name, Address, Phone) across web properties
- Wikipedia/Wikidata presence (if notable enough)
- Crunchbase, G2, Capterra profiles with accurate information
- Press coverage that mentions your brand in context of your category
- About page that clearly states what you do, for whom, and since when

### 5. Brand Mention Monitoring

Regularly query AI systems with:
- "[Your brand name]" — what do they say about you?
- "Best [your category]" — are you mentioned?
- "[Your brand] vs [competitor]" — is the comparison accurate?
- "[Your category] for [your audience]" — are you recommended?

Track accuracy, sentiment, and presence over time. If AI responses contain
inaccurate information, the fix is usually content-side: publish correct,
authoritative content that AI systems can learn from.

## Measurement

GEO doesn't have mature measurement frameworks yet. Track what you can:

- **AI Overview citations:** Is your domain cited in AIO results for tracked
  keywords? (Manual check or tool-assisted)
- **Brand presence in LLM responses:** Monthly spot-check across platforms
- **Organic CTR shifts:** If AIO is answering queries, organic CTR for those
  terms will decline even if rankings hold — track CTR independent of position
- **Direct traffic changes:** Some AIO/LLM users click through; others don't.
  Monitor whether direct/referral patterns shift as AI search grows

## Caveats

- This field is evolving rapidly. What works today may not work in 6 months.
- AI citation patterns vary by model, query type, and update cycle.
- There is no guaranteed way to "rank" in AI responses the way you can in
  traditional search.
- The best GEO strategy is also good SEO: authoritative, structured, accurate
  content that answers real questions.
