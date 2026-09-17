# performance-marketer — Journal

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.


## 2026-09-15T15:30:00Z | Daily Tick (Wed) + Scorecard Pass

### Environment
PERFORMANCE_MARKETER_EXECUTE=off (shadow) · DEMO_MODE · ~~ads (Google Ads) data via fixtures/CSV · ~~web analytics (GSC) via CSV.

### Data Pulls
spend-14d.csv → `paid_creative` 84 rows · gsc-7d.csv → `keyword_rankings` 20 keywords (4 weekly snapshots on file).

### Spend Check — 2026-09-15 vs 7d avg
Brand — Core $1,540 (+18%) LOW · Nonbrand — Incident Mgmt $3,624 (+2%) CLEAR · Competitor — Conquest $1,134 (-5%) CLEAR.

### Keyword Snapshot
20 tracked · 3 WATCH flags (≥3 positions lost WoW) · best mover: "orrery terraform provider" 4 → 1.

### Weekly Analysis — Scorecard Pass (Wednesday)
Traffic block written to `gtm_scorecard` (8 metrics × 8 months, definition v1.5). Funnel block expected from revops-watchdog. Position pass produced 4 proposals: 2 auto_3a (greenlit, shadow), 1 human_3b (change list), 1 creative (awaiting copy review, MAR-7076).

### Handoffs Written
- performance-marketer → chief-of-staff | MED | Weekly GTM Scorecard (traffic) — Tier 2 greenlight ask
- performance-marketer → Scribe | LOW | Weekly GTM Scorecard traffic block ready

### State
`spend_alerts` +1 · `paid_change_proposals` +4 · `applied_changes` +1 (shadow).

## 2026-09-16T15:30:00Z | Daily Tick (Wed)

### Environment
PERFORMANCE_MARKETER_EXECUTE=off (shadow) · DEMO_MODE · ~~ads (Google Ads) data via fixtures/CSV · ~~web analytics (GSC) via CSV.

### Data Pulls
spend-14d.csv → `paid_creative` 84 rows · gsc-7d.csv → `keyword_rankings` 20 keywords (4 weekly snapshots on file).

### Spend Check — 2026-09-16 vs 7d avg
Brand — Core $1,265 (-6%) CLEAR · Nonbrand — Incident Mgmt $4,508 (+27%) **MED** · Competitor — Conquest $1,113 (-6%) CLEAR.

### Keyword Snapshot
20 tracked · 3 WATCH flags (≥3 positions lost WoW) · best mover: "orrery terraform provider" 4 → 1.

### Rollback Watch
Shadow bid change on "incident management platform" — CVR holding (6.0% vs 6.1%), no reversal trigger.

### Handoffs Written
- none (watch only)

### State
`spend_alerts` +1 · `paid_change_proposals` unchanged · `applied_changes` unchanged.

## 2026-09-17T15:52:04Z | Daily Tick (Thu, forced daily)

### Environment
PERFORMANCE_MARKETER_EXECUTE=off (shadow) · DEMO_MODE · ~~ads (Google Ads) via fixture CSV · ~~web analytics (GSC) via fixture CSV. Anchor: Thu 2026-09-17, Sep, Q3 2026. Handoffs since 2026-09-16T15:30Z: none addressed to performance-marketer; noted Scribe MED (scorecard rows lack organic_users / channel_users / Sep MTD), which gets fixed in the next scorecard pass.

### Data Pulls
spend-14d.csv → `paid_creative` +42 campaign-aggregate rows (2026-09-04..09-17) · gsc-7d.csv → `keyword_rankings` +15 rows (2026-09-17).
Data note: the fixture aggregates for 09-08..09-16 disagree with the older seeded ad-level (`enabled`) rows for the same days (e.g. Nonbrand 09-16 aggregate $3,968.70 vs seeded $4,507.79). The baselines below use the aggregate series only. The 09-16 MED alert came from the seeded series.
LinkedIn: no spend source. The HubSpot PAID_SOCIAL lead-flow check was not run (no ~~crm tool used this Tick).

### Spend Check — 2026-09-17 vs 7d avg (09-10..09-16)
Brand — Core → spend $2,428.94 (baseline $2,439.60, Δ -0.4%) · CPL $75.90 (-0.7% DoD) · CLEAR
Nonbrand — Incident Mgmt → spend $9,860.07 (baseline $4,020.59, Δ +145.2%) **MED**
Nonbrand — Incident Mgmt → CPL $318.07 (prior $152.64, Δ +108.4% DoD) **MED** · CTR 3.89% (-8.0%, under the 15% bar) · CVR 2.57% vs 4.80% (-46.5%)
Competitor — Conquest → spend $1,907.20 (baseline $1,911.72, Δ -0.2%) · CPL $381.44 (-1.5%) · CLEAR

### Keyword Snapshot
sidereal on call → position 27 (prior: 14, Δ -13) **HIGH**: left the top 20; also over the >10 MED bar. Cause unknown.
on call scheduling software → 33 (prior 32, Δ -1) · incident management platform, best incident management tools, what is mttr, incident severity levels → +1 each · 9 terms unchanged.
No SERP volatility (1 term moved >5). 15 of 20 tracked terms came back in today's pull. The 5 branded terms (orrery pricing / login / on call / incident management / terraform provider) are missing from the GSC fixture, so they have no snapshot today.

