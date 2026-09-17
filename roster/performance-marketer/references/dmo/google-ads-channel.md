# Google Ads Channel Reference

## Metric Definitions & Benchmarks

| Metric | What it means | Strong | OK | Weak |
|--------|--------------|--------|----|------|
| CTR (search) | Clicks ÷ Impressions | >5% | 2–5% | <2% |
| CTR (display/discovery) | Clicks ÷ Impressions | >0.5% | 0.2–0.5% | <0.2% |
| Avg. CPC | Average cost per click | <$3 (B2B SaaS varies widely) | — | >$15 for general terms |
| Conv. Rate | Conversions ÷ Clicks | >5% | 2–5% | <2% |
| Quality Score | Google's 1–10 ad relevance score | 7–10 | 5–6 | 1–4 |
| Search Impression Share | % of eligible impressions captured | >60% | 30–60% | <30% |
| Cost / Conversion | Spend ÷ Conversions | Context-dependent | — | >$150 for SaaS demo |
| ROAS | Revenue ÷ Ad Spend | >400% | 200–400% | <200% |

**B2B SaaS / incident management context:** {{COMPANY}} competes in a mid-to-high-CPC category against better-funded incumbents. Category head terms — "incident management platform," "incident management software," "incident response tools" — run **$8–$25 CPC**; the on-call cluster — "on call scheduling software," "on call rotation software" — runs **$6–$15** and converts better at the small-team end. Anything below $8 CPC on a category head term is a Quality Score win worth protecting.

Two benchmark exceptions specific to this account:

- **Brand CTR reads low and that is expected.** Most B2B SaaS brand campaigns clear 15% CTR. `Brand — Core` runs closer to 6–7% because the bare brand term collides with the astronomical instrument and pulls encyclopedic intent into the auction. Judge brand health on Quality Score (currently 9) and impression share (~72%), not CTR — and keep the exact-match set qualified ("{{company_slug}} incident management," "{{company_slug}} on call," "{{company_slug}} pricing").
- **Conquest conversion rate will look weak against the table.** `Competitor — Conquest` converts at ~2–3% against a 2–5% "OK" band. That is the going rate for switching intent in a category where migration means re-pointing every alert source; judge it on trial starts, not on the raw rate.

---

## RSA (Responsive Search Ad) Creative Limits

| Element | Character limit | Notes |
|---------|----------------|-------|
| Headline | **30 characters** | Up to 15 per RSA; Google recommends at least 8–10 populated |
| Description | **90 characters** | Up to 4 per RSA; at least 2 required |
| Final URL | No character limit | Must match display URL domain |
| Display path | 15 chars each (2 paths) | Optional; shown as "domain/path1/path2" |

Count characters precisely. "On-Call Without the Noise" = 25 chars; "Clear Ownership, Fast Fixes" = 27 chars (including the comma and space). When in doubt, count manually — Google Ads Editor will reject over-limit assets.

**Ad Strength:** Google rates ads from "Poor" to "Excellent" based on headline/description variety. Aim for at least 10 distinct headlines and 3–4 descriptions to hit "Good" or above. Vary the angles — some should be feature-based, some outcome-based, some question-format.

---

## Bid Strategy Quick Reference

| Strategy | When to use | Objective mode | Requires |
|----------|-------------|----------------|----------|
| **Target CPA** | Maximize conversions at a fixed cost | Pipeline, Efficiency | 30+ conversions/30 days in campaign |
| **Target ROAS** | Maximize revenue at a fixed return | Efficiency (revenue-focused) | Revenue tracking set up, 50+ conv/30 days |
| **Maximize Conversions** | Get as many conversions as possible within budget | Pipeline | No minimum — good for scaling a new campaign |
| **Maximize Conversion Value** | Maximize total revenue, not volume | Efficiency (value-weighted) | Revenue values assigned to conversions |
| **Manual CPC** | Full bid control; useful when testing or when Smart Bidding is learning | Any | Ongoing management attention |
| **Enhanced CPC** | Manual with Smart Bidding adjustments | Transition to smart bidding | Some conversion history |
| **Target Impression Share** | Dominate for brand terms | Awareness | — |
| **Maximize Clicks** | Drive traffic volume (top-of-funnel) | Awareness | — |

**Smart Bidding learning period:** After changing bid strategies, expect 1–2 weeks of performance instability. Don't panic-adjust during this window. The "Bid Strategy Status" column in Google Ads shows if a strategy is still learning.

