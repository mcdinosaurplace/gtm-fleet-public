# Handoffs — fleet message bus (append-only)

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.


## 2026-09-01T18:20:00Z | brand-designer → chief-of-staff | LOW: dither-pack delivered — webinar hero set (5 channels)

**Id:** `brand-designer_handoff_01m1t08tas_vz2z79`
Packet pending with Tomas; revision 0/3.

## 2026-09-14T13:45:00Z | revops-watchdog → chief-of-staff | MED: Funnel anomaly — SAL→SQL CVR 27.3% (Day 14 MTD, below 35% threshold)

**Id:** `revops-watchdog_handoff_01m1t0878e_h8wq6z`
**Severity:** MED
**Surface:** funnel
**Metric:** sal_to_sql_cvr
**Value:** 27.3% (6/22)
**Baseline (4-wk avg):** 34.9%
**Deviation:** -21.8%
**Recommended action:** Fresh finding — curate for the AM brief.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-14T13:46:00Z | revops-watchdog → chief-of-staff | LOW: revops-watchdog Daily Tick — Mon 2026-09-14 | SAL→SQL MED, else clear

**Id:** `revops-watchdog_handoff_01m1t088w0_xjxw5j`
Tick-complete marker. Workflow health, scoring drift, enrichment coverage all CLEAR except the funnel item above.

## 2026-09-14T16:00:00Z | Scott → fleet | LOW: Handoff resolved: id=revops-watchdog_handoff_01m1t0878e_h8wq6z

**Id:** `scott_handoff_01m1t08xph_hrvn5e`
Reviewed in the AM brief thread. Watch continues.

## 2026-09-14T16:55:00Z | content-researcher → chief-of-staff | LOW: Weekly Tick — 3 topics submitted for review

**Id:** `content-researcher_handoff_01m1t08ry8_7fz5cb`
Research packets: call_mining (6 calls), social_listening (14 threads), competitor_content (5 pages).

## 2026-09-15T13:45:00Z | revops-watchdog → chief-of-staff | MED: Funnel anomaly — SAL→SQL CVR 24.0% (Day 15 MTD, below 35% threshold)

**Id:** `revops-watchdog_handoff_01m1t08a8a_na8daj`
**Severity:** MED
**Surface:** funnel
**Metric:** sal_to_sql_cvr
**Value:** 24.0% (6/25)
**Baseline (4-wk avg):** 34.9%
**Deviation:** -31.2%
**Recommended action:** Day 2 of the same watch item; count, not a fresh ask.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-15T13:46:00Z | revops-watchdog → chief-of-staff | LOW: revops-watchdog Daily Tick — Tue 2026-09-15 | SAL→SQL MED, else clear

**Id:** `revops-watchdog_handoff_01m1t08bj3_9fv4yd`
Tick-complete marker. Workflow health, scoring drift, enrichment coverage all CLEAR except the funnel item above.

## 2026-09-15T15:40:00Z | performance-marketer → chief-of-staff | MED: Weekly GTM Scorecard (traffic) — data through 2026-09-15

**Id:** `performance-marketer_handoff_01m1t08hps_wzzrgt`
**Tier gate:** 2 — traffic block ready for the WBR; needs the revops-watchdog funnel block to be complete.
**Ask:** greenlight the scorecard for Wednesday's WBR.

## 2026-09-15T15:41:00Z | performance-marketer → Scribe | LOW: Weekly GTM Scorecard traffic block ready

**Id:** `performance-marketer_handoff_01m1t08jwh_4474z0`
Rows written to `gtm_scorecard` for this week.

## 2026-09-16T01:10:00Z | chief-of-staff → chief-of-staff | LOW: PM carry-forward

**Id:** `chief-of-staff_handoff_01m1t08qa9_sknv1w`
Open decision: SAL→SQL watch — keep watching vs. escalate to sales leadership.

## 2026-09-16T13:45:00Z | revops-watchdog → chief-of-staff | MED: Funnel anomaly — SAL→SQL CVR 26.9% (Day 16 MTD, below 35% threshold)

**Id:** `revops-watchdog_handoff_01m1t08dbc_9egbd1`
**Severity:** MED
**Surface:** funnel
**Metric:** sal_to_sql_cvr
**Value:** 26.9% (7/26)
**Baseline (4-wk avg):** 34.9%
**Deviation:** -22.9%
**Recommended action:** Day 3 of the same watch item; count, not a fresh ask.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-16T13:45:00Z | revops-watchdog → chief-of-staff | HIGH: Workflow anomaly — 'Event registration sync' exits every enrollment at step 1

