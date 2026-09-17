---
name: scribe:wbr-prep
description: >
  Weekly Business Review preparation. Reads revops-watchdog's funnel snapshot and
  anomaly state from shared state, creates the next WBR page in Notion
  by duplicating the prior week's page, populates the Summary section
  with fresh metrics (plus a prior-month recap block right after a month
  turns over) and refreshes the Traffic section every week from performance-marketer's
  gtm_scorecard rows (rolling 6-month Organic Search + 3-month Channel
  Mix), and posts a single grouped message to #team-marketing naming
  section owners, prior-week callouts, and the Thursday 7:00 AM PT deadline.
---

# WBR Prep

## When This Runs

- **Tick integration:** Every Wednesday 09:00 PT, as Scribe's weekly Tick
- **Standalone:** `/scribe wbr-prep` or `/scribe weekly`
- **Off-cadence manual:** supported, but will note the non-Wednesday run in the journal

## Invocation arguments

- No argument → weekly WBR, post to `#team-marketing`
- `--notify=channel` (default for wbr-prep) → group message to `#team-marketing`
- `--notify=dm` → per-owner direct messages instead of channel post (ad-hoc only)
- `--channel=<name>` → override the default channel (only when `--notify=channel`)
- `--dry-run` → write the local preview to `wbr/YYYY-MM-DD.md` but do not touch Notion
  or Slack
- `--slack-only` → SEND-ONLY retry path. Skips Notion write entirely; reads the
  most recent `wbr/YYYY-MM-DD.md` for the page URL and `localwork/scribe/
  slack-draft-YYYY-MM-DD.md` for the composed message; sends the deferred
  `#team-marketing` post. Use this when a prior weekly run created the Notion
  page but Slack was unbound at the time. See Step 12.

For the scheduled Wednesday run, none of these flags apply — the flow is fixed.

## Definitions

- **Updates database:** `collection://{{NOTION_UPDATES_DB_ID}}`
- **Department "Marketing" relation:** `https://www.notion.example/{{NOTION_DEPT_MARKETING_PAGE_ID}}`
- **Review in "Business Review" relation:** `https://www.notion.example/{{NOTION_BUSINESS_REVIEW_PAGE_ID}}`
- **Default channel:** `#team-marketing`
- **WBR meeting day:** Friday (the page date is the upcoming Friday)
- **Deadline for owners:** Thursday 07:00 AM PT (the day after posting)
- **"This week":** Monday 00:00 through Sunday 23:59 UTC of the current week

## Section Owners

| Section | Owner | Updates via |
|---------|-------|------------|
| Summary (funnel metrics) | Scott McKeighen | Auto-populated by Scribe |
| Project Updates | {{HEAD_OF_MARKETING}} | Manual — prompted via `#team-marketing` |
| Content and Product Marketing | {{CONTENT_LEAD}} | Manual — prompted via `#team-marketing` |
| Website and Design | {{DESIGN_LEAD_FIRST}} | Manual — prompted via `#team-marketing` |
| GTM Ops (MOPs / RevOps) | Scott McKeighen | Manual — prompted via `#team-marketing` |
| Challenges / Next Up / Asks / Notes | All | Manual — open space |

## Audience & Tone

This report is read by people from other teams (engineering, product, leadership).

**Content rule (non-negotiable):** The WBR is strictly human content, with two
exceptions: HubSpot funnel literals (MEL counts, MQL counts, SAL counts, SQL
counts, pipeline dollars, conversion rates) in the Summary section, and GA4
traffic literals (users, sessions, channel breakdowns) in the Traffic section.
Both are numbers-only — Scribe does NOT generate:

- Trend narratives ("MQL inflow up 38% week over week")
- WoW or DoD delta commentary in prose
- Anomaly interpretations or "Known anomalies" sub-sections
- Data-source notes or methodology callouts
- Summary-property prose beyond the literal metrics

If there's a data gap or an anomaly that seems material, Scribe writes a handoff to
chief-of-staff — NOT into the WBR page. The WBR page stays clean. Owners add their own
commentary by editing their sections after the `#team-marketing` prompt.

This rule exists because the WBR is read as human-authored content by people outside
the marketing team. Agent interpretations buried in the page erode that signal.
Keep Scribe's output on the page to HubSpot actuals only.

Voice guidance for the one place Scribe does author prose (the Summary Notion
property — a 1-2 sentence literal restatement of the funnel numbers):

- Avoid marketing jargon without context
- Keep it concrete: names, numbers, dates — no trend framing
- Do not use em-dashes
- No AI writing patterns: no "leverage", "utilize", "streamline", "robust",
  "comprehensive"

