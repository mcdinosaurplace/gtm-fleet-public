---
name: performance-marketer:serp-analysis
description: >
  SERP feature and generative search monitoring. Tracks featured snippets, PAA,
  video carousels, and knowledge panels. Monitors AI Overview citations across
  Google SGE/AIO, ChatGPT, Perplexity, and Claude. Evaluates brand presence in
  LLM-powered search and assesses llms.txt, structured data, and content as
  AI-consumable signals. This is the Generative Engine Optimization (GEO)
  capability.
---

# SERP Analysis

## When This Runs

- **Standalone:** `/performance-marketer serp-analysis`
- **Typical cadence:** Weekly monitoring + deeper monthly GEO assessment

## Inputs

- Google Search Console data (queries, positions, CTR, impressions)
- SERP feature data (from `~~SEO` or manual SERP inspection)
- Optional: AI Overview/SGE observation data
- Optional: Brand mention checks in ChatGPT, Perplexity, Claude responses
- Target keywords to analyze (use tracked terms from ranking-watch or
  provide a custom list)

## Analysis Framework

### 1. SERP Feature Inventory

For each tracked keyword, document the current SERP layout:

| Feature | Our Status | Opportunity |
|---------|-----------|-------------|
| **Featured Snippet** | Do we hold it? / Who does? | Content format match needed |
| **People Also Ask** | Are our pages appearing in PAA? | FAQ content opportunity |
| **Video Carousel** | Do we have video content ranking? | Video content opportunity |
| **Knowledge Panel** | Does our brand trigger one? | Schema/entity optimization |
| **Image Pack** | Are our images appearing? | Image optimization |
| **Local Pack** | Relevant for our queries? | Local SEO (if applicable) |
| **AI Overview** | Is an AIO shown? Are we cited? | GEO optimization |
| **Sitelinks** | Do we get sitelinks on brand terms? | Site structure signal |

### 2. Featured Snippet Audit

For keywords where a featured snippet appears:
- Who currently holds it?
- What format is it? (paragraph, list, table, video)
- Does our ranking page have content structured to win it?
- What content restructuring would improve our chances?

**Snippet-winning patterns:**
- Direct answer in first 40-60 words of the relevant section
- Content matches the snippet format (use lists for "how to," tables for
  comparisons, paragraphs for definitions)
- H2/H3 headings match the query phrasing

### 3. People Also Ask Mining

PAA boxes reveal related questions searchers ask. For each tracked keyword:
- Capture the PAA questions shown
- Identify which questions we can answer with existing content
- Flag questions that represent content gaps
- Note recursive PAA chains (clicking a PAA reveals more questions)

These feed directly into content planning and FAQ optimization.

### 4. AI Overview / Generative Search Monitoring

**Google AI Overviews (AIO):**
- For each tracked keyword, check if an AI Overview is displayed
- If yes: which sources are cited? Are we among them?
- What content type gets cited most? (long-form, FAQ, structured data, stats)
- How does the AIO change the effective organic CTR for positions 1-10?

**LLM-Powered Search (GEO):**

Reference `roster/performance-marketer/references/geo-playbook.md`.

For priority branded and category queries, check brand presence in:
- **ChatGPT** — "What is the best incident management tool for a 100-person engineering org?" / "Tell me about {{COMPANY}}"
- **Perplexity** — Same queries, note which sources are cited
- **Claude** — Same queries (knowledge cutoff applies)
- **Google Gemini** — Same queries in Google's AI products

Track:
- Are we mentioned? Positively, negatively, or neutrally?
- Which competitors are mentioned alongside us?
- What sources do these tools cite about us?
- Is our information accurate or outdated?

### 5. Structured Data as AI Signal

Evaluate whether our structured data makes our content more parseable
for AI systems:

- **JSON-LD schema coverage** — Organization, Product, FAQ, HowTo, Article,
  BreadcrumbList (reference schema-catalog.md)
- **`llms.txt`** — Does our site have an llms.txt file? Does it accurately
  describe our product, positioning, and key differentiators?
- **Content machine-readability** — Is our content in clean HTML (not buried in
  JS rendering)? Are key facts in structured formats (tables, lists, headers)?
- **FAQ sections** — Pages with explicit Q&A formatting get cited more in AIO

### 6. CTR Impact Analysis

SERP features compress organic CTR. For each keyword:
- What's our current CTR vs. expected CTR for our position?
- If CTR is below expected: what SERP feature is likely cannibalizing clicks?
- Estimate the traffic impact: (expected CTR - actual CTR) * impressions = lost clicks

## Output Format

```markdown
## SERP Analysis — {Date}

### Summary
- **Keywords with AI Overview:** {N} of {total tracked}
- **Featured snippets held:** {N}
- **Featured snippet opportunities:** {N}
- **GEO brand presence:** {strong / moderate / weak / absent}

### SERP Feature Map
| Keyword | Feat. Snippet | PAA | AIO | Video | Our Status |
|---------|-------------|-----|-----|-------|-----------|

### Featured Snippet Opportunities
| Keyword | Current Holder | Format | Our Rank | Action Needed |
|---------|---------------|--------|----------|--------------|

### AI Overview Citations
| Keyword | AIO Present | We're Cited | Cited Sources | Opportunity |
|---------|------------|------------|--------------|-------------|

### GEO Brand Presence
| Platform | Query | Mentioned | Sentiment | Accuracy | Sources Cited |
|----------|-------|----------|-----------|----------|--------------|

### CTR Impact
| Keyword | Position | Expected CTR | Actual CTR | Est. Lost Clicks | Cause |
|---------|---------|-------------|-----------|-----------------|-------|

### PAA Questions (Content Opportunities)
| Question | Volume Proxy | Existing Coverage | Gap? |
|----------|-------------|------------------|------|

### Recommendations
1. {Featured snippet wins to pursue}
2. {GEO improvements — structured data, llms.txt, content formatting}
3. {Content gaps revealed by PAA/AIO analysis}
```

## Reference Files

- `roster/performance-marketer/references/geo-playbook.md`
- `roster/performance-marketer/references/schema-catalog.md`