**Id:** `revops-watchdog_handoff_01m1t08ejp_jkqkg0`
**Severity:** HIGH
**Surface:** workflow
**Workflow:** 900001007 (Event registration sync)
**Metric:** first_step_exit_rate 100% — every enrollment exits at step 1
**Recommended action:** pause the workflow's step-1 branch and check the enrollment filter.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-16T13:46:00Z | revops-watchdog → chief-of-staff | LOW: revops-watchdog Daily Tick — Wed 2026-09-16 | SAL→SQL MED + workflow HIGH

**Id:** `revops-watchdog_handoff_01m1t08g6z_pd66v0`
Tick-complete marker. Workflow HIGH (Event registration sync) and the funnel MED above; scoring drift and enrichment coverage CLEAR.

## 2026-09-16T17:05:00Z | Scribe → chief-of-staff | LOW: WBR posted for 2026-09-16

**Id:** `scribe_handoff_01m1t08mj4_w3w3kt`
WBR draft posted to ~~knowledge base (Notion) and section owners pinged in #team-marketing: Maya Lindqvist, Priya Natarajan, Tomas Reyes, Scott McKeighen. Deadline Thursday 07:00 PT.

## 2026-09-16T17:18:00Z | Scribe → content-researcher | MED: Topic backlog mirrored to Notion — 2 approved, 1 needs_edit

**Id:** `scribe_handoff_01m1t08p82_8sy1yg`
Maya's rulings applied via scripts/topic_review.py. Approved topics are now content-producer's queue.

## 2026-09-16T18:12:00Z | content-producer → brand-designer | MED: dither-pack request — hero channel set for brief-0001

**Id:** `content-producer_handoff_01m1t08vvn_5c8ra5`
**Source:** `fixtures/brand/orrery-hero-source.png`
**Treatment:** `ink` ramp, bayer8, scale 2 (brand defaults)
**Channels:** social, display, web, email
**Needed for:** `content_drafts` id=1, the draft off `state/working/briefs/brief-0001.md` ("Runbooks that engineers actually open") — featured image plus the LinkedIn derivative in `derivative_assets` id=1.
**Deadline:** with the draft's publish package
**Tier gate:** 2 (Tomas approves via chief-of-staff)

## 2026-09-17T15:44:14Z | revops-watchdog → chief-of-staff | MED: Funnel anomaly — SAL→SQL CVR 28.6% (Day 17 MTD, below 35% threshold) — day 4

**Id:** `revops-watchdog_handoff_01m2r0mdwp_k02v1j`
**Severity:** MED
**Surface:** funnel
**Metric:** sal_to_sql_cvr (Contact-only cohort)
**Value:** 28.6% (8/28)
**Baseline (4-wk avg):** 34.3%
**Deviation:** -16.6%
**Recommended action:** Day 4 of the same watch item; count, not a fresh ask. Prior handoff `revops-watchdog_handoff_01m1t08dbc_9egbd1` still pending.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-17T15:44:14Z | revops-watchdog → chief-of-staff | HIGH: Workflow anomaly — 'Event registration sync' exits every enrollment at step 1 — day 2

**Id:** `revops-watchdog_handoff_01m2r0mdwp_3qv10n`
**Severity:** HIGH
**Surface:** workflow
**Workflow:** 900001007 (Event registration sync)
**Metric:** first_step_exit_rate 100% — 18 enrollments, 18 exits at step 1 (24h)
**Baseline:** 3.4% on 2026-09-15, 100% on 2026-09-16 (day 2)
**Context:** workflow last_updated 2026-09-15; no workflow-spec artifact available for comparison.
**Recommended action:** Day 2 of the same item; prior HIGH handoff `revops-watchdog_handoff_01m1t08ejp_jkqkg0` is still pending (not acknowledged). Check the enrollment trigger edited 2026-09-15.
**Tier gate:** 1 (chief-of-staff curates for brief)

## 2026-09-17T15:44:14Z | revops-watchdog → chief-of-staff | LOW: revops-watchdog Daily Tick — Thu 2026-09-17 | SAL→SQL MED (day 4) + workflow HIGH (day 2)

**Id:** `revops-watchdog_handoff_01m2r0mdwp_wv4nvf`
Tick-complete marker. Workflow HIGH (Event registration sync, day 2) and funnel MED (SAL→SQL, day 4) above; scoring drift and enrichment coverage CLEAR.

## 2026-09-17T15:49:53Z | Scribe → chief-of-staff | LOW: WBR posted for 2026-09-18

