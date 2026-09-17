# Lifecycle Map — Q2-2026 Snapshot

**Period represented:** Q2 2026 (end-of-quarter close, 2026-06-30).
**Captured:** from model **v1.0.0** (`docs/lead-lifecycle-model.md`).
**Definitions locked:** SAL/SQL cohort method as of scorecard v1.1 (`roster/funnel-stats/prompt.md`); human definitions per `docs/gtm-scorecard-definitions.md`.
**Living version:** [`docs/lead-lifecycle-model.md`](./lead-lifecycle-model.md) — always consult that for the current model.
**Owner:** Scott (marketing operations)

> **What this file is.** A point-in-time record of the lead lifecycle model as it
> stood at the close of Q2 2026, captured from model v1.0.0. Kept for historical
> reference and as the machine-readable map consumed by `revops-watchdog:lifecycle-audit`
> (which globs `docs/lifecycle-map-*.md` and reads the most recent). Do **not**
> edit this file to change the model — edit the living doc
> ([`lead-lifecycle-model.md`](./lead-lifecycle-model.md)) and cut a new dated
> snapshot.

---

## The two-layer model

{{COMPANY}}'s funnel has two layers, and conflating them is the source of most
historical confusion:

| Layer | What it is | Cardinality |
|-------|-----------|-------------|
| **Lifecycle stage** | The *current state* of a contact record in HubSpot | A contact has exactly **one** at a time |
| **Funnel metric** | A *date-stamped event* recording entry into a stage, counted monthly | A contact accumulates **many** over time |

A stage is a state; a metric is a dated event. They are not the same object.

---

## 1. Canonical lifecycle stages (ordered)

Real HubSpot `lifecyclestage` values, in forward order.

| Order | Stage (HubSpot label) | Internal value | Metric stamped | Owner | Required properties |
|-------|------------------------|----------------|----------------|-------|---------------------|
| 1 | Prospect | `{{HUBSPOT_WORKFLOW_ID_4}}` | — | Marketing | — |
| 2 | Marketing Engaged | `{{HUBSPOT_WORKFLOW_ID_1}}` | MEL | Marketing | `mel_date` |
| 3 | Marketing Qualified Lead | `marketingqualifiedlead` | MQL | Marketing → *(handoff)* | `mql_date__latest_`, `mql_type_latest` |
| 4 | Sales Accepted Lead | `{{HUBSPOT_WORKFLOW_ID_2}}` | SAL | Sales | `sal_date__latest_`, `mql_date__latest_` |
| 5 | Sales Qualified Lead | `salesqualifiedlead` | SQL | Sales | `sql_date__latest_`, `sal_date__latest_`, ≥1 associated deal |
| 6 | Sales Accepted Opportunity | `opportunity` | — (Active Open Pipeline) | Sales | ≥1 open deal on pipeline `{{HUBSPOT_PIPELINE_ID}}` at Stage 1+ |
| 7 | Customer | `customer` | — (deal Closed Won) | Sales → CS | associated deal at Closed Won `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` |

> **Skip detection for SAO & Customer:** these stamp no contact date property (they
> are deal-derived), so entry must be verified via **deal association** (open deal
> on `{{HUBSPOT_PIPELINE_ID}}`; Closed Won `{{HUBSPOT_STAGE_CLOSED_WON_ID}}`), not a stage-date comparison.

### Regression / terminal states (off the forward path — do **not** flag as backward transitions)

| State | HubSpot value | Rule |
|-------|---------------|------|
| Nurture | `{{HUBSPOT_WORKFLOW_ID_3}}` | Legitimate reverse/hold edge; re-engagement returns to Marketing Engaged or MQL. |
| Unqualified | `{{HUBSPOT_WORKFLOW_ID_5}}` | Terminal ("Disqualified"); entry from any active stage is legitimate. |

### Legacy / redundant contact stages (present in HubSpot, not part of the canonical funnel)

