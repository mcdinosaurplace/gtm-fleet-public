# Notion Brief Template

The durable copy of chief-of-staff's AM brief. Loaded on demand by the brief-synthesis
step (prompt step 10), not pre-read.

---

## Surfaces

**The `~~chat` DM is the primary surface and does not change.** chief-of-staff composes
the plain-text brief, shows it to Scott, gets confirmation, and sends the DM
(step 11). That is the brief.

The Notion page is a **durable copy** of the same brief, written after the DM
lands, to the Intelligence Briefs database `{{NOTION_INTEL_BRIEFS_DB_ID}}`. It
exists so the brief is searchable next month, not so it can say something the DM
did not.

- The Notion write never gates or delays the DM. Compose, confirm, send, then
  write the page.
- `~~knowledge base` (Notion) is an *optional* connector for chief-of-staff
  (`docs/mcp-preflight.md`). If it is unbound, skip the durable copy and note the
  skip in the journal entry. Do not escalate, do not retry the Tick.
- In `DEMO_MODE=1` both surfaces land in `state/demo-outbox/` — the DM and the
  Notion page are written as files, never to a live surface.

The Notion copy carries more than the DM does: the DM is capped near 30 lines
and curates hard, while the page holds the full lists behind toggles. Same
findings, more room.

---

## Required reading before writing

- [`docs/notion-markdown-syntax.md`](../../../docs/notion-markdown-syntax.md) —
  canonical syntax. The rules below are a summary of it, not a replacement.
- [`docs/linear-reference-formatting.md`](../../../docs/linear-reference-formatting.md)
  — every Linear issue ID and project name on this page must be a markdown link
  `[MAR-XXXX](url)`, never a bare ID. Use the `url` field from the Linear
  response verbatim. Notion renders standard markdown.

---

## Syntax rules that break the page when ignored

1. **Callouts** are XML tags: `<callout icon="🤖" color="purple_bg">` …
   `</callout>`. Never `>` blockquotes, never `> [!NOTE]`.
2. **Toggles** are heading attributes: `## Heading {toggle="true"}`. Never
   `<details><summary>`.
3. **Columns** are `<columns><column>` … `</column></columns>`.
4. **Nesting uses TAB characters**, one per level. Spaces break the layout.
   Non-negotiable.
5. **Empty blocks** — `<empty-block/>` for vertical spacing inside callouts and
   columns.
6. **No `---` dividers** inside toggled or nested content.
7. **Checkboxes** inside callouts: `- [ ]` / `- [x]`.

Every page opens with one toggleable top-level heading containing all content.
That keeps the database view clean while the page itself expands fully.

---

## Page properties

```
Name:       "chief-of-staff AM Brief — YYYY-MM-DD"
Brief Type: "Daily Update"
Status:     "Draft"
Date:       today (YYYY-MM-DD)
Icon:       🗓️
```

Status stays "Draft". Scott marks it Final after review.

---

## Daily template

> **INDENTATION NOTE**: each `→` below represents one TAB character. When
> building the content string for the Notion write, emit literal tabs at every
> level. Do not use spaces. Do not use `>` prefixes.

