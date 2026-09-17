# {{COMPANY}} Funnel Architecture

Operating summary of the lifecycle for GTM-Ops tasks. The definitional authority is
`docs/lead-lifecycle-model.md` — where this file and that one disagree, that one wins
and this one is the defect.

## Lifecycle Stage Path

```
Prospect → Marketing Engaged → Marketing Qualified Lead → Sales Accepted Lead →
Sales Qualified Lead → Sales Accepted Opportunity → Customer

Detours (reachable from several active stages): Nurture · Unqualified
```

### Stage Definitions

| Stage | Definition | Metric stamped | Primary Owner |
|-------|-----------|----------------|---------------|
| Prospect | CRM record exists, no engagement signal yet | — | Marketing |
| Marketing Engaged | First meaningful marketing engagement (content, event, site conversion) | MEL | Marketing |
| Marketing Qualified Lead | Meets the sales-ready bar — handraiser, score threshold, or outbound-sourced | MQL | Marketing → *(handoff)* |
| Sales Accepted Lead | Sales has accepted the lead and is pursuing a meeting | SAL | Sales |
| Sales Qualified Lead | A meeting is successfully booked after pursuit | SQL | Sales |
| Sales Accepted Opportunity | Qualified open deal carrying pipeline value | — (Active Open Pipeline) | Sales |
| Customer | An associated deal is Closed Won | — | Sales → CS |
| Nurture | Warm but not ready — a timing or priority pause, not a fit problem | — | Marketing |
| Unqualified | Out of fit, out of region, or explicitly disqualified | — | Sales |

**Handoff point:** MQL → SAL. Marketing owns everything through MQL; Sales owns from SAL on.

**Two layers, always:** a *stage* is the contact's current state (one at a time); a
*metric* is a date-stamped entry event (many over time). Never report a stage count as a
metric.

### Known Issues with Current Lifecycle

- **Self-serve and sales-led share one funnel.** A workspace that signs up and routes a
  real service never passes through Marketing Engaged in the usual way; product-led
  records can appear at MQL with a thin engagement history.
- **PQL is defined but unused.** Product-usage qualification exists as a lifecycle value
  with no telemetry wired into the CRM, so it stays empty. Do not design against it yet.
- **Detour re-entry is lossy.** A record that goes to Nurture and returns re-stamps its
  `*_date__latest_` properties, so a past month's cohort can restate.
- **Routing is brittle when enrichment is missing.** Engineering-headcount-band routing
  fails on unenriched records and falls through to a single default owner.
- **Legacy stage names still circulate** in older decks ("Value Identified", "Demo &
  Business Case", "Proposal", "Quote & Signing"). They are not live stages. Map them to
  the deal stages below before using them in any analysis.

### Lead Routing Logic (Current)

1. Incoming MQL triggers the assignment workflow
2. `~~crm` checks territory and engineering-headcount band from the enrichment cascade
3. If criteria match → assign to the owning AE
4. If no match (missing enrichment) → default owner, and the record is flagged for enrichment backfill
5. Proposed: if no match → round robin among active AEs, with the enrichment flag retained

---

## Deal Pipeline (inside Sales Accepted Opportunity)

Once a contact reaches Sales Accepted Opportunity, progress is tracked on the **deal**
object, not the contact lifecycle.

| Order | Deal stage | Expected max days in stage | Flag beyond |
|-------|-----------|---------------------------|-------------|
| 1 | Discovery Requested | 7 | 14 days → MED |
| 2 | Discovery Scheduled | 14 | 21 days → MED |
| 3 | Demo Requested | 10 | 21 days → MED |
| 4 | Demo Scheduled | 14 | 21 days → MED |
| 5 | Selection | 21 | 30 days → MED |
| 6 | Contract Negotiations | 21 | 30 days → MED |
| 7 | Quote Sent | 14 | 21 days → MED |
| 8 | Onboarding / Ramp Up | — (post-sale implementation) | not a selling stage |
| 9 | Closed won / Closed lost | — | terminal |

Thresholds are planning defaults for this profile, not measurements. Defer to actual
stage-history data whenever it is available.

**Contact ↔ deal crosswalk:** SQL = a deal at Discovery Scheduled or later · Sales
Accepted Opportunity = an open deal in an active selling stage carrying value · Customer
= a deal at Closed won.

---

## Primary Buyer Personas

Full persona files live in `context/personas/`.

### Aaron the Platform Engineer (Primary — technical champion)
- Staff Platform Engineer, SRE Lead, Infrastructure Engineer, Head of Platform
- Mid-market B2B SaaS, roughly 50–500 engineers
- Evaluates by reading provider docs and running a shadow rotation before booking a demo
- Discovery: peer reliability communities, public postmortems, open-source tooling threads

### Erin the Technical Founder (Primary — self-serve entry)
- Founder, CTO, co-founder at Series A or earlier, 5–40 engineers
- Is the escalation policy today; buys, evaluates, and gets paged, all as one person
- Sole decision-maker and budget owner; converts self-serve or not at all
- Discovery: founder communities, developer forums, referrals

### Hannah the VP Engineering (Primary — business buyer)
- VP/Head/Director of Engineering at Series B–C, roughly 90–200 engineers
- Owns the uptime number, on-call policy, and engineering retention
- Shared buying decision across Platform, Security, and Finance
- Discovery: engineering-leadership peer networks, conference hallways, analyst-free word of mouth

---

## Attribution Model

- **Primary**: Multi-touch attribution in `~~crm`
- **First-touch**: for awareness effectiveness — read the write-once `*___initial` UTM family
- **Last-touch**: for conversion-trigger analysis — read the live `utm_*` family
- **Gap**: no product usage data in the CRM yet, so self-serve activation is invisible to attribution
- **Reporting**: source-to-pipeline and multi-touch in `~~crm`, cross-checked against
  `~~web analytics`, on a monthly cadence

---

## Data Hygiene Known Issues

- Duplicate contact and company records, concentrated in event and list imports
- Product workspaces are not unified with CRM companies — no shared key
- Enrichment coverage is uneven; engineering-headcount band is the field most often missing
- Free-tier signups arrive with personal email domains and no company association
- No product usage data in the CRM yet (planned: product telemetry integration)

---

## Funnel Conversion Benchmarks (Use as Planning Defaults)

Invented planning defaults for this profile — not measurements. Always defer to actual
`~~crm` data when it is available, and say which you used.

| Transition | Typical Rate |
|-----------|-------------|
| MEL → MQL | 20–35% |
| MQL → SAL | 45–65% |
| SAL → SQL | 35–55% |
| SQL → Sales Accepted Opportunity | 50–70% |
| Sales Accepted Opportunity → Customer | 20–30% |