---

## Step 0. MCP Preflight — abort BEFORE any Notion or Slack write if connectors unbound

This step is non-skippable. It guarantees the skill aborts cleanly when an
essential MCP connector is unbound, rather than producing a half-finished WBR
(Notion page created, Slack post never sent). A weekly Tick hit exactly this
failure mode and motivated this Step 0.

Run the bounded retry sequence from `docs/mcp-preflight.md` for Scribe's
required connectors:

| Connector | Essentiality | Probe |
|-----------|--------------|-------|
| Notion    | essential    | `+notion search`        |
| Slack     | essential    | `+slack send_message`   |
| HubSpot   | essential¹   | `+hubspot crm_objects`  |

¹ HubSpot is only required if revops-watchdog's same-day snapshot is missing (Step 1b
fallback). If a fresh revops-watchdog snapshot exists, HubSpot is optional. The preflight
still probes it so the journal entry has a complete connector inventory, but a
HubSpot-only failure with a fresh revops-watchdog snapshot does not abort.

### Step 0a. Probe (t=0)

Run `ToolSearch` for each probe in parallel. Each must return at least one
matching tool schema.

### Step 0b. First retry (t≈60s)

If any essential connector is missing, wait 60 seconds, re-probe missing only.

```bash
python3 -c "import time; time.sleep(60)"
```

### Step 0c. Final retry (t≈4min)

If still missing, wait 180 seconds, re-probe missing only.

```bash
python3 -c "import time; time.sleep(180)"
```

### Step 0d. Fail state — abort

If any essential connector is still missing after Step 0c:

1. Append HIGH ops-incident to `state/journal/ops-incidents.md`:

   ```
   ## {ISO 8601 UTC} | HIGH | Scribe | MCP_BIND_FAILURE — {connector(s)} unbound after preflight retries

   Required connectors: Notion (essential), Slack (essential), HubSpot (essential)
   Bound: {list}
   Missing after 3 attempts (~5 min): {list}

   Action: aborted before Notion write. No WBR created.
   Recovery: operator to confirm MCP connector(s) bound, then re-run /scribe wbr-prep
     in a fresh session. If Slack is the only failing connector and the Notion
     page was created in a prior aborted run (rare), use /scribe wbr-prep --slack-only.
   ```

2. Append HIGH handoff to `state/journal/handoffs.md` addressed to Scott
   (NOT chief-of-staff — this is operator-action-required, not data routing):

   ```markdown
   ## {ISO 8601 UTC} | Scribe → Scott | HIGH: WBR aborted — MCP_BIND_FAILURE on {connector}

   - Cause: {connector} essential MCP unbound after 3 preflight retries (~5 min total).
   - Action: aborted before Notion write. No partial state committed.
   - Recovery (operator): {steps}
   - Blast radius: this week's Marketing WBR not posted. Owners not notified.
   - Severity rationale: WBR is a recurring deliverable for Friday's review meeting.
     Two Tick misses in a row leaves Friday's meeting without fresh funnel literals.
   ```

3. PushNotification (best-effort, non-blocking):
   - Message: `Scribe Tick aborted — {connector} MCP unbound. WBR for {Friday date} not posted. See ops-incidents.md.`
   - This pulls the operator's attention immediately rather than waiting for
     chief-of-staff's next AM Tick to surface the incident.

4. Append a journal entry to `state/journal/scribe.md` flagging the abort.
5. Commit and push state.
6. **EXIT.** Do not proceed to Step 1.

If all essential connectors are bound (or HubSpot-only is unbound and revops-watchdog
snapshot is fresh), proceed to Step 1.

---

## Step 1. Pull funnel data — prefer revops-watchdog state, fall back to HubSpot

### 1a. Try revops-watchdog's same-day snapshot first

```sql
SELECT id, snapshot_date, mqls, sals, sqls, pipeline_value,
       mql_to_sal_rate, sal_to_sql_rate, notes, created_at
FROM funnel_snapshots
WHERE agent = 'revops-watchdog'
  AND snapshot_date = date('now')
ORDER BY id DESC
LIMIT 1;
```

If a row exists and `created_at` is within the last 24 hours, use it as the
canonical figure for today's WBR. Record the source as "revops-watchdog snapshot (id=N)" in
the journal.

### 1b. Fall back to HubSpot only when revops-watchdog data is missing or stale

