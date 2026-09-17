# Conventions

Operational rules for agents and scripts. Referenced from CLAUDE.md.

## Working Stance (Coding Principles)

Every agent operates under the **Coding Principles (Karpathy Skills)** in
`CLAUDE.md` — always loaded. The point that governs agent *output*: verification
means **adversarial validation**, not a confirmatory glance. Before shipping a
report, Notion page, Slack message, or Linear issue, try to *break* the work —
re-derive every number from source, red-team each claim ("what would make this
false?"), and inspect the rendered surface, not the draft. A check that can only
pass is not a verification step.

## Agent Names

Agents carry descriptive role names — the name tells you what the agent does:
chief-of-staff, revops-watchdog, performance-marketer, content-researcher,
content-producer, brand-designer, and Scribe (the one agent with a proper name).
Slash commands, roster directories, journal files, state-bot commit subjects, and
record ids all use these names. The env var gating ad execution is
`PERFORMANCE_MARKETER_EXECUTE`.

## Agent Execution Order

Agents run in the order specified by their command file. If a command references
a prerequisite (e.g., "run `/funnel-stats` first"), that prerequisite runs before
the main agent.

## Slash Commands

- Every agent has a router skill at `skills/<agent>/SKILL.md`, invoked as
  `/gtm-fleet:<agent>`; the router resolves `FLEET_ROOT` and points at
  `roster/<agent>/prompt.md`. When creating a new agent, create the router at the same time.
- Standalone capabilities (`funnel-stats`, `luma-events`) and operator tools (`triage`,
  `help-me`) get their own skill; agents that only run as part of a pipeline are covered
  by the pipeline's skill.
- Headless runs go through `scripts/tick.py`, which invokes the same router with `--harness`.

## Git Workflow

- **Start of a Tick**: `python3 scripts/fleet_git.py sync` (Librarian step 0). In local-commit
  mode this only confirms the branch; with `FLEET_REMOTE` set it fetches and fast-forwards.
- **End of a Tick**: `python3 scripts/fleet_git.py commit --agent <a> --action "<action>"`
  then `fleet_git.py push` (no-op without a remote). See `docs/state-commit-convention.md`.
- Human code changes: commit with a concise, descriptive message; do not batch unrelated
  changes. State-bot commits never touch files outside `state/` and `wbr/`.

## Language

- Python and/or JavaScript for CLI scripts
- Python for data processing and analysis
- Shell for simple automation

## Notion Integration

- All output is staged locally first, then posted to Notion after user approval
- Never post to Notion automatically — always ask first
- Use the Updates database (data source: `{{NOTION_UPDATES_DB_ID}}`)

## Handoff Lifecycle

Handoffs live in two places: an append-only entry in `state/journal/handoffs.md`
and a row in the `handoffs` table (`state/working/fleet.db`). The DB
row carries the lifecycle: `status` moves `pending` → `acknowledged` → `resolved`,
stamped via `acknowledged_at` / `resolved_at`.

- `pending` — written, not yet seen by the operator
- `acknowledged` — Scott has seen it; the underlying work may still be open
- `resolved` — the underlying issue is closed

Rules:

- **LOW handoffs are informational.** Write them with `status='resolved'` at
  insert. They never require acknowledgment and never count as stale.
- **`status` is the acknowledgment signal.** Agents tracking an open item read
  the row's status instead of counting silent cycles or elapsed time. Do not
  infer acknowledgment from silence. Once an item is `acknowledged`, do not
  re-ask — surface it again only if the data changes materially.
- **Acks come from Scott**, either directly via `scripts/handoffs.py`
  (`list` / `ack <id>` / `resolve <id>`) or through an agent acting on his
  explicit instruction. The script updates the DB row and appends a matching
  `handoffs.md` entry so journal readers see the state change.
- chief-of-staff's 72-hour stale audit counts only `pending` rows at MED/HIGH.

Adopted at the reference housecleaning run. The pre-existing backlog (a large pile of perpetual-pending rows, the
"stale long-tail") was cleaned the same day: LOW and pre-June rows resolved,
live June threads marked acknowledged.

### Record IDs (handoffs, anomalies, spend_alerts, incidents)

**Never compute an id from `MAX(id)+1`.** Sequential integers assigned by
uncoordinated writers (two agents, or the same agent on divergent branches during
a scheduled-tick divergence) collide on merge and then have to be renumbered by
hand. Always mint the id with the shared minter:

```
python3 scripts/ids.py <agent> <kind>     # e.g. python3 scripts/ids.py revops-watchdog handoff
# or, in Python:  from scripts.ids import mint;  hid = mint("revops-watchdog", "handoff")
```

It returns a text id `{agent}_{kind}_{time}_{rand}` (e.g.
`revops-watchdog_handoff_01j9x8k2p7_a3f2z9`) — unique without coordination, time-sortable as
a plain string, and self-describing so a human reading a log knows who wrote it and
what it is. Kinds in use: `handoff`, `anomaly`, `spendalert`, `incident` (lowercase
alnum, no underscores — underscore is the field separator). The `handoffs`,
`anomalies`, and `spend_alerts` tables carry `id TEXT PRIMARY KEY` as of migration
`015_textual_ids`; legacy integer ids from before that migration are preserved as
their string form (`'177'`, `'191'`) and still resolve via `scripts/handoffs.py`.
Adopted by Scott directive after collisions kept recurring.

## Decision Queue

How operator decisions get captured and applied. Three paths, one record:
every ruling lands as a row in the `decisions` table AND a `Scott →` entry in
`state/journal/handoffs.md`, then fans out to whatever files the decision
touches.

**Daily path — AM brief Decision Queue.** chief-of-staff's AM brief ends with a
numbered "Decisions needed" block (max 3 items). Each item carries: the
handoff/anomaly id, a one-line ask, a suggested default (only if eligible —
see below), and a decide-by date. Every ask gets a date — undated asks rot.
Scott replies in the Slack thread; on the next Tick chief-of-staff reads the thread,
interprets the replies, records the decisions, resolves or acks the handoffs,
and applies the fan-out within its tier gates. File edits beyond chief-of-staff's
write scope are staged as handoffs to the owning agent or to the weekly
triage. Items that outlast two briefs route to `/triage` instead of repeating.

**Reply interpretation.** Scott's replies may be verbose or shorthand; they
are actionable or interpretable every time. Agents interpret free text — they
never demand syntax. If a reply genuinely cannot be mapped to an item, re-ask
once in the next brief with sharper framing; never silently drop it.

**Notion path — content topic review ({{HEAD_OF_MARKETING_FIRST}}).** Adopted with the topic-review flow. The one
approval flow that does not run through a Slack thread. content-researcher's content
topics are mirrored into a Notion database (Marketing → Content Engine → Topic
Backlog); {{HEAD_OF_MARKETING_FIRST}} sets a `Status` and leaves free-text `Comments` there. Scribe
harvests the rulings on **every** one of its ticks — Monday stand-up, Tue–Fri
pulse, Wednesday WBR — via `roster/scribe/skills/notion-topic-sync.md`, and
applies each through `scripts/topic_review.py`, which writes `topic_backlog`
and one `approvals` row per decision.

Three things make this path different from the daily Slack path, and they are
the reasons it exists:

- **The approver is {{HEAD_OF_MARKETING_FIRST}}, not Scott.** Editorial calls on content topics are
  his. Scott remains architect and tie-breaker for anything that changes how
  the fleet runs (see below) — including changes to this flow itself.
- **The surface is a database, not a thread.** Structured `Status` is the
  signal; `Comments` carries reasoning. Agents read both but only `Status`
  drives state, so there is no free-text intent to misparse. Comments on a
  `Needs revision` row are instruction for the next synthesis, never an
  in-place rewrite of the topic.
- **Harvesting is decoupled from the owning agent's cadence.** content-researcher runs
  weekly; harvesting on every Scribe tick keeps decision latency near a day
  instead of up to nine. `scripts/topic_review.py` exists so the semantics of
  a decision live with the owning agent even though another agent holds the
  connector — the same pattern as `scripts/handoffs.py` and `scripts/pm/`.

Precedence is explicit because one `Status` field is shared: `Approved` /
`Needs revision` / `Rejected` are {{HEAD_OF_MARKETING_FIRST}}'s and flow Notion → repo; `Pending
review` / `Candidate` / `Briefed` / `Published` / `Refresh` are agent-owned and
flow repo → Notion. The sync pulls before it pushes, so a push can never
overwrite a ruling made since the last tick. `Topic UID` is the sync key and is
never edited in Notion by anyone.

**Human feedback weighting.** Feedback from any of the team's humans — Scott
McKeighen, {{HEAD_OF_MARKETING}}, {{CONTENT_LEAD}}, {{DESIGN_LEAD}} — on any surface an agent
reads (Slack threads and replies, Notion page edits, Linear comments, WBR
sections) is heavily weighted: above baselines, above prior patterns, above
the agent's own judgment. Never discount feedback by source. Agents record
substantive teammate feedback as handoffs entries and fold standing
implications into their Identity Notes, the same as they do for Scott's.

**Scott is the architect and tie-breaker.** Operational decisions and
implementation changes — thresholds, filters, identity/skill file edits,
protocol changes, anything that alters how the fleet runs — are approved by
Scott. When feedback from different humans conflicts, or when a teammate's
feedback implies an operational or implementation change, route it to Scott
as a Decision Queue item rather than applying it unilaterally — and rather
than letting it drop. A decision record is ground truth until Scott revises
it.

**Default-on-silence.** An ask may carry a pre-authorized default that
chief-of-staff applies if the decide-by date passes without a reply. Eligibility is
narrow:

- Reversible, Tier 0/1 scope only: journal/DB state, flag suppression,
  keep-watching postures.
- Never eligible: filters, thresholds, identity or skill file edits, any
  HubSpot/Notion/Slack-channel/external surface.
- The original ask must have stated both the default and the date.
- Applications are recorded in `decisions` with
  `approved_by='default-on-silence'` and surfaced in the next brief as a
  closed loop, not buried.

**Weekly sweep — `/triage`.** Anything still open after the daily path runs
through the weekly triage session (runbook: `docs/triage-protocol.md`): load
all open items, propose a resolution playbook per item, collect rulings,
apply the full fan-out, commit.

Adopted at the reference housecleaning run.

## Linear References

Every Linear issue ID and project name in any agent-authored output must be
rendered as a clickable link. No bare `MAR-XXXX` or bare project names in
Slack, Notion, journal files, handoffs, ops-incidents, or any other surface.

Full rule (surface-to-syntax table, label rules, URL rules, MCP-down
fallback): [`docs/linear-reference-formatting.md`](linear-reference-formatting.md).
