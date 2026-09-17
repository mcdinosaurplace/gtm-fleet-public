# Brief: A fair on-call rotation in five rules

| | |
|---|---|
| **Topic ID** | topic-0002 (topic_backlog #2) |
| **Type** | refresh |
| **Content type** | blog (topic_backlog.content_type) — refresh of https://orrery.example/blog/post-2 (Erin, on-call fairness, published 2026-08-08): spec the delta, not a rewrite |
| **Target persona** | erin |
| **Tone code** | blog B |
| **Funnel stage** | mid |
| **Word-count target** | 1,000–1,400 (house blog band; no comparable ranking page in keyword_rankings) |
| **Topic score** | 84/100 · evidence quotes: 3 |

## Working titles
1. **A fair on-call rotation in five rules** ← recommended
2. On-call rotations that don't go to whoever shouts loudest
3. How to tell whether your on-call rotation is fair

## The educational job
The reader leaves with a written five-rule rotation policy they can adopt as-is, plus one fairness check they can run against last quarter's pages.

## Keywords
- **Primary:** fair on-call rotation (informational; matches mid funnel) — source: theme (rung 4). keyword_rankings has no fairness term and no search_volume values; the closest tracked term, "on call scheduling software" (pos 33), is commercial intent, which does not fit a mid-funnel education piece, so it is not used. No candidate-keyword handoffs from content-researcher exist (rung 2 empty).
- **Secondary:** on-call fairness, on-call rotation rules, how to keep on-call fair, on-call burnout

## AEO question set
- How do startups set up an on-call rotation for the first time? (register #7 · erin · bucket 4)
- How do engineering teams measure on-call fairness? (register #9 · hannah · bucket 2)
- How do engineering leaders reduce on-call burnout? (register #14 · hannah · bucket 4)
- How should on-call compensation work? (register #24 · On-Call Health & Fairness · hannah · bucket 4)
- How do other teams keep on-call fair without burning people out? (candidate — not in register; voice-bank #2)

## Outline (H2 / H3)
1. **Why rotations keep getting rebuilt** — answers: job (diagnosis) · evidence: voice-bank #21 (meeting:mtg-004); #2 as direction only
2. **The five rules** — answers: register #7 · evidence: per rule below
   - Rule 1: Every service has a named owner before it gets a pager (evidence: voice-bank #10, meeting:mtg-010)
   - Rule 2: Quiet weeks come from the schedule, not from negotiation (evidence: voice-bank #21, meeting:mtg-004)
   - Rules 3–5: each rule needs a primary source the pod finds and fact-checks. A rule with no source gets cut, and the title count changes to match. The pod never pads to five.
3. **How to measure whether your rotation is fair** — answers: register #9 · evidence: pod-sourced metric definition (see below); the fairness check is the reusable artifact
4. **Burnout and compensation** — answers: register #14, #24 · evidence: pod-sourced primary references; voice-bank #2 as direction only
5. **Setting up your first rotation** — answers: register #7 · evidence: the five rules turned into a starter policy the reader can copy
<!-- SERP features to target: PAA — earned by section 3. -->

## Evidence bundle (verbatim — from topic_evidence → voice_bank)
- [quote · erin · mid] "We rebuilt the rotation three times this year; whoever shouts loudest gets the quiet weeks. (#21)" (meeting:mtg-004 · first_party · voice-bank #21)
- [quote · aaron · top] "We page everyone because nobody knows who owns the service. (#10)" (meeting:mtg-010 · first_party · voice-bank #10)
- [question · erin · mid] "How do other teams keep on-call fair without burning people out? (#2)" (thread:0002 · open_ugc · voice-bank #2) [open_ugc — do not publish]

### Additional evidence the pod must source + fact-check
- A defensible definition of on-call load (pages per engineer per shift, off-hours pages, or similar), sourced from a primary SRE or practitioner reference, for section 3.
- A primary source for each of rules 3–5; unsourced rules are removed.
- Compensation practices (register #24) from a named survey or published policy. No invented percentages.
- A copyable starter rotation policy or schedule config for section 5. Any Orrery product capability it references must be checked against current docs, because overclaiming is a hard fail.

## Internal links (from content_inventory)
- **Link to:** https://orrery.example/blog/post-1 — alert fatigue; the "page everyone" failure behind Rule 1
- **Link to:** https://orrery.example/blog/post-5 — tool sprawl, Erin; the ownership gap across tools
- **Link from:** https://orrery.example/blog/post-7 and https://orrery.example/blog/post-12 — both are on-call fairness posts (Aaron, Hannah) and should point at the refreshed piece
- **Cannibalization:** warns: post-2, post-7 and post-12 all list "on-call fairness" in top_queries (gsc). This brief refreshes post-2 instead of adding a fourth competing page. Consolidation of post-7 and post-12 is a performance-marketer call, flagged in the handoff.

## Refresh delta (refresh pieces only)
- **Existing piece:** https://orrery.example/blog/post-2
- **What this adds:** turns general content into prescriptive rules; adds a fairness measurement section (register #9) and burnout/compensation answers (register #14, #24); adds a copyable starter policy (register #7); grounds the piece in first-party call evidence (mtg-004, mtg-010). Inventory titles are placeholders, so the pod must read post-2 before drafting to confirm the delta holds.

## CTA
Mid funnel, Erin: take the five rules as a starter policy, then see how Orrery on-call scheduling applies them. No demo ask at this stage; the pod verifies the destination page exists before linking.

---
*Built by content-producer:brief-builder from topic_backlog #2. Status set per the
calibration gate. Creation-pod: draft strictly from this brief and its evidence.*
