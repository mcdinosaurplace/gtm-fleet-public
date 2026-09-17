---
name: content-researcher:call-miner
description: >
  Mines Grain sales-call transcripts (org-wide, read-only) for content signal.
  Targets prospect and customer calls hosted by {{AE_FIRST}} or {{CEO_FIRST}}, weighting by
  HubSpot deal/ICP context, then extracts verbatim questions, friction/objections,
  competitor mentions, and category vocabulary into voice_bank — anonymized, with
  every distinct signal preserved so cross-call recurrence becomes evidence weight.
  Writes one research_packets row and a mined_meetings ledger entry per call.
  Read-only on Grain and HubSpot. Runs early in the weekly Tick, before
  topic-synthesizer.
---

# Call Miner

Mines what the market actually says in sales conversations. This skill is the
content engine's highest-signal source: a question asked in seven prospect calls
is stronger evidence than the same question seen once on LinkedIn.

**Boundary vs. chief-of-staff's brief:** chief-of-staff's meeting pull covers the *operator's own*
meetings for personal productivity. Call-miner mines *org-wide sales calls* for
content signal. Same Grain workspace, different lane, different output.

## When This Runs

- **Tick integration:** Weekly (Mon), early in the sweep — before `topic-synthesizer`.
- **Standalone:** `/content-researcher call-miner`

## MCP Dependencies

- **Grain** — essential. If Grain is unbound after the preflight retries, abort
  this skill, log it, and let the Tick continue with social/competitor signal only.
- **HubSpot** — optional. Used to classify call type and tag ICP/funnel context.
  If unbound, degrade: classify from Grain participants + title/summary heuristics,
  tag `icp_persona='unknown'`, and note reduced confidence in the journal.

## Inputs

| Source | What To Read |
|--------|--------------|
| `mined_meetings` ledger | meeting_ids already decided on (dedup — never reprocess) |
| `research_packets` | watermark: max `created_at` where `packet_type='call_mining'` |
| Grain | `list_meetings` (org-wide), `fetch_meeting_transcript` / `_notes` / `_action_items` |
| HubSpot (read-only) | company `type`/`numberofemployees`/`industry`, contact `jobtitle`/lifecycle, associated deals (`dealtype`, `dealstage`) |
| `context/personas/aaron-platform-engineer.md` | primary ICP — defines persona-fit signals |
| `context/personas/erin-technical-founder.md`, `hannah-vp-engineering.md` | secondary personas |

---

## STEP 1 — Targeting Funnel (which transcripts to ingest)

A deterministic funnel. Scope makes a call *reachable*; the prospect makes it
*on-target*. We do not filter by who hosted the call except via the prospect-path
host gate below.

### 1.0 Watermark

```sql
SELECT MAX(created_at) FROM research_packets
WHERE agent='content-researcher' AND packet_type='call_mining';
```

- If a value exists → `since = ` that timestamp (normal weekly run, ~7 days).
- If NULL (first run) → `since = datetime('now','-30 days')` (30-day backfill seed).

### 1.1 Candidate pull

`list_meetings(filters={ participant_scope: 'external', after_datetime: since })`,
paginating via `cursor` to the end of the window. Use `list_meetings` (org-wide),
**not** `list_attended_meetings`. Internal-only meetings never appear here.

Then merge in the deferred backlog:

```sql
SELECT * FROM mined_meetings WHERE outcome = 'deferred';
```

These were over the cap in a prior run and now live older than the watermark, so
`list_meetings` won't return them — they must be added to the candidate pool
explicitly. Their ledger row already carries the full Step-1 classification
(`call_type`, `icp_persona`, `funnel_stage`, `host`, `company_size`), so they
re-enter ranking with no Grain/HubSpot re-lookup.

### 1.2 Drop already-decided meetings

```sql
SELECT meeting_id FROM mined_meetings
WHERE outcome IN ('mined','mined_empty','skipped_offtarget');
```

Exclude these meeting_ids from the candidate set. `deferred` is intentionally
absent from this list, so deferred calls remain eligible and re-enter ranking
(see 1.1).

### 1.3 Quality floor (skip + ledger as `skipped_offtarget`)

