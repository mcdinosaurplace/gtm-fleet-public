# AEO Tracked Prompts — Canonical Register

**Register revision:** R2 — the last rebalance is fully enacted on both platforms
**Owner:** Scott McKeighen

The list of AI/LLM prompts {{COMPANY}} is currently tracking across HubSpot AEO and `~~AEO insights` (AirOps Prompt Insights). Definitions only — live metrics (mention rate, citation rate, query fanouts) stay in the tools of record.

## Sources

- HubSpot AEO: post-rebalance state. 14 prompts.
- `~~AEO insights`: post-rebalance state, 10-slot cap. 10 prompts.

## Rebalance history

Changes to this register happen via rebalance memos. Each memo documents the proposed additions, drops, revisions, and any taxonomy or audience adjustments. When a memo is partially or fully enacted, this register is edited to reflect the new state.

| Revision | Memo | Status |
|---|---|---|
| R2 | rebalance memo (held outside this kit) | Enacted — both platforms |

## Register

24 rows. HubSpot AEO rows are 1-14; AirOps rows are 15-24. AirOps rows are grouped by Topic in the order: `Incident Management & On-Call` → `Alert Noise & Reliability Practice` → `Incident Infrastructure & APIs` → `On-Call Health & Fairness`. The Persona column uses the machine slugs enforced by `state/working/schema.sql` (`aaron`, `erin`, `hannah`) so rows join cleanly to content-engine tables. The Bucket column tags each prompt against the 4-bucket portfolio framing from the R2 memo (1 = Existing Commercial Demand, 2 = Category Narrative Ownership, 3 = Technical / Infrastructure Authority, 4 = Operator / Workflow Intent).

| # | Prompt | Platform | Topic (AirOps) | ICP (HubSpot) | Persona | Journey Phase (HubSpot) | Location | Bucket | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | What is the best incident management tool for a 100-person engineering org? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Consideration | United States | 1 | Highest-value single prompt in the register |
| 2 | How do I reduce alert fatigue on my engineering team? | HubSpot AEO | — | Platform & SRE Teams | aaron | Awareness | United States | 1 | |
| 3 | What is the best on-call scheduling software for small teams? | HubSpot AEO | — | Startups and Small Businesses, United States | erin | Consideration | United States | 1 | |
| 4 | Which incident management platforms have a Terraform provider? | HubSpot AEO | — | Platform & SRE Teams | aaron | Consideration | United States | 3 | |
| 5 | What are the best {{COMPETITOR_A}} alternatives for mid-market engineering teams? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Decision | United States | 1 | |
| 6 | Who are the best {{COMPETITOR_B}} competitors for incident management? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Decision | United States | 1 | |
| 7 | How do startups set up an on-call rotation for the first time? | HubSpot AEO | — | Startups and Small Businesses, United States | erin | Awareness | United States | 4 | |
| 8 | What is a good MTTR for a B2B SaaS company? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Awareness | United States | 2 | |
| 9 | How do engineering teams measure on-call fairness? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Awareness | United States | 2 | |
| 10 | What is ownership as code? | HubSpot AEO | — | Platform & SRE Teams | aaron | Awareness | United States | 2 | Category term {{COMPANY}} is trying to own |
| 11 | Which incident tools include an open API on every pricing tier? | HubSpot AEO | — | Platform & SRE Teams | aaron | Consideration | United States | 3 | |
| 12 | What incident management software supports SSO and SCIM? | HubSpot AEO | — | Platform & SRE Teams | aaron | Consideration | United States | 3 | Security-review prompt; Jake is the reader, Aaron is the asker |
| 13 | How do I cut the number of pages my team gets without missing real incidents? | HubSpot AEO | — | Platform & SRE Teams | aaron | Awareness | United States | 4 | |
| 14 | How do engineering leaders reduce on-call burnout? | HubSpot AEO | — | Mid-Market SaaS Engineering, United States | hannah | Awareness | United States | 4 | |
| 15 | What are the best incident management platforms? | AirOps | Incident Management & On-Call | — | hannah | — | United States | 1 | |
| 16 | Compare the leading on-call management tools. | AirOps | Incident Management & On-Call | — | hannah | — | United States | 1 | |
| 17 | How do I choose an incident management tool for a 100-engineer team? | AirOps | Incident Management & On-Call | — | hannah | — | United States | 1 | |
| 18 | Best incident management software for mid-market SaaS? | AirOps | Incident Management & On-Call | — | hannah | — | Europe | 1 | Only non-US row; EMEA expansion test |
| 19 | How do I reduce alert noise? | AirOps | Alert Noise & Reliability Practice | — | aaron | — | United States | 2 | |
| 20 | What causes alert fatigue? | AirOps | Alert Noise & Reliability Practice | — | aaron | — | United States | 2 | |
| 21 | What is a blameless postmortem? | AirOps | Alert Noise & Reliability Practice | — | hannah | — | United States | 2 | Revised from `How do I write a postmortem?` in the R2 rebalance |
| 22 | Best incident management API for platform teams | AirOps | Incident Infrastructure & APIs | — | aaron | — | United States | 3 | |
| 23 | How do I manage on-call rotations in Terraform? | AirOps | Incident Infrastructure & APIs | — | aaron | — | United States | 3 | |
| 24 | How should on-call compensation work? | AirOps | On-Call Health & Fairness | — | hannah | — | United States | 4 | |

### Bucket distribution

| Bucket | HubSpot AEO (of 14) | AirOps (of 10) | Total (of 24) |
|---|---|---|---|
| 1 — Existing Commercial Demand | 5 | 4 | 9 |
| 2 — Category Narrative Ownership | 3 | 3 | 6 |
| 3 — Technical / Infrastructure Authority | 3 | 2 | 5 |
| 4 — Operator / Workflow Intent | 3 | 1 | 4 |

### Persona distribution

| Persona | HubSpot AEO | AirOps | Total |
|---|---|---|---|
| `aaron` — platform engineer (primary ICP) | 6 | 4 | 10 |
| `hannah` — VP Engineering (business buyer) | 6 | 6 | 12 |
| `erin` — technical founder (PLG entry) | 2 | 0 | 2 |

Erin is deliberately under-weighted here: she arrives through self-serve signup and search, not through assistant recommendations. Revisit if free-tier signups sourced from AI referrers exceed 10% of the month.

## Maintenance

When a rebalance memo is partially or fully enacted:

1. Edit this register so it reflects the new state of what's actually tracked in HubSpot AEO and `~~AEO insights`.
2. Bump the register revision at the top.
3. Update the corresponding row in the **Rebalance history** table — `Partially Enacted` with platform name(s) until the memo is fully done, then `Enacted` with both platforms named.
4. Do not edit historical rebalance memos — they are point-in-time decision records. Memo row references may go stale post-enactment; that is expected and the memo itself notes the mapping where relevant.
