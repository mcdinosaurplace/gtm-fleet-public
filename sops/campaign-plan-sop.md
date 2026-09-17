# Campaign Plan -- Team SOP

**Version:** 1.0
**Owner:** Marketing / Demand Gen
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 -> `/campaign-plan`

---

## What This Is

The `/campaign-plan` skill generates a full campaign brief from a short input. Given your objective, audience, timeline, and budget, it produces audience segmentation, channel strategy, a week-by-week content calendar, KPIs, and a creative requirements list. Use it when launching a new campaign, planning a product launch, building a content calendar, allocating budget across channels, or defining campaign KPIs.

**Time to complete:** ~10-15 minutes (brief input + output review)

---

## Section 1: Prerequisites

- **Claude Co-Work** open with the {{COMPANY}} Marketing Plugin v1.5.0 active.
- **Campaign context ready before you start.** The skill produces better output when you have a clear objective, rough timeline, and target audience in mind before invoking it. Vague inputs produce generic output.
- You do not need a finalized budget. A rough envelope is enough to improve channel recommendations.
- You do not need to know the channel mix upfront. You can ask the skill to recommend channels given your objective and budget.

---

## Section 2: What to Include in Your Campaign Brief

The more specific your input, the more actionable the output. At minimum, include:

- **Campaign name or working title** -- Even a placeholder helps structure the output.
- **Primary objective** -- What this campaign needs to accomplish. Examples: drive demo requests, generate MQLs from mid-market engineering orgs, build category awareness among platform engineers, support a product launch, fill the reliability roundtable.
- **Target personas** -- Erin the Technical Founder (Founder/CTO, 5-40 engineers, pre-seed through Series A, is the rotation herself), Hannah the VP Engineering (VP/Head of Engineering or Director of SRE, 90-200 engineers, Series B/C, owns MTTR and the on-call policy), both, or a different segment you define.
- **Timeline** -- Start date, end date, and any hard milestones (e.g., product launch date, event date, end of quarter).
- **Approximate budget envelope** -- Optional, but improves channel recommendations. Total or per-channel if you have it.
- **Channels in scope** -- List the channels you want the plan to cover, or say "recommend channels for me." {{COMPANY}}'s standard channels: Google Ads (search + display), LinkedIn Sponsored Content, email (HubSpot), content/blog, social (LinkedIn, X).
- **Key message or product area** -- What are you promoting? What is the main value proposition for this campaign?
- **Constraints** -- Anything the plan should avoid or work around. Examples: "no paid LinkedIn this quarter," "must include email as a primary channel," "creative assets won't be ready until week 3."

### Example Input

> Campaign: Q3 Eng-Leader Push
> Objective: Generate MQLs from VP Engineering buyers at companies running 90-200 engineers
> Persona: Hannah the VP Engineering (Series B/C, owns MTTR and the on-call rota)
> Timeline: Q3, weeks 1-12
> Budget: $40,000 total
> Channels: LinkedIn Sponsored Content, email (HubSpot), content/blog
> Key message: {{COMPANY}} sends an engineering org far fewer pages and gives every page that remains a named owner -- shorter incidents, a fairer rotation, engineers who stay
> Constraints: No Google Ads this quarter. Content assets land in week 2.

---

## Section 3: Reading the Output

The skill returns six sections. Here is what each contains and what to check.

### Campaign Brief Summary

Name, objective, timeline, and budget envelope restated and confirmed. Verify the objective is framed correctly -- this drives the rest of the plan. If it is off, correct it before reviewing the other sections.

### Target Audience Segmentation

Primary and secondary persona breakdown. Each includes firmographic profile, role context, key pain points, and messaging angle. Check that the pain points reflect your current positioning. The skill uses {{COMPANY}}'s standard personas (Erin and Hannah) unless you specified otherwise. If your campaign targets a different segment, review this section carefully.

### Channel Strategy

A table listing each channel in scope, its role in the campaign (awareness, consideration, conversion), rationale for inclusion, and budget allocation if you provided a budget envelope. Confirm the rationale matches your actual strategic context. The skill does not know your current channel performance -- if a channel it recommends is underperforming, flag it and ask for an alternative.

### Content Calendar

A week-by-week plan covering the full campaign timeline. Each week lists the content format, topic or angle, channel, and the persona it targets. Review for gaps and pacing. If certain weeks are heavy, ask the skill to redistribute. If an asset type is not feasible given your production capacity, note it and request substitutions.

### KPIs and Success Metrics