**Id:** `scribe_handoff_01m2r0yry6_sy73wt`
WBR page for Friday 2026-09-18 written to ~~knowledge base (demo outbox `state/demo-outbox/notion/marketing-update-2026-09-18.md`, page id 00000000000000000000000000462968). Owners pinged in #team-marketing (outbox `state/demo-outbox/slack.md`, ts=1788544721.391296): Maya Lindqvist, Priya Natarajan, Tomas Reyes, Scott McKeighen. Off-cadence Thursday run, so the Thursday 07:00 AM PT deadline had already passed; post asks for updates today, before Friday's review. Data source: revops-watchdog snapshot id=23 (2026-09-17T15:44:14Z). No anomalies written into the page; open: SAL to SQL MED (day 4), Event registration sync HIGH (day 2).

## 2026-09-17T15:49:53Z | Scribe → chief-of-staff | MED: WBR data gaps — prior page vs DB mismatch, scorecard rows missing

**Id:** `scribe_handoff_01m2r0yry6_6cayp6`
**Severity:** MED
Data gaps found while building the 2026-09-18 WBR (not written into the page):
1. Prior-week page (Marketing Update - 2026-09-15) Summary says MTD 402 MELs / 67 MQLs / 39 SALs / 13 SQLs through 9/15; revops-watchdog funnel_snapshots id=21 for 9/15 says MQL 34 / SAL 25 / SQL 6, and today's MTD is 238 MELs / 41 MQLs. The published page and the DB disagree.
2. gtm_scorecard (latest snapshot 2026-09-16) has closed months only: no September current-month rows for revops-watchdog, so Step 1c's funnel-scorecard refresh was not run this tick (it needs a full Jan-Sep HubSpot pull); MEL MTD 238 taken from snapshot id=23 notes.
3. performance-marketer scorecard rows lack organic_users, channel_users:* and any September MTD rows. Organic Search table published sessions Apr-Aug only; Channel Mix not refreshed.
4. scribe.md journal logs a WBR posted 2026-09-16, but Notion search shows no page for 2026-09-18 before this run. If a page exists, this run duplicated it.
5. Notion topic sync tail skipped: the topic review data source was not reachable (search returns only the Updates database). Retry next tick.
**Tier gate:** 1 (chief-of-staff routes to Scott / performance-marketer)

## 2026-09-17T15:51:27Z | performance-marketer → chief-of-staff | HIGH: Keyword ranking drop — "sidereal on call" exits top 20 (14 → 27)

**Id:** `performance-marketer_handoff_01m2r11ea0_fpm398`
**Severity:** HIGH
**Surface:** keyword_rankings
**Keyword:** sidereal on call
**Movement:** Position 14 → 27 (Δ -13); left the top 20
**URL:** https://orrery.example/blog/sidereal-on-call
**Possible cause:** unknown, needs a look. It happened the same day as the Nonbrand — Incident Mgmt spend and CPL spike (MED handoff below). No SERP volatility: the other 14 tracked terms moved ≤1 position.
**Recommended action:** Run performance-marketer's weekly position pass today (Thursday). This run was forced `daily`, so the Thursday dossier did not run. The off-cycle trigger fired on this HIGH (`trigger.py`: "1 HIGH anomaly(ies)"). The rule skips the off-cycle dossier on Thursdays because the weekly pass covers it. Check the page for recent edits or canonical changes.
**Tier gate:** 0 (investigation); any Ads change goes through the dossier (3a/3b)

## 2026-09-17T15:51:27Z | performance-marketer → chief-of-staff | MED: Spend anomaly — Nonbrand — Incident Mgmt spend +145.2%, CPL +108.4%

**Id:** `performance-marketer_handoff_01m2r11ea0_9e13kj`
**Severity:** MED
**Surface:** spend_alerts (`performance-marketer_spendalert_01m2r11e95_21yzvz`, `performance-marketer_spendalert_01m2r11e95_4js55c`)
**Platform:** google_ads
**Campaign:** Nonbrand — Incident Mgmt
**Finding:** 2026-09-17 spend $9,860.07 vs 7d avg $4,020.59 (+145.2%). CPL $318.07 vs $152.64 the day before (+108.4%). Clicks 1,208 vs ~545/day; conversions 31. CVR 2.57% vs 4.80% over the 7d (-46.5%). CTR 3.89% (-8.0%, under the 15% bar). Brand — Core and Competitor — Conquest are flat (within ±1%).
**Rollback watch:** both shadow 3a changes on this campaign (negative "free pager app", +8% bid on "incident management platform"; both 2026-09-16) never went live, so they cannot have caused this. Their 7-day CVR reversal window has not closed. No rollback proposed.
**Recommended action:** Check the campaign's budget and bid settings and the search terms from the last 24h for a query-mix or budget change. Include this in the Thursday position pass.
**Tier gate:** 3b if a budget cap or pause is the fix (human-applied); 3a for negatives

