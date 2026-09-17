---
name: revops-watchdog:opsos-watch
description: >
  Daily {{ENRICHMENT_VENDOR}} / {{ENRICHMENT_DATA_PROVIDER}} sync health watch. Checks whether new contacts have
  values in `opsos__person_id` and `opsos__company_id` on the Contact object.
  Presence of these IDs means the {{ENRICHMENT_VENDOR}} cascade (which uses {{ENRICHMENT_DATA_PROVIDER}}) is
  syncing back to HubSpot. Absence on a newly created contact means the
  sync failed for that record. Flags coverage drops and day-over-day
  degradation.
---

# {{ENRICHMENT_VENDOR}} Watch

## When This Runs

- **Tick integration:** Every daily Tick (default mode: `quick`)
- **Standalone quick:** `/revops-watchdog opsos-watch` or `/revops-watchdog opsos-watch quick`
- **Standalone complete:** `/revops-watchdog opsos-watch complete`

## Modes

This skill has two modes. They run the same underlying query and the same
anomaly rules — they differ only in which contacts enter the denominator.

### `quick` mode (default)

Filters out freemail and pseudo-inbox domains that {{ENRICHMENT_VENDOR}} / {{ENRICHMENT_DATA_PROVIDER}} cannot
meaningfully enrich. The resulting coverage percentages reflect only the
enrich-able (ICP-shaped) portion of new contacts, so the anomaly flags
describe real sync health rather than top-of-funnel noise.

**Excluded email domains (exact match or subdomain wildcard):**

- `gmail.com`
- `yahoo.com`
- `outlook.com`
- `hotmail.com`
- `icloud.com`
- `qq.com` (masked and throwaway registrations the cascade cannot resolve —
  per Scott, after a run of consumer-domain signups tripped the HIGH flag)
- `naver.com` (same ruling)
- the support desk's ticket subdomain, matched as a suffix wildcard — pseudo-inbox
  addresses minted from forwarded support tickets, which are never enrich-able.
  Set this to whatever suffix the help-desk in use generates; it is one entry,
  and leaving it out is the most common reason `quick` mode still looks noisy.

A contact is excluded if its `email` property's domain matches any entry in
the list. Records with null/empty email are kept in the sample (they may be
manually-created contacts that still went through {{ENRICHMENT_VENDOR}}).

### `complete` mode

No email-domain filter. Every new contact in the 7-day window enters the
denominator, including consumer gmail/yahoo accounts and support-desk
forwarded addresses. Use this mode when:

- Auditing the raw sync receipts literally (e.g., quarterly data hygiene)
- Investigating whether {{ENRICHMENT_VENDOR}} is writing IDs to unexpected record types
- Producing a reference number for comparison against `quick`-mode output

`complete` mode is slower to interpret (more noise) but is the correct
methodology when the question is "what is {{ENRICHMENT_VENDOR}} actually doing to every
record in HubSpot?" rather than "is the sync healthy on contacts that
should be enriched?"

### Which mode to use

| Purpose | Mode |
|---------|------|
| Daily Tick anomaly detection | `quick` |
| Weekly summary headline metric | `quick` |
| Quarterly data hygiene audit | `complete` |
| Investigating a specific sync regression | both, compared |
| Producing the delta between the two | run both back-to-back |

Whichever mode runs, the `opsos_signals` row records which filter was
applied in `field_coverage_json` (key: `"mode"` = `"quick"` or
`"complete"`; key: `"excluded_domains"` lists the filter for `quick`).

## What This Skill Measures

{{ENRICHMENT_VENDOR}} enriches {{COMPANY}}'s HubSpot contacts via a cascade that includes {{ENRICHMENT_DATA_PROVIDER}}.
When the cascade succeeds, two sentinel properties get written back to the
Contact object:

| HubSpot Internal Name | Display Name | Meaning When Populated |
|----------------------|--------------|----------------------|
| `opsos__person_id` | {{ENRICHMENT_VENDOR}} - Person ID | {{ENRICHMENT_VENDOR}}'s person-level enrichment reached this contact |
| `opsos__company_id` | {{ENRICHMENT_VENDOR}} - Company ID | {{ENRICHMENT_VENDOR}}'s company-level enrichment reached this contact |

**A new contact with both IDs populated = healthy sync.**
**A new contact missing either = sync failure for that record.**

These two fields are the authoritative proxy for "is {{ENRICHMENT_DATA_PROVIDER}} → {{ENRICHMENT_VENDOR}} →
HubSpot working?" No other field inspection is needed for this check.

## Inputs

