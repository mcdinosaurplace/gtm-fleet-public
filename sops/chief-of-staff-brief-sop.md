# chief-of-staff Briefs — Team SOP

**Version:** 1.0
**Owner:** Marketing / GTM Ops
**Applies to:** Scott (brief recipient) and anyone reading the Notion copy
**Tool:** Claude Code Agent → `/gtm-fleet:chief-of-staff am|pm`

---

## What This Is

chief-of-staff is the fleet's chief of staff. Twice a weekday it runs a Tick: the **AM
Tick** collects (calendar, Linear, inbox signals, overnight handoffs) and
delivers a brief; the **PM Tick** judges (what moved, what stalled, what carries
into tomorrow) and mostly stays quiet. chief-of-staff never does specialist work — it
routes, curates, and holds the narrative thread between the other agents.

This SOP covers the human side: what arrives, where, how to answer it, and what
to do when a piece is missing.

**Time to complete:** 2 minutes to read the AM brief. Replies take as long as
the decisions do.

---

## Section 1: What Arrives, and When

| Tick | Schedule entry | Time (PT) | Days | What you get |
|---|---|---|---|---|
| AM | `chief-of-staff-am` | 07:00 | Mon–Fri | The brief: today's meetings, Linear snapshot, inbox signals, risks, top 3 priorities, decisions needed |
| PM | `chief-of-staff-pm` | 16:00 | Mon–Fri | Usually nothing. A DM only if something needs you before tomorrow morning. |

**Silence from the PM Tick is the expected outcome.** It writes a journal entry,
a meditation, and a carry-forward note for tomorrow's AM. It escalates only for
a HIGH/CRITICAL specialist finding, a decision that cannot wait until morning,
or a gate about to slip overnight.

**Schedules are declared, not installed.** `schedule.yaml` is the manifest; every
entry ships `enabled: false`. To actually get a 07:00 brief, render the entry for
your scheduler and install it yourself:

```bash
python3 scripts/schedule_render.py --format crontab
python3 scripts/schedule_render.py --format routine --only chief-of-staff-am
```

---

## Section 2: Where It Lands

| Surface | What it is |
|---|---|
| **`~~chat` (Slack) DM** | **Primary.** The brief itself, plain text, under 30 lines, curated hard. This is the one to read. |
| **Notion — Intelligence Briefs** (`{{NOTION_INTEL_BRIEFS_DB_ID}}`) | The durable copy. Same findings, more room: full issue lists behind toggles, page Status `Draft` until you mark it Final. Searchable next month. |
| **`state/demo-outbox/`** | Where both land when `DEMO_MODE=1`. Fixtures mode never writes to a live surface. |

The DM always ships first. The Notion page is written after it lands and never
delays it — Notion is an optional connector for chief-of-staff, so if it is unbound the
page is skipped and the skip is noted in chief-of-staff's journal. The DM is unaffected.

In an interactive run chief-of-staff shows you the composed brief and asks for
confirmation before sending. Scheduled runs send without asking.

---

## Section 3: What Is in the Brief

Sections appear only when they have content. An empty section is omitted, not
padded.

| Section | What it contains |
|---|---|
| Today's calendar | Time-sorted meetings with join and agenda links; ⚠️ on missing RSVPs, back-to-back blocks, and meetings with no agenda doc |
| Linear snapshot | Open issues by status and priority, every ID a clickable link |
| Inbox | Up to 5 emails where someone is actually waiting on you, each with a deep link. No survivors means no section — never a raw unread count |
| Top 3 priorities | Specific: an issue, a person, or a decision |
| Risks | Blocked, overdue, or drifting. A risk on its second day is hardening and says so |
| Closed loops | Rulings chief-of-staff processed this Tick, including any default applied on silence |
| Creative review queue | Greenlit paid-creative moves awaiting copy review, assigned {{CONTENT_LEAD_FIRST}} and reassignable |
| Decisions needed | Max 3, numbered, each with a default and a decide-by date |

---

## Section 4: How to Reply

**Reply in the thread on the brief DM.** chief-of-staff reads that thread at the start
of the **next AM Tick**, interprets your replies, records each ruling, and fans
it out. The PM Tick does not process the queue — a reply sent at 4pm is picked
up the following morning.

### The conventions

- **Reply by number.** Decision items are numbered so `1 yes, 2 hold until
  Friday, 3 no — ask {{HEAD_OF_MARKETING_FIRST}} first` resolves all three.
- **Write however you write.** Verbose or shorthand, both work. chief-of-staff
  interprets free text and never demands a syntax. If a reply genuinely cannot
  be mapped to an item, it re-asks once with sharper framing rather than
  dropping it.
- **Every ask carries a `Default:` and a `Decide by:` date.** If the default is
  a real action, silence past the decide-by date applies it — and it is reported
  back to you under *Closed loops*, never silently. Defaults exist only on
  reversible, low-tier actions (suppressing a flag, keeping a watch open,
  journal or database state). Anything touching filters, thresholds, agent
  identity files, or an external surface reads `Default: none — needs your
  call` and simply waits for you.
