# {{COMPANY}} Marketing & Revenue Operations Context

## Team Identity

Marketing & Revenue Operations at {{COMPANY}} is the operational engine for the entire GTM funnel — from self-serve signup to closed-won. Lean team, high ownership. Responsible for building and maintaining the systems, processes, and data infrastructure powering the go-to-market motion across both the product-led and sales-assisted paths.

**Team lead**: Scott McKeighen, Senior Manager / Head of Marketing Operations
**Reports to**: {{HEAD_OF_MARKETING}}, Head of Marketing (leads global marketing including demand gen, brand, lifecycle, and content; values cross-functional alignment, operational rigor, and autonomy backed by measurable outcomes)

## Primary KPIs

- Qualified pipeline volume (by source, segment, and attribution)
- SAL-to-SQL conversion rate
- MQL velocity and funnel pacing vs. monthly targets
- Self-serve signup → activated workspace rate (first routed page within 7 days)
- Data hygiene benchmarks (property completeness, validation, duplicates)
- System uptime and operational reliability
- Lead handoff time and process efficiency

## Tech Stack

**Core GTM platforms**: HubSpot (`~~crm`, system of record), `~~enrichment` (Clay / Apollo), `~~automation` (Zapier), `~~BI` (Metabase)
**Reporting**: HubSpot, GA4, `~~BI`
**Documentation**: Notion (documentation), Google Docs / Sheets (working drafts)
**Project management**: Linear
**Data sources**: HubSpot, {{ENRICHMENT_VENDOR}} — the internal service that cascades {{ENRICHMENT_DATA_PROVIDER}} and `~~enrichment` firmographics into `~~crm` — product telemetry (planned; the signup and activation events exist in the product but do not reach the CRM yet)

## Funnel Architecture

MEL → MQL → SAL → SQL → Discovery Scheduled → Value Identified → Demo & Business Case → Proposal → Quote & Signing → Won / Lost

Key lifecycle note: the current lifecycle has redundant states (Prospect / Subscriber / Lead; MQL vs. PQL) and is being simplified. A "Detour" stage handles acceleration paths — most commonly a free-tier workspace that crosses the seat threshold and jumps straight to SAL. Canonical definitions live in `docs/lead-lifecycle-model.md`; where anything here disagrees with that document, that document wins.

## Key Workflows

| Workflow | Description | Cadence |
|----------|-------------|---------|
| Lead Routing & Assignment | Distribute MQLs to AE owners via HubSpot rules | Daily |
| Lifecycle Stage Management | Define and govern contact / company / deal lifecycle criteria | Ongoing / weekly QA |
| Attribution Reporting | Source-to-pipeline and multi-touch attribution in HubSpot and `~~BI` | Monthly |
| Lead Scoring Optimization | Monitor and iterate on contact scoring models | Bi-weekly |
| GTM Tech Stack Maintenance | Triage and enhance HubSpot, the `~~enrichment` cascade, and {{ENRICHMENT_VENDOR}} | Ongoing |
| Sprint / Process Governance | Team sprints, documentation, tooling, and process layer for GTM execution | Weekly or project-based |

## Current Priorities (Q3–Q4)

- Lifecycle stage revamp (target: Q4 rollout)
- Product-telemetry-to-CRM pipeline so self-serve activation can drive scoring (the PQL definition is blocked on this)
- Attribution and reporting improvements (before Q4 pipeline targets finalize)
- GTM automation and tool governance
- Content and lead-gen funnel audit and rebuild

## Known Challenges

**Lead routing**: Headcount-based AE assignment is brittle due to missing enrichment data; engineering headcount in particular is rarely populated on inbound records, and the rule defaults to the COO when it is incomplete. Round robin is being evaluated.

**Lifecycle stages**: Redundant states need simplification. Proposed path: Subscriber → MQL → SAL → SQL → (deal stages).

**Deal stages**: Existing stages are overly granular. Proposed simplified sequence: Discovery Scheduled → Value Identified → Demo & Business Case → Proposal → Quote & Signing → Won / Lost.

**Data hygiene**: CRM has duplicates and fragmented company records; free-tier workspaces are not unified with their company records, so the same account can appear three times. No product usage data in CRM yet.

**Content / lifecycle marketing**: Organic content has grown stale, causing traffic decline. No lifecycle marketing programs exist yet to accelerate warm leads into MQLs, and nothing routes an active free-tier workspace toward a sales conversation.

## Cross-Functional Dependencies

**Sales**: Sales leadership also runs a de facto RevOps function. Sales engineering owns {{ENRICHMENT_VENDOR}}, the internal enrichment-and-scoring service: it cascades {{ENRICHMENT_DATA_PROVIDER}} and `~~enrichment` firmographics into `~~crm`, orchestrates outbound cadences, and computes four account scores — prospect, signup, usage, and MRR. Sellers are primary end-users of GTM Ops workflows.

**Marketing**: Marketing defines campaign success criteria that GTM Ops operationalizes.

**Product**: Product owns the signup and activation events GTM Ops needs in the CRM; the telemetry dependency is tracked jointly with {{PRODUCT_LEAD_FIRST}}.

## Working Preferences

Scott's AI interaction preferences:
- **Documentation / analysis**: direct, professional, structured with headings and bullet checklists
- **Brainstorming**: casual and creative
- **Verbosity**: concise for quick answers; detailed for planning, scoping, or architecture
- **Human approval required for**: external communications, production tooling changes, budget decisions
- **Sensitive / do not include**: internal compensation, customer incident data, unreleased roadmap
