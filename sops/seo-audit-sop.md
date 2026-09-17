# SEO Audit — Team SOP

**Version:** 1.0
**Owner:** Marketing / Content
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 → `/seo-audit`

---

## What This Is

The `/seo-audit` skill runs a structured SEO audit covering keyword research, on-page analysis, content gaps, technical checks, and competitor benchmarking. Use it when launching a new content initiative, auditing existing pages, identifying keyword opportunities, or sizing up how {{COMPANY}} stacks up against competitors in search.

Output is scoped to {{COMPANY}}'s operating market — mid-market B2B SaaS engineering organizations, US first — and to its primary keyword territory: incident management, on-call scheduling, alert noise and alert fatigue, MTTR and error budgets, blameless postmortems, and escalation-policy design.

**Time to complete:** ~15-30 minutes (web research + output review)

---

## Section 1: Prerequisites

**Required:**
- Access to Claude Co-Work with the {{COMPANY}} Marketing Plugin v1.5.0 installed. If you don't see `/seo-audit` as an available command, ask Scott to verify the plugin is active.
- Web access is used for live research — the skill performs searches during the run, so results reflect current rankings and competitor data at the time of execution.

**Optional but improves output quality:**
- One or more specific URLs from {{COMPANY_DOMAIN}} if you're doing a page-level audit. Paste them directly into the prompt.
- Google Search Console data (keyword rankings, impressions, CTR) pasted into the prompt or uploaded as a file. The tool doesn't connect to GSC directly, but will use any data you provide to make recommendations more precise.
- Known target keywords or a content brief if you already have a direction in mind.

---

## Section 2: Scoping the Audit

There are three ways to scope an `/seo-audit` run. Choose the one that matches what you're trying to learn.

### 1. Full site audit

A general health check of {{COMPANY_DOMAIN}} across keyword coverage, content gaps, and technical signals. Use this when you're doing a quarterly review, onboarding a new agency or contractor, or haven't run an audit in several months.

**What to include in the prompt:**
- "Run a full site audit for {{COMPANY_DOMAIN}}"
- Your top 3-5 priority keyword areas (e.g., incident management platform, on-call scheduling software, alert fatigue) — this helps the tool prioritize rather than spread thin
- Any known issues you want flagged (e.g., "we think our title tags are weak")

### 2. Page-level audit

Analysis of one or more specific URLs. Use this when a page is underperforming (low traffic, low ranking), when you're pre-publishing a new page, or when you want on-page recommendations for a specific piece of content.

**What to include in the prompt:**
- The URL(s) you want audited — paste them directly
- The target keyword or keyword cluster for each page
- Optional: current GSC data for those URLs (impressions, average position, CTR)

**Example prompt:**
> `/seo-audit` — page-level audit. URLs: {{COMPANY_DOMAIN}}/product/incident-response, {{COMPANY_DOMAIN}}/docs/terraform-provider. Target keywords: "incident management platform," "terraform on call rotation." Here's our GSC data for those pages: [paste data]

### 3. Keyword opportunity audit

Research into a specific topic or keyword cluster to find what {{COMPANY}} should be ranking for but isn't. Use this when planning a new content vertical, evaluating whether to go after a new keyword area, or building out a topic cluster.

**What to include in the prompt:**
- The topic or keyword cluster (e.g., "on call compensation," "slo vs sla")
- Who you're trying to reach (Aaron the platform engineer, Erin the technical founder, or Hannah the VP Engineering — defaults to Aaron if not specified)
- Any competitors you want benchmarked specifically (defaults to {{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_B}}, {{COMPETITOR_D}}, {{COMPETITOR_F}})

**Example prompt:**
> `/seo-audit` — keyword opportunity audit. Topic: on-call compensation and rotation fairness. We want to understand what terms {{COMPETITOR_A}} and {{COMPETITOR_C}} are ranking for in this cluster that we're not.

---

## Section 3: Reading the Audit Output

The audit produces six output sections. Here's what each one tells you and what to look for.

### Keyword analysis table

Lists target keywords with estimated search volume, keyword difficulty (KD), and current ranking position where known. Head terms (high volume, high competition) are separated from long-tail terms (lower volume, lower competition, higher conversion intent).

**What to look for:** Long-tail terms where {{COMPANY}} is ranking 6-20 — these are quick-win candidates where a content or on-page improvement can move you into page-one positions. Head terms with high KD are longer-term plays.

### On-page findings (page-level and full-site audits)