- **Two briefs without a reply is the limit.** An item that has gone unanswered
  twice does not appear a third time — it routes to the weekly
  `/gtm-fleet:triage` sweep, and the brief says so under *Risks*.
- **Rulings are ground truth.** Each one becomes a `decisions` row plus a
  `Scott → {agent}` entry in the handoff journal, which the owning agent reads
  on its next Tick. Anything outside chief-of-staff's write scope is staged as a
  handoff rather than edited directly.
- **Teammate feedback counts as much as yours.** Substantive input from
  {{HEAD_OF_MARKETING_FIRST}}, {{CONTENT_LEAD_FIRST}}, or {{DESIGN_LEAD_FIRST}}
  on any surface chief-of-staff reads is weighted equally and recorded. If it implies
  an operational change or conflicts with other human feedback, it comes back to
  you as a decision item naming whose feedback raised it — you are the
  tie-breaker.

### Things that are not decisions

You do not need to reply to acknowledge a brief. Checking a box on the Notion
page is a fine way to close out a task; chief-of-staff reads the page state, not your
silence.

---

## Section 5: Running One Ad Hoc

```
/gtm-fleet:chief-of-staff am
```

Runs the full AM Tick now: sync, identity, journal, handoffs, connector
preflight, cross-agent audit, data pull, synthesis, and delivery. `pm` runs the
evening pass. With no argument, chief-of-staff picks the mode from the clock (before
noon PT = AM).

Use it when the scheduled run did not fire, when you want a mid-day refresh, or
after resolving a connector problem. Running AM twice in one day is safe — the
second run supersedes the first and reads any replies you left in between.

Headless equivalent: `python3 scripts/tick.py --agent chief-of-staff --mode am`.

---

## Section 6: Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| No brief at 07:00 | The schedule is declared but not installed — `schedule.yaml` ships every entry `enabled: false` | Render and install `chief-of-staff-am` with `scripts/schedule_render.py`, or run `/gtm-fleet:chief-of-staff am` by hand |
| Calendar or inbox section shows `⚠️ ... unavailable` | The connector was unbound **and** the script fallback also failed (missing `GOOGLE_OAUTH_*` credentials or an API error) | Follow `docs/connector-reauth-runbook.md`. chief-of-staff files an `MCP_BIND_FAILURE` incident every run this happens — it will not quietly normalize the gap |
| Sections are present but a connector is unbound | Normal in headless runs. chief-of-staff falls back to `scripts/gcal_pull.py` / `scripts/gmail_pull.py`, which authenticate independently | Nothing to do. This is the designed path, not a degraded brief |
| No inbox section at all | Nothing survived classification. Volume is not signal | Working as intended. The method is in `roster/chief-of-staff/references/gmail-classification.md` |
| The brief landed in `state/demo-outbox/` instead of your DM | `DEMO_MODE=1` — the fleet is running on fixtures | Unset `DEMO_MODE` for live runs. Demo mode never writes to a live surface |
| DM arrived but no Notion page | Notion is optional for chief-of-staff and was unbound | Bind `~~knowledge base` and it resumes next Tick. The journal entry records the skip |
| A decision item you already answered came back | The reply landed somewhere chief-of-staff does not read, or after the Tick had already run | Reply in the thread on the brief DM. Rulings are picked up at the next AM Tick |
| The same item has appeared twice and vanished | By design — it routed to the weekly triage sweep | Resolve it in `/gtm-fleet:triage` |
| A bare Linear ID (`MAR-7123`, unlinked) in the brief | A defect. The pre-send gate should block it | Report it — every Linear reference on every chief-of-staff surface must be a clickable link |
| The Tick aborted with `MCP_BIND_FAILURE` | Slack or Linear failed to bind after three attempts — chief-of-staff cannot deliver or has no core data | Check the connector, then re-run `/gtm-fleet:chief-of-staff am`. See `docs/mcp-preflight.md` |

---

## Quick Reference

| Item | Value |
|---|---|
| **Command** | `/gtm-fleet:chief-of-staff am` · `/gtm-fleet:chief-of-staff pm` |
| **Schedule entries** | `chief-of-staff-am` (07:00 PT, Mon–Fri) · `chief-of-staff-pm` (16:00 PT, Mon–Fri) |
| **Primary surface** | `~~chat` DM |
| **Durable copy** | Notion Intelligence Briefs (`{{NOTION_INTEL_BRIEFS_DB_ID}}`), Status `Draft` |
| **Demo mode output** | `state/demo-outbox/` |
| **Where to reply** | The thread on the brief DM |
| **When replies are read** | Start of the next AM Tick |
| **Decision cap** | 3 items per brief; unanswered twice routes to `/gtm-fleet:triage` |
| **Agent prompt** | `roster/chief-of-staff/prompt.md` |
| **References** | `roster/chief-of-staff/references/gmail-classification.md` · `roster/chief-of-staff/references/notion-brief-template.md` |

---

*Questions? Ping Scott or raise it in the weekly triage sweep.*
