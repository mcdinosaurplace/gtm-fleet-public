---
name: revops-watchdog:attribution-integrity-audit
description: >
  Weekly attribution data integrity audit. Checks UTM coverage on new
  contacts, original source tracking completeness, campaign→contact
  association health, and offline conversion import health (supporting
  performance-marketer's paid media attribution work). Validates UTM format against the
  {{COMPANY}} naming convention (used by utm-builder).
---

# Attribution Integrity Audit

## When This Runs

- **Standalone:** `/revops-watchdog attribution-integrity-audit`
- **Typical cadence:** Weekly (Monday, after the prior week closes)

## Inputs

- HubSpot contacts created in the past 7 days (new contacts)
- HubSpot Campaigns (native Campaign objects)
- Offline conversion import logs from Google Ads / LinkedIn (if accessible)
- GA4 data (optional, for cross-validation)

## Cross-Agent Input: UTM Convention

Reference {{COMPANY}}'s UTM naming convention from
`skills/gtm-ops/references/stack.md` (the reference used by
`gtm-fleet:utm-builder`).

Expected format pattern:
- `utm_campaign` = `{year}-{quarter}-{type}-{audience}-{theme}`
- `utm_source` = channel source (e.g., `google`, `linkedin`, `newsletter`)
- `utm_medium` = traffic type (e.g., `cpc`, `social`, `email`, `organic`)
- `utm_content` = creative variant (optional)
- `utm_term` = paid keyword (optional, paid search only)

If the convention reference is inaccessible, fall back to checking for
presence/absence of UTM fields and basic format sanity (no spaces, no
special characters except hyphen/underscore).

## Audit Checks

### 1. UTM Coverage on New Contacts

**Audit the `*___initial` first-touch family, not the live `utm_*` fields.**
The live fields are overwritten by later sessions (latest-touch) and are
unsafe for original-source attribution. The initial family
(`utm_source___initial`, `utm_campaign___initial`, etc.) is written once
and never again — it is the designed original-source record. See
`roster/performance-marketer/references/hubspot-ads-bridge.md` for verified semantics.

For the past 7 days of new contact records:
- `utm_initial_coverage` = % with any `utm_*___initial` field populated
- `utm_source_initial_coverage` = % with `utm_source___initial`
- `utm_campaign_initial_coverage` = % with `utm_campaign___initial`

Segment by `hs_analytics_source` — coverage expectations differ:
- PAID_SEARCH: hidden fields fire on form fills, but capture the
  *form-fill session's* values — see known baseline below
- PAID_SOCIAL: expect ~0% — LinkedIn Lead Gen Form leads never hit website
  forms (structural, do not flag)
- OFFLINE: event/list imports often carry initial UTMs (this is healthy)

**The failure mode to expect on PAID_SEARCH — cross-session UTM loss.** The
hidden-field engine and the latest→initial propagation both work; the loss
happens upstream of them. A paid click lands, the visitor reads, leaves, and
converts days later in a session whose URL carries no UTM parameters. The
initial family is therefore written from the *return* session: `utm_source___initial`
records a derived source such as `google/organic` or `(direct)/(none)` rather
than the ad click, and `utm_campaign___initial` / `utm_term___initial` never get
a value at all.

This is the {{COMPANY}} shape specifically because the consideration window is
long — Aaron reads the provider docs, runs a shadow rotation, and comes back
through a bookmark or a branded search. The fix is client-side first-touch UTM
persistence in the tracking script.

Track `utm_campaign___initial` coverage as the indicator (illustrative numbers,
derived from the pattern rather than measured): near-0% with
`utm_source___initial` healthy = pre-fix state — open MED finding, report weekly;
rising coverage = the persistence fix shipped, flag as a noteworthy recovery.

Flag:
- PAID_SEARCH `utm_campaign___initial` coverage <40% → MED (currently
  expected; keep open until UTM persistence ships)
- `utm_source___initial` present but `utm_campaign___initial` missing →
  this IS the cross-session-loss signature; count it, don't re-flag per
  contact
- `utm_source___initial` contradicting `hs_analytics_source` on paid
  leads (e.g. "organic" on PAID_SEARCH) → LOW, informational — quantifies
  how misleading the UTM engine is for paid attribution pre-fix

### 2. UTM Format Compliance

For contacts with utm_campaign populated, check format against the
{{COMPANY}} naming convention:
- Matches `{year}-{quarter}-{type}-{audience}-{theme}` pattern?
- Year is current or prior (not future, not nonsense)?
- Quarter is Q1-Q4 or q1-q4?
- All lowercase and hyphenated?

Count non-compliant formats. Flag if >10% of tagged contacts use a
non-standard format.

### 3. Original Source Tracking

HubSpot's `hs_original_source` and related fields should be populated on
every contact. Check:
- % of contacts with `hs_original_source` populated
- Distribution of original source values (make sure tracking is producing
  reasonable variety, not everything falling to "OFFLINE_SOURCES" or
  "DIRECT_TRAFFIC")

Flag:
- <95% coverage of `hs_original_source` → MED
- >80% of contacts showing "DIRECT_TRAFFIC" or "OFFLINE_SOURCES" → MED
  (indicates tracking failure, not genuine direct traffic)

### 4. Campaign-to-Contact Association

For each active HubSpot Campaign object:
- How many contacts are associated?
- How many contacts with matching `utm_campaign` string are NOT associated
  with the Campaign object? (Attribution gap)

Flag:
- Any active campaign with zero associated contacts (likely setup error)
- Mismatch >50 contacts between utm_campaign and Campaign object membership

### 5. Offline Conversion Import Health

This check supports performance-marketer's paid media attribution. Verify the Google Ads
and LinkedIn → HubSpot offline conversion imports:

- Are Google Ads click IDs (gclid) being captured on new paid-source contacts?
- Are offline conversions being imported back to Google Ads on deal
  closed-won events?
- Is the import volume consistent week-over-week, or has it dropped off?

Flag any drop in gclid capture >50% WoW as HIGH (breaks Smart Bidding
optimization).

## Output Format

```markdown
## Attribution Integrity Audit — {Week of Date}

### UTM Convention Reference
- Source: {`skills/gtm-ops/references/stack.md` § UTM Naming Convention, or "fallback format sanity checks"}
- Pattern: `{year}-{quarter}-{type}-{audience}-{theme}`

### Summary
| Check | Status | Severity |
|-------|--------|----------|
| UTM coverage on new contacts | {pct}% | {OK/MED} |
| UTM format compliance | {pct}% compliant | {OK/MED} |
| Original source coverage | {pct}% | {OK/MED} |
| Campaign object linkage | {N} active / {N} with contacts | {OK/MED} |
| Gclid capture (paid contacts) | {pct}% | {OK/HIGH} |

### UTM Coverage Detail
- New contacts (7d): {N}
- With any UTM: {N} ({pct}%)
- With utm_source: {N} ({pct}%)
- With utm_campaign: {N} ({pct}%)
- With utm_medium: {N} ({pct}%)
- Paid source without utm_campaign: {N} (attribution gap)

### UTM Format Compliance
- Total with utm_campaign: {N}
- Matching convention: {N} ({pct}%)
- Non-compliant examples:
  - `{example1}` — {issue}
  - `{example2}` — {issue}

### Original Source Distribution
| Source | Contact Count | % of Total |
|--------|--------------|-----------|
| DIRECT_TRAFFIC | {N} | {pct}% |
| PAID_SEARCH | {N} | {pct}% |
| ... | | |

### Campaign-to-Contact Drift
| Campaign | Associated Contacts | UTM-Matched (not associated) |
|----------|-------------------|------------------------------|

### Gclid / Offline Conversion Health
- Paid-source new contacts (7d): {N}
- With gclid populated: {N} ({pct}%)
- WoW change: {delta}%
- Offline conversions imported (7d): {N}
- WoW change: {delta}%

### Recommended gtm-ops action
{If UTM convention drift: "Run /utm-builder to regenerate standardized
UTMs for upcoming campaigns"}
{If Campaign linkage broken: "Investigate HubSpot Campaign object
association workflow"}
{If gclid capture dropping: "Notify performance-marketer — attribution data degradation
may affect paid search optimization"}
```

## Anomaly Table Writes

INSERT into `anomalies` with `surface='attribution'`. One row per failing
check that exceeds threshold.

## Handoff

Weekly handoff to chief-of-staff. If gclid capture or campaign linkage issues are
detected, additionally note "This affects performance-marketer's attribution-review
skill — consider flagging."