`Subscriber` (`subscriber`), `Lead` (`lead`), `Product Qualified Lead`
(`{{HUBSPOT_WORKFLOW_ID_6}}`), `Evangelist` (`evangelist`), `Other` (`other`). Flagged for RevOps
consolidation; `Prospect`/`Subscriber`/`Lead` are frequently confused.

---

## 2. Stage definitions

#### 1. Prospect — `{{HUBSPOT_WORKFLOW_ID_4}}`
- **Meaning:** First-time CRM record; cold; no engagement yet.
- **Entry:** New contact record created (import, enrichment, form without engagement, manual).
- **Exit:** Any brand engagement → Marketing Engaged.
- **Owner:** Marketing.

#### 2. Marketing Engaged — `{{HUBSPOT_WORKFLOW_ID_1}}`
- **Meaning:** ≥1 meaningful engagement action.
- **Entry:** Engagement/conversion event (email click, download, event registration, return visit) or re-engagement.
- **Exit:** Qualifies as MQL → Marketing Qualified Lead; or Nurture; or Unqualified.
- **Owner:** Marketing. **Metric:** MEL (`mel_date`, first entry).

#### 3. Marketing Qualified Lead — `marketingqualifiedlead`
- **Meaning:** Enough intent/fit to warrant Sales attention (sales-ready).
- **Entry:** One of three mandatory MQL paths — **P1 Handraiser** (explicit intent: demo/pricing/reply), **P2 Score Threshold** (lead score), **Outbound** (sales-sourced).
- **Exit:** Sales accepts → Sales Accepted Lead; or Nurture; or Unqualified.
- **Owner:** Marketing (Marketing → Sales handoff point). **Metric:** MQL (`mql_date__latest_` + `mql_type_latest`).

#### 4. Sales Accepted Lead — `{{HUBSPOT_WORKFLOW_ID_2}}`
- **Meaning (Q2-2026):** Sales accepts the lead and pursues a meeting — acceptance and active pursuit, *before* a meeting exists.
- **Entry:** A rep accepts the MQL and begins pursuing a meeting.
- **Exit:** Meeting booked → Sales Qualified Lead; or Nurture; or Unqualified; (deal layer → Closed Lost).
- **Owner:** Sales. **Metric:** SAL (`sal_date__latest_`).

#### 5. Sales Qualified Lead — `salesqualifiedlead`
- **Meaning (Q2-2026):** A meeting is successfully booked after pursuit. (Scorecard header "SQLs (Meeting Scheduled)" — Meeting Booked = Meeting Scheduled.)
- **Entry:** A meeting is booked/scheduled.
- **Exit:** Qualified into an opportunity → Sales Accepted Opportunity; or Unqualified; (deal layer → Closed Lost).
- **Owner:** Sales. **Metric:** SQL (`sql_date__latest_`).
- **Note:** The meeting *being held* is not a lifecycle stage — it is the deal event **Meetings Held** (`demo_done_date`).

#### 6. Sales Accepted Opportunity — `opportunity`
- **Meaning:** Fit + need confirmed; a real deal exists with pipeline value (Stage 1+).
- **Entry:** Qualification met; deal logged at Stage 1+ on pipeline `{{HUBSPOT_PIPELINE_ID}}`.
- **Exit:** Closed Won (→ Customer) or Closed Lost (deal layer).
- **Owner:** Sales. **Metric:** none as a count; measured by Active Open Pipeline. "SAO" is the stage acronym, not a reported count.

#### 7. Customer — `customer`
- **Meaning:** An associated deal is signed; record is a customer.
- **Entry:** A deal reaches Closed Won (`{{HUBSPOT_STAGE_CLOSED_WON_ID}}`).
- **Exit:** None in acquisition; triggers the post-sale journey (out of scope).
- **Owner:** Sales → Customer Success.

### Detours