- HubSpot contact data (via MCP or API)
  - All contacts created in the past 7 days
  - For each: value of `opsos__person_id`, `opsos__company_id`, and `email`
  - `email` is required so the `quick`-mode domain filter can be applied

## Workflow

### 1. Pull 7-Day New Contacts

Query HubSpot for contacts created in the past 7 days. For each record,
capture:
- `contact_id`
- `createdate`
- `email`
- `opsos__person_id` (value or null)
- `opsos__company_id` (value or null)

### 1a. Apply Mode Filter

If running in **`quick` mode** (default):

1. For each contact, extract the domain from `email` (the substring after `@`,
   lowercased).
2. Exclude the contact from the denominator if the domain is one of:
   `gmail.com`, `yahoo.com`, `outlook.com`, `hotmail.com`, `icloud.com`,
   `qq.com`, `naver.com`, or any subdomain of the configured support-desk
   ticket domain (suffix match).
3. Contacts with null/empty email are kept.
4. Track `excluded_count` and `excluded_by_domain` for reporting.

If running in **`complete` mode**: skip this step; every contact enters the
denominator.

### 1b. Aggregate Counts

Against the post-filter set:

- `total_new_contacts` (after filter in `quick`, raw in `complete`)
- `person_id_populated` (count where `opsos__person_id IS NOT NULL AND != ''`)
- `company_id_populated` (count where `opsos__company_id IS NOT NULL AND != ''`)
- `both_populated` (count where both fields have values)
- `neither_populated` (count where both fields are empty)

In `quick` mode also track: `raw_total`, `excluded_count`,
`excluded_by_domain` (map of domain → count).

### 2. Calculate Coverage Percentages

```
person_id_pct     = person_id_populated  / total_new_contacts * 100
company_id_pct    = company_id_populated / total_new_contacts * 100
both_populated_pct = both_populated       / total_new_contacts * 100
neither_pct       = neither_populated    / total_new_contacts * 100
```

The headline metric for this skill is **`both_populated_pct`** — the
percentage of new contacts fully enriched by {{ENRICHMENT_VENDOR}}.

### 3. Read Prior Snapshot

Query `opsos_signals` for the most recent entry to detect day-over-day
changes:

```sql
SELECT field_coverage_json, coverage_pct
FROM opsos_signals
WHERE agent = 'revops-watchdog'
ORDER BY check_date DESC
LIMIT 1;
```

Parse `field_coverage_json` for the prior `opsos__person_id` and
`opsos__company_id` coverage values.

### 4. Apply Anomaly Rules

| Condition | Severity | Flag |
|-----------|----------|------|
| `both_populated_pct < 70` | MED | "low_opsos_coverage" |
| `person_id_pct < 70` | MED | "person_sync_degraded" |
| `company_id_pct < 70` | MED | "company_sync_degraded" |
| `neither_pct > 20` | HIGH | "widespread_sync_failure" |
| Either ID coverage drops >30 percentage points day-over-day | HIGH | "sync_cliff" |
| Either ID was >80% yesterday and is <50% today | HIGH | "signal_type_dropout" |

The split between `person_id` and `company_id` matters: {{ENRICHMENT_VENDOR}} enriches
them through different pathways in the cascade. Person-level failure
without company-level failure (or vice versa) narrows the investigation
to one leg of the pipeline.

### 5. Write {{ENRICHMENT_VENDOR}} Signals Record

INSERT one row per day:

```sql
INSERT INTO opsos_signals (
  agent, check_date, new_contacts_7d, enriched_count, coverage_pct,
  field_coverage_json, flag, created_at
) VALUES (
  'revops-watchdog', '{today}', {total_new_contacts}, {both_populated},
  {both_populated_pct}, '{field_coverage_json}',
  {flag_description_or_null}, '{iso_now}'
);
```

- `enriched_count` = `both_populated` (contacts fully enriched)
- `coverage_pct` = `both_populated_pct` (headline metric)
- `field_coverage_json` tracks per-field breakdown and the mode used:

Illustrative payload (shape, not a measurement):

```json
{
  "mode": "quick",
  "excluded_domains": ["gmail.com", "yahoo.com", "outlook.com",
                       "hotmail.com", "icloud.com", "qq.com", "naver.com",
                       "*.helpdesk.example"],
  "raw_total": 120,
  "excluded_count": 36,
  "excluded_by_domain": {"gmail.com": 24, "*.helpdesk.example": 12},
  "opsos__person_id": 75.0,
  "opsos__company_id": 95.2,
  "both_populated": 73.8,
  "neither_populated": 3.6,
  "total_new_contacts": 84
}
```

