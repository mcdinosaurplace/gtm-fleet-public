# Draft Content — Team SOP

**Version:** 1.0
**Owner:** Marketing / Content
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 → `/draft-content`

---

## What This Is

The `/draft-content` skill drafts marketing content across channels. You provide a brief describing what you need; the skill returns a ready-to-review draft in the correct format for the content type. It handles six content types: blog posts, social media posts, email newsletters, landing pages, press releases, and case studies.

**Time to complete:** ~3-10 minutes depending on content length

---

## Section 1: Prerequisites

Before invoking the skill, confirm the following:

- **Claude Co-Work is open** with the {{COMPANY}} Marketing Plugin v1.5.0 active. This is Path A (Co-Work), not Claude Code.
- **Plugin is enabled.** Verify `/draft-content` is available by typing `/` in any Co-Work conversation. If it does not appear, re-enable the {{COMPANY}} Marketing Plugin in your Co-Work settings.
- **No external connectors required.** Content drafting is self-contained. HubSpot, Notion, and Slack connectors are not needed for this skill.

Tip: have your brief fully drafted before invoking the skill. A detailed brief produces a significantly better first draft and reduces revision rounds.

---

## Section 2: What to Include in Your Brief

The quality of the brief determines the quality of the output. This is the most important step.

Every brief should include:

- **Content type** — blog post, social post, email newsletter, landing page, press release, or case study
- **Topic or subject** — what the piece is about; be specific
- **Target audience** — Erin the Technical Founder (founder/CTO, 5-40 engineers), Hannah the VP Engineering (VP or Head of Engineering, 90-200 engineers), Aaron the Platform Engineer (owns the paging stack), or general (technical evaluators, developers)
- **Goal** — awareness, conversion, or nurture
- **Key message or angle** — the one idea the reader should walk away with
- **Any specific requirements** — word count, tone notes, SEO keyword (blog posts), subject line direction (emails)
- **Reference content** (optional) — examples of pieces you liked, or competitor content to differentiate from

For blog posts only, also include the primary SEO keyword and any secondary keywords.

For case studies, include the customer name, the problem they were solving, and the measurable results.

For emails, include the desired subject line direction and any preview text constraints.

### Example brief (blog post)

```
Content type: Blog post
Topic: How growing engineering teams cut page volume without missing real incidents
Target audience: Hannah the VP Engineering — VP or Head of Engineering at a 150-400 person company
Goal: Awareness / top of funnel
Key message: {{COMPANY}} groups related signals and routes the survivors to a named owner, so the team takes fewer pages and every page that lands has someone waiting for it
Word count: ~1,200 words
SEO keyword: how to reduce alert noise
Secondary keywords: async project management, remote team updates
Tone: Approachable and confident. Draw on the "fewer meetings" angle. No fear language.
```

---

## Section 3: Content Types and What to Expect

| Content Type | Typical Length | Format | Special Inputs |
|---|---|---|---|
| Blog post | 800-1,500 words | H1, intro, 3-5 H2 sections, conclusion, CTA | Primary SEO keyword, secondary keywords |
| LinkedIn post | 150-300 words | Hook line, body, CTA, no hashtag spam | Goal (awareness vs. conversion), audience |
| X / Twitter post | 1-3 tweets, under 280 chars each | Hook-focused, punchy | Same as LinkedIn; note if thread format needed |
| Email newsletter | 300-600 words body | Subject line, preview text, greeting, body, CTA, sign-off | Subject line direction, CTA destination |
| Landing page | 200-400 words copy | Headline, subheadline, 2-3 body sections, CTA | Offer or conversion goal, any form fields |
| Press release | 400-600 words | Dateline, lead paragraph, 2-3 body paragraphs, 1-2 quotes, boilerplate | Announcement details, quote attribution, release date |
| Case study | 500-800 words | Challenge, solution, results, pull quote | Customer name, problem, measurable results data |

The skill outputs clean, ready-to-review copy. It does not produce design files, HTML templates, or published content.

---

## Section 4: Reviewing the Draft

Before using the draft, check the following:

