# WBR Audit Artifact — {YYYY-MM-DD} (Scribe Weekly Tick)

Template for the audit artifact Scribe writes to `wbr/YYYY-MM-DD.md` alongside the
~~knowledge base (Notion) page. Every number on the published page must trace to a row
in this file; every row here must trace to a query. The worked values below are the
Orrery demo seed (`scripts/seed_demo_state.py --as-of yesterday`), not real data.

**Run:** scheduled Wednesday weekly Tick, on-cadence ({Wed YYYY-MM-DD}, {Qn YYYY})
**Target page:** Marketing Update — {upcoming Friday}
**Prior-week page:** Marketing Update — {prior Friday} (`{{NOTION_COLLECTION_ID}}`)

---

## Data provenance

| Block | Source |
|-------|--------|
| MQL / SAL / SQL / CVRs / Pipeline | revops-watchdog `funnel_snapshots` latest row, `snapshot_date={today}` ({hours} h old at Tick start — must be ≤ 24 h) |
| MELs | `gtm_scorecard` freeze run this Tick (Step 1c), `agent='revops-watchdog'`, `metric='mel'`, `period='{YYYY-MM}'` |
| Traffic (Organic Search + Channel Mix) | performance-marketer `gtm_scorecard` snapshot `{today}`, `definition_version='v1.5'` — zero days stale required; otherwise fall back to the last complete week and say so |

**Step 1c freeze:** {rows} rows ({metrics} metrics × {months} months), `definition_version='v1.5'`, verified present from a fresh connection after commit.

**Month-turnover trigger (Step 1e): {TRUE|FALSE}.** `day_of_month < 7` AND `month(today) != month(last journaled Tick)` → carry the prior-month recap block alongside MTD. Otherwise Summary carries the MTD block only.

---

## Funnel literals written to Summary ({Month} MTD, Day {N})

| Metric | Value | Source row |
|---|---|---|
| MEL | 412 | `gtm_scorecard` id={id} |
| MQL | 71 | `funnel_snapshots` id={id} |
| SAL | 42 | same row |
| SQL | 12 | same row |
| MQL→SAL CVR | 59.2% | computed from the row, not re-derived from ~~crm |
| SAL→SQL CVR | 28.6% (**MED** — below the 35% threshold, day 3 of the watch) | same row |
| Pipeline | $1,126,400 / 88 open deals | same row |

### Across-moment source drift (not a trust breach)
When revops-watchdog's morning snapshot and a live ~~crm re-pull disagree by a few units, the snapshot wins on the page and the delta is logged here. Restate only when the snapshot itself is corrected.

### Pipeline rendering note
Pipeline is written as `$X / N deals`. If the deal count is unavailable, write the amount alone and flag it — never invent the count.

## Step 1c restatements: {count}
List each restated cell as `metric / period: old → new (reason)`.

## Traffic (Step 1d)
Organic sessions 31,200 (+4% WoW) · Paid sessions 8,900 (−2%) · Demo requests 138 (+6%). Source: performance-marketer `gtm_scorecard` rows for `{today}`.

## Page composition
Summary → Traffic (Organic Search, Channel Mix) → Project Updates → Content and Product Marketing → Website and Design → GTM Ops → Challenges → Next up → Asks → Notes. Headings and property names follow `docs/notion-markdown-syntax.md`.

## Notion properties
| Property | Value |
|---|---|
| Department | Marketing (`{{NOTION_DEPT_MARKETING_PAGE_ID}}`) |
| Review in | Business Review (`{{NOTION_BUSINESS_REVIEW_PAGE_ID}}`) |
| Week of | {Monday of the review week} |
| Status | Draft — owners fill sections by Thursday 07:00 PT |

## Page content as published

### Summary
{The MTD funnel block above, one line per metric, with the MED watch item called out in one sentence.}

### Traffic
#### Organic Search
{Top movers from `keyword_rankings`: 3 gains, 3 losses, one sentence each.}
#### Channel Mix (users)
{Regime per Step 1e: MTD-only or prior-month recap + MTD.}

### Project Updates
Owner: {{HEAD_OF_MARKETING}}. {Pre-filled from `pm_projects` health: on_track / at_risk / off_track counts, then the owner's narrative.}

### Content and Product Marketing
Owner: {{CONTENT_LEAD}}. {Topic backlog delta from content-researcher's last Tick; briefs in flight from content-producer.}

### Website and Design
Owner: {{DESIGN_LEAD}}. {brand-designer packets delivered / pending.}

### GTM Ops (MOPs / RevOps)
Owner: Scott McKeighen. {revops-watchdog anomalies opened / resolved this week; workflow health flags.}

### Challenges · Next up · Asks · Notes
{Owner-authored. Scribe leaves these empty except for carried-forward items it was told to keep.}

## Section owners notified
{{HEAD_OF_MARKETING}}, {{CONTENT_LEAD}}, {{DESIGN_LEAD}}, Scott McKeighen — one grouped ~~chat message in `#team-marketing`, deadline Thursday 07:00 PT.

---

## OPERATOR-DIRECTED CORRECTION — {timestamp} ({operator}, live)
{Only present when a human corrected the page after the Tick. Record what changed, the verification re-pull, and any standing implication flagged — but not self-applied — for the next Tick.}