If step 1a returned no row, or the row is >24h old, invoke the HubSpot queries
defined in `roster/funnel-stats/prompt.md` verbatim. This is the same query set
revops-watchdog uses via `funnel-watch`. Note the fallback in the journal and include a one-
liner in the handoff to chief-of-staff so the HubSpot MCP availability is tracked.

### 1c. Refresh the GTM scorecard funnel snapshot (alongside the extraction)

The WBR consumes monthly funnel series and projections from the
`gtm_scorecard` table (see `docs/gtm-scorecard-definitions.md`). Per Scott,
this snapshot is taken **alongside the WBR funnel extraction**
— at WBR-crafting time, not on a separate clock — so the WBR and the
scorecard always cite the same frozen data.

Check for a same-day funnel snapshot:

```sql
SELECT COUNT(*) FROM gtm_scorecard
WHERE agent = 'revops-watchdog' AND snapshot_date = date('now');
```

If zero rows: run `revops-watchdog:funnel-scorecard`
(`roster/revops-watchdog/skills/funnel-scorecard.md`) now — it writes the frozen
rows, computes projections and restatements, and journals under revops-watchdog's
protocol. If rows exist, use them as-is.

The Summary section continues to carry the MTD literals from Step 1a/1b;
the scorecard rows supply monthly series + projections wherever the WBR
template calls for them.

**MELs:** `funnel_snapshots` (Step 1a/1b) does not carry a
MEL column — MEL is standing-sourced from this step's `gtm_scorecard` rows
instead (`agent='revops-watchdog'`, `metric='mel'`), for BOTH the current month
(`period` = this month, `is_complete=0`, MTD value) and, when the
month-turnover trigger (Step 1e) fires, the month that just closed
(`is_complete=1`). No `funnel_snapshots` migration, no change to revops-watchdog's daily
`funnel-watch` — this reuses data this step already guarantees is fresh.

```sql
SELECT period, value, is_complete FROM gtm_scorecard
WHERE agent = 'revops-watchdog' AND snapshot_date = (SELECT MAX(snapshot_date) FROM gtm_scorecard WHERE agent='revops-watchdog')
  AND metric = 'mel' AND period IN ('{current YYYY-MM}', '{prior YYYY-MM if turned_over}');
```

## Step 1d. Pull traffic data — gtm_scorecard rows from performance-marketer

**The Traffic section (Organic Search + Channel Mix) is Scribe-refreshed every
Tick, not frozen/copy-forwarded.** Source:
`gtm_scorecard` table, `agent='performance-marketer'` (populated by
`roster/performance-marketer/skills/traffic-scorecard.md`, definitions in
`docs/gtm-scorecard-definitions.md` v1.4+).

### Staleness check — provoke performance-marketer if stale

```sql
SELECT MAX(snapshot_date) FROM gtm_scorecard WHERE agent = 'performance-marketer';
```

If the most recent `performance-marketer` snapshot is more than 6 days old (or no
`performance-marketer` row exists), spawn a standalone ad hoc run of
`roster/performance-marketer/skills/traffic-scorecard.md` before proceeding. This is a
casual nudge, not a formal escalation — frame it as "I need this for the
WBR, can you run it" per the skill's v1.4 "Ad-hoc trigger from Scribe"
clause. Wait for it to finish, then re-query.

If performance-marketer's ad hoc run itself fails (GA4 unreachable, credentials
missing), fall back to the most recent `performance-marketer` snapshot available, note
the staleness in the journal, and log a LOW ops-incident. Do NOT block the
WBR on a Traffic refresh — funnel data (Step 1a/1b) is the load-bearing
content; a stale-but-present Traffic section is an acceptable degradation.

### Organic Search — rolling 6-month window (5 trailing closed + current MTD)

```sql
SELECT metric, period, value, is_complete, projected
FROM gtm_scorecard
WHERE agent = 'performance-marketer'
  AND snapshot_date = (SELECT MAX(snapshot_date) FROM gtm_scorecard WHERE agent='performance-marketer')
  AND metric IN ('organic_users', 'organic_sessions')
ORDER BY period;
```

Keep the 5 most recently closed months (`is_complete=1`) plus the current
month (`is_complete=0`). Drop anything older — the table always shows
exactly 6 month-rows; the oldest one rolls off on its own each week as a
new month closes.

For the row representing the month that **just closed** (the freshest
`is_complete=1` row), also look up the projection that was made for it
while it was still in progress:

```sql
SELECT value AS mtd_at_time, projected
FROM gtm_scorecard
WHERE agent = 'performance-marketer' AND metric = '{organic_users|organic_sessions}'
  AND period = '{that month, YYYY-MM}' AND is_complete = 0
ORDER BY snapshot_date DESC LIMIT 1;
```

