# Gmail Classification

How chief-of-staff turns a raw inbox into the handful of *inbox signals* the AM brief
carries. Loaded on demand by the AM Tick's Gmail step (prompt step 8c), not
pre-read.

The unread backlog routinely runs to 200+. A raw unread count is not a task
list and must never be reported as one. Classify first, surface only survivors,
and fetch full message bodies only for the handful you intend to surface.

---

## Two intake paths, one classifier

The classification below is tool-agnostic. It applies identically whichever path
supplied the messages.

| Path | When | Intake |
|---|---|---|
| `~~email` (Gmail) MCP | connector bound | `search_threads` for the seeds, `get_message` for survivors only |
| `scripts/gmail_pull.py` | connector unbound (the normal headless case) | one call returns JSON: `unread` / `starred`, each message carrying sender, subject, snippet, labels, `link` |

Seed queries (same for both paths, run in parallel):

```
is:unread in:inbox      (pageSize 30)
is:starred in:inbox     (pageSize 25)
```

Field mapping between the paths:

| Signal used below | MCP field | `gmail_pull.py` field |
|---|---|---|
| Sender identity | `from` | `sender` |
| Subject heuristics | `subject` | `subject` |
| Body / first-paragraph shape | `get_message` body (survivors only) | `snippet` |
| Bulk-mail markers | list headers, `labels` | `labels` |
| Deep link | built from `messageId` | `link` (pre-built) |

The `gmail_pull.py` path gives you a snippet rather than a full body. That is
enough to classify: every exclude signal below reads on subject, sender, and the
first lines. Only pull the full message when a survivor's ask is genuinely
ambiguous.

Connector-fallback handling itself lives in prompt step 8c and step 7 — this
document does not restate it.

---

## The survivor rule

An email survives classification only if **someone is waiting on Scott for a
reply or a decision**. That is the whole test. Everything below is the accrued
detail of applying it.

Two consequences worth stating plainly:

- Volume is not signal. Fifty newsletters produce zero survivors, and that is a
  correct result.
- A survivor is an *ask*, not a topic of interest. Something Scott would find
  interesting but that requires nothing of him is not a survivor.

---

## Exclude

**Vendor sales and cold outreach.** Vendor reps pushing pricing deadlines,
upgrade offers, feature announcements, or cold first-touch. Signals: subject
lines carrying "pricing", "offer expires", "limited time", "your trial",
"schedule a demo", "final reminder"; a named rep at a SaaS vendor Scott has not
been in an actual thread with.

**Drip and nurture sequences.** Automated cadences dressed as personal mail.
Signals: a short personal-sounding paragraph plus one CTA; template-shaped
structure; the same sender appearing on a cadence; no prior back-and-forth from
Scott's side.

**Newsletters and promotional mail.** Bulk sends with an unsubscribe link, sent
through a marketing platform (Mailchimp, HubSpot, Marketo, SendGrid marketing),
promotional subject lines.

**Routine system notifications.** Issue-tracker digests, PR notifications, CRM
activity alerts, CI/CD success notices, import-ready confirmations, receipts,
product blasts, calendar auto-reminders.

---

## Include

Colleagues, customers, and partners. Any email where a human is directly asking
Scott for a reply or a decision.

---

## Precedence

Rules are applied in this order. A later rule never resurrects what an earlier
one settled.

1. **A direct human ask beats every exclude category.** If a real person is
   asking Scott for something, it survives even when the mail also looks
   promotional or arrives from a vendor domain.
2. **The actionable-notification exception beats "routine system
   notification".** A system notification survives when it signals something
   urgent with a real cost attached: billing failures, security alerts, a broken
   automation (a paused Zap, a failed sync), a deployment failure or outage, a
   trial expiring with money on the line, an urgent or high-priority task
   assignment. Everything else in that category stays suppressed.
3. **Otherwise the exclude categories apply**, and the message is suppressed
   without comment.

---

## chief-of-staff-specific dedup

Two rules that exist because chief-of-staff pulls sources the concierge did not pull
side by side.

- **Skip calendar-invite and meeting-recap mail.** `Invitation:`,
  `Updated invitation:`, `Declined:`, Google Calendar auto-notifications, and
  automated recap mail from the `~~meeting notes` tool (Grain) are suppressed
  outright. Calendar is pulled live in step 8a and the recordings themselves are
  content-researcher's `call-miner` territory; surfacing either from Gmail as
  well double-counts the same meeting.
- **Starred is user-curated but often stale.** Surface a starred thread only if
  it is recent or clearly still open. Treat an old star as a bookmark Scott left
  himself, not as an ask.

A survivor that belongs to a Linear issue or a meeting already in the brief is
merged into that item rather than listed twice — the cross-source merge rule
lives in the prompt's synthesis rules (step 10).

---

## What reaches the brief

For each survivor, carry forward exactly two things: the `messageId` (or the
pre-built `link`) for the deep link, and a one-line read of what the sender
needs.

- **Cap at five**, most urgent first. Curate rather than enumerate.
- **Every surfaced email carries a clickable link** —
  `https://mail.google.com/mail/u/0/#inbox/{messageId}`, or the `link` field
  when the fallback script supplied it. An inbox line Scott cannot click into
  is half an item.
- **If nothing survives, omit the inbox section entirely.** Do not write "inbox
  clear" and do not report the unread count as a consolation number.
- Suppressed mail is not summarized, counted, or apologized for anywhere in the
  brief.

---

## When a call is genuinely close

Prefer surfacing. A wrongly surfaced email costs Scott one line of a brief; a
wrongly suppressed one costs him the reply. Bias toward the survivor and keep
the one-line read honest about the uncertainty ("looks like a nudge on the
contract, may be automated").