- Duration < 3:00, or no fetchable transcript → `skip_reason='too_short'` / `'no_transcript'`.
- **Bot-only / no genuine external human:** the only external-scoped participant(s)
  are notetaker bots (name or email matching Fathom, Fireflies, Otter, Read.ai,
  Grain notetaker, or `*notetaker*`, or null-email bot-shaped names). This catches
  {{AE_FIRST}}↔{{CEO_FIRST}} 1:1s where a bot is the false "external" attendee →
  `skip_reason='bot_only'`.

### 1.4 Classify call type (HubSpot first, title heuristic fallback)

For each surviving candidate, take the genuine external attendee's email domain →
HubSpot company/contact/deal lookup. **First match wins:**

| Class | Signal | Action |
|-------|--------|--------|
| `partner_reseller` | `company.type ∈ {PARTNER, RESELLER}`; fallback title/summary cues: partnership, reseller, referral, revenue-share, co-host, workshop | skip + ledger (`partner_reseller`) |
| `recruiting` | title/summary cues: interview, candidate, hiring; recruiting-agency domain | skip + ledger (`recruiting`) |
| `vendor_inbound` | someone selling **to** {{COMPANY}}, not buying. Signals: ≥2 internal participants from {{COMPANY}} leadership (or a `leadership-team@` / all-hands style address) **and** the external attendee is on a freemail or consultancy domain with no HubSpot company match; title/summary cues: proposal, pitch, our platform/tool, engagement, statement of work | skip + ledger (`vendor_inbound_pitch`) |
| `prospect_sales` | open deal (`dealtype=newbusiness`, stage≠closed) **or** contact lifecycle ∈ lead→opportunity **or** `company.type=PROSPECT` | keep — **prospect path** |
| `customer` | `lifecyclestage=customer` / closed-won / `dealtype=existingbusiness` / CS pipeline | keep — **customer path** |
| `unknown` | no HubSpot match, ambiguous | see paths below |

### 1.5 Inclusion paths

A candidate enters extraction only if it matches one path:

**▸ Prospect path** *(ranked first)*
1. **Host gate:** {{AE}} **or** {{CEO}} is an internal
   participant. Match by name, or email in
   `{{AE_FIRST_LOWER}}@`, `{{CEO_FIRST_LOWER}}@` on `{{COMPANY_DOMAIN}}`.
2. **AND** ≥1 genuine external human (per 1.3).
3. **AND** either:
   - (a) `prospect_sales` per 1.4 (HubSpot contact match; open deal *not* required —
     favor pure prospects), **or**
   - (b) `unknown` per 1.4 **but** hosted by {{AE_FIRST}}/{{CEO_FIRST}} **and** neither
     partnership-shaped **nor** vendor-inbound-shaped (per the `vendor_inbound`
     row in 1.4) → ingest, tag `icp_persona='unknown'`.

   > **Why the vendor-inbound gate exists.** An inbound pitch *to* {{COMPANY}} scopes as
   > `participant_scope='external'`, clears the host gate whenever a founder sits
   > in, and survives 1.3 (the pitcher is a genuine external human, not a bot). Without
   > this gate it enters extraction and a vendor's own pitch language gets stored as
   > market voice. The shape to picture: a consultant on a freemail domain pitching a
   > reliability-tooling engagement to two {{COMPANY}} leaders. Every heuristic upstream
   > says "qualified external conversation"; the content is a sales deck aimed at us.

**▸ Customer path** *(no host gate — CS/onboarding is often led by others)*
- `customer` per 1.4 **and** sub-type ∈ {onboarding/implementation,
  QBR/check-in/expansion, renewal/at-risk/churn}. Skip billing/offboarding/support
  → ledger `skipped_offtarget` (`unknown_offtarget`).

Anything matching no path → skip + ledger `skipped_offtarget` (with `skip_reason`).
A `prospect_sales`/`unknown` call with no {{AE_FIRST}}/{{CEO_FIRST}} host → `no_host_gate`.

### 1.6 ICP sizing (weight, never a gate)

