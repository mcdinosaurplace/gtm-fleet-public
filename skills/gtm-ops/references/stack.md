# {{COMPANY}} GTM Tech Stack Reference

The canonical integration catalog for {{COMPANY}}'s go-to-market systems. Tools are
named by connector **category** (`~~crm`, `~~chat`, …) with the default product this
kit is built against in parentheses — see `CONNECTORS.md`. Swap the product, keep the
category, and everything downstream still resolves.

## Declared stack

| Category | Placeholder | Default product | Role in GTM |
|---|---|---|---|
| CRM / marketing automation | `~~crm` | HubSpot | System of record: lifecycle, scoring, workflows, attribution, reporting |
| Chat | `~~chat` | Slack | Alerting, approvals, handoffs, stand-ups |
| Issue tracker | `~~issue tracker` | Linear | GTM Ops sprints, backlog, campaign and content tasks |
| Knowledge base | `~~knowledge base` | Notion | SOPs, briefs, governance docs, durable agent output |
| Calendar / email | `~~calendar`, `~~email` | Google | Meeting and inbox signal for the operator brief |
| Ads | `~~ads` | Google Ads | Paid acquisition; spend and creative pulled by `scripts/google_ads_pull.py` |
| Web analytics | `~~web analytics` | Google Analytics + Search Console | Traffic, content performance, conversion tracking |
| Enrichment / signal | — | {{ENRICHMENT_VENDOR}} (internal) | Signal consumption, enrichment orchestration, cadence triggers |
| Firmographic data | — | {{ENRICHMENT_DATA_PROVIDER}} | Firmographic cascade feeding {{ENRICHMENT_VENDOR}} |

Anything not in this table is not a declared {{COMPANY}} GTM system. Do not invent one
in a workflow spec; name the category and flag the gap instead.

---

## `~~crm` (System of Record)

**Role**: CRM, lifecycle management, lead scoring, workflow automation, attribution, reporting
**Key objects**: Contacts, Companies, Deals, Activities
**Key properties**: Lifecycle stage, lead score, MEL/MQL/SAL/SQL date stamps, original source, attribution fields
**Workflows**: Lead routing, lifecycle transitions, score threshold triggers, handoff notifications
**Pipeline**: the new-business deal pipeline (`{{HUBSPOT_PIPELINE_ID}}`) sits inside the
Sales Accepted Opportunity lifecycle stage — stage definitions live in `references/funnel.md`.

### HubSpot Workflow Spec Standards

When specifying a workflow, always document:
1. **Trigger type**: Contact-based / Company-based / Deal-based / Activity-based
2. **Enrollment criteria**: Property conditions, list membership, form submission, etc.
3. **Re-enrollment**: Yes/No + conditions
4. **Actions** (in order): delays, property updates, notifications, task creation, branching
5. **Exit criteria**: What removes a contact from the workflow
6. **Property dependencies**: Which properties must be set before enrollment works correctly
7. **{{ENRICHMENT_VENDOR}} hooks**: Any enrichment or signal handoff points
8. **Human review note**: Flag if the workflow touches live pipeline or scoring thresholds

---

## {{ENRICHMENT_VENDOR}} (Internal Platform)

**Role**: Signal consumption, enrichment orchestration, cadence management
**Type**: Internal I/O platform built and maintained by {{COMPANY}}'s Sales/RevOps team
**Data sources**: {{ENRICHMENT_DATA_PROVIDER}} plus one internal source (service-graph
telemetry exported from the product, firmographic only — never customer incident content)

### What {{ENRICHMENT_VENDOR}} Consumes

#### Marketing Conversion Signals
{{ENRICHMENT_VENDOR}} can receive and act on any marketing engagement event, including:
- Content downloads (gated guides, reliability benchmarks, runbook templates)
- Event registrations (webinars, live roundtables, online conferences)
- Campaign interactions — any conversion event tied to a marketing campaign (form fills, CTA clicks, demo requests)
- Self-serve signup and trial-workspace creation (the founder-led entry path)

#### Lifecycle and Sales Signals
{{ENRICHMENT_VENDOR}} also ingests CRM-side signals:
- Deal created, deal stage changed, deal closed-won, deal closed-lost
- Meeting accepted and attended (from calendar / activity data)
- SAL and SQL progression events

#### Enrichment
- Company domain enrichment from a professional-profile URL
- Enrichment cascade: runs through {{ENRICHMENT_DATA_PROVIDER}} and the secondary source to fill
  firmographic gaps (company size, engineering headcount band, industry, HQ region, funding stage)

