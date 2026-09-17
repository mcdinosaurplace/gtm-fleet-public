# content-researcher — Journal

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.


## 2026-09-07T16:55:00Z | Weekly Tick

### Anchor
Monday 2026-09-07 · week of 2026-09-07.

### MCP Preflight
~~meeting notes (Grain) → bound · WebSearch → available · ~~issue tracker (Linear) → bound (optional).

### Migration
none pending.

### Handoffs Processed
none addressed to content-researcher.

### Research Sweep
call_mining: 6 calls hosted by Leo Marchetti or Dana Whitfield, 4 mined, 1 empty, 1 skipped (vendor inbound) · social_listening: 14 threads · competitor_content: 5 pages (Beaconline, Rostrum).
Voice bank +12 entries (trust tiers: first_party / attributed / open_ugc). Dedup against `content_inventory` (15 live posts): 1 refresh candidate.

### Backlog Delta
5 topics in backlog: 3 submitted for review, 2 candidates.

### Handoffs Written
- content-researcher → chief-of-staff | LOW | Weekly Tick — 3 topics submitted for review

## 2026-09-14T16:55:00Z | Weekly Tick

### Anchor
Monday 2026-09-14 · week of 2026-09-14.

### MCP Preflight
~~meeting notes (Grain) → bound · WebSearch → available · ~~issue tracker (Linear) → bound (optional).

### Migration
none pending.

### Handoffs Processed
Scribe → content-researcher: rulings pre-applied (2 approved, 1 needs_edit) — read, not re-applied.

### Research Sweep
call_mining: 6 calls hosted by Leo Marchetti or Dana Whitfield, 4 mined, 1 empty, 1 skipped (vendor inbound) · social_listening: 14 threads · competitor_content: 5 pages (Beaconline, Rostrum).
Voice bank +20 entries (trust tiers: first_party / attributed / open_ugc). Dedup against `content_inventory` (15 live posts): 1 refresh candidate.

### Backlog Delta
8 topics in backlog: 2 approved → content-producer queue, 1 briefed, 1 needs_edit (angle toward platform engineers), 2 submitted, 1 candidate, 1 rejected.

### Handoffs Written
- content-researcher → chief-of-staff | LOW | Weekly Tick — 3 topics submitted for review

## 2026-09-17T15:57:36Z | Weekly Tick

### Anchor
Thursday 2026-09-17 · September · Q3 2026. Run off-cadence (the schedule is Mondays). Harness mode: sync, migrations and commit are left to `scripts/tick.py`.

### MCP Preflight
~~meeting notes (Grain) → bound (fixture, DEMO_MODE, 1 probe) · ~~crm (HubSpot) → bound (fixture) · WebSearch → not used (DEMO_MODE).

### Handoffs Processed
- Scribe → content-researcher (2026-09-16T17:18Z): the rulings were already applied, so I read them without re-applying. topic-0001 and topic-0002 are approved; topic-0003 is `needs_edit` with the note "Sharpen the angle toward platform engineers". The rulings match approvals row 2 (approved 2026-09-16T17:15Z by Maya Lindqvist), so there is no sync defect.
- No rejections since the last Tick. topic-0008 is still rejected ("Too close to a vendor comparison"); no cluster this week matched it.

### Research Sweep
[call_mining] → 1 call, 6 new entries (1 prospect / 0 customer). Packet id 4.
quiet_week=1 (LOW): 6 entries, under 10. Grain had only 1 external call in the window since 2026-09-14T16:50Z.
Skipped: 0 off-target · Deferred: 0
Classification: prospect_sales (HubSpot contact lifecycle=lead, Director of Platform Engineering) · host gate passed (AE) · company_size mid · persona aaron. Quotes are anonymized to a role/segment label; the competitor name Beaconline is kept.
Themes: oncall_fairness_burnout 1 · stakeholder_trust_anxiety 1 · automation_chain_breaks 1 · competitor_mention 1 · untagged 2 (CSV schedule export for compliance; runbook length). No theme has more than 2 entries.
Not stored: "A yes or no by Thursday is enough." This is deal logistics, not market voice. Note for the sales lane: the prospect wanted a yes or no on rotation-survives-rename by Thursday (today). That is outside my lane and is not handed off.
HubSpot: bound.
social-listening: skipped (DEMO_MODE — live web sweeps disabled)
competitor-content-scan: skipped (DEMO_MODE). There is no fixture corpus for competitor pages, so the scan was skipped rather than simulated, following social-listening §DEMO_MODE.
Stale packets: none. The social_listening and competitor_content packets are 3 days old.

### Backlog Delta
- "MTTR numbers platform engineers can trust" (topic-0003) → score 67/100: ICP 21 · AEO 12 · Ev 11 · Edu 12 · Search 11. Evidence: 1 first_party call + 1 attributed thread. This is the `needs_edit` topic re-clustered per Maya's note: same uid, persona hannah → aaron, back to submitted. It overlaps the live post-3/8/13 "MTTR reporting" posts. I kept it `submitted` rather than `refresh` so the ruling loop closes; the refresh overlap is noted in the draft.
- "Postmortems that change behavior" (topic-0004) → +1 first_party evidence link (Beaconline "postmortem workflow felt bolted on"). Scores and status are unchanged; it still has no ruling.
- "On-call ownership that survives a reorg" → score 63/100: ICP 23 · AEO 14 · Ev 5 · Edu 16 · Search 5 — new, `content-researcher_topic_01m2r1bg8c_q3ewne`. It is held as `candidate` because it has a single source, even though the prospect called it a signing blocker. Call-miner should listen for it.
- "Why paging everyone is a design failure" (topic-0001, approved) and "Runbooks that engineers actually open" (topic-0007, briefed) → evidence links only, for brief-builder. Status and scores are untouched.
- "CSV schedule export for compliance" → about 23/100, a product requirement with no editorial angle. Logged, not inserted.
- Open_ugc-only clusters blocked: none this week.
- Data defects in the seeded backlog (LOW, not corrected, for the operator):
  - score_search on topics 1–8 is 15–18, but the rubric caps it at 15.
  - Several seed topic_evidence links are off-topic. topic-0004 links to paging/MTTR quotes. topic-0003 links to an on-call fairness thread, which I excluded from its evidence count (2, not 3).
  - topic-0006 (68) is `candidate` even though its score is above the floor.
  - Seed voice_bank themes use free-text labels, not the shared vocabulary.

### Handoffs Written
- MED (Tier 2) Topic backlog ready for batch approval: 1 topic, state/pending/2026-09-17/content-researcher-topic-backlog.md → chief-of-staff (`content-researcher_handoff_01m2r1bx17_m390te`, pending)
- Candidate keywords → performance-marketer: none (no question-shaped phrasings). AEO prompts → Scott: none.
- Harness: session=37d77f95-b21b-4288-80a9-a5a7916bcbcc turns=29 cost=$2.41
