# Email Sequence — Team SOP

**Version:** 1.0
**Owner:** Marketing / Demand Gen
**Applies to:** Marketing team members using Claude Co-Work
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 → `/email-sequence`

---

## What This Is

The `/email-sequence` skill designs and drafts multi-email sequences for nurture flows, onboarding campaigns, drip campaigns, re-engagement, and event follow-ups. You provide a brief describing the sequence goal and audience; the skill returns a full sequence map plus per-email drafts with subject lines, preview text, body copy, and CTAs. {{COMPANY}}'s HubSpot workflows are the delivery mechanism for all sequences produced by this skill.

**Time to complete:** ~15-30 minutes (brief + review, varies by sequence length)

---

## Section 1: Prerequisites

Before invoking the skill, confirm the following:

- **Claude Co-Work is open** with the {{COMPANY}} Marketing Plugin v1.5.0 active. This is Path A (Co-Work), not Claude Code.
- **Plugin is enabled.** Verify `/email-sequence` is available by typing `/` in any Co-Work conversation. If it does not appear, re-enable the {{COMPANY}} Marketing Plugin in your Co-Work settings.
- **HubSpot access confirmed.** You or someone on your team will need to build the resulting workflow in HubSpot. Confirm who owns the build step before starting.
- **No sequence currently live for this audience.** Check HubSpot for existing active workflows targeting the same enrollment trigger or segment before generating a new sequence. Do not duplicate active sequences.

Have the following ready before you write your brief:

- The sequence goal (what action should the recipient take by end of sequence?)
- Target audience or persona
- Enrollment trigger (what qualifies someone to enter the sequence?)
- Approximate length preference, or "recommend for me"
- Any existing sequences to reference or avoid duplicating

---

## Section 2: What to Include in Your Sequence Brief

The quality of the brief determines the quality of the output. This is the most important step.

Every brief should include:

- **Sequence type** — nurture, onboarding, demo follow-up, re-engagement, event/webinar follow-up, or product announcement drip
- **Target persona** — Erin (founder/CEO, 10-200 person company), Hannah (VP Engineering, scaling team), or a specific segment (e.g., "free trial users, days 0-30")
- **Enrollment trigger** — the event or condition that adds someone to the sequence (e.g., form fill on the demo page, deal stage moves to "Demo Completed," trial start date, webinar attended)
- **Sequence goal** — the action you want the recipient to take by the end (e.g., book a demo, complete onboarding step 3, register for the event, re-engage with product)
- **Number of emails and cadence** — specify (e.g., "5 emails over 14 days") or request a recommendation ("recommend based on sequence type")
- **Tone preference** — educational, conversational, or promotional
- **Topics to cover** — key points, product features, objections to address, or resources to reference
- **Topics to avoid** — competitor mentions, pricing specifics, anything under legal or marketing review

### Example brief (MQL nurture)

```
Sequence type: MQL nurture
Target persona: Erin — founder or CEO at a 10-200 person company, evaluating project management tools
Enrollment trigger: MQL status reached (HubSpot lifecycle stage = MQL, no demo booked in last 30 days)
Sequence goal: Book a product demo
Number of emails: 4-5 emails over 10-12 business days
Tone: Conversational and direct. Not salesy. Educational with a clear CTA in each email.
Topics to cover: How {{COMPANY}} solves cross-functional visibility, async-first work management, customer proof points, easy onboarding
Topics to avoid: Competitor names, pricing
```

---

## Section 3: Reading the Sequence Output

The skill returns output in two parts: the sequence map first, then per-email drafts. Review them in order.

**Sequence map**

The map shows the full sequence structure before you read any email copy. Check:

- **Timing makes sense.** Delays between emails should fit the urgency of the sequence type. Onboarding sequences move fast (days); re-engagement sequences move slowly (weeks).
- **Enrollment logic is accurate.** Confirm the trigger described in the map matches what you specified and what HubSpot can actually execute.
- **Branching is achievable in HubSpot.** The skill may recommend if/then branching based on opens or clicks (e.g., "If Email 2 is opened but link not clicked, send Email 3A; if link is clicked, skip to Email 4"). Verify that your HubSpot plan supports workflow branching before committing to this structure.
- **Exit conditions are present.** Confirm the map includes suppression or exit logic (e.g., "exit if demo is booked," "exit if contact unsubscribes").

**Per-email drafts**

Each email draft includes subject line, preview text, full body copy, and primary CTA. Check:

- **Subject line length.** Keep subject lines under 50 characters for mobile. Flag anything over 60 characters for revision.
- **Preview text.** Should complement the subject line, not repeat it. Aim for 85-100 characters.
- **CTA specificity.** Each email should have one clear CTA. Vague CTAs ("learn more") should be made specific ("See how Erin's team cut standups by half").
- **Body length appropriate to position in sequence.** Email 1 (intro) and Email 4-5 (re-engagement/break-up) are typically shorter. Middle emails can carry more detail.
- **Tone consistency.** Read the sequence end-to-end to confirm voice does not shift between emails.

