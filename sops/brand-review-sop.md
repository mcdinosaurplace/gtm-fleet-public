# Brand Review -- Team SOP

**Version:** 1.0
**Owner:** Marketing / Brand
**Applies to:** All marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 -> `/brand-review`

---

## What This Is

The Brand Review skill checks marketing content against {{COMPANY}}'s brand voice, style guide, and messaging pillars before it goes external. It runs structured checks across voice, prohibited language, style rules, product naming, persona alignment, and CTA quality, then returns a scored verdict with line-level callouts and suggested rewrites. Use it to catch brand issues before they reach an audience, not after.

**Time to complete:** ~2-5 minutes per piece

---

## Section 1: When to Use This

**Required before publishing:**

- Paid ad copy (search, display, social) before going live
- Blog posts before publishing
- Emails before sending (run `/brand-review` first, then hand off to `/email-qa`)
- Press releases before distributing
- Landing page copy before launch

**Recommended but not required:**

- Social posts (especially LinkedIn)
- Internal documents going to leadership or board

When in doubt, run it. A review takes less time than a correction.

---

## Section 2: How to Submit Content for Review

Open Claude Co-Work and invoke the skill with `/brand-review`. Paste the full content directly into the chat window. Do not link to an external doc, the skill needs the raw text to run line-level analysis.

**Include this context with your submission:**

- Content type (e.g., "Google Ads headlines and descriptions", "blog post intro", "nurture email")
- Target persona: Erin or Hannah
- Channel (e.g., LinkedIn, paid search, website, email)

**Example of a well-framed submission:**

> `/brand-review`
>
> Content type: LinkedIn sponsored post
> Persona: Hannah
> Channel: LinkedIn
>
> [paste content here]

If you omit context, the skill will still run but persona alignment and CTA checks will be less precise. Providing it takes ten seconds and improves the output.

---

## Section 3: Reading the Review Output

The skill returns output in three layers.

**Per-check verdicts**

Each brand check returns one of two results:

- **Pass** -- the content meets the standard for that check
- **Flag** -- the content has one or more issues against that check

Checks cover: brand voice pillars, prohibited language, style rules, product name casing, persona alignment, and CTA quality.

**Line-level callouts**

Flagged checks include the specific line or phrase that triggered the flag, the issue, and a suggested rewrite. Suggested rewrites are starting points, not final copy. Adapt them to fit the content's flow and context.

**Overall recommendation**

The review closes with one of two verdicts:

- **Ready to Publish** -- all checks passed or flags are minor and noted. Proceed.
- **Revise Before Publishing** -- one or more material flags. Make the edits, then re-run before publishing.

**A flag is a recommendation, not a block.** A senior marketer has final say. If you override a flag, document the exception so it does not create confusion later. See Section 6 for escalation guidance.

---

## Section 4: Common Brand Issues

These are the flags that appear most frequently across content types.

| Issue | What It Looks Like | How to Fix |
|---|---|---|
| Fear language | "stay compliant", "avoid fines", "legal exposure", "don't get caught" | Reframe around the outcome or the opportunity. "Stay ahead of regulatory changes" not "avoid fines." |
| Competitor names | Naming a competitor in general-audience copy | Remove. Competitor names are only allowed in approved competitor-targeting campaigns. When in doubt, remove. |
| Em-dashes | Using -- or -- to connect clauses | Replace with a comma, a period, or "and." Split into two sentences if the clause is long. |
| Vague CTAs | "Learn more", "Get started", "See how" | Make the CTA specific to the action and outcome. "See how teams cut onboarding time" over "Learn more." |
| AI-speak | "leverage", "utilize", "streamline", "robust", "comprehensive" | Use plain verbs. "Use" not "utilize." "Improve" not "streamline." "Strong" not "robust." |
| Wrong product casing | "{{COMPANY_UPPER}}", "{{company_slug}}", "{{COMPANY_DOMAIN}}" in body copy | Use "{{COMPANY}}" -- capital P, no all-caps. Feature and product names follow the same rule: capitalize correctly per the brand guide. |
| Passive voice | "was created by", "is used by", "has been designed" | Rewrite in active voice. Subject acts; do not have the subject receive the action. |
| Unexplained jargon | Using "MQL", "RevOps", "ICP" without defining them on first use | Define on first use, or cut the jargon if the audience is external and non-technical. |

---

## Section 5: After the Review

**Ready to Publish**

Proceed to the next step in your publishing workflow. No further brand review is needed for this version of the content.

**Revise Before Publishing**

1. Address the flagged items. Use the suggested rewrites as a starting point.
2. Re-run `/brand-review` on the revised version before publishing. A revision can introduce new issues.
3. If a flag is minor and you are choosing to override it, document the exception.

**Hand-offs after review:**

- **Email:** After `/brand-review` passes, hand off to `/email-qa` for deliverability and structural checks before sending.
- **Paid ads:** After `/brand-review` passes, hand off to the paid search team or run through performance-marketer's creative optimizer if the copy is part of a larger campaign set.
- **Blog / landing page:** After `/brand-review` passes, proceed to editorial review and publication workflow.

---

## Section 6: Troubleshooting

| Situation | What to Do |
|---|---|
| The review flags something you disagree with | Escalate to a senior marketer. If the override is approved, document the exception with a note on why. Do not suppress the flag without review. |
| The review passes something that later gets flagged by a human reviewer | Note the edge case. If it reflects a gap in the brand guide, bring it to Scott to update the guide or the skill's training. Do not assume the skill is always wrong, it may have been a context issue in how the content was submitted. |
| The skill does not recognize the content type | Specify it explicitly in your submission. For example: "Content type: homepage hero headline, above the fold, no supporting body copy." The more context you give, the more accurate the checks. |
| The review returns a verdict but no line-level callouts | This typically means all checks passed at the line level but an overall concern was noted. Read the overall recommendation carefully. |
| You are unsure which persona to specify | Default to Erin for SMB and mid-market content, Hannah for enterprise. If the content targets both, specify both and note it in your submission. |

---

## Quick Reference

**Command:** `/brand-review`

**Required inputs:**
- Full content text (pasted directly)
- Content type
- Target persona (Erin or Hannah)
- Channel

**Output verdict types:**
- Pass / Flag per check
- Ready to Publish / Revise Before Publishing overall

**Required before publishing checklist:**

- [ ] Paid ad copy
- [ ] Blog posts
- [ ] Emails (follow with `/email-qa`)
- [ ] Press releases
- [ ] Landing page copy