Render that one row with three numbers: **Actual** (this snapshot's closed
value) / **Projected** (the last pre-close projection found above) / **Δ**
(% actual vs projected). Every other closed month in the window renders a
single Actual number, as before. The current (in-progress) month renders
MTD Actual + Projected, same two-value shape the table has always used for
the in-progress month — it just now lives inside the same 6-row window
instead of a separate "projected" row.

Keep the inline pacing-note sentence below the table (the existing
"Organic pacing ~flat MoM..." style) — update its content each week to
reflect the current comparisons. This note is narrower than the Summary
content rule (a little framing is fine here, as it always has been); keep
it to 1-2 sentences, numbers-first.

### Channel Mix — shape depends on where in the month the WBR falls (Scott)

Users only — Channel Mix has never tracked sessions; do not add a sessions
column. Include every channel GA4 returns (Direct, Organic Search, Organic
Social, Paid Search, Paid Social, Referral, Email, AI Assistant, Cross-network,
Unassigned, Paid Other, …) — not a fixed list, whatever rows exist in the
snapshot — ordered by the previous full month's value descending.

Which of two shapes to use is set by the **WBR page date** (the upcoming
Friday), day-of-month:

**Early-month — WBR Friday on/before the 14th (the first ~2 WBRs of the month,
i.e. through the first full business week).** The current month is too sparse
to project reliably, so show the two most recently CLOSED full months and the
delta between them:

`Channel | {Month-2} (full) | {Month-1} (full) | Δ ({Month-1} vs {Month-2})`

(e.g. the July 3rd and July 10th WBRs show May full / June full / Δ.) This is
also the window in which the Summary month-turnover recap block appears — the
two mechanics share the same early-month window.

**Mid/late-month — WBR Friday on/after the 15th (3rd Friday onward).** The
current month now has enough data to pace. Show the previous locked full month,
the current-month MTD, the current-month projection, and the delta of the
projection vs the locked month:

`Channel | {Previous Month} (full) | {Current Month} MTD | {Current Month} (projected) | Δ (projected vs {Previous Month})`

(e.g. the July 17th / 24th / 31st WBRs show Jun full / Jul MTD / Jul projected / Δ.)

In BOTH regimes the delta is full-month vs full-month — closed-vs-closed early,
projected-full vs closed late — never MTD vs a full month (apples-to-oranges).

```sql
SELECT metric, period, value, is_complete, projected
FROM gtm_scorecard
WHERE agent = 'performance-marketer'
  AND snapshot_date = (SELECT MAX(snapshot_date) FROM gtm_scorecard WHERE agent='performance-marketer')
  AND metric LIKE 'channel_users:%'
  AND period IN ('{the periods the active regime needs}')
ORDER BY metric, period;
```

Per-channel `projected` (full-month pacing) is populated on the in-progress
month's rows. For any channel whose current-month figures are still settling —
the set performance-marketer flags, historically Referral / Unassigned / Cross-network,
driven by GA4's same-day attribution processing — leave its projection and
delta cells blank ("—" / "not yet settled") rather than publish a distorted
pacing number.

**Interpretive note below the table:** plain English for a lay audience — the
largest source, what is pacing up or down, which small channels are not
reliable yet. Do NOT surface internal shorthand or the technical "GA4 same-day
attribution-processing lag" phrasing; say it in plain terms (e.g. "still
settling and would overstate the month-end trend"). Keep it to 1-3 sentences.

performance-marketer's own standalone weekly scorecard document may still use the
same-day-count comparator for its Monday-call purposes per
`traffic-scorecard.md` v1.4 — that is a different document, not the WBR.

## Step 1e. Determine the month-turnover trigger (Summary recap)

Compute once per Tick:

```
turned_over = (day_of_month(today) < 7) OR (month(today) != month(last journaled Scribe Tick date))
```

The "last journaled Scribe Tick date" is the timestamp of the most recent
`## {timestamp} | Weekly Tick` entry in `state/journal/scribe.md` — already
read in Librarian Protocol Step 2, no extra read needed.

If `turned_over` is TRUE, the Summary section gets an additional recap
block for the month that just closed, placed BEFORE the current MTD block
(see Step 4). If FALSE, Summary contains only the current MTD block — the
existing behavior, unchanged.

This is intentionally narrow: it fires for the Tick(s) right after a month
boundary and then stops on its own — day-of-month climbs past 6, and "last
Tick was a different month" becomes false once Scribe has run at least
once in the new month. No manual reset needed. It is independent of the
Traffic section's rolling 6-month window (Step 1d), which always shows the
same 6 months regardless of this trigger.