### {{ENRICHMENT_VENDOR}}'s Output / Actions

- **Cadence orchestration**: Triggers or adjusts sales outreach sequences based on signals
- **Enrichment fill**: Populates `~~crm` company/contact properties from the {{ENRICHMENT_DATA_PROVIDER}} cascade
- **Scoring input**: Feeds data into lead scoring models
- **Routing signals**: Informs lead assignment logic based on enriched firmographic data

### When to Reference {{ENRICHMENT_VENDOR}} in Workflow Specs

Include a {{ENRICHMENT_VENDOR}} integration note whenever a workflow involves:
- Marketing campaign conversion events that should trigger sales action
- Company enrichment that gates routing or scoring decisions
- Deal-stage changes that should feed back into marketing lifecycle logic
- Profile-based enrichment as part of a prospecting or routing flow
- Self-serve workspace activity that should promote a record out of Prospect

---

## Integration Catalog

The expected inbound/outbound syncs, and what "healthy" means for each. Consumed by
`revops-watchdog:integration-health-check`.

| Integration | Direction | Expected cadence | Critical? |
|---|---|---|---|
| {{ENRICHMENT_VENDOR}} → `~~crm` | Inbound | Near real-time | Yes |
| {{ENRICHMENT_DATA_PROVIDER}} → {{ENRICHMENT_VENDOR}} → `~~crm` | Inbound (via cascade) | Daily batch | Yes |
| Product signup / workspace telemetry → {{ENRICHMENT_VENDOR}} | Inbound | Near real-time | Yes |
| `~~ads` ↔ `~~crm` | Bidirectional (click id in, offline conversions out) | Daily | Yes |
| `~~web analytics` → `~~crm` | Reference | Real-time (tag-based) | Medium |
| `~~cms` forms → `~~crm` | Inbound | Real-time | Yes |
| `~~events` → `~~crm` | Inbound | Per event, then daily reconcile | Medium |
| `~~crm` → `~~chat` | Outbound (alerts, approvals) | Event-driven | Medium |
| `~~crm` → `~~issue tracker` | Outbound (task creation) | Event-driven | Low |
| Webhook / automation layer | Varies | Varies | Varies |

**Health signals to check per integration**: connection state, last successful sync
timestamp vs. expected cadence, error rate trend, coverage (share of records the sync
should have touched that it did), and whether a re-auth is pending.

---

## Reporting Surfaces

- **`~~crm` reports and dashboards** — source-to-pipeline, multi-touch attribution,
  lifecycle funnel, data-hygiene lists. Dashboard `{{HUBSPOT_DASHBOARD_ID}}` is the
  GTM standing view.
- **`~~web analytics`** — traffic, content, and on-site conversion; joined to `~~crm`
  by UTM and click id, never by a shared user key.
- **`state/working/fleet.db`** — the fleet's own longitudinal store (funnel snapshots,
  scorecards, keyword rankings). Agents read history here rather than re-querying `~~crm`.

There is no separate BI warehouse in the declared stack. If an analysis needs one, say so
and raise it as a gap rather than assuming a connection exists.

---

## UTM Naming Convention

{{COMPANY}}'s standard UTM parameter structure:

| Parameter | Format | Example |
|-----------|--------|---------|
| `utm_source` | Platform/origin (lowercase, hyphens) | `google`, `newsletter`, `partner-site` |
| `utm_medium` | Traffic type (lowercase) | `cpc`, `social`, `email`, `content`, `referral` |
| `utm_campaign` | `{year}-{quarter}-{type}-{audience}-{theme}` | `<year>-q3-paid-platform-ownership-as-code` |
| `utm_content` | Asset or creative identifier | `blog-post-title`, `ad-variant-a` |
| `utm_term` | Paid search keyword (paid only) | `incident-response-platform` |

**Campaign naming rules**:
- Always lowercase, hyphens between words, no spaces or special characters
- Year: 4-digit
- Quarter: `q1` / `q2` / `q3` / `q4`
- Type: `paid` / `organic` / `email` / `event` / `content` / `partner`
- Audience: `founders` / `platform` / `eng-leaders` / `security` / `general`
- Theme: short descriptor of the campaign angle (2–4 words max)

**Original source vs. latest touch**: the live `utm_*` properties are latest-touch and are
overwritten on every form fill. For original-source attribution use the write-once
`*___initial` family. See `roster/performance-marketer/references/hubspot-ads-bridge.md`
for the verification method.
