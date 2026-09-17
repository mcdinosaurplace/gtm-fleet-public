# Competitive Brief — Team SOP

**Version:** 1.0
**Owner:** Marketing / Product Marketing
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 → `/competitive-brief`

---

## What This Is

The `/competitive-brief` skill researches a named competitor and generates a structured positioning and messaging comparison relative to {{COMPANY}}. Use it when analyzing a competitor, building or refreshing battlecards, identifying content gaps, comparing feature messaging, or preparing counter-messaging for paid and organic campaigns. Output is intended for internal use only.

**Time to complete:** ~10-20 minutes (live web research + output review)

---

## Section 1: Prerequisites

Before invoking the skill, confirm the following:

- **Claude Co-Work is open** with the {{COMPANY}} Marketing Plugin v1.5.0 active. This is Path A (Co-Work), not Claude Code.
- **Plugin is enabled.** Verify `/competitive-brief` is available by typing `/` in any Co-Work conversation. If it does not appear, re-enable the {{COMPANY}} Marketing Plugin in your Co-Work settings.
- **Web access is used for live research.** No additional connectors (HubSpot, Notion, Slack) are required. The skill fetches public-facing content from the competitor's website, blog, ads library, and search results at runtime.
- **Have two things ready before invoking:** the competitor name and your specific focus area (see Section 2). Running without a focus area produces a general overview that is useful but less actionable.

{{COMPANY}}'s current primary competitive set: {{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_B}}, {{COMPETITOR_F}} On-Call, {{COMPETITOR_D}} (alert routing and notification space).

---

## Section 2: What to Request

Provide the following when invoking the skill. Include only what applies — not every field is required for every use case.

- **Competitor name** — one competitor per run for best results. Do not batch multiple competitors in a single request.
- **Focus area** — select one or more: messaging, pricing, content/SEO, ICP, or all. Narrowing the focus area sharpens the output significantly.
- **Specific question to answer** — the single question driving the brief (e.g., "How do they position against {{COMPANY}} on per-responder pricing?" or "What content are they producing that we have no equivalent for?").
- **Intended output use** — internal battlecard, repositioning brief, counter-messaging for ads, content calendar gap analysis. This shapes how the skill structures recommendations.

### Example request

```
Competitor: {{COMPETITOR_B}}
Focus area: Messaging + ICP
Question: How does {{COMPETITOR_B}} frame on-call and incident response for mid-market engineering leaders vs. how {{COMPANY}} frames it for platform engineers?
Output use: Internal battlecard for AE enablement
```

---

## Section 3: Reading the Output

The brief is organized into six sections. Here is what each section contains and how to interpret it.

**Competitor overview**
Positioning statement, inferred ICP, and key differentiators as the competitor presents them publicly. This reflects their marketing, not their product capabilities. Treat it as "how they want to be perceived."

**Messaging comparison table**
Side-by-side view of how the competitor and {{COMPANY}} talk about the same features, problems, or use cases. Use this to spot language patterns they own that {{COMPANY}} does not, or vice versa.

**Positioning gaps**
Two-column breakdown: where {{COMPANY}} is stronger and where the competitor claims ground {{COMPANY}} does not. The "where they claim ground" column is observational — it does not mean the competitor's claim is accurate or defensible.

**Content and SEO presence comparison**
What the competitor publishes, where they show up in search, and what content formats they rely on. This section is directional. Exact traffic figures are estimated or inferred from public signals, not pulled from a data source.

**Battlecard summary**
Condensed reference card for AEs and SDRs: competitor strengths (as claimed), {{COMPANY}} counter-points, and objection-handling starters. Formatted for quick use in a discovery or deal call.

**Counter-messaging suggestions**
Draft messaging directions {{COMPANY}} can take in response to the competitor's positioning. These are inputs for briefs and campaigns, not final copy. Do not use competitor names in brand content (see Section 6).

**What to trust vs. what to verify**
- Trust: observed public messaging, content topics, ICP language pulled from their website and ads
- Verify before acting on: internal pricing details, product capabilities not publicly documented, market share figures, any claim marked as inferred