## Step 2. (removed) No anomaly narrative in the WBR

Earlier versions of this skill inserted a "Known anomalies from revops-watchdog" sub-section
under Summary. That violates the content rule: it is agent interpretation on a
human-authored page. Do NOT include it.

Anomalies are revops-watchdog's responsibility to handoff to chief-of-staff; chief-of-staff decides how to
surface them. Scribe's job on the WBR is to publish the funnel actuals and leave
commentary to the humans who will read and add to the page.

If the anomalies table has open HIGH/MED rows and you believe the WBR reader should
see them, write a separate handoff to chief-of-staff — not a section in the page.

## Step 3. Find last week's WBR page

```
notion-search query="Marketing Update" data_source_url="collection://{{NOTION_UPDATES_DB_ID}}"
```

Find the page with the most recent date. This is the template for this week.

Fetch the full content via `notion-fetch` on the page ID. Parse each section:
Project Updates, Content and Product Marketing, Website and Design, GTM Ops,
Challenges, Next Up, Asks, Notes. Save each section's text — you'll need it both
for the new page (1:1 copy-forward) and for the `#team-marketing` message (prior-
week callouts).

If last week's page is missing, note "no prior-week reference" and proceed. The new
page will use the Summary-only format with empty section placeholders (owners will
write from scratch).

## Step 4. Build the new page

### Properties

Relation properties must be passed as plain strings (not arrays) to `notion-create-pages`.

- **Name:** `Marketing Update — <mention-date start="YYYY-MM-DD"/>` (date = upcoming Friday)
- **Status:** "On track" (default — owners can change after review)
- **Department:** `"https://www.notion.example/{{NOTION_DEPT_MARKETING_PAGE_ID}}"`
- **Review in:** `"https://www.notion.example/{{NOTION_BUSINESS_REVIEW_PAGE_ID}}"`
- **date:Date:start:** upcoming Friday's date in YYYY-MM-DD format
- **date:Date:is_datetime:** 0
- **From:** {{HEAD_OF_MARKETING}} (Notion user ID: `{{NOTION_COLLECTION_ID}}`) —
  plain string, not mention syntax
- **Summary:** a 1-2 sentence literal restatement of the funnel numbers. NO trend
  framing. NO WoW deltas in prose. Example:
  > "April MTD (as of 4/22) has 62 MELs, 59 MQLs (19 inbound, 40 auto), 13
  > scheduled demos and 10 completed. Active open pipeline: $4.60M across 47 deals."

### Content structure

Copy the EXACT structure and content from last week's page, with these changes:

1. **Replace the Summary section** with the fresh funnel metrics block from Step 1.
   Use the exact shape of the prior week's Summary block — bullet hierarchy, label
   capitalization, asterisk footnote, and pipeline line — so that Scribe's output
   is visually indistinguishable from the funnel-stats-authored predecessors.
   Do not add narrative. Do not add "Known anomalies". Do not add data-source notes.

   **Every block (current MTD, and the recap block when present) leads with a
   MELs line**: "**MELs - {count}**" as the first bullet,
   before the MQL breakdown — a plain literal count, no CVR shown here (the
   `mel_to_mql_pct` scorecard metric is not part of the WBR block). Source per
   Step 1c's MEL note above (`gtm_scorecard`, `agent='revops-watchdog'`, `metric='mel'`
   — current month's MTD row for the MTD block, closed-month row for the
   recap block). This is now standing — every Tick, not conditional on
   anything.

   **If the month-turnover trigger (Step 1e) is TRUE**, insert a recap block for
   the month that just closed BEFORE the current MTD block, in the SAME bullet
   shape as the MTD block (MELs, MQL breakdown, MQL→SAL, SAL→SQL), labeled with
   the month name (e.g. "**June**" / "**July MTD**"). Source the closed month's
   numbers from `gtm_scorecard` (revops-watchdog's `funnel-scorecard` rows, Step 1c) —
   do not re-derive from HubSpot. If a verified MQL P1/P2/Outbound sub-breakdown
   isn't available for the closed month (e.g. `gtm_scorecard` only stores the
   total), publish the MQL total without the sub-breakdown rather than showing
   an unverified split. The recap block does NOT get its own pipeline
   line — pipeline is a point-in-time snapshot, not a monthly aggregate, so it
   stays as a single "Active Open Pipeline" bullet below BOTH blocks, current as
   of today only. If `turned_over` is FALSE, omit the recap block entirely —
   Summary contains only the current MTD block, as before.