```notion-markdown
# chief-of-staff AM Brief — {Day of week}, {Month} {Day} {toggle="true"}
→<callout icon="🤖" color="purple_bg">
→→## AM Summary
→→[Direct 2-3 sentence read of the day. Meeting load, the one commitment that
→→has to land, anything overnight that changed the shape of the day. Second
→→person. No em-dashes. No AI-speak.]
→</callout>
→<columns>
→→<column>
→→→<callout icon="📋">
→→→→## Top 3 Priorities
→→→→1. [Specific — name the issue (linked), the person, or the decision.
→→→→Bold the issue or topic, plain explanation after. Not "check email".]
→→→</callout>
→→</column>
→→<column>
→→→<callout icon="💡">
→→→→## Insights
→→→→- [2-4 bullets of the numbers behind the brief: meeting count, open issue
→→→→count and breakdown, inbox survivors, cross-agent audit result, and any
→→→→pattern Scott would otherwise miss ("your only deep-work block is Wednesday").]
→→→</callout>
→→</column>
→</columns>
→<callout icon="🚨" color="red_bg">
→→## Risks {toggle="true"}
→→→- [Specific risks. Name the issue, the person, the deadline. Blocked work,
→→→hardening risks carried a second day, decisions that must land today,
→→→open threads awaiting a reply. If none: "Nothing flagged."]
→</callout>
→<callout icon="❇️" color="green_bg">
→→## Opportunities {toggle="true"}
→→→- [Positive signals and open windows: deep-work blocks, work that closed
→→→overnight and can be built on, quick wins available today. Omit the
→→→section if there is nothing real to say.]
→</callout>
→## 📫 Inbox Signals {toggle="true"}
→→[One callout per survivor of roster/chief-of-staff/references/gmail-classification.md.
→→Checkbox inside each. ALWAYS a clickable link to the source so Scott can drill
→→in from the page. Cap at 5, most urgent first.
→→
→→Format: "- [ ] **{Sender} ([Email](gmail_link))** — {what they need}"
→→
→→Source icon guide:
→→✉️ = email (https://mail.google.com/mail/u/0/#inbox/{messageId})
→→🟣 = Linear issue comment (link to the issue URL)
→→📅 = calendar invite needing an RSVP (link to the event)
→→
→→Each item is its own callout. Do not group them into one.
→→If nothing survived classification, OMIT this whole section — never
→→"inbox clear", never a raw unread count.]
→→<callout icon="✉️">
→→→- [ ] **{Sender} ([Email](gmail_link))** — {one-line read of the ask}
→→</callout>
→## 📅 Today's Calendar {toggle="true"}
→→<callout icon="🗓️" color="{day_color}">
→→→#### {Day of week}, {Month} {Day} — {count} meetings
→→→[Time-sorted. Format each as:
→→→"**9:00 AM - Meeting Name** ([Join](meet_or_zoom_link)) ([Agenda](doc_link))
→→→— Attendees: A, B. RSVP: Accepted."
→→→Omit Join or Agenda only when none exists. Flag missing RSVPs, back-to-back
→→→blocks with no buffer, and meetings with no agenda doc using ⚠️ inline.
→→→If no meetings: "No meetings today — full deep-work day."]
→→→<empty-block/>
→→</callout>
→→[Day color: green_bg = light (0-1 meetings, deep work available);
→→yellow_bg = moderate to heavy (2+); red_bg = very heavy (3+ back-to-back,
→→no focus time); blue_bg = OOO, vacation, or holiday.]
→## ☑️ Linear Snapshot {toggle="true"}
→→[All issues use checkbox format so Scott can check them off in Notion
→→during the day. Every ID is a link — no bare MAR-XXXX anywhere.]
→→<callout icon="🔄" color="blue_bg">
→→→### Carried Forward {toggle="true"}
→→→→[From the PM carry-forward handoff (prompt PM-10) read in step 4. What
→→→→last night said today should open with. Omit the callout if the PM wrote
→→→→no carry-forward — a clean day does not need one.]
→→</callout>
→→<callout icon="☑️" color="gray_bg">
→→→### 🔎 In Review ({count}) {toggle="true"}
→→→→- [ ] [{TEAM}-XXXX](url) — Title
→→</callout>
→→<callout icon="☑️" color="gray_bg">
→→→### 🛠️ In Progress ({count}) {toggle="true"}
→→→→- [ ] [{TEAM}-XXXX](url) — Title
→→</callout>
→→<callout icon="☑️" color="purple_bg">
→→→### 🔥 To Do — Urgent / High ({count}) {toggle="true"}
→→→→- [ ] [{TEAM}-XXXX](url) — Title
→→→### 🎧 To Do — Medium ({count}) {toggle="true"}
→→→→- [ ] [{TEAM}-XXXX](url) — Title
→→→### ⬇️ To Do — Low or None ({count}) {toggle="true"}
→→→→- [ ] [{TEAM}-XXXX](url) — Title
→→→→<empty-block/>
→→</callout>
→## 📡 Fleet Status {toggle="true"}
→→<callout icon="📬">
→→→### Handoffs read ({count})
→→→[One line per handoff newer than the last journal timestamp: who sent it,
→→→what it says, what you did with it. If none: "None since the last Tick."]
→→</callout>
→→<callout icon="🔍">
→→→### Cross-agent audit
→→→[Clean, or N incidents with a one-line read of each.]
→→</callout>
→<callout icon="🔁" color="gray_bg">
→→## Closed Loops {toggle="true"}
→→→- {item} → {Scott's ruling, one line} (decisions id={n})
→→→[Only when replies or expired defaults were processed this Tick. Defaults
→→→applied on silence are reported here, never silently. Omit if none.]
→</callout>
→<callout icon="🎨">
→→## Creative Review Queue {toggle="true"}
→→→- {N} copy reviews open: {linked Linear refs} — assigned {{CONTENT_LEAD_FIRST}} (reassignable)
→→→[From `paid_change_proposals WHERE status='awaiting_creative'`. Omit if none.]
→</callout>
→<callout icon="⚖️" color="yellow_bg">
→→## Decisions Needed
→→→1. {One-line ask} — id={handoff/anomaly id}
→→→**Default:** {pre-authorized action, or "none — needs your call"} · **Decide by:** {date}
→→→[Max 3, numbered to match the DM exactly so a reply by number resolves the
→→→same item on both surfaces. Handoff ids are NOT Linear refs — do not link
→→→them. Omit the section if there are none.]
→</callout>
→<empty-block/>
→_chief_of_staff AM Tick | {ISO 8601 timestamp}_
```