- **Nurture** (`{{HUBSPOT_WORKFLOW_ID_3}}`) — warm-but-not-ready (timing/priority, not fit). Entry from MQL/SAL/SQL/SAO or a Closed Lost deal. Exit via re-engagement → Marketing Engaged or MQL. Owner: Marketing.
- **Unqualified** (`{{HUBSPOT_WORKFLOW_ID_5}}`, "Disqualified") — permanently ruled out (fit, opt-out, non-viable). Entry from any active stage. Exit: none (terminal). Owner: Sales (or the disqualifying team).

> **Detour ownership** is an operating convention (not defined in the GTM-Ops
> profile): Nurture → Marketing; Unqualified → whichever team disqualified the
> record (Sales for a sales-stage disqualification, Marketing at Marketing
> Engaged / MQL).

---

## 3. Funnel metrics (Q2-2026 definitions)

Defined here; **counted** by `roster/funnel-stats/prompt.md` (canonical). Window
is month-to-date (`GTE month_start` / `LTE today`).

| Metric | Definition | Stage | Property | Notes |
|--------|------------|-------|----------|-------|
| MEL | First entry into Marketing Engaged | 2 | `mel_date` | Not `mel_date__latest_` (diverges on re-engagement). |
| MQL | Became Marketing Qualified | 3 | `mql_date__latest_` + `mql_type_latest` | P1 / P2 / Outbound; Outbound mandatory. |
| SAL | Sales accepts the lead and pursues a meeting | 4 | `sal_date__latest_` | Cohort: MQL **and** SAL in-window. |
| SQL | A meeting is successfully booked after pursuit | 5 | `sql_date__latest_` | Cohort: MQL **and** SAL **and** SQL in-window. |
| Meetings Held | Discovery meeting completed for an in-month-scheduled deal | deal event | deal `demo_done_date` + `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` ≥ month start | Not the same as SQL; no acronym. |
| Active Open Pipeline | Sum of open deal `amount` | 6 | deal `pipeline = {{HUBSPOT_PIPELINE_ID}}`, `dealtype != existingbusiness` (new-business only), excl. Closed Won `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` / Closed Lost `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}` | Deal-layer measure for Opportunity. |

**Cohort note:** the SAL/SQL cohort is **anchored at MQL** — a contact counts only
if it became an MQL and every subsequent stage up to that metric's stage within
the same MTD window. MEL / Marketing Engaged is not part of the filter.

**Caveats:** `*_date__latest_` re-stamping moves intraday counts both directions
(compare timestamps, not raw numbers); import pollution can inflate SAL cohorts;
MEL backfill restates historical months upward for ~4–8 weeks.

---

## 4. Required HubSpot Properties per Stage