---

## Section 4: Using the Brief

**Battlecard output**
Send to {{HEAD_OF_MARKETING_FIRST}} (sales enablement) for review and distribution to AEs and SDRs. {{HEAD_OF_MARKETING_FIRST}} owns the battlecard library — do not publish directly to sales channels without his sign-off.

**Counter-messaging output**
Feed into `/draft-content` or the paid search optimizer as a context input. Reference the counter-messaging section when writing ad copy or landing page variants targeting competitive keywords.

**Content gaps identified**
Create Linear tasks in the content calendar project for any identified gaps that warrant a response. Tag with the relevant quarter and assign to the appropriate content owner.

**Positioning gaps**
If the gap analysis surfaces something structurally significant (e.g., a competitor has claimed a positioning space {{COMPANY}} has no response to), escalate to a product marketing review before acting. Do not respond to positioning gaps with ad hoc copy changes.

---

## Section 5: Keeping Briefs Current

Competitor messaging shifts. Every brief should be treated as a point-in-time snapshot.

- **Note the date** on any brief you reference or share. The header of the output includes the run date.
- **Re-run quarterly** for primary competitors: {{COMPETITOR_A}}, {{COMPETITOR_C}}, and {{COMPETITOR_B}}. Secondary competitors ({{COMPETITOR_F}} On-Call, {{COMPETITOR_D}}) can be re-run semi-annually or when a specific trigger occurs.
- **Trigger an immediate re-run** if a competitor launches a new product, announces a pricing change, runs a visible campaign targeting {{COMPANY}}'s ICP, or earns significant press coverage. Do not wait for the quarterly cycle in those cases.
- Store completed briefs in the `localwork/` folder if they contain analysis you want to reference later. Briefs in `localwork/` are not committed to the shared repo.

---

## Section 6: Troubleshooting

| Problem | Fix |
|---------|-----|
| Output is too high-level | Specify a narrower focus area and a concrete question. "Messaging" alone is broad; "how they price on-call seats for teams under 50 engineers" is actionable. |
| Competitor website is gated or paywalled | The skill will note what it cannot access. For gated content (e.g., competitor pricing pages, login-required product tours), supplement the brief manually with information you have from sales calls, review sites, or analyst reports. |
| Counter-messaging includes competitor names in copy | Do not use those suggestions directly in brand content. Counter-messaging that names competitors is appropriate only in competitor-targeting paid campaigns (e.g., conquest search). Flag any such copy for {{HEAD_OF_MARKETING_FIRST}}'s review before it goes live. |
| Output mixes up two competitors or conflates positioning | This can happen if you reference more than one competitor in the same prompt. Run one competitor per request. |
| Pricing data appears incorrect or outdated | Treat all pricing information as directional. Competitor pricing is not reliably accessible via public sources and changes frequently. Verify directly before using in sales materials. |
| Battlecard language is too generic to use in a call | Add your specific deal context to the follow-up prompt: the competitor you're displacing, the buyer persona, and the objection being raised. The skill can refine the battlecard for that scenario. |

---

## Quick Reference

| Item | Detail |
|---|---|
| **Command** | `/competitive-brief` |
| **Tool** | {{COMPANY}} Marketing Plugin v1.5.0 in Claude Co-Work (Path A) |
| **Required inputs** | Competitor name, focus area |
| **Recommended inputs** | Specific question, intended output use |
| **Primary competitive set** | {{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_B}}, {{COMPETITOR_F}} On-Call, {{COMPETITOR_D}} |
| **Output sections** | Competitor overview, messaging comparison table, positioning gaps, content/SEO presence, battlecard summary, counter-messaging suggestions |
| **Connectors required** | None (web access only) |
| **Re-run frequency** | Quarterly for primary competitors; immediately on trigger events |
| **Typical use cases** | Battlecard creation, counter-messaging for ads, content gap analysis, repositioning briefs |

---

*Questions? Ping Scott or drop a note in #marketing-pmm.*