2. **Replace the Traffic section** (Organic Search + Channel Mix) with the
   rolling data from Step 1d. This is no longer a verbatim copy-forward — the
   Organic Search table always shows the current 6-month rolling window (5
   trailing closed months + current MTD, oldest dropping off each week), and
   the Channel Mix table always shows current MTD + previous full month + month-
   prior full month + Δ, per Step 1d's exact shapes. Update the inline Organic
   Search pacing note each week; do not carry forward a stale one.

3. **Copy ALL remaining sections verbatim** — Project Updates, Content and
   Product Marketing, Website and Design, GTM Ops, Challenges, Next Up, Asks, and
   Notes. Every section retains its full content from last week. Owners edit in
   place after the `#team-marketing` prompt. Do NOT clear any section. The
   copy-forward is the whole point: owners see last week's content and update it
   rather than starting from scratch.

Keep all callout blocks (the gray instruction prompts). Keep all links, bullets,
sub-bullets, and formatting exactly as they appeared.

**CRITICAL:** Only Summary and Traffic change (Traffic every week now; Summary's
recap block only when `turned_over` is TRUE). Everything else is 1:1 from last
week.

## Step 5. Local preview — scheduled runs auto-proceed, interactive runs gate

### Scheduled run (default Wednesday 09:00 PT)

No preview gate. The schedule is the pre-authorization. Save `wbr/YYYY-MM-DD.md` as
an audit artifact and continue to Step 6 immediately.

### Interactive / manual run

1. Save the complete page to `wbr/YYYY-MM-DD.md` (date = today)
2. Print the full WBR content to the conversation
3. Print the proposed Notion properties
4. Ask: "WBR preview is saved to `wbr/YYYY-MM-DD.md`. Ready to publish to Notion?"
5. Wait for explicit confirmation before creating the Notion page

### `--dry-run` mode

Save `wbr/YYYY-MM-DD.md` and stop. Do not call Notion. Do not call Slack.

## Step 6. Post to Notion

Create the page using `notion-create-pages` with the properties and content from
Step 4. Capture the returned page URL. Notion's browser/app may take 5-30 seconds
to reflect the new page after the API call returns successfully.

## Step 7. Post the `#team-marketing` group message

### 7a. Resolve the channel

```
slack_search_channels query="team-marketing"
```

Capture the channel ID. If `#team-marketing` cannot be resolved, fall back to
per-owner DMs (same `--notify=dm` flow) and flag this in the journal + a
LOW-severity ops-incident.

### 7b. Resolve the owner handles

For each section owner, query `slack_search_users`:

- {{HEAD_OF_MARKETING}}
- {{CONTENT_LEAD}}
- {{DESIGN_LEAD_FIRST}}
- Scott McKeighen

Capture each user ID for `<@USER_ID>` Slack mention syntax.

### 7c. Compose the message

Format (Slack markdown):

```
*Marketing WBR for {upcoming Friday, Month D}* is ready for your input. :memo:
Page: <{notion_url}|Open in Notion>

*Updates due Thursday, 07:00 AM PT.*

*Sections and owners:*
• *Project Updates* — <@mark_user_id>
   _Last week:_ "{verbatim quote from last week's Project Updates section}"
• *Content and Product Marketing* — <@asta_user_id>
   _Last week:_ "{verbatim quote from last week's section}"
• *Website and Design* — <@danae_user_id>
   _Last week:_ "{verbatim quote from last week's section}"
• *GTM Ops (MOPs / RevOps)* — <@scott_user_id>
   _Last week:_ "{verbatim quote from last week's section}"

*Summary is auto-populated* with this week's MTD funnel metrics (MEL/MQL/SAL/SQL/pipeline)
from HubSpot.

Reply in thread if you need the deadline extended.

_Posted by Scribe | {ISO 8601 UTC timestamp}_
```

**Prior-week callouts:** Quote, do NOT summarize. Pick a single notable bullet or
phrase from the prior-week section content and reproduce it verbatim inside quotes.
The goal is to remind the owner of what they wrote last week — in their own words —
not Scribe's interpretation of it.

Selection order when the section has multiple bullets:
1. Any bullet containing a verb indicating near-term action ("shipping", "launching",
   "completing", "finalizing") or a completed state ("Done ✅", "Completed") — quote
   it verbatim.
2. Otherwise, quote the first bullet under the owner's section.

If the prior-week section is blank or contains only the default instruction
callouts, write `"no carry-over"` (literal) rather than fabricating content.

### 7d. Send the message