**Target CPA guidance for {{COMPANY}}:**
- New campaigns without conversion data: start with Maximize Conversions until you hit 30+ conversions, then switch to Target CPA
- Set Target CPA at ~20% above your historical CPA to give the algorithm room to learn
- If actual CPA is running >50% above target for 2+ weeks, Target CPA is set too aggressively

---

## Export Instructions (14-Day Ads Report)

1. Log in to ads.google.com → select account
2. Left sidebar → **Ads & assets** → **Ads**
3. Set date range to **last 14 days**
4. Click **Columns** → ensure these are visible:
   - Campaign, Ad group, Headline 1–15, Description 1–4, Final URL
   - Impressions, Clicks, CTR, Avg. CPC, Cost, Conversions, Conv. rate, Quality Score
   - (Optional) Search Impression Share, Search Lost IS (budget), Search Lost IS (rank)
5. Click the download icon → **CSV** → download

**For WoW analysis:** The optimizer splits this CSV at day 7 automatically. If you want sharper segmentation, export two separate 7-day CSVs (label them `week1.csv` and `week2.csv`) and upload both.

---

## {{COMPANY}}-Specific Campaign Structure Context

**Live campaigns (the names the export will carry):**
- **Nonbrand — Incident Mgmt** / ad group *Nonbrand — Incident Response* — the category motion; highest volume and highest CPC. Primary persona: Hannah, evaluating "the best incident management tool for a 100-person engineering org." Aaron arrives here too, on the provider and API long tail. Lands on `/product/incident-response`.
- **Brand — Core** / ad group *Brand — Exact* — protect qualified brand terms; Target Impression Share ≥85%. Primary persona: whoever the other two campaigns already reached. Lands on `/`.
- **Competitor — Conquest** / ad group *Competitor — Alternatives* — bidding on competitor keywords (e.g., "{{COMPETITOR_A_LOWER}} alternative," "{{COMPETITOR_B_LOWER}} vs {{company_slug}}," "{{COMPETITOR_C}} pricing," "{{COMPETITOR_D_LOWER}} alternative"). Primary persona: Hannah at renewal, Aaron doing the migration math. Lands on `/compare`. Naming competitors in headlines and descriptions is standard conquesting practice for these campaigns and is explicitly **not a brand violation**. The general rule prohibiting competitor names applies to brand content and non-competitor campaigns only. See the competitor campaign exception in `prompt.md` Step 3.

**Next campaign (not yet live):**
- **Nonbrand — On-Call Scheduling** — "on call scheduling software" is the closest category win available (striking distance in the ranking watch) and the cheapest half of the CPC band. Primary persona: Erin — she signs up on the free tier the same session, so the conversion action is trial start, not demo request. Do not stand this up inside `Nonbrand — Incident Mgmt`; the clinical and trade negatives it needs are large enough to distort the parent campaign's match data.

**Product-line map** (a campaign owns a surface; a surface owns a landing page):

| Surface | Campaign home | Landing page | Persona |
|---|---|---|---|
| Response Rooms | Nonbrand — Incident Mgmt | `/product/incident-response` | Hannah |
| Signal Grouping | Nonbrand — Incident Mgmt | `/product/signal-grouping` | Aaron |
| Ownership Graph | Nonbrand — Incident Mgmt | `/product/ownership-graph` | Aaron |
| Rotation Studio | Nonbrand — On-Call Scheduling (planned) | `/product/rotation-studio` | Erin |
| Learning Loops | Organic only — no paid intent worth bidding | `/product/learning-loops` | Hannah |
| Fairness Report | Organic only — no paid intent worth bidding | `/product/fairness-report` | Hannah |

Learning Loops and Fairness Report stay out of paid on purpose: nobody searches for them by name, and the queries that lead to them ("blameless postmortem," "on call compensation") are job-seeker-adjacent or already ours organically.

**Keyword intent tiers:**
- High intent: "incident management platform," "on call scheduling software," "incident response tools," "{{COMPETITOR_A_LOWER}} alternative"
- Mid intent: "best incident management tools," "how to reduce alert noise," "on call rotation best practices," "terraform on call rotation"
- Research intent: "what is mttr," "error budget," "blameless postmortem," "incident severity levels"

Focus Pipeline mode budget on high-intent tier. Efficiency mode cuts research-intent first — and research intent is where {{COMPANY}} already ranks, so cutting it costs less than it looks.