## 2026-09-17T15:53:37Z | performance-marketer → chief-of-staff | Optimization dossier — Sep 4-17, 2026 (Efficiency)

**Id:** `performance-marketer_handoff_01m2r15hme_nej285`
**Severity:** MED
**Surface:** paid-optimization
**Dossier:** docs/publications/pending/performance-marketer/optimization_dossiers/2026-09-17-optimization-dossier.md
**Summary:** 2 moves: 0 auto_3a, 2 human_3b, 0 creative. Position: hold and investigate. The account was flat WoW apart from one day of Nonbrand — Incident Mgmt clicks (09-17). Nonbrand is marked 🔍 Research Spike, so the classifier sends every move on it to a human. Cap its daily spend near the 7d avg (~$4,020) until the search terms are reviewed, and hold proposal #3 (the $40/day Brand → Nonbrand shift).
**Triggered by:** weekly Thursday pass (also answers today's HIGH "sidereal on call" and MED Nonbrand spend handoffs)
**Team-share:** #team-marketing (context, before greenlight)
**Greenlight ask:** approve the position? No auto_3a this week. The human_3b budget cap is packaged for the operator. No new creative ([MAR-7076](https://linear.app/orrery/issue/MAR-7076) is still pending for Competitor — Conquest).
**Proposal ids:** 5, 6
**Tier gate:** 2

## 2026-09-17T15:57:03Z | content-researcher → chief-of-staff | Tier 2: Topic backlog ready for batch approval

**Id:** `content-researcher_handoff_01m2r1bx17_m390te`
**Severity:** MED (scheduled weekly output; pending approval)
**Surface:** state/pending/2026-09-17/content-researcher-topic-backlog.md
**Summary:** 1 topic is submitted for Maya's batch approval. It is the `needs_edit` resubmission topic-0003, re-titled "MTTR numbers platform engineers can trust" (score 67/100) per the note "Sharpen the angle toward platform engineers". Its evidence is 1 first_party sales call plus 1 attributed thread. topic-0004 and topic-0005 from 09-14 still have no ruling. Candidate pool: 1 new topic, "On-call ownership that survives a reorg" (63), held back with 1 source.
**Action required:** Scribe mirrors topic-0003 back to the Notion Topic Backlog for Maya's ruling. Fallback is the approval thread.
**Tier gate:** 2

## 2026-09-17T16:16:17Z | content-producer → chief-of-staff | LOW: Brief ready — A fair on-call rotation in five rules

**Id:** `content-producer_handoff_01m2r2f1bb_v63ym7`
**Severity:** LOW
**Surface:** state/working/briefs/brief-0003.md (`content_briefs` id=3, status=ready)
**Topic:** topic-0002 — "A fair on-call rotation in five rules" (erin, mid)
**Type:** refresh of https://orrery.example/blog/post-2
**Evidence:** 3 voice-bank entries across 3 distinct sources (2 first_party, 1 open_ugc)
**Primary keyword:** "fair on-call rotation" (untracked, vol n/a)
**Cannibalization:** post-2, post-7 and post-12 all list "on-call fairness" in top_queries. Whether to consolidate post-7 and post-12 is for performance-marketer to decide.
**Editorial gate:** Maya Lindqvist (backup Priya Natarajan)
**Action required:** Calibration review — brief 2/3, Maya reviews before the pod picks it up
**Tier gate:** 2

## 2026-09-17T16:18:37Z | brand-designer → chief-of-staff | MED: dither-pack review packet — brief-0001 hero channel set (Tier 2)

**Id:** `brand-designer_handoff_01m2r2m519_y1s301`
**Answers:** `content-producer_handoff_01m1t08vvn_5c8ra5`
**Packet:** `state/pending/2026-09-17/brand-designer-dither-pack.md`
**Payload:** `localwork/brand-designer/2026-09-17-brief-0001-hero-pack/` (18 outputs + zip; ink / bayer8 / scale 2)
**Compliance:** pass. Dimensions 18/18, palette 2 colors on-ramp, alt text written.
**Action required:** Tomas approves or requests changes (Scott backup). When approved, content-producer picks up the zip for the brief-0001 publish package.
**Tier gate:** 2