```
slack_send_message channel_id=<team_marketing_channel_id> message=<composed_text>
```

Capture the returned `message_link` for the journal.

## Step 8. Fallback: per-owner DM mode (`--notify=dm` only)

If the invoker passed `--notify=dm` (or channel resolution failed), send individual
Slack DMs to each owner instead of a channel post. Each DM contains:
- Page link
- Section name
- One-line prior-week callout for that section
- Deadline (Thursday 07:00 AM PT)

Scott combines the Summary + GTM Ops mentions into a single DM so he's not paged
twice.

## Step 9. Write handoff to chief-of-staff

Append to `state/journal/handoffs.md`:

```markdown

## {ISO 8601 UTC} | Scribe → chief-of-staff | WBR posted for {upcoming Friday date}

- Notion page: {page_url}
- Slack post: {message_link} in `#team-marketing` (or "per-owner DMs" if that path ran)
- Owners notified: {{HEAD_OF_MARKETING_FIRST}}, {{CONTENT_LEAD_FIRST}}, {{DESIGN_LEAD_FIRST}}, Scott
- Deadline for owner fills: Thursday 07:00 AM PT
- Data source: {revops-watchdog snapshot id=N / HubSpot fallback}
- Open anomalies included in Summary: {count, one-line}

Recommend chief-of-staff reference this in Thursday AM brief and again Friday AM.
```

Also INSERT into the `handoffs` table:

```sql
INSERT INTO handoffs (from_agent, to_agent, subject, body, severity, status, created_at)
VALUES ('scribe', 'chief-of-staff',
  'WBR posted for {friday_date}',
  '{condensed body text}',
  'LOW', 'pending', '{iso_now}');
```

## Step 10. Journal entry

Append to `state/journal/scribe.md`:

```markdown

## {ISO 8601 UTC} | Weekly Tick — WBR posted
- Date: YYYY-MM-DD ({Day}) | Quarter: Q# YYYY
- Page: {notion_page_url}
- Slack: {message_link} ({channel or DMs})
- Data source: revops-watchdog snapshot id=N ({created_at}) OR HubSpot fallback
- Prior-week page: {found / missing} — callouts: {count extracted}
- Open anomalies surfaced: {list by severity}
- Owners prompted: {{HEAD_OF_MARKETING_FIRST}}, {{CONTENT_LEAD_FIRST}}, {{DESIGN_LEAD_FIRST}}, Scott
- Deadline set: Thursday 07:00 AM PT
- Notes: {any caveats, misfires, fallbacks used}
```

## Step 11. Commit + push

```bash
python3 scripts/fleet_git.py commit --agent scribe --action "Weekly Tick | WBR posted"
python3 scripts/fleet_git.py push
```

Never bypass hooks. Never force-push. Never amend.

---

## Step 12. `--slack-only` send-only retry path

When invoked with `--slack-only`, Scribe skips Notion entirely and posts the
deferred `#team-marketing` message for the most recent WBR. Use this when a
prior weekly run created the Notion page successfully but Slack was unbound
at post time (the failure mode that motivated this path).

### Step 12a. MCP Preflight — Slack only, with hard-stop

Run the bounded retry sequence from Step 0, but for Slack only:

| Connector | Essentiality | Probe |
|-----------|--------------|-------|
| Slack     | essential    | `+slack send_message` |

If Slack remains unbound after the full bounded retry (~5 min), this is a
hard abort with operator alert. The retry path's job is to send the message.
If Slack is unreachable, there is nothing else to try in-session.

**On Slack preflight failure:**

1. Append HIGH ops-incident to `state/journal/ops-incidents.md`:

   ```
   ## {ISO 8601 UTC} | HIGH | Scribe | --slack-only retry FAILED — Slack MCP still unbound

   Prior failure: {timestamp of original deferred-post incident}
   Retries: 3 attempts over ~5 min within --slack-only invocation
   Bound: {list}
   Missing: Slack
   Action: aborted. Original WBR Notion page unchanged. Slack message still not sent.
   Recovery options:
     1. Operator confirm Slack MCP server is connected at the Cowork session level
        (URL: https://mcp.slack.com/mcp), complete OAuth handshake if needed, then
        start a fresh Claude Code session and re-run /scribe wbr-prep --slack-only.
     2. If Slack is durably unavailable, manually paste the composed message from
        localwork/scribe/slack-draft-YYYY-MM-DD.md into #team-marketing.
   ```