---

## Section-to-source map

| Page section | Comes from |
|---|---|
| AM Summary | step 10 synthesis |
| Top 3 Priorities · Insights | step 10 synthesis over steps 8a/8b/8c + step 8 audit |
| Risks | step 10 synthesis; risks carried a second day are hardening, say so |
| Opportunities | step 10 synthesis |
| Inbox Signals | step 8c survivors, per `references/gmail-classification.md` |
| Today's Calendar | step 8a (`list_events`, or `scripts/gcal_pull.py` when unbound) |
| Linear Snapshot | step 8b (`list_issues assignee="me"`) |
| Carried Forward | step 4 handoffs — the PM-10 carry-forward |
| Fleet Status | step 4 handoffs + step 8 cross-agent audit |
| Closed Loops · Decisions Needed | step 10 Decision Queue rules |
| Creative Review Queue | `paid_change_proposals` (performance-marketer's table) |

The DM and the page are built from one synthesis pass. If a number differs
between them, the page is wrong.

---

## Degraded sources

When Calendar or Gmail fell through to the script path and the script also
failed, the page carries the same loud banner the DM does, inside the affected
section's callout:

```
⚠️ Calendar unavailable — MCP connector unbound and the API pull failed;
see docs/connector-reauth-runbook.md
```

Never "offline (expected)". Never "security rollover". Never carry a prior
tick's excuse forward. The rule and its history are in prompt step 7.

---

## Weekly variant (held)

The concierge produced a Monday **Weekly Forecast** alongside the Tue–Fri daily
brief. chief-of-staff's AM Tick pulls a single day, so it writes the daily template
every weekday including Monday. The weekly shape is recorded here because it is
the accumulated design, and it becomes writable the day chief-of-staff pulls a week
range:

- Page name `chief-of-staff Weekly Forecast — YYYY-MM-DD`, Brief Type
  `"Weekly Forecast"`.
- **Agenda becomes five day-columns** (Mon–Fri) instead of one full-width
  callout, each its own `<callout icon="🗓️" color="{day_color}">` inside
  `<columns>`, colored by that day's meeting load.
- **Summary and priorities span the week** rather than the day: meeting load
  across five days, the single most important thing to get done, which day is
  the only real deep-work block.
- **A `## 📡 Collaboration Radar {toggle="true"}` section** appears, two columns
  of `<callout icon="👤">` blocks, one per collaborator, each a
  `#### **{Person}** {toggle="true"}` with 2-3 sentences aggregating every
  touchpoint with that person: shared meetings, threads, issues they commented
  on, pending mail. The daily brief does not repeat it — the weekly sets the
  picture.
- **No carry-forward callout** on Monday; there is no prior day inside the week.

Do not write a weekly page until a week-range pull exists. Half the sections
would be empty and the rest would be a re-labeled daily brief.

---

## Sections the concierge had that chief-of-staff does not write yet

Recorded so the design is not lost, and so nobody re-derives them when the
source lands (prompt → Expansion Plan):

- **Meeting Intelligence** (`## 📅 ⚡️`) — per-meeting callouts from `~~meeting
  notes` recordings: name as heading, one-paragraph summary, action items
  filtered to the ones assigned to or relevant to Scott. Needs Grain (4c).
- **Untracked Work** (`<callout icon="ℹ️">` beside a `💡 Heads Up` capacity
  callout, in columns above the task list) — commitments made in threads or
  meetings that have no Linear issue, each with a recommendation to open one.
  Needs the Slack pull (4a) to have anything to detect.

Do not emit an empty callout for either. A section with no source is omitted,
not stubbed.

---

## Tone

One reader: Scott. Second person. Direct and concrete — names, linked issue
IDs, times, deadlines. No em-dashes. No AI-speak ("leverage", "streamline",
"robust", "actionable", "holistic"). The page is roomier than the DM, so when in
doubt surface more here; Scott can skim a toggle he does not need. The summary
should read as a trusted chief of staff speaking plainly, not a performance
review.