**Brand voice**
- Writing is clear, direct, and reader-first. No jargon or padding.
- Confident and grounded in expertise. No hedging phrases.
- Human and warm. Not stiff or corporate.
- Banned words and phrases: "leverage," "utilize," "streamline," "robust," "comprehensive," fear-based language, competitor names.
- No em-dashes anywhere in the copy.

**Product and company names**
- {{COMPANY}} product names are capitalized correctly. When in doubt, check the brand guidelines.
- Acronyms stay uppercase: MTTR, MTTA, SLO, SLA, SCIM. Never "Mttr" or "Slo".

**Format**
- Blog posts have a clear H1, H2 section structure, and a closing CTA.
- Emails have subject line, preview text, and body copy as distinct labeled sections.
- Social posts are within character limits (LinkedIn: no hard cap but aim under 300 words; X: 280 characters per tweet).
- Press releases follow the standard AP-style structure: dateline, lead, body, quotes, boilerplate.

**Requesting revisions**
Stay in the same conversation thread and ask the skill to adjust. Specific requests work best:

- "Shorten the intro to two sentences."
- "The tone is too formal — make it more conversational."
- "Add a stronger CTA at the end of the email."
- "Rewrite the LinkedIn hook to be more provocative."

---

## Section 5: Routing After Draft

Once the draft is approved, route it based on content type:

| Content Type | Next Step | Who |
|---|---|---|
| Blog post | Brand review | `/brand-review` skill, then {{HEAD_OF_MARKETING_FIRST}} for final approval |
| Email newsletter | Copy approval, then email QA | {{HEAD_OF_MARKETING_FIRST}} for copy approval, then `/email-qa` before send |
| Social posts | Copy approval | {{HEAD_OF_MARKETING_FIRST}} for approval before scheduling |
| Landing page | Copy approval, then design handoff | {{HEAD_OF_MARKETING_FIRST}} for copy, then {{DESIGN_LEAD_FIRST}} for design |
| Press release | Copy approval | {{HEAD_OF_MARKETING_FIRST}} for approval before distribution |
| Case study | Copy approval, then design handoff | {{HEAD_OF_MARKETING_FIRST}} for copy, then {{DESIGN_LEAD_FIRST}} for designed PDF version |

If follow-up tasks need to be logged in Linear (e.g., "design handoff," "schedule post"), you can ask the skill or use the Linear connector in Co-Work to capture them in the current sprint.

---

## Section 6: Troubleshooting

| Problem | Fix |
|---------|-----|
| Output is too generic | Sharpen the brief. Add a more specific angle, name the exact audience persona, and include the one key message you want the reader to take away. |
| Draft does not match {{COMPANY}} brand voice | Add "check against {{COMPANY}} brand voice: clear, authoritative, approachable. No em-dashes. No banned words: leverage, utilize, streamline, robust, comprehensive." to your next prompt in the conversation. |
| Wrong content type or format | Specify the format explicitly in your next message (e.g., "rewrite this as a press release in standard AP format with a dateline and boilerplate"). |
| Character limit exceeded for social posts | Tell the skill the hard limit in your next message (e.g., "trim the LinkedIn post to under 250 words" or "rewrite as a single tweet under 280 characters"). |
| Case study lacks specificity | Provide the actual customer results data. The skill cannot fabricate metrics; you must supply the numbers. |
| Press release quotes sound generic | Provide the name, title, and preferred quote direction for each speaker. The skill will draft quotes to match that voice. |

---

## Quick Reference

| Item | Detail |
|---|---|
| **Command** | `/draft-content` |
| **Tool** | {{COMPANY}} Marketing Plugin v1.5.0 in Claude Co-Work (Path A) |
| **Required inputs** | Content type, topic, target audience, goal, key message |
| **Optional inputs** | Word count, tone notes, SEO keywords, reference examples |
| **Content types** | Blog post, LinkedIn post, X / Twitter post, email newsletter, landing page, press release, case study |
| **Output format** | Clean draft copy, labeled by section (headline, body, CTA, etc.) |
| **Connectors required** | None |
| **Typical use cases** | First drafts for all written marketing content |

---

*Questions? Ping Scott or drop a note in #marketing-content.*