A table of primary and secondary KPIs, with measurement approach for each. Primary KPIs tie directly to the campaign objective (e.g., MQLs, demo requests). Secondary KPIs track channel-level performance (e.g., LinkedIn CTR, email open rate). Check that the KPI names match what you actually track in HubSpot and your reporting dashboards. If they do not, ask the skill to substitute specific metric names.

### Creative and Copy Requirements

A list of creative assets and copy pieces needed to execute the plan -- ad copy, email subject lines and body, blog posts, landing page copy, and so on. Use this as a production checklist. Hand it off to {{CONTENT_LEAD_FIRST}} (content and product marketing) or route relevant pieces to the appropriate owner.

---

## Section 4: Customizing the Plan

The output is a starting point. Refine it in the same conversation without starting over.

- **Channel mix is wrong** -- Ask for an alternative mix. Example: "Remove LinkedIn and reallocate that budget to email and content."
- **Timeline needs adjustment** -- Ask the skill to compress or extend the calendar. Specify working days vs. calendar days if it matters.
- **KPIs do not match your reporting** -- Name the exact metrics you track. Example: "Replace 'MQLs' with 'Marketing Qualified Leads as defined in HubSpot stage: SQL-ready.'"
- **Personas need refinement** -- If your campaign targets a sub-segment of Erin or Hannah, describe it and ask the skill to adjust the segmentation.
- **Creative requirements are too broad** -- Ask the skill to break out specific deliverables by week or channel.
- **Budget allocation looks off** -- State your preferred split and ask the skill to revise the channel strategy table accordingly.

You can ask follow-up questions in the same session without re-invoking `/campaign-plan`. The skill retains the context of the current campaign plan throughout the conversation.

---

## Section 5: Turning the Plan into Action

Once the plan is reviewed and customized:

| Next Step | How |
|-----------|-----|
| Draft campaign copy and ad creative | Use `/draft-content` with the creative requirements list as input |
| Build or update paid search campaigns | Use `/paid-search-optimizer` for the copy pass, then `performance-marketer:optimization-dossier` for the bid and budget moves |
| Set up email sequences | Use the content calendar and copy requirements to brief HubSpot workflows |
| Push tasks to Linear | Use `/linear-task-capture` to convert the content calendar and creative list into tracked tasks |
| Design handoff | Share the creative requirements list with {{DESIGN_LEAD_FIRST}}. Include asset dimensions, channel specs, and timeline from the content calendar |
| Review and iterate weekly | Compare actuals against the KPI table each week. Use `performance-marketer:creative-optimizer` for the week-over-week creative read and `performance-marketer:optimization-dossier` for bid and budget moves |

---

## Section 6: Troubleshooting

| Problem | Fix |
|---------|-----|
| Plan is too generic | Add more constraint to your input: tighter timeline, specific persona sub-segment, named channels, budget envelope, or explicit messaging angle. The skill produces generic output when given generic input. |
| Channel mix does not fit your situation | Specify channels explicitly in your input, or tell the skill which channels to exclude. It does not know your current channel performance or budget constraints unless you state them. |
| KPIs do not match your reporting | Name the exact metrics and sources you use. Example: "We track pipeline-sourced MQLs in HubSpot, not just form fills." Ask the skill to rebuild the KPI table using those definitions. |
| Timeline is off | Clarify whether you mean calendar days or working days. Include any blackout periods (holidays, team offsites, product freezes). |
| Content calendar is too aggressive for your team | State your production capacity. Example: "We can produce one long-form piece and two short-form pieces per week." Ask the skill to revise the calendar within that constraint. |
| Persona segmentation does not reflect your audience | Describe your actual target segment in detail and ask the skill to re-run the audience breakdown. You are not limited to Erin and Hannah. |
| Budget allocation does not make sense | Provide your preferred channel split or your historical CPL/CPA benchmarks per channel. The skill will adjust the allocation rationale accordingly. |

---

## Quick Reference

| Item | Detail |
|------|--------|
| **Command** | `/campaign-plan` |
| **Plugin** | {{COMPANY}} Marketing Plugin v1.5.0 |
| **Environment** | Claude Co-Work (Path A) |
| **Required inputs** | Campaign objective, target persona(s), timeline |
| **Recommended inputs** | Budget envelope, channels in scope, key message, constraints |
| **Output sections** | Campaign brief summary, audience segmentation, channel strategy, content calendar, KPIs and success metrics, creative and copy requirements |
| **Typical use cases** | New campaign launch, product launch planning, content calendar build, budget allocation, KPI definition |
| **Output format** | Structured brief in-conversation; can be copied to Notion or used as input for other skills |
| **Follow-on skills** | `/draft-content`, `/paid-search-optimizer`, `performance-marketer:creative-optimizer`, `performance-marketer:optimization-dossier`, `/linear-task-capture` |