Revision requests work best when specific. Stay in the same conversation thread:

- "Email 3 is too long — cut to under 150 words."
- "The subject line for Email 1 is too generic — try a version with a specific pain point."
- "Email 4 feels too promotional — soften the tone and lead with a case study reference instead."

---

## Section 4: Building the Sequence in HubSpot

After the sequence is approved, the workflow build in HubSpot follows this general flow. Reference HubSpot workflow documentation for platform-specific steps.

1. **Create a new workflow** in HubSpot (Marketing > Automation > Workflows). Use "Contact-based" workflow type for all sequences produced by this skill.
2. **Set the enrollment trigger** to match the enrollment logic from the sequence map. Use the exact contact properties, list memberships, or lifecycle stage transitions specified.
3. **Add emails to the workflow** using delays between each send. Match the timing to the sequence map. Use "Business days" delays unless the sequence specifies calendar days (e.g., onboarding sequences often use calendar days to align with trial timing).
4. **Configure branching logic** if the sequence map includes if/then paths. Build each branch with the correct open or click conditions and route contacts to the appropriate email variant or skip step.
5. **Set suppression lists.** Add the suppression lists recommended in the sequence output. At minimum: already-a-customer, demo-booked, unsubscribed, hard-bounced.
6. **Set exit conditions.** Add goal-based or property-based exit triggers (e.g., "lifecycle stage = SQL," "meeting booked = true") so contacts leave the sequence when the goal is met.
7. **Run `/email-qa` on every email** before activating. Do not activate the workflow until all emails pass QA.

---

## Section 5: QA Before Activating

Every email in the sequence must pass `/email-qa` before the workflow goes live. This is not optional.

- Run each email through `/email-qa` individually. Copy and paste the subject line, preview text, and body copy for each email into the QA skill one at a time.
- Do not activate the HubSpot workflow until all emails in the sequence have passed.
- If an email fails QA, revise in the Co-Work conversation thread and re-run QA on the revised version.
- GTM Ops (Scott) must review and approve any workflow in HubSpot before it is turned on. Tag Scott in the relevant Linear ticket when all emails are QA-cleared and the workflow is built.

---

## Section 6: Troubleshooting

| Problem | Fix |
|---------|-----|
| Output emails are too similar to each other | Ask the skill for more variation in angle and hook. Specify: "Each email should open with a distinct hook — vary between question, data point, customer story, and direct statement." |
| HubSpot branching logic does not match the sequence output | Simplify the branching in your next prompt (e.g., "remove the open-based branch and make this a linear 4-email sequence"), or escalate the workflow build to GTM Ops. |
| Sequence feels too long for the goal | Ask for a condensed version: "Condense this to 3 emails that hit the same goal. Keep the strongest subject lines and CTAs." |
| Timing seems off | Specify calendar days vs. business days explicitly in your brief or revision request. The default assumption may not match your workflow setup. |
| Branching recommended but HubSpot plan does not support it | Ask the skill to output a linear version of the sequence that achieves the same result without conditional branching. |
| Enrollment trigger cannot be built in HubSpot as described | Describe your HubSpot constraint to the skill and ask for an alternate enrollment approach. Escalate to GTM Ops if a workaround is not straightforward. |
| Copy does not match {{COMPANY}} brand voice | Add to your next message: "Revise against {{COMPANY}} brand voice: clear, direct, no em-dashes, no words like leverage, utilize, streamline, robust, or comprehensive." |

---

## Quick Reference

| Item | Detail |
|---|---|
| **Command** | `/email-sequence` |
| **Tool** | {{COMPANY}} Marketing Plugin v1.5.0 in Claude Co-Work (Path A) |
| **Required inputs** | Sequence type, target persona, enrollment trigger, sequence goal, tone preference |
| **Optional inputs** | Number of emails and cadence (or request a recommendation), topics to cover, topics to avoid |
| **Sequence types supported** | MQL nurture, onboarding, demo follow-up, re-engagement, event/webinar follow-up, product announcement drip |
| **Output structure** | Sequence map (timing, enrollment logic, branching, suppression) + per-email drafts (subject line, preview text, body copy, primary CTA) |
| **Delivery mechanism** | HubSpot workflows |
| **QA requirement** | All emails must pass `/email-qa` before HubSpot workflow activation |
| **HubSpot activation** | Requires GTM Ops (Scott) approval before turning on |

**HubSpot activation checklist**

- [ ] All emails approved by copy reviewer
- [ ] All emails passed `/email-qa`
- [ ] Workflow built in HubSpot with correct enrollment trigger
- [ ] Delays set (confirm calendar days vs. business days)
- [ ] Branching configured (if applicable)
- [ ] Suppression lists added
- [ ] Exit conditions set
- [ ] GTM Ops reviewed and approved
- [ ] Workflow activated

---

*Questions? Ping Scott or drop a note in #marketing-demand-gen.*