Tag `company_size` from HubSpot `numberofemployees`:
`50–500 → mid` (full Aaron weight), `10–49 → smb`, `<10 → micro` (down-weighted at
scoring, **not** excluded — a micro-SMB's API/MCP question is still Aaron signal),
unknown → `unknown`. This tag rides to the ledger; the weighting is applied by
`topic-synthesizer`, not here.

### 1.7 Rank + cap

Order the kept set: pure-prospect → existing-customer; within tier, ICP fit
(aaron > hannah > erin > unknown) then recency. Cap at **20 calls per run**.
Overflow is **not** mined this run; ledger each overflow call as
`outcome='deferred'` (capturing its Step-1 classification) and log `{N} calls
deferred`. Deferred calls are re-merged into the candidate pool every run (1.1)
and re-ranked until they make the cut — so backfill overflow is never lost when
the watermark advances.

Output: an ordered work-list `{ meeting_id, title_redacted, call_type,
icp_persona, funnel_stage, host, company_size }` → Step 2.

---

## STEP 2 — Extraction (transcript → voice_bank)

For each call in the work-list, in rank order.

### 2.1 Fetch

`fetch_meeting_transcript` (full, verbatim — the source of truth for quotes), plus
`fetch_meeting_notes` and `fetch_meeting_action_items` as a structural aid. Use the
transcript's speaker labels to split **market voice** (external speakers) from
**rep voice** (`@{{COMPANY_DOMAIN}}` speakers). Capture the market's voice; capture a rep
line only when it restates a prospect's recurring objection.

### 2.2 Extract — three entry types

| `entry_type` | Capture |
|--------------|---------|
| `question` | Literal questions the prospect/customer asked |
| `pain_point` | Friction, frustration, objections, unmet needs |
| `quote` | Verbatim language: how they word the problem, desired outcomes, competitor mentions |

**Store every distinct on-topic signal.** Dedup only *within* a single call (don't
store the same utterance twice). Never dedup across calls — cross-call recurrence
is exactly the evidence signal `topic-synthesizer` counts.

### 2.3 Theme tagging — shared vocabulary

Reuse the `voice_bank` theme labels already used by `social-listening` so the
synthesizer can cluster across sources. Shared labels:

`api_access_gating` · `automation_chain_breaks` · `multi_system_patchwork` ·
`alert_noise_ratio` · `oncall_fairness_burnout` · `shadow_it_workarounds` ·
`stakeholder_trust_anxiety` · `role_definition`

Call-specific additions (sales conversations surface these where social rarely does):

`product_ux_friction` (confusing setup, hidden settings, "no guide") ·
`migration_switching` (from an incumbent: importing rotations, re-pointing alert
sources, carrying over incident history) ·
`pricing_commercial` (cost objections, discounts, comparisons) ·
`competitor_mention` (what they compare us to / incumbent gaps) ·
`vocabulary` (the market reaching for words — category-creation signal)

Do not force a theme; leave `theme` NULL and note it if none fits.

### 2.4 Persona + funnel tagging

- `persona` inherits the call's `icp_persona` (Step 1), overridden only on strong
  per-entry signal (an MCP/API question on a Hannah-tagged call → `aaron`).
- `funnel_stage` inherits the deal stage, refined by entry content: "how do I even
  start" → `top`; "which tool does X" / comparisons → `mid`; "what's your rate
  limit / can an agent write back" / migration / pricing → `bottom`.

### 2.5 Anonymization (cardinal rule)

Scrub the customer's name, company, and any PII → a role/segment label
(*"a platform lead at a ~200-person fintech"*). **Keep** competitor and product
names and the substance — `voice_bank` is internal research; the competitor-name
block applies only to content-producer's *published* output. `source_ref` = the Grain meeting
id/URL (an internal pointer, not customer-identifying).

---

## Quiet Week Detection

Count `voice_bank` rows written across all calls this run. If **< 10**, set
`quiet_week = 1` on the `research_packets` row and log it. A quiet week is a
finding, not a failure (e.g., a light sales week, or most calls already mined).

## Workflow

### Step A — Build the work-list
Run the Step 1 funnel (1.0–1.7). Produces the ordered, capped work-list.

### Step B — Extract per call
For each call, run Step 2 (2.1–2.5). Collect voice_bank rows in memory.

### Step C — Write voice_bank rows
```sql
INSERT INTO voice_bank (
  agent, entry_type, source, trust_tier, persona, theme, content,
  source_ref, funnel_stage, captured_at, created_at
)
VALUES (
  'content-researcher', ?, 'sales_call', 'first_party', ?, ?, ?,
  ?, ?, ?, datetime('now')
);
```
`captured_at` = the call's `start_datetime`. `source_ref` = Grain meeting id/URL.

`trust_tier` is always `first_party` here and is not a judgement call: the speaker
was in an authenticated meeting we recorded, and the transcript is Grain's, not
something a stranger could author. This is the only skill that mints `first_party`
evidence — which is why call signal alone can clear the Tier 2 floor while open
web signal cannot. See `docs/agent-content-trust-policy.md`.

### Step D — Write the mined_meetings ledger
One row per call touched this run: every mined call, every skip (1.3–1.5), and
every deferred-overflow call (1.7). Use an UPSERT so a previously `deferred` row
is promoted to its terminal outcome once the call is finally mined:
```sql
INSERT INTO mined_meetings (
  agent, meeting_id, title_redacted, meeting_date, outcome, skip_reason,
  call_type, icp_persona, funnel_stage, host, company_size,
  entries_written, packet_id, mined_at
)
VALUES (
  'content-researcher', ?, ?, ?, ?, ?,
  ?, ?, ?, ?, ?,
  ?, ?, datetime('now')
)
ON CONFLICT(meeting_id) DO UPDATE SET
  outcome=excluded.outcome, skip_reason=excluded.skip_reason,
  entries_written=excluded.entries_written, packet_id=excluded.packet_id,
  mined_at=excluded.mined_at;
```
`outcome`: `mined` (≥1 entry), `mined_empty` (fetched, no usable signal),
`skipped_offtarget` (with `skip_reason`), or `deferred` (over the cap this run).

### Step E — Write the research_packets row
```sql
INSERT INTO research_packets (
  agent, packet_type, week_starting, source_count,
  quiet_week, summary, payload_path, created_at
)
VALUES (
  'content-researcher', 'call_mining',
  date('now', 'weekday 1', '-7 days'),  -- Monday of the run week
  ?,    -- count of calls mined (outcome='mined'), NOT entry count
  ?,    -- 0 or 1 quiet_week flag
  ?,    -- one-paragraph summary (format below)
  NULL, -- entries live in voice_bank; no separate payload file
  datetime('now')
);
```
**Summary format:** `"Mined {N} calls ({P} prospect, {C} customer); {E} voice_bank
entries across {T} themes. Skipped {S} off-target. Strongest signal: [{theme}] —
{count} entries, e.g. '{verbatim snippet}'. {Quiet week note if applicable.}"`

## Output to Journal

Under `### Research Sweep`:
```
[call_mining] → {calls_mined} calls, {voice_bank_count} new entries ({P} prospect / {C} customer)
{quiet_week flag if <10 entries}
Skipped: {S} off-target ({breakdown by skip_reason})
Deferred: {N} calls over the 20-cap (re-surface next run)
Top themes: {themes with >2 entries}
HubSpot: {bound | unbound — reduced ICP confidence}
```

## Boundary Rules

- **Read-only on Grain and HubSpot.** Never write, tag, or modify anything on
  either platform.
- **Sales calls only.** Do not mine internal meetings, all-hands, or the running
  operator's personal 1:1s — that is chief-of-staff's lane (see roster/chief-of-staff/prompt.md,
  Expansion Plan 4c).
- **Verbatim + anonymized.** Quotes are stored exactly as said, customer identity
  scrubbed. Never paraphrase a quote; never store a customer name or company.
- **No fabrication.** If a transcript is empty or a call yields no usable signal,
  ledger it `mined_empty`. Never invent representative quotes or composite signals.
- **Cap discipline.** Never exceed 20 mined calls per run; ledger overflow as
  `deferred` so it is re-evaluated next run rather than lost.