### Rollback Watch
applied_changes 1 (negative "free pager app") and 2 (+8% bid "incident management platform"), both shadow as of 2026-09-16. Reversal rule is "CVR drops >20% over 7 days". The campaign's CVR fell 46.5% today, but the changes were never live, so they can't be the cause, and the 7-day window is still open. Not tripped; no rollback proposed.

### Off-Cycle Position Trigger
`should_form_position` → trigger=True (1 HIGH: sidereal on call). Today is Thursday, which is the position day, so no off-cycle dossier. But this run was forced `daily`, which also skipped the weekly pass. The HIGH handoff asks for the weekly position pass today.

### Handoffs Written
- HIGH "sidereal on call" exits top 20 (14 → 27) → chief-of-staff (`performance-marketer_handoff_01m2r11ea0_fpm398`)
- MED Nonbrand — Incident Mgmt spend +145.2% / CPL +108.4% → chief-of-staff (`performance-marketer_handoff_01m2r11ea0_9e13kj`)

### State
`spend_alerts` +2 (MED, open) · `keyword_rankings` +15 (1 flagged HIGH) · `paid_creative` +42 · `handoffs` table +2 (pending) · `paid_change_proposals` / `applied_changes` unchanged.
- Harness: session=ec671003-ec7b-4f7b-9464-c1ca0330dd3a turns=23 cost=$1.58

## 2026-09-17T15:54:20Z | Position Pass (Thu, forced weekly)

### Environment
PERFORMANCE_MARKETER_EXECUTE=off (shadow) · DEMO_MODE · harness run. Anchor: Thu 2026-09-17, Sep, Q3 2026. Handoffs since 15:52:04Z: none addressed to performance-marketer.

### Spend Check
The daily Tick already ran at 15:52:04Z. spend-watch and ranking-watch were not re-run, because a second run would have duplicated both `spend_alerts` and the HIGH/MED handoffs. Today's results carry over: Nonbrand — Incident Mgmt spend +145.2% / CPL +108.4% (MED, 2 open alerts). Brand — Core and Competitor — Conquest are CLEAR.

### Keyword Snapshot
Carried over from 15:52:04Z: "sidereal on call" 14 → 27 (HIGH, left the top 20). No SERP volatility. This is an organic issue, so it is out of scope for the paid dossier. The page check (recent edits / canonical) is still open.

### Weekly Analysis
Pull: google-ads-14d.csv (DMO ad-level by day, 84 rows, 09-04..09-17). GA4 7d pull skipped (landing-page-review not run this pass).
WoW (09-11..09-17 vs 09-04..09-10), account: spend $64,376.15 vs $58,422.78 (+10.2%) · conv 448 vs 443 (+1.1%) · CPL $143.70 vs $131.88 (+9.0%).
- 🔍 Nonbrand — Incident Mgmt: spend +20.6%, CPL $178.90 vs $151.48 (+18.1%), CVR 4.21% vs 4.82%. All of the increase came on 09-17: clicks 1,208 vs ~545/day, IS unchanged at 41.2%, 31 conv. Both ads moved together (CTR 4.13%), so this is not ad-level.
- 🟡 Competitor — Conquest: flat. CPL $381.93, QS 5, IS 27.7%. Copy refresh [MAR-7076](https://linear.app/orrery/issue/MAR-7076) is still awaiting_creative.
- 🟢 Brand — Core: flat. CPL $76.31, QS 9.
Search-terms-miner: NOT RUN. DEMO_MODE has no search-terms report fixture, so no negatives or match-type promotions are proposed. This gap blocks confirming H1.
Creative-optimizer: no new creative moves, so no variations and no creative_variations draft.
Scored hypotheses: experiment #1 (outcome vs feature headline) INCONCLUSIVE, because it is shadow-only and variant B never served. Rollback: applied_changes #1/#2 are shadow. Nonbrand CVR is -12.7% WoW, under the 20% bar, and the window closes 09-23. Not tripped.
Dossier: docs/publications/pending/performance-marketer/optimization_dossiers/2026-09-17-optimization-dossier.md. 2 moves, both human_3b via classify.py (research-spike rule): (5) cap Nonbrand daily spend near ~$4,020 pending search-terms review; (6) hold proposal #3, the $40/day Brand → Nonbrand shift. Objective assumed Efficiency, carried from the prior pass.
Hypotheses for next week: H1, the 09-17 spike is a query-mix shift (>=40% of clicks on new queries); H2, the cap brings CPL back under $160 within 5 days with <10% conversion loss.
Note: the dossier renderer printed MAR-7076 as a bare id, so it was patched to a link after the render. dossier.py should link Linear refs found in diagnosis text.

### Handoffs Written
- MED Optimization dossier — Sep 4-17, 2026 (Efficiency) → chief-of-staff (`performance-marketer_handoff_01m2r15hme_nej285`; handoffs table row pending)

### State
`paid_change_proposals` +2 (ids 5, 6, proposed, human_3b) · `handoffs` table +1 · `spend_alerts` / `keyword_rankings` / `paid_creative` / `experiments` unchanged this pass.
- Harness: session=1d2336c6-e853-4dcf-8bb2-c6c9c58b2b28 turns=28 cost=$1.65
