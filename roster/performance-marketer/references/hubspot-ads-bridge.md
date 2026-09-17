# HubSpot Ads Bridge — Verification Method

How to establish what `~~ads` data is actually readable through the `~~crm` connection
for this portal, and how to join it to platform-side spend. This is a **method**, not a
findings record: run the probes below against whatever portal is bound, write the answers
into the run's journal entry, and re-run the method when the portal or the connector scope
changes.

Used by `performance-marketer:spend-watch` (paid-social lead side) and
`performance-marketer:attribution-review`. `revops-watchdog:attribution-integrity-audit`
reads the UTM-family semantics below.

## The Shape of the Problem

`~~crm` reliably gives the **numerator** — leads by platform, campaign, and day. It does
not give the **denominator** — spend, impressions, clicks. Assume cost data is absent from
the connector surface until a probe proves otherwise, and treat its absence as structural
rather than as a permissions failure.

Cost comes from the platform side: `scripts/google_ads_pull.py` for Google Ads, and the
paid-social platform's own reporting API or a manual export for everything else.

---

## Probe 1 — What object types and properties exist

1. Ask the connector for its own tool and object-type inventory. Record whether any ads
   entity types (campaign, ad group, ad, creative) are exposed as CRM objects at all.
2. Sweep the contact and deal property schemas for any cost-bearing field (`spend`,
   `cost`, `impressions`, `clicks`, `cpc`, `cpl`). Record the result as a yes/no.
3. Attempt the campaign-analytics call once. Record one of: works, requires
   re-authorization, or not registered server-side.

**Write down the answer and stop re-probing it inside the same portal.** A negative here
is a standing constraint for the rest of the cycle, not something to retry every run.

## Probe 2 — Lead counts by platform / campaign / day

Search `contacts` filtered on `hs_analytics_source` with a `createdate` range. The search
`total` is the authoritative cohort size; request only the properties you will use.

Properties worth requesting:

- `hs_analytics_source`, `hs_latest_source` — original vs. latest touch cohorts
- `hs_analytics_source_data_1`, `hs_analytics_source_data_2` — the drilldown pair
- `hs_analytics_first_url` — carries the `hsa_*` join keys
- `hs_google_click_id` and the paid-social click-id property — presence checks
- `createdate`

`HAS_PROPERTY` / `NOT_HAS_PROPERTY` are the operators for coverage audits. Null properties
are silently omitted from results, so absence in a returned record means unpopulated.

## Probe 3 — Confirm drilldown semantics per platform

**The meaning of the drilldown pair differs by platform.** Never assume
`source_data_1` is "campaign" everywhere. Verify, per source value, by sampling records
whose campaign you can identify independently:

| Property | Verify what it holds for `PAID_SEARCH` | Verify what it holds for `PAID_SOCIAL` |
|----------|----------------------------------------|----------------------------------------|
| `hs_analytics_source_data_1` | campaign name, or the platform label | campaign name, or the platform label |
| `hs_analytics_source_data_2` | converting keyword, or campaign name | campaign name, or the ad-set label |

Record the mapping you confirmed. Campaign names arrive lowercased — normalize both sides
before joining to platform data.

## Probe 4 — Entity ids via first-URL parsing

`hs_analytics_first_url` preserves the landing URL including the `hsa_*` parameters that
the ads bridge appends. Parse and confirm which are present:

| Param | Meaning |
|-------|---------|
| `hsa_acc` | Ad account id |
| `hsa_cam` | Campaign id |
| `hsa_grp` | Ad group / ad set id |
| `hsa_ad` | Creative id |
| `hsa_kw` | Keyword (paid search) |
| `gclid` | Google click id |

Leads that arrive through a platform's **native lead form** never visit the site, so check
whether their first URL is the platform's own lead-form URL — it can still carry
`hsa_cam` / `hsa_grp` / `hsa_ad`, which keeps them joinable to campaign and creative
without a site session. Numeric ids resolve to names only on the platform side.

---

## UTM Properties: Initial vs. Live

The portal carries two parallel UTM families on contacts. They are **not**
interchangeable, and choosing the wrong one silently corrupts source attribution.

| Family | Properties | Behavior | Use for |
|--------|-----------|----------|---------|
| **Initial (first-touch)** | `utm_source___initial`, `utm_medium___initial`, `utm_campaign___initial`, `utm_term___initial`, `utm_content___initial` | Written once, never updated | Original-source attribution — the designed purpose |
| **Live (latest-touch)** | `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content` | Overwritten on each subsequent form fill | Latest-touch context only; never original source |

**How the engine works:** site forms carry hidden UTM fields that write the live `utm_*`
properties on every fill; a propagation step copies live → `*___initial` when the initial
value is blank.

### The failure mode to test for

The hidden fields capture the **form-fill session's** parameters, not the originating ad
click's. If the paid click and the form fill happen in different sessions, the campaign
identity is lost before the form ever fires. Test it:

1. Take the recent cohort where `hs_analytics_source` is a paid value.
2. Measure coverage of `utm_source___initial` and `utm_campaign___initial` separately.
   High source coverage with near-zero campaign coverage is the signature of cross-session
   UTM loss — the source is being derived from the *return* session.
3. Check whether live and initial values are identical across the cohort. If they are, the
   propagation step is working and the defect is upstream, in capture.
4. Check the paid-social cohort separately. Native-lead-form leads never touch a site form,
   so their UTM family is expected to be empty by construction, not by defect.
5. Check whether list imports are populating the family. Imports write these properties
   directly and will inflate any coverage number that does not exclude them.

**The fix is UTM persistence, not the forms.** Persist first-touch UTM parameters
client-side on first landing (write-once when parameters are present), and have the form
script read the persisted values into the hidden fields. Until that ships:

- `hs_analytics_*` drilldowns plus `hsa_*` first-URL parameters are the only reliable
  campaign-level source for paid leads — the tracking cookie pins original source at first
  visit, while the UTM engine restarts every session.
- Treat `utm_source___initial` on paid leads as suspect; it often records a later session.

`revops-watchdog:attribution-integrity-audit` tracks `utm_campaign___initial` coverage on
new paid-search contacts. Rising coverage is the signal that UTM persistence landed.

---

## How performance-marketer Uses This

**Daily (spend-watch, paid-social lead side):** count paid-social contacts created
yesterday against the trailing 7-day average. Zero leads on a day a campaign is supposed
to be live is a meaningful anomaly even with no spend data. Group by the confirmed
campaign-name property for per-campaign lead flow.

**Weekly (creative-optimizer):** parse `hsa_ad` from the week's paid-social first URLs →
leads per creative id → join to the platform's creative report for cost per lead.

**CPL math:** `platform spend ÷ ~~crm lead count`, joined on campaign id (`hsa_cam`) or on
the lowercased campaign name.

## Quirks to Re-check Each Cycle

- Null properties are omitted from search results — absence means unpopulated, not zero.
- Campaign names are lowercased in drilldowns; normalize before joining.
- A custom source-category property can disagree with `hs_analytics_source` because the
  rollup logic differs. Do not use a custom rollup for paid filtering.
- Decide pagination strategy from the cohort size the probe returns, not from habit.
- Re-run Probe 1 after any connector re-authorization or scope change.
