# Paid Search Optimizer — Team SOP

**Version:** 1.0
**Owner:** Marketing / Demand Gen
**Tool:** {{COMPANY}} Marketing Plugin → `/paid-search-optimizer`

---

## What This Is

The Paid Search Optimizer is an AI-powered weekly workflow built into Cowork. You feed it a Google Ads CSV and tell it what you're trying to achieve, and it produces new headline and description variations — optimized, brand-compliant, and ready to upload to Google Ads Editor.

It runs two sub-agents in parallel: one writes headlines (≤30 chars each), one writes descriptions (≤90 chars each). Every variation is checked against {{COMPANY}}'s brand voice before it lands in your output files.

**The two things you need every time:**
1. A Google Ads CSV export (see Section 1)
2. An optimization direction — one clear sentence (see Section 2)

Without both, the tool will ask you for the missing piece before doing anything.

---

## Section 1: Pulling the Right CSV from Google Ads

### Which report to use

You want the **Ads report** — not the Keywords report, not the Campaigns report. The Ads report is the only one that exposes individual headline and description text alongside performance metrics.

### Step-by-step: Google Ads UI export

1. Log in to [ads.google.com](https://ads.google.com) and select your account.
2. In the left sidebar, click **Ads & assets** → **Ads**.
3. Use the **campaign filter** (top of the table) to scope your export:
   - To run one specific campaign: filter by that campaign name
   - To run a specific ad group: filter by campaign, then ad group
   - To run the full account: leave filters cleared
4. Set your **date range** to the last 7, 14, or 30 days (14 days recommended — enough data to surface patterns without being stale).
5. Click the **Columns** button (top right of the table) and make sure these columns are visible. Add any that are missing:

| Column | Where to find it |
|--------|-----------------|
| Campaign | Default — always present |
| Ad group | Default — always present |
| Headline 1 through Headline 15 | Attributes → Ad content |
| Description 1 through Description 4 | Attributes → Ad content |
| Final URL | Attributes → Ad content |
| Impressions | Performance |
| Clicks | Performance |
| CTR | Performance |
| Avg. CPC | Performance |
| Conversions | Performance |
| Conv. rate | Performance |
| Quality score | Quality score (may require adding separately) |

6. Click **Download** (the down arrow icon, top right) → select **CSV (.csv)** → download.

> **Tip:** Quality Score can be tricky to export — it only appears when you're looking at the Ads view (not keywords). If it's missing from your export, the optimizer will flag it and proceed with the metrics it has.

### Step-by-step: Google Ads Editor export

If you use Google Ads Editor for bulk management, you can also export from there:

1. Open Google Ads Editor → select the account/campaign.
2. In the left panel, select **Ads** under the relevant campaign.
3. Click **File → Export → Current view as CSV**.
4. The column names may differ slightly (e.g., "Ad Group Name" vs. "Ad group") — the optimizer handles common naming variations automatically.

### What to do if columns are missing

The optimizer will note any missing columns in its report. The minimum viable export requires: Campaign, Ad group, at least Headline 1–3, Description 1–2, Final URL, Impressions, Clicks, and CTR. Everything else adds precision but isn't a blocker.

---

## Section 2: Writing an Effective Optimization Direction

The direction is the single most important input after the CSV. It tells the optimizer what to prioritize in its analysis and how to angle the new copy. A vague direction produces generic output. A sharp direction produces copy that's ready to test.

### Direction taxonomy

Use one of these proven directions, or combine elements from two:

| Direction | When to use it | Example phrasing |
|-----------|---------------|-----------------|
| **Optimize for CTR** | Ads are getting impressions but low click-through | "Optimize for CTR — focus on `Nonbrand — Incident Mgmt`" |
| **Optimize for conversions** | Clicks are decent but demos or signups are low | "Improve conversion rate on `Competitor — Conquest` — it converts at 2.7% against 5.5% on brand" |
| **Reduce CPC** | Cost per click is running above budget | "Reduce CPC in `Nonbrand — Incident Mgmt` — it's running $7.43 against $4.20 on brand" |
| **Founder POV shift** | Copy feels corporate or feature-heavy, needs energy | "Shift the `Nonbrand — On-Call Scheduling` ads to founder POV — Erin persona, removal-first" |
| **Campaign theme alignment** | Running a launch or seasonal push, ads don't reflect it | "Align all ads to the Rotation Studio launch — 'Your rotation belongs in version control'" |
| **Brand voice cleanup** | Ads contain fear language or competitor-adjacent framing | "Clean up brand voice — remove any cost-of-downtime math or 'never miss an alert' language from all active ads" |
| **Persona shift** | Ads are hitting platform engineers but should be hitting engineering leaders, or vice versa | "Shift `Nonbrand — Incident Mgmt` ads from Aaron to Hannah — MTTR, SLA, and rotation-fairness framing" |

### What makes a good direction

**Be specific about scope.** Name the campaign or ad group if you're not running the full account. The optimizer handles scoping automatically based on what's in the CSV — but if your direction targets a specific group, call it out.

> Good: "Optimize for CTR in the `Nonbrand — Incident Response` ad group"
> Too broad: "Make the ads better"

**Include context if you have it.** If you know last week's test results, or you're aligning to a specific message from a campaign brief, put that in the direction. The optimizer uses prior hypothesis data when it's available.

> Good: "Optimize for CTR — question-format headlines won last week at 4.2% vs 1.8% for benefit-first, so lean into that"
> Missing context: "Optimize for CTR again"

**One direction per run.** Don't try to optimize for CTR and do a persona shift in the same pass. Pick the priority, run it, measure, then tackle the next one.

> Good: "Founder POV shift across the `Nonbrand — On-Call Scheduling` ads"
> Conflicting: "Optimize CTR and also do a brand voice cleanup and shift to Erin persona"

**Avoid vague adjectives.** The optimizer needs something it can operationalize — a metric, a persona, a theme, or a specific problem.

> Good: "Improve conversion rate — we think descriptions are too feature-heavy and not CTA-forward enough"
> Not actionable: "Make them more compelling"

### Guardrails built into the tool

These are enforced regardless of your direction — you don't need to specify them:

- **No competitor names** will appear in generated copy ({{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_D}}, {{COMPETITOR_G}}, {{COMPETITOR_B}}, {{COMPETITOR_F}}, {{COMPETITOR_H}}, {{COMPETITOR_E}}, {{COMPETITOR_I}}, {{COMPETITOR_M}})
- **No fear-based reliability language** — "never miss an alert," "downtime is not an option," "sleep soundly," cost-of-downtime math, and outage-shaming are all blocked
- **Character limits are hard-checked** — every headline is verified ≤30 chars, every description ≤90 chars before it lands in output
- **{{COMPANY}} personas** default to Aaron (platform engineer) for the nonbrand category ad groups; Hannah (VP Engineering) for conquest and leadership ad groups; Erin (technical founder) for on-call scheduling and free-tier ad groups

---

## Section 3: Running the Optimizer in Cowork

1. Open Claude in Cowork mode.
2. Type `/paid-search-optimizer` (the plugin must be installed — ask Scott if you don't have it).
3. The tool will confirm it's ready. If you haven't uploaded the CSV yet, it will ask for it.
4. Upload your CSV file by dragging it into the chat or using the attachment button.
5. When prompted for the optimization direction, type your direction (see Section 2).
6. The tool will confirm both inputs and start the run:
   > CSV received ✓
   > Direction: [your direction restated]
   > Running optimization pass…
7. Wait for it to finish — it runs headline and description sub-agents in parallel, so the full pass usually completes in under a minute.

### What you get back

Three output files saved to your marketing folder:

| File | What it is |
|------|-----------|
| `ads-optimization-report-[date].md` | Full analysis — tiered ad prioritization, top performer patterns, diagnosis for each ad, and new headline/description variations |
| `ads-new-variations-[date].csv` | Upload-ready CSV formatted for Google Ads Editor bulk import |
| `ads-optimization-log.md` | Running hypothesis log — updated with this week's changes and testable predictions |

### Uploading variations to Google Ads

1. Open **Google Ads Editor** and sync your account.
2. Go to **File → Import → From CSV**.
3. Select `ads-new-variations-[date].csv`.
4. Review the import preview — spot check 2–3 ads to confirm headlines and descriptions look right.
5. Click **Apply** to stage the changes, then **Post** to push live.

> **Note:** The upload CSV is structured for Editor's bulk import format. Do not open it in Excel and save before uploading — Excel sometimes reformats CSV files in ways that break the import.

---

## Section 4: The Weekly Loop

This tool is designed as a repeatable weekly ritual, not a one-off fix. Here's how the loop works:

**Week 1:** Run the optimizer → new variations go live → hypotheses logged
**Week 2:** Pull fresh CSV → start a new run → tool checks for last week's log and asks if you want to incorporate results → bake winning patterns into this week's copy → update log with outcomes

The hypothesis log (`ads-optimization-log.md`) accumulates over time. As patterns are confirmed or disproven, the optimizer uses that history to weight its recommendations. The longer you run it, the sharper it gets.

**Suggested weekly cadence:**

- **Monday:** Pull CSV from the past 7 days → run optimizer → review output
- **Tuesday:** Upload variations to Google Ads Editor → post to live
- **Following Monday:** Pull fresh data → start next run → check prior hypotheses

---

## Section 5: Troubleshooting

**"I don't have a CSV but I know an ad is tanking — can I still use it?"**
Yes. You can describe the ad manually (campaign name, ad group, current headline text, current performance) and the optimizer will generate new variations based on what you tell it. You won't get the full tiered analysis, but you'll get on-brand copy with a diagnosis.

**"Quality Score isn't in my export."**
The optimizer will note it as missing and run on the other metrics. To add it: in the Google Ads UI, go to Columns → Competitive metrics → Quality Score. Save that column configuration before your next export.

**"The upload CSV broke when I opened it in Excel."**
Use the CSV directly from your marketing folder — don't open, edit, and re-save in Excel. If you need to preview it, open it in Numbers or Google Sheets (read-only), then use the original file for the Ads Editor import.

**"The optimizer asked me for a direction but I'm not sure what to pick."**
Start with "Optimize for CTR" if you're not sure — it's the most universal starting point and surfaces copy problems quickly. You can always run a persona or theme direction in the next pass.

---

## Appendix: Sample CSV Template

The file `templates/google-ads-sample-template.csv` contains:
- Correct column headers in the expected order
- 3 example rows, one per live campaign — `Brand — Core` (the high performer: 6.51% CTR, $4.20 CPC, Quality Score 9), `Nonbrand — Incident Mgmt` (the refresh candidate: 4.18% CTR, $7.43 CPC, Quality Score 7), and `Competitor — Conquest` (the rewrite candidate: 3.12% CTR, $9.51 CPC, Quality Score 5)
- Each row is a 14-day aggregate for one ad, so you can see the shape a real export takes
- Values you can replace with your own data

Use it as a reference if your export is missing columns or if you want to manually build a CSV for a specific ad group.

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