| Stage | Required properties | Orphan condition |
|-------|---------------------|------------------|
| Marketing Engaged | `mel_date` | stage = Marketing Engaged with no `mel_date` |
| Marketing Qualified Lead | `mql_date__latest_`, `mql_type_latest` | date without type, or type without date |
| Sales Accepted Lead | `sal_date__latest_`, `mql_date__latest_` | SAL stage with no `mql_date__latest_` |
| Sales Qualified Lead | `sql_date__latest_`, `sal_date__latest_` | SQL stage with no associated open deal at Discovery Scheduled (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later |
| Sales Accepted Opportunity | open deal on `{{HUBSPOT_PIPELINE_ID}}` | Opportunity stage with no open deal |
| Customer | associated deal at Closed Won (`{{HUBSPOT_STAGE_CLOSED_WON_ID}}`) | Customer stage with no associated Closed Won deal |

> **Exact spellings matter:** `mql_date__latest_` has a **double** underscore
> before `latest` and a **trailing** underscore; `mql_type_latest` has single
> underscores and no trailing one.

---

## 5. Allowed transitions

Forward path: `Prospect → Marketing Engaged → Marketing Qualified Lead → Sales
Accepted Lead → Sales Qualified Lead → Sales Accepted Opportunity → Customer`.

**Legitimate non-forward edges (do not flag):**
- Any active stage → **Unqualified** (disqualification).
- MQL / SAL / SQL / SAO → **Nurture** (timing/priority hold).
- **Nurture → Marketing Engaged / Marketing Qualified Lead** (re-engagement).
- SQL / SAO → **Unqualified** when a deal goes Closed Lost with no future potential.

**Flag as suspicious:** any other backward move; any skip bypassing an
intermediate stage (e.g., Marketing Engaged → Sales Qualified Lead with no MQL or
SAL date). For SAO/Customer, verify via deal association, not a stage-date.

---

## 6. Time-in-stage benchmarks

**Status: provisional** — not ratified, pending RevOps. `revops-watchdog:lifecycle-audit`
should surface a "(provisional thresholds — pending RevOps ratification)" note
wherever it flags stuck contacts from this table. Values are placeholders so the
audit does not fall back to a blanket 60-day threshold; tune with actual HubSpot
time-in-stage data before relying on stuck-contact flags.

| Stage | Expected (days) | Stuck threshold (days) |
|-------|-----------------|------------------------|
| Prospect | 30 | 90 |
| Marketing Engaged | 21 | 60 |
| Marketing Qualified Lead | 7 | 21 |
| Sales Accepted Lead | 3 | 10 |
| Sales Qualified Lead | 14 | 45 |
| Sales Accepted Opportunity | 30 | 90 |

---

## 7. Deal-stage alignment (contact ↔ pipeline)

Pipeline `{{HUBSPOT_PIPELINE_ID}}` (live label "Sales"). Stages below are the pipeline
path; open-deal counts are illustrative placeholders, not a reading of any live portal:

| Order\* | Deal stage | Internal ID | Open deals (illustrative) |
|--------|-----------|-------------|---------------------------|
| 1 | 🙋‍♀️ Discovery Requested | `{{HUBSPOT_STAGE_ID_4}}` | 12 |
| 2 | 📆 Discovery Scheduled | `{{HUBSPOT_STAGE_DISCOVERY_ID}}` | 18 |
| 3 | 👩🏻‍💻 Demo Requested | `{{HUBSPOT_STAGE_ID_5}}` | 11 |
| 4 | 🖥 Demo Scheduled | `{{HUBSPOT_STAGE_ID_8}}` | 14 |
| 5 | ❓ Selection | `{{HUBSPOT_STAGE_ID_9}}` | 16 |
| 6 | 🛫 Onboarding | `{{HUBSPOT_STAGE_ID_6}}` | 13 |
| 7 | 🚀 Ramp Up | `{{HUBSPOT_STAGE_ID_7}}` | 10 |
| 8 | 📜 Contract Negotiations | `{{HUBSPOT_STAGE_ID_10}}` | 15 |
| 9 | ✍️ Quote Sent | `{{HUBSPOT_STAGE_ID_11}}` | 17 |
| 10 | 🎉 Closed won | `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` | 22 |
| 11 | 😥 Closed lost | `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}` | 31 |

> \*Order inferred from the `dealstage` enumeration, not a confirmed HubSpot
> `displayOrder`. IDs and labels confirmed; the placement of Onboarding / Ramp Up
> should be confirmed against the live board.

| Lifecycle stage | Expected deal stage(s) | Rule |
|-----------------|------------------------|------|
| Sales Qualified Lead | Discovery Scheduled (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later | ≥1 open, non-closed-lost deal |
| Sales Accepted Opportunity | active selling stage (Demo Scheduled → Quote Sent) | carries pipeline `amount` |
| *(any)* | Closed Lost (`{{HUBSPOT_STAGE_CLOSED_LOST_ID}}`) | regress to Nurture or Unqualified; do not remain SQL/SAO |

No `Prospect`, `Subscriber`, or `Lead` contact should have an active open deal.

---

*Q2-2026 snapshot captured from model v1.0.0. For the current model and
full narrative (purpose, glossary, version history), see
[`docs/lead-lifecycle-model.md`](./lead-lifecycle-model.md).*