Per-URL breakdown covering: title tag (length, keyword inclusion, click appeal), meta description (length, presence, CTA quality), header structure (H1/H2/H3 hierarchy, keyword usage), and internal linking (pages that should link to each other but don't).

**What to look for:** Missing or duplicate title tags and meta descriptions are the fastest fixes. Poor internal linking is often the highest-leverage on-page improvement after titles and metas.

### Content gap list

Topics and keywords that competitors rank for in {{COMPANY}}'s territory that {{COMPANY}} doesn't have content for. Organized by estimated traffic opportunity.

**What to look for:** Clusters of related gaps signal a topic area where a single well-structured piece (or a short content series) could capture significant ground. One-off gaps may not be worth prioritizing immediately.

### Technical flags

Issues affecting crawlability, indexation, or page experience. Common flags: slow load signals, pages returning non-200 status codes, duplicate content across similar URLs, missing canonical tags, and pages blocked from indexation.

**Important:** These are estimates derived from web research and public signals. They are not a Screaming Frog crawl. Use them as a starting investigation list, not a definitive technical audit.

### Competitor comparison

Shows which competitors rank for the same terms as {{COMPANY}}, their estimated positions, and any patterns in their content approach. Default competitors: {{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_B}}, {{COMPETITOR_D}}, {{COMPETITOR_F}}.

**What to look for:** Competitors consistently outranking {{COMPANY}} on core terms (incident management platform, on call scheduling software) signals a content depth or domain authority gap. Competitors ranking on long-tail terms {{COMPANY}} hasn't targeted is a direct opportunity list.

### Prioritized recommendations

Recommendations sorted into two buckets:

**Quick wins:** Changes that can be made within a week with high confidence of impact. Typically: fixing title tags and meta descriptions, improving header structure on existing pages, adding internal links between related content.

**Longer-term plays:** Content creation, technical fixes requiring engineering involvement, or domain authority improvements (backlink strategy). These are higher effort and longer time-to-result.

---

## Section 4: Acting on Recommendations

Use this routing table to move recommendations from the audit into action.

| Recommendation type | Who owns it | How to route |
|---------------------|-------------|--------------|
| Fix title tags or meta descriptions | {{DESIGN_LEAD_FIRST}} (website and design) | Send the on-page findings section directly; include the specific URL and recommended change |
| Improve header structure on an existing page | {{DESIGN_LEAD_FIRST}} | Same as above — include current structure and recommended changes |
| Add internal links | {{DESIGN_LEAD_FIRST}} | List the source and destination pages |
| Create content for a gap topic | Content team | Log as a content calendar item; create a Linear task via `/linear-task-capture` with the target keyword and gap context |
| Technical flags (crawl errors, canonicalization, page speed) | Engineering or website team | Route through {{DESIGN_LEAD_FIRST}} first; they'll escalate to engineering if dev work is required |
| Keyword strategy changes (entering a new cluster, deprioritizing a term) | Scott | Bring to campaign planning — don't act on keyword strategy changes from a single audit without a discussion |
| Backlink or authority-building opportunities | Scott | Flag in the weekly marketing sync for prioritization |

---

## Section 5: Limitations

**No direct GSC access.** The tool does not connect to Google Search Console. Ranking positions and traffic estimates are derived from web research and public data sources. If you paste in GSC data, recommendations will be more accurate. Always validate prioritization decisions against your actual GSC data.

**Technical data is directional, not definitive.** Technical flags (page speed, crawl issues, duplicate content) are surfaced from public signals. They will not catch everything a full technical crawl would catch. For a thorough technical audit, use Screaming Frog or a comparable crawl tool and treat the skill's technical output as a pre-screen.

**Competitor data quality varies.** Competitors with limited public footprint or heavy JavaScript rendering may have thin data in the output. The skill will note when competitor data is sparse.

**Keyword volumes are estimates.** Volume figures are directional. Use `~~SEO` (Ahrefs) or GSC to validate before making prioritization decisions based on volume alone.

**Scope affects quality.** A full site audit is broader but shallower. A page-level or keyword opportunity audit is narrower but more precise. If you need deep recommendations, scope tightly.

---

## Section 6: Troubleshooting

| Problem | What to do |
|---------|-----------|
| Audit output is too broad to act on | Narrow the scope. Run a page-level or keyword opportunity audit instead of a full site audit. Give the tool a tighter keyword list or fewer URLs. |
| Competitor data is thin | Note it in the audit output and proceed. Competitors may have limited public data (e.g., paywalled content, heavy JS rendering). Cross-check with `~~SEO` if competitor benchmarking is the primary goal. |
| Technical flags don't match what you're seeing in GSC | The skill's technical data is estimated from public signals. GSC is authoritative. When they conflict, trust GSC. Use the skill's flags as a checklist to investigate, not as a verdict. |
| Keyword volumes seem too high or too low | Treat them as directional order-of-magnitude signals. Validate with `~~SEO` before using them to justify a content investment. |
| Rankings don't match what GSC shows for a page | GSC shows your actual average position across all queries. The skill shows estimated rankings for specific target terms — they measure different things. Both can be correct simultaneously. |
| The tool asks for clarification mid-run | Respond with the requested detail (target keyword, URL, scope clarification). The tool won't proceed with assumptions when it needs specific input. |

---

## Quick Reference

**Command:** `/seo-audit`

**Audit scopes:**

| Scope | Use when |
|-------|---------|
| Full site audit | Quarterly review, general health check |
| Page-level audit | Specific URL is underperforming; pre-publish check |
| Keyword opportunity audit | Exploring a new topic cluster or content vertical |

**Required inputs:**

| Scope | Required | Recommended |
|-------|----------|-------------|
| Full site audit | Scope declaration, priority keyword areas | Known issues to investigate |
| Page-level audit | URL(s), target keyword(s) | GSC data for those URLs |
| Keyword opportunity audit | Topic or keyword cluster | Target persona, specific competitors to benchmark |

**Output sections:**

1. Keyword analysis (head terms + long tail)
2. On-page findings (title tags, meta descriptions, headers, internal links)
3. Content gap list
4. Technical flags
5. Competitor comparison
6. Prioritized recommendations (quick wins vs. longer-term plays)

**Routing table:**

| Output | Route to |
|--------|---------|
| Title tags, meta descriptions, headers, internal links | {{DESIGN_LEAD_FIRST}} |
| Content gaps | Content calendar + Linear via `/linear-task-capture` |
| Technical issues | {{DESIGN_LEAD_FIRST}} → engineering if dev work needed |
| Keyword strategy changes | Scott — campaign planning |
| Backlink opportunities | Scott — weekly marketing sync |

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