2. Append HIGH handoff to `state/journal/handoffs.md` addressed to Scott
   directly (operator-action-required):

   ```markdown
   ## {ISO 8601 UTC} | Scribe → Scott | HIGH: --slack-only retry FAILED — Slack MCP unbound

   - Cause: Slack MCP unbound after 3 preflight retries within the --slack-only
     retry path. This is the second consecutive Slack failure for this WBR cycle.
   - Original deferred post: {original incident timestamp}
   - Notion WBR page (unchanged): {page URL from wbr/YYYY-MM-DD.md}
   - Slack draft (still ready to send): localwork/scribe/slack-draft-YYYY-MM-DD.md
   - Recovery: see ops-incident for fresh-session steps OR manual paste fallback.
   - Blast radius: owners not notified. Friday WBR meeting may proceed without owner
     pre-fills if recovery does not happen by Thursday 07:00 AM PT deadline.
   ```

3. PushNotification (best-effort, non-blocking):
   - Message: `Slack retry FAILED for {Friday date} WBR. Reconnect Slack MCP + fresh session, or paste from slack-draft-{YYYY-MM-DD}.md manually.`

4. Journal entry to `state/journal/scribe.md` flagging the retry failure.
5. Commit and push state.
6. **EXIT.** Do not attempt the send.

### Step 12b. Locate the page and the draft

Read the latest `wbr/YYYY-MM-DD.md` audit artifact (most recent file by date).
Extract:
- Page URL (the `Properties` block contains the Notion page; the URL is logged
  by the original Step 6 to `wbr/YYYY-MM-DD.md` and to the prior journal entry)
- Friday date (from the `Name` property line)

Read `localwork/scribe/slack-draft-YYYY-MM-DD.md` for the composed message and
owner handles. If the draft file is missing, recompose the message using:
- Page URL from `wbr/YYYY-MM-DD.md`
- Owner handles from the most recent `state/journal/scribe.md` entry that
  contains them
- Prior-week verbatim quotes from the page that was the predecessor at original
  post time (look up via the same `notion-search` query used in Step 3)

If neither the draft nor sufficient context to recompose exists, abort the
retry path and write a handoff to Scott explaining the gap.

### Step 12c. Resolve channel + handles, then send

Use the channel and handle resolution from Step 7a/7b. Owner handles cached in
the prior Scribe journal entry are reusable across same-week retries — no need
to re-search if they're recent (<7 days).

Send via `slack_send_message` per Step 7d. Capture `message_link`.

### Step 12d. Update prior incident as resolved + write recovery handoff

1. Append a resolution note to the original deferred-post ops-incident in
   `state/journal/ops-incidents.md` (do NOT edit the original entry — append a
   new line at the end of the file referencing the original incident's
   timestamp):

   ```
   ## {ISO 8601 UTC} | LOW | Scribe | --slack-only retry SUCCEEDED — message posted

   Resolves: {original deferred-post incident timestamp}
   Channel: #team-marketing ({channel ID})
   Slack message_link: {link}
   Latency from original deferred post to recovery: {hours}
   ```

2. Append handoff to chief-of-staff (LOW) noting the recovery so chief-of-staff's next AM
   brief reflects the corrected state.

### Step 12e. Journal entry, commit, push

Journal entry format:

```markdown
## {ISO 8601 UTC} | --slack-only retry — Slack post recovered

- Resolves prior deferred post: {original timestamp}
- Page (unchanged): {page URL}
- Slack: {message_link}
- Owners notified: {list}
- Deadline (unchanged from original): {Thursday date 07:00 AM PT}
- Notes: {OAuth-completed-this-session, MCP rebind worked, etc.}
```

Commit message: `[state-bot] Scribe | --slack-only retry | Slack post recovered | {ISO 8601 UTC}`

---

## Error handling

- **revops-watchdog snapshot missing:** Fall back to HubSpot, log in journal, continue.
- **HubSpot MCP unavailable AND no revops-watchdog snapshot:** Abort before Notion write. Log
  HIGH ops-incident. Write handoff to chief-of-staff flagging the gap. Do NOT create a WBR
  page with missing or fabricated numbers.
- **Prior-week Notion page missing:** Note "first WBR in window" and create a new
  page from scratch using the section template. Owners will fill from empty.
- **`#team-marketing` channel resolution fails:** Fall back to per-owner DMs. Log
  LOW incident.
- **Slack send fails:** Notion page stays published; retry once; if still failing,
  write handoff to chief-of-staff and note the gap in the journal (humans can still
  discover the page via Notion, they just won't get the Slack nudge).
- **Owner handle not found in Slack:** Use the section name without an @-mention
  and flag the missing handle in the journal.
