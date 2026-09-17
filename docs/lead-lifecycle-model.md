# Lead Lifecycle Model — Definitions & Stage SOP

**Version:** 1.0.0
**Status:** Active
**Owner:** Scott (marketing operations)
**Applies to:** Everyone who reads, reports on, or automates against {{COMPANY}}'s
lead funnel — GTM Ops, Marketing, Sales, and the agent fleet (revops-watchdog, Scribe,
funnel-stats, performance-marketer).

> **This document is the single source of truth for {{COMPANY}}'s lead lifecycle
> stages and funnel metrics.** It supersedes the legacy lifecycle map and any
> prior stage-definition drafts. Where any other
> document, dashboard, or slide disagrees with this one, this one wins — and
> the other document should be corrected. Definitions here are version
> controlled: any change requires a version bump and a changelog entry
> (see [Version history](#8-version-history)).

---

## 1. Purpose & scope

{{COMPANY}} has accumulated several partial, conflicting descriptions of its funnel
over time (a legacy HubSpot-classic path, an intent-based redesign, and the
current redefinition of Sales Accepted / Sales Qualified). This document
consolidates them into one accurate, unambiguous reference:

- **A glossary** of every term and acronym (§3).
- **The canonical lifecycle stages** with entrance/exit criteria and owners (§4).
- **The funnel metrics** (MEL, MQL, SAL, SQL, meetings held, pipeline) with
  their current definitions and how they are counted (§5).
- **Detours, terminal states, and legacy stages** (§6).
- **The deal pipeline** that sits inside the Opportunity stage (Appendix A, §7).
- **The model's version history**, so the SAL/SQL redefinition is on the record (§8).
- **A machine-readable lifecycle map** consumed by `revops-watchdog:lifecycle-audit` (§9).

**In scope:** the contact lifecycle from first CRM record to Customer, plus the
funnel metrics reported weekly. **Out of scope:** post-sale motions (onboarding,
expansion, CS), lead-scoring model internals (see the lead-score doc), and
routing logic (see the routing spec).

---

## 2. How to read this — the two-layer model

The single most important thing to understand, and the source of most historical
confusion, is that the funnel has **two layers**:

| Layer | What it is | Cardinality | Example |
|-------|-----------|-------------|---------|
| **Lifecycle stage** | The *current state* of a contact record in HubSpot | A contact has exactly **one** at any time | "This contact is a `Sales Accepted Lead`." |
| **Funnel metric** | A *date-stamped event* recording entry into a stage, counted monthly for reporting | A contact accumulates **many** over time | "This contact became an SAL on the 14th of the month." |

A contact moves through stages; each entry stamps a date property; we count those
date stamps per month to produce MEL/MQL/SAL/SQL. **A stage and its metric are
not the same object** — the stage is a state, the metric is a dated event.

The error that this document exists to fix came from collapsing these
two layers: attaching an *intent label* ("Meeting Booked," "Meeting Held") to a
stage as if it were the metric's definition, then discovering the metric actually
fired somewhere else. When you read a definition below, always note **which layer
it belongs to.**

---

## 3. Glossary & acronyms

| Term | Expansion / meaning |
|------|---------------------|
| **CRM** | HubSpot — the system of record for all contact lifecycle stages and deals. |
| **Lifecycle stage** | The single current state of a contact record (a HubSpot `lifecyclestage` value). |
| **Funnel metric** | A date-stamped conversion event, counted month-to-date for reporting. Defined here; **counted** by `roster/funnel-stats/prompt.md`. |
| **MEL** | Marketing Engaged Lead — a contact that first entered the `Marketing Engaged` stage. |
| **MQL** | Marketing Qualified Lead — a contact that became sales-ready. Three sub-types: **P1 Handraiser**, **P2 Score Threshold**, **Outbound**. |
| **SAL** | Sales Accepted Lead — Sales accepts the lead and pursues a meeting. *(Current definition — the cohort method.)* |
| **SQL** | Sales Qualified Lead — a meeting is successfully booked after pursuit. *(Current definition — the cohort method.)* |
| **SAO** | Sales Accepted Opportunity — a qualified, open deal with pipeline value. A stage, not a reported count (see §5). |
| **PQL** | Product Qualified Lead — reserved for product-usage-triggered qualification. Defined in HubSpot, effectively unused (no product telemetry in CRM yet). |
| **ICP** | Ideal Customer Profile. |
| **CVR** | Conversion rate between two adjacent stages/metrics. |
| **MTD** | Month-to-date (`month start` → `today`), the standard funnel reporting window. |
| **Detour** | An off-forward-path state (`Nurture`, `Unqualified`) reachable from multiple active stages. |
| **Stage 0 / Stage 1+** | HubSpot **deal**-pipeline numbering. *Stage 0* = a deal exists but is not yet a qualified opportunity (e.g., a meeting happened but need/budget/fit are unconfirmed). *Stage 1+* = a qualified opportunity carrying pipeline value. |
| **Funnel-consistent cohort** | The counting method (standing since scorecard v1.1): a contact counts for a metric only if it became an **MQL** and reached every subsequent funnel stage up to and including that metric's stage within the same MTD window. The cohort is **anchored at MQL** — MEL / Marketing Engaged is not part of the filter. |
| **Handoff** | The Marketing → Sales ownership transfer, which occurs at **MQL → SAL** (Sales accepting the lead). |

---

## 4. Canonical lifecycle stages

These are the **real HubSpot contact lifecycle stages**, in forward order, that
make up {{COMPANY}}'s funnel. Internal values are the HubSpot `lifecyclestage`
property values (used by automations and by `revops-watchdog:lifecycle-audit`).

| # | Stage (HubSpot label) | Internal value | Metric stamped | Owner |
|---|------------------------|----------------|----------------|-------|
| 1 | **Prospect** | `{{HUBSPOT_WORKFLOW_ID_4}}` | — | Marketing |
| 2 | **Marketing Engaged** | `{{HUBSPOT_WORKFLOW_ID_1}}` | MEL | Marketing |
| 3 | **Marketing Qualified Lead** | `marketingqualifiedlead` | MQL | Marketing → *(handoff)* |
| 4 | **Sales Accepted Lead** | `{{HUBSPOT_WORKFLOW_ID_2}}` | SAL | Sales |
| 5 | **Sales Qualified Lead** | `salesqualifiedlead` | SQL | Sales |
| 6 | **Sales Accepted Opportunity** | `opportunity` | — (Active Open Pipeline) | Sales |
| 7 | **Customer** | `customer` | — (deal Closed Won) | Sales → CS |

> **Ownership note.** MQL (Marketing), SAL (Sales), and Closed Won/Lost (Sales)
> are documented in the GTM-Ops context profile. The remaining owners follow the
> operating convention: **Marketing owns everything through MQL; Sales owns from
> SAL onward.** The **handoff** is the moment Sales accepts the MQL (MQL → SAL).

### Stage detail

Each block gives the stage's meaning, what moves a record in, and what moves it
out. No stage includes a "why it matters" rationale — that is deliberate; this is
a definitions document.

#### 1. Prospect — `{{HUBSPOT_WORKFLOW_ID_4}}`
- **Meaning:** First-time CRM record. Cold — {{COMPANY}} has a way to reach the contact
  but has seen no engagement signal.
- **Entrance:** A new contact record is created — list import, enrichment
  (`~~enrichment` / {{ENRICHMENT_DATA_PROVIDER}}), a form capture without further engagement, or manual
  entry by a rep.
- **Exit:** Any brand engagement → **Marketing Engaged**.
- **Owner:** Marketing.

#### 2. Marketing Engaged — `{{HUBSPOT_WORKFLOW_ID_1}}`
- **Meaning:** The contact has taken at least one meaningful engagement action.
- **Entrance:** An engagement/conversion event (email click, content download,
  event/webinar registration, return site visit) or re-engagement after dormancy.
- **Exit:** Qualifies as an MQL → **Marketing Qualified Lead**; or → **Nurture**;
  or → **Unqualified**.
- **Owner:** Marketing.
- **Metric stamped:** **MEL** (`mel_date`, first entry — see §5).

#### 3. Marketing Qualified Lead — `marketingqualifiedlead`
- **Meaning:** Enough intent and/or fit to warrant Sales attention (sales-ready).
- **Entrance:** An MQL trigger, one of **three mandatory paths**:
  - **P1 Handraiser** — an explicit high-intent action (demo request, pricing
    request, direct reply to a rep).
  - **P2 Score Threshold** — the lead score crosses the qualification threshold.
  - **Outbound** — sales-sourced (prospected/sequenced). *This path is mandatory
    and easy to forget; omitting it materially undercounts MQLs.*
- **Exit:** Sales accepts and pursues → **Sales Accepted Lead**; or →
  **Nurture** (not yet the right time); or → **Unqualified** (not ICP).
- **Owner:** Marketing. **This stage is the Marketing → Sales handoff point.**
- **Metric stamped:** **MQL** (`mql_date__latest_` + `mql_type_latest`).

#### 4. Sales Accepted Lead — `{{HUBSPOT_WORKFLOW_ID_2}}`
- **Meaning (current):** **Sales accepts the lead and pursues a meeting.**
  Acceptance and active pursuit — *before* a meeting exists.
- **Entrance:** A rep accepts the MQL and begins pursuing a meeting.
- **Exit:** A meeting is booked → **Sales Qualified Lead**; or → **Nurture**; or
  → **Unqualified**. (At the deal layer, unresponsiveness can go **Closed Lost**.)
- **Owner:** Sales.
- **Metric stamped:** **SAL** (`sal_date__latest_`, "latest date entered the
  Sales Accepted stage").

#### 5. Sales Qualified Lead — `salesqualifiedlead`
- **Meaning (current):** **A meeting is successfully booked after pursuit.**
  (The scorecard header for this metric is "SQLs (Meeting Scheduled)" — *Meeting
  Booked* and *Meeting Scheduled* are the same event.)
- **Entrance:** A meeting is booked/scheduled on the calendar.
- **Exit:** Qualified into a real opportunity → **Sales Accepted Opportunity**;
  or → **Unqualified**. (At the deal layer → **Closed Lost**.)
- **Owner:** Sales.
- **Metric stamped:** **SQL** (`sql_date__latest_`, "latest date entered Sales
  Qualified stage").
- **Note:** The meeting *being held* is **not** a lifecycle stage. It is tracked
  as the deal event **Meetings Held** (`demo_done_date`) — see §5.

#### 6. Sales Accepted Opportunity — `opportunity`
- **Meaning:** Fit **and** need are confirmed; a genuine deal exists with pipeline
  value (deal at **Stage 1+**).
- **Entrance:** Qualification criteria met; the deal is logged at Stage 1 or later
  on the Sales pipeline (`{{HUBSPOT_PIPELINE_ID}}`).
- **Exit:** **Closed Won** (→ Customer) or **Closed Lost** (deal layer).
- **Owner:** Sales.
- **Metric stamped:** none as a count. This stage is measured by **Active Open
  Pipeline** (sum of open deal `amount`; see §5). "SAO" is the stage acronym, not
  a reported funnel count.

#### 7. Customer — `customer`
- **Meaning:** An associated deal is signed; the record is a customer.
- **Entrance:** A deal reaches **Closed Won** (deal stage `{{HUBSPOT_STAGE_CLOSED_WON_ID}}`).
- **Exit:** None within the acquisition funnel. Triggers the post-sale journey
  (onboarding, expansion, customer marketing), which lives outside this model.
- **Owner:** Sales → Customer Success.

---

## 5. Funnel metrics

Metrics are **date-stamped events**, counted **month-to-date** (`GTE month_start`
/ `LTE today`). **This document defines them; `roster/funnel-stats/prompt.md`
counts them** — the queries there are canonical and the GTM scorecard defers to
them (`docs/gtm-scorecard-definitions.md`). If a definition here and a query
there ever disagree, that is a defect to fix, not a judgment call.

| Metric | Definition (current) | Stage | HubSpot property | Notes |
|--------|-------------------------------|-------|------------------|-------|
| **MEL** | First entry into `Marketing Engaged` | 2 | `mel_date` | Use `mel_date`, **not** `mel_date__latest_` (the latter diverges on re-engagements — a re-engagement-heavy month read 235 against 177). |
| **MQL** | Became Marketing Qualified | 3 | `mql_date__latest_` + `mql_type_latest` | Sub-types P1 / P2 / Outbound; **Outbound is mandatory** in the count. |
| **SAL** | Sales accepts the lead and pursues a meeting | 4 | `sal_date__latest_` | Funnel-consistent cohort: counts only if the contact became MQL **and** SAL in-window. |
| **SQL** | A meeting is successfully booked after pursuit | 5 | `sql_date__latest_` | Cohort: counts only if MQL **and** SAL **and** SQL in-window. |
| **Meetings Held** | A discovery meeting was completed for an in-month-scheduled deal | (deal event, maps to a held SQL meeting) | deal `demo_done_date` **and** `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` (Discovery Scheduled entry) ≥ month start | Deal-object metric, no letter acronym. Not the same as SQL. |
| **Active Open Pipeline** | Sum of open deal `amount` | 6 | deal `pipeline = {{HUBSPOT_PIPELINE_ID}}`, `dealtype != existingbusiness` (new-business only), excl. Closed Won `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` / Closed Lost `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}` | The deal-layer measure for the Opportunity stage. |

### Stage ↔ metric crosswalk (current truth)

| Lifecycle stage | Funnel metric | Property |
|-----------------|---------------|----------|
| Marketing Engaged | MEL | `mel_date` |
| Marketing Qualified Lead | MQL | `mql_date__latest_`, `mql_type_latest` |
| Sales Accepted Lead | SAL | `sal_date__latest_` |
| Sales Qualified Lead | SQL | `sql_date__latest_` |
| *(deal: meeting completed)* | Meetings Held | deal `demo_done_date` (+ Discovery-Scheduled co-filter) |
| Sales Accepted Opportunity | *(none — Active Open Pipeline)* | deal `amount` on pipeline `{{HUBSPOT_PIPELINE_ID}}` |

### Data caveats (carry these anywhere numbers are shown)

- **Latest-date re-stamping.** `*_date__latest_` properties re-stamp on
  re-qualification, so intraday counts can move **in both directions** and past
  months can restate downward. Compare **timestamps**, not raw numbers, across
  pulls. Closed months must match exactly across surfaces.
- **Import pollution.** A bulk list import inflates MEL/MQL on the import day
  and can inflate that month's SAL cohort. Flag affected months (`import_polluted`);
  the seeded demo dataset carries no such day, so the flag only appears in live runs.
- **MEL backfill.** Retroactive MEL stamping keeps adding to historical months
  for ~4–8 weeks after close; expect upward restatements.

---

## 6. Detours, terminal states, and legacy stages

### Detours (off the forward path, reachable from multiple stages)

#### Nurture — `{{HUBSPOT_WORKFLOW_ID_3}}`
- **Meaning:** Warm but not ready — a **timing or priority** pause, not a fit
  problem. The contact is being kept warm for future re-engagement.
- **Entrance:** From `Marketing Qualified Lead`, `Sales Accepted Lead`,
  `Sales Qualified Lead`, `Sales Accepted Opportunity`, or a `Closed Lost` deal,
  when the block is timing/priority rather than fit.
- **Exit:** Re-engagement → returns to the active funnel (typically back to
  `Marketing Engaged` or `Marketing Qualified Lead`, depending on signal
  strength). This is a legitimate backward transition.
- **Owner:** Marketing.

#### Unqualified — `{{HUBSPOT_WORKFLOW_ID_5}}` *(informally "Disqualified")*
- **Meaning:** Permanently ruled out — a fundamental fit issue, an explicit
  opt-out, or a determination the contact will never be viable.
- **Entrance:** From **any** active stage once disqualification criteria are met.
- **Exit:** **None — terminal.** No further Marketing or Sales effort.
- **Owner:** Sales.

> **Detour ownership** is an operating convention (not defined in the GTM-Ops
> profile): Nurture sits with Marketing (re-engagement); Unqualified sits with
> whichever team disqualified the record — Sales for a sales-stage
> disqualification, Marketing for one at Marketing Engaged / MQL.

### Legacy / redundant contact stages (present in HubSpot, **not** part of the canonical funnel)

These `lifecyclestage` values exist in HubSpot but are not part of the funnel we
design, report, or optimize against. They are documented here so automations and
audits can recognize (and eventually retire) them.

| Stage | Internal value | Status |
|-------|----------------|--------|
| Subscriber | `subscriber` | Legacy; overlaps Prospect / Marketing Engaged. |
| Lead | `lead` | Legacy; overlaps Marketing Engaged. |
| Product Qualified Lead | `{{HUBSPOT_WORKFLOW_ID_6}}` | Reserved (PQL); no product telemetry in CRM yet. (The PQL *MQL-type* has carried ~0 records in every month observed so far; the PQL lifecycle-stage volume is not separately verified.) |
| Evangelist | `evangelist` | HubSpot default; post-customer advocacy; unused in acquisition. |
| Other | `other` | Catch-all; not funnel-meaningful. |

> **Known data-hygiene issue (GTM-Ops backlog):** `Prospect`, `Subscriber`, and
> `Lead` are frequently confused; MQL vs. PQL is not cleanly enforced.
> Consolidating these redundant states is a standing RevOps cleanup item.

### Deal-layer terminal states (not contact lifecycle stages)

- **Closed Won** — deal stage `{{HUBSPOT_STAGE_CLOSED_WON_ID}}`. Drives the contact to `Customer`.
- **Closed Lost** — deal stage `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}`. A lost deal; the associated contact is
  triaged to **Nurture** (future potential) or **Unqualified** (none). *Closed
  Won/Lost are **deal** states — do not confuse them with contact lifecycle
  stages.*

---

## 7. Appendix A — the deal pipeline inside "Opportunity"

Once a contact reaches **Sales Accepted Opportunity**, progress is tracked on the
**deal** object (HubSpot pipeline `{{HUBSPOT_PIPELINE_ID}}`, live label "Sales"), not the contact
lifecycle. The deal-stage path is a separate governance surface; it is included
here as a crosswalk so the two layers line up.

**Deal-stage path — pipeline `{{HUBSPOT_PIPELINE_ID}}` ("Sales"). Open-deal counts are
illustrative placeholders sized to the seeded funnel (≈21–25 SQLs a month), not a
reading of any live portal:**

| Order\* | Deal stage | Internal ID | Open deals (illustrative) |
|--------|-----------|-------------|---------------------------|
| 1 | 🙋‍♀️ Discovery Requested | `{{HUBSPOT_STAGE_ID_4}}` | 8 |
| 2 | 📆 Discovery Scheduled | `{{HUBSPOT_STAGE_DISCOVERY_ID}}` | 11 |
| 3 | 👩🏻‍💻 Demo Requested | `{{HUBSPOT_STAGE_ID_5}}` | 6 |
| 4 | 🖥 Demo Scheduled | `{{HUBSPOT_STAGE_ID_8}}` | 8 |
| 5 | ❓ Selection | `{{HUBSPOT_STAGE_ID_9}}` | 7 |
| 6 | 🛫 Onboarding | `{{HUBSPOT_STAGE_ID_6}}` | 4 |
| 7 | 🚀 Ramp Up | `{{HUBSPOT_STAGE_ID_7}}` | 3 |
| 8 | 📜 Contract Negotiations | `{{HUBSPOT_STAGE_ID_10}}` | 5 |
| 9 | ✍️ Quote Sent | `{{HUBSPOT_STAGE_ID_11}}` | 3 |
| 10 | 🎉 Closed won | `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` | 9† |
| 11 | 😥 Closed lost | `{{HUBSPOT_STAGE_CLOSED_LOST_ID}}` | 24† |

> \*Order is inferred from the `dealstage` property enumeration, **not** a
> confirmed HubSpot `displayOrder`. Stage IDs and labels are confirmed; the
> placement of **Onboarding / Ramp Up** should be confirmed against the live
> pipeline board (they read as implementation stages, not linear sell steps).
> The legacy names in the GTM-Ops context profile (`Value Identified`, `Demo &
> Business Case`, `Proposal`, `Quote & Signing`) do **not** exist in the live
> pipeline and are replaced by the real stages above.
>
> †The two terminal rows are not open deals — they count deals closed in the
> trailing quarter, so the win rate reads against a comparable denominator.

**Contact ↔ deal crosswalk:**

| Contact lifecycle | Deal layer |
|-------------------|-----------|
| Sales Qualified Lead (meeting booked) | Deal at **Discovery Scheduled** (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later |
| *(meeting completed)* | deal `demo_done_date` set → **Meetings Held** |
| Sales Accepted Opportunity (Stage 1+) | Open deal in an active selling stage (Demo Scheduled → Quote Sent) carrying pipeline value |
| Customer | Deal at **🎉 Closed won** (`{{HUBSPOT_STAGE_CLOSED_WON_ID}}`) |

These are **deal**-object stages, distinct from the contact lifecycle.

---

## 8. Version history

The lifecycle model has three eras. Recording them is the point of this section —
the SAL/SQL redefinition is exactly what most stale artifacts miss. The version
labels below belong to the *lifecycle map* and the *scorecard*; this document's
own version is the one in the Changelog.

### Era 0 — Legacy HubSpot-classic funnel (pre-redesign)
Single-layer path where MQL/SAL/SQL were treated as stages with no distinct
metric layer, and redundant early states (`Prospect`/`Subscriber`/`Lead`)
coexisted: `Subscriber → MQL → SAL → SQL → Discovery Scheduled → Value Identified
→ Demo & Business Case → Proposal → Quote & Signing → Won/Lost`. Documented in
`context/gtm-ops-project-context.yaml`. **Superseded.**

### Era 1 — The v1.0 lifecycle map (intent-based redesign)
Introduced intent-based stage labels and the **Detour** concept (Nurture, Closed
Lost, Disqualified). It overlaid intent labels onto the funnel and **mapped
`SAL = Meeting Booked` and `SQL = Meeting Held`.** That mapping is the origin of
the later confusion — it attached "meeting" milestones to the SAL/SQL stages one
step too late.

### Era 2 — The funnel-consistent cohort method (current)
Effective with the cohort method in `roster/funnel-stats/prompt.md` (scorecard
v1.1) and the human definitions locked in `docs/gtm-scorecard-definitions.md`.
SAL and SQL were **redefined and each moved one step earlier**:

| Stage | Era 1 label | Era 2 meaning (current) |
|-------|--------------------|--------------------------|
| Marketing Qualified Lead | MQL | MQL (unchanged) |
| **Sales Accepted Lead** | *(was "Meeting Booked")* | **Sales accepts the lead and pursues a meeting** |
| **Sales Qualified Lead** | *(was "Meeting Held")* | **A meeting is successfully booked** |
| *(meeting held)* | was "SQL" | now the deal event **Meetings Held** (no acronym) |
| Sales Accepted Opportunity | SAO | SAO (unchanged) |

**Corroboration:** the retired Era-0/1 mapping is exactly the deprecated
*deal-based* SAL/SQL queries retained in the funnel-stats appendix (SAL keyed on
entering Discovery Scheduled = a booked meeting; SQL keyed on `demo_done_date` =
a held meeting). The contact-cohort method moved both one step earlier.

### Changelog

| Version | Change |
|---------|--------|
| 1.0.0 | Initial canonical model. Consolidates Eras 0–2; anchors on real HubSpot stage names; records the SAL/SQL redefinition; adds the machine-readable lifecycle map (§9). |

---

## 9. Machine-readable lifecycle map (for `revops-watchdog:lifecycle-audit`)

`revops-watchdog:lifecycle-audit` reads the most recent `docs/lifecycle-map-*.md` to get
canonical stages, transitions, and required properties. That frozen snapshot
(`docs/lifecycle-map-2026-06-30.md`) is a point-in-time copy of this section; this
is the living version.

### 9.1 Canonical stages (ordered)

| Order | Stage | HubSpot value | Required properties |
|-------|-------|---------------|---------------------|
| 1 | Prospect | `{{HUBSPOT_WORKFLOW_ID_4}}` | — |
| 2 | Marketing Engaged | `{{HUBSPOT_WORKFLOW_ID_1}}` | `mel_date` |
| 3 | Marketing Qualified Lead | `marketingqualifiedlead` | `mql_date__latest_`, `mql_type_latest` |
| 4 | Sales Accepted Lead | `{{HUBSPOT_WORKFLOW_ID_2}}` | `sal_date__latest_`, `mql_date__latest_` |
| 5 | Sales Qualified Lead | `salesqualifiedlead` | `sql_date__latest_`, `sal_date__latest_`, ≥1 associated deal |
| 6 | Sales Accepted Opportunity | `opportunity` | ≥1 open deal on pipeline `{{HUBSPOT_PIPELINE_ID}}` at Stage 1+ |
| 7 | Customer | `customer` | associated deal at Closed Won `{{HUBSPOT_STAGE_CLOSED_WON_ID}}` |

### 9.2 Regression / terminal states (off the forward path — do **not** flag as backward transitions)

| State | HubSpot value | Rule |
|-------|---------------|------|
| Nurture | `{{HUBSPOT_WORKFLOW_ID_3}}` | Legitimate reverse/hold edge; re-engagement returns to Marketing Engaged or MQL. |
| Unqualified | `{{HUBSPOT_WORKFLOW_ID_5}}` | Terminal; entry from any active stage is legitimate. |

### 9.3 Required HubSpot Properties per Stage

| Stage | Required properties | Orphan condition |
|-------|---------------------|------------------|
| Marketing Engaged | `mel_date` | stage = Marketing Engaged with no `mel_date` |
| Marketing Qualified Lead | `mql_date__latest_`, `mql_type_latest` | date set without type, or type set without date |
| Sales Accepted Lead | `sal_date__latest_`, `mql_date__latest_` | SAL stage with no `mql_date__latest_` |
| Sales Qualified Lead | `sql_date__latest_`, `sal_date__latest_` | SQL stage with no associated open deal at Discovery Scheduled (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later |
| Sales Accepted Opportunity | open deal on `{{HUBSPOT_PIPELINE_ID}}` | Opportunity stage with no open deal |
| Customer | associated deal at Closed Won (`{{HUBSPOT_STAGE_CLOSED_WON_ID}}`) | Customer stage with no associated Closed Won deal |

> **Exact spellings matter** for orphan checks: `mql_date__latest_` has a **double**
> underscore before `latest` and a **trailing** underscore; `mql_type_latest` has
> single underscores and no trailing one.

### 9.4 Allowed transitions

Forward path: `Prospect → Marketing Engaged → Marketing Qualified Lead → Sales
Accepted Lead → Sales Qualified Lead → Sales Accepted Opportunity → Customer`.

**Legitimate non-forward edges (do not flag):**
- Any active stage → **Unqualified** (disqualification).
- `Marketing Qualified Lead` / `Sales Accepted Lead` / `Sales Qualified Lead` /
  `Sales Accepted Opportunity` → **Nurture** (timing/priority hold).
- **Nurture → Marketing Engaged / Marketing Qualified Lead** (re-engagement).
- `Sales Qualified Lead` / `Sales Accepted Opportunity` → **Unqualified** when a
  deal goes Closed Lost with no future potential.

**Flag as suspicious:** any other backward move, and any skip that bypasses an
intermediate stage (e.g., Marketing Engaged → Sales Qualified Lead with no MQL or
SAL date).

> **Skip detection for Sales Accepted Opportunity & Customer:** these two stages
> stamp no contact date property (they are deal-derived), so entry must be
> verified via deal association (an open deal on `{{HUBSPOT_PIPELINE_ID}}`; a Closed Won deal
> `{{HUBSPOT_STAGE_CLOSED_WON_ID}}`) rather than a stage-date comparison.

### 9.5 Time-in-stage benchmarks — **PROVISIONAL (pending RevOps ratification)**

**Status: provisional** — not ratified. `revops-watchdog:lifecycle-audit` should surface a
"(provisional thresholds — pending RevOps ratification)" note wherever it flags
stuck contacts from this table. Values below are placeholders so the audit does
not fall back to a blanket 60-day threshold; **tune with actual HubSpot
time-in-stage data before relying on stuck-contact flags.**

| Stage | Expected (days) | Stuck threshold (days) |
|-------|-----------------|------------------------|
| Prospect | 30 | 90 |
| Marketing Engaged | 21 | 60 |
| Marketing Qualified Lead | 7 | 21 |
| Sales Accepted Lead | 3 | 10 |
| Sales Qualified Lead | 14 | 45 |
| Sales Accepted Opportunity | 30 | 90 |

### 9.6 Deal-stage alignment (contact ↔ pipeline)

| Lifecycle stage | Expected deal stage(s) | Rule |
|-----------------|------------------------|------|
| Sales Qualified Lead | Discovery Scheduled (`{{HUBSPOT_STAGE_DISCOVERY_ID}}`) or later | ≥1 open, non-closed-lost deal |
| Sales Accepted Opportunity | Value Identified and later (Stage 1+) | carries pipeline `amount` |
| *(any)* | Closed Lost (`{{HUBSPOT_STAGE_CLOSED_LOST_ID}}`) | regress contact to Nurture or Unqualified; do not remain SQL/SAO |

No `Prospect`, `Subscriber`, or `Lead` contact should have an active open deal.

---

## Sources

- `roster/funnel-stats/prompt.md` — canonical funnel-metric queries (MEL/MQL/SAL/SQL/pipeline) and the SAL/SQL definition note.
- `docs/gtm-scorecard-definitions.md` — locked, version-controlled metric definitions the scorecard uses.
- `context/gtm-ops-project-context.yaml` — GTM-Ops funnel/tech-stack context (Era-0 legacy path, owners, tooling).
- `roster/revops-watchdog/skills/lifecycle-audit.md` — the audit that consumes this model's `lifecycle-map` snapshot.
- Live HubSpot (`lifecyclestage` property + funnel date properties), verified read-only.