For `complete` mode, omit `excluded_*` keys and set `"mode": "complete"`.

### 6. Write Anomalies

For each flag fired, INSERT into `anomalies` with `surface='opsos'`:

```sql
INSERT INTO anomalies (
  agent, detected_at, surface, metric, value, baseline,
  deviation_pct, severity, description, status, created_at
) VALUES (
  'revops-watchdog', '{iso_now}', 'opsos', '{flag_name}', {current_pct}, {prior_pct},
  {deviation_pp}, '{severity}', '{description}', 'open', '{iso_now}'
);
```

Description should state clearly which field is affected and the
interpretation:

> "opsos__person_id coverage dropped from 89% to 41% day-over-day
> (-48 pp). Indicates person-level {{ENRICHMENT_VENDOR}} enrichment is failing for
> new contacts. {{ENRICHMENT_DATA_PROVIDER}} → {{ENRICHMENT_VENDOR}} → HubSpot sync path compromised."

### 7. Write Handoffs

HIGH severity → immediate handoff to chief-of-staff.
MED severity → batched into next AM handoff.

Handoff body should name the specific ID(s) affected, the coverage
percentages, and the likely source to investigate:

> **Severity:** HIGH
> **Surface:** opsos
> **Finding:** `opsos__company_id` coverage at 18% on 7-day new contacts
> (was 86% prior week). 82% of new contacts are missing company-level
> {{ENRICHMENT_VENDOR}} enrichment.
> **Likely cause:** {{ENRICHMENT_DATA_PROVIDER}} → {{ENRICHMENT_VENDOR}} → HubSpot sync failure on company
> pathway.
> **Recommended action:** Check {{ENRICHMENT_VENDOR}} integration status in HubSpot;
> verify {{ENRICHMENT_DATA_PROVIDER}} credentials and recent cascade logs.
> **Tier gate:** 1 (chief-of-staff surfaces; Scott investigates)

## Output

- `opsos_signals` row (always, one per day)
- `anomalies` rows (zero or more)
- `handoffs` rows for HIGH (immediate), MED (batched)
- Journal entry section showing:
  - `both_populated_pct` (headline)
  - `opsos__person_id` coverage
  - `opsos__company_id` coverage
  - Day-over-day delta on each
  - Any flags fired

## Phase 1 Grace

If HubSpot contact data is not yet accessible via the current MCP
connection:
- Log "contact data unavailable — skipped" in journal
- Flag as LOW infrastructure incident once per week
- Do not treat as a sync anomaly

If fewer than 2 days of `opsos_signals` history exist:
- Write the snapshot normally
- Skip day-over-day drop detection
- Note "baseline establishing" in journal
- Still apply absolute-threshold rules (`coverage < 70%`,
  `neither > 20%`)

## Why `quick` Is the Default

{{COMPANY}}'s top of funnel is dominated by free-tier signups, and a free-tier
signup arrives with a personal email address and no company association. Add
the pseudo-inbox addresses the support desk mints from forwarded tickets, and a
large share of "new contacts" on any given day are records the cascade was never
going to enrich. Counting them in the denominator makes the unfiltered coverage
number drift toward the share of signups that happened to use a work address —
which is a top-of-funnel mix metric, not sync health, and it will cross the HIGH
`widespread_sync_failure` threshold on a good week as easily as a bad one.

Filtering those domains is what makes the threshold mean something: the question
`quick` answers is "did the cascade reach the contacts it should have reached?"
Running it by default prevents the skill from crying wolf on noise. `complete`
remains available for audits that need the literal record-by-record picture, and
comparing the two is the fastest way to tell a sync regression from a change in
acquisition mix.

## Why Two Fields Instead of a Catalog

The prior version of this skill tried to audit a broad catalog of
enrichment fields (industry, company size, tech stack, etc.). That
approach had two problems:

1. **Noise.** Many of those fields legitimately fail to populate for
   certain contacts (e.g., `funding_stage` is null for bootstrapped
   companies). Low coverage doesn't necessarily mean sync failure.
2. **Indirection.** Those fields are downstream *results* of
   enrichment. Some are filled by one `~~enrichment` source in the cascade,
   others by the next, others by {{ENRICHMENT_DATA_PROVIDER}} — making it hard
   to isolate which part of the cascade broke.

The two {{ENRICHMENT_VENDOR}} ID fields are different: they are **explicit sync
receipts**. {{ENRICHMENT_VENDOR}} only populates them when its cascade successfully
reaches HubSpot. Missing IDs on a new contact is a clear signal that
the sync failed for that record, not that the contact happens to lack
enrichable attributes.
