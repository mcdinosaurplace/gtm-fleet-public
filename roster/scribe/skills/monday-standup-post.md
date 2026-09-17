# Skill: monday-standup-post

Posts the Monday async stand-up to `#team-marketing`: a fixed master broadcast plus a
per-member tagged reply scheduled at each person's local time. The thread anchor is
persisted so later ticks can capture replies (B2) and resolve commitments (B3).

Invoked via `/scribe standup` or the scheduled Monday fire (the schedule is the standing
Tier 2 pre-authorization). Determinism: all message text is rendered by
`scripts/pm/standup_post.py`; this skill only orchestrates the Slack + DB I/O and may
vary only conversational phrasing in ad-hoc replies (never the master post or templates).

## Preflight

- PM Librarian steps (see `roster/scribe/prompt.md`): load `scribe.md` + `scribe-pm.md`;
  validate the cadence config — `python3 -m scripts.pm.config` (abort on non-zero exit,
  fail closed); read the PM journal; run pending migrations.
- Anchor: confirm today is Monday. If invoked off-cadence (manual), proceed and note it.
- MCP preflight: **Slack essential** for this skill. Linear is not required to post; it
  becomes essential for capture (B2) and resolution (B3). Abort before any Slack send if
  Slack fails to bind.

## Steps

1. **Compute the plan.** Run `python3 -m scripts.pm.standup_post` (defaults to today UTC;
   pass `YYYY-MM-DD` to override). It prints JSON:
   `{channel_id, week_starting, master_text, tag_text}`.

2. **Post the master.** `slack_send_message` to `channel_id` with `master_text`. Capture
   the returned message `ts` — this is the thread anchor.

3. **Persist the thread anchor.** Upsert `pm_standup_threads` (key `week_starting`) via
   `scripts/pm/db.py`: `{week_starting, channel_id, master_ts, master_posted_at (ISO8601), created_at (ISO8601)}`.
   Commit the connection.

4. **Post the consolidated tag in-thread.** One `slack_send_message` reply with
   `thread_ts = master_ts` and `message = tag_text` — it @-mentions every member once
   (native `<@id>` mentions, so each person is notified). No per-member scheduling:
   Slack has no sub-threads, so members reply directly to the master thread.

5. **No DMs.** `accountability_mode = state_only` for cycle 1 — channel post only; no nudges.

6. **Journal.** Append one entry to `state/journal/scribe_project_management.md`:
   `## <ISO8601> | Monday stand-up posted — week of <week_starting>`, recording `master_ts`,
   the channel, and the consolidated tag's `ts`.

7. **Handoff.** Append to `handoffs.md` (scribe → chief-of-staff, LOW): stand-up posted; capture
   sweep due at EOD.

8. **Commit** all `state/` changes with the `state-bot` identity:
   `[state-bot] Scribe | Skill: monday-standup-post | <ISO8601 UTC>`. Push. (These are
   `state/` data commits; the PM pre-commit gate does not fire on them.)

## Linear reference formatting

Any Linear ID or project name in the post or journal must be a clickable link
(`docs/linear-reference-formatting.md`). The master/tag templates carry none by design.

## Sweep (EOD capture) — `/scribe standup sweep`

Runs at the Monday response deadline (D1 cron). Reads the thread, archives it raw, and
writes parsed responses + external dependencies. Anchor-first deterministic parse;
model-fallback only for non-conforming input, under the fixed prompts below.

1. **Load the anchor.** Read the week's `pm_standup_threads` row (`master_ts`, `channel_id`).
2. **Read the thread.** `slack_read_thread(channel_id, master_ts)` -> messages `[{user_id, text, ts}]`.
3. **Archive raw.** Append the full thread verbatim to `state/journal/scribe_project_management.md` (the audit source) — every message, `members` and `context` alike.
4. **Deterministic pass.** Pipe `{"thread_messages": [...]}` to `python3 -m scripts.pm.capture` -> `{members:[...], non_responders:[...], context:[...]}`. `capture()` splits each roster member's aggregated reply by whether any of the four section anchors matched:
   - **`members`** — at least one anchor matched: a real stand-up response.
   - **`context`** — zero anchors matched: thread chatter (a reply to someone else's blocker question, cross-talk about a project, etc.). **Not** a response — the member stays in `non_responders` and gets no `pm_standup_responses` row, but the raw text is preserved (step 3) and is a candidate for the section-split prompt (step 5) in case it happens to carry a real commitment.
5. **Model-fallback (rigid procedure)** — flagged items only:
   - every **`context`** entry -> run the **section-split prompt** on `raw_text`. If every
     extracted field comes back null (the common case — pure chatter, e.g. answering
     someone else's blocker question), stop there; nothing is written. If a field is
     non-null, classify which of the two shapes it is before writing anything (agent
     judgment — this split isn't reducible to a fixed regex the way negative-response
     detection is):
     - **New commitment, stated by the chatter's own author** (first-person, future
       action — "I'll do that list pull this week"). Route it into commitment resolution
       exactly like a `this_week` line for that person: `linear_resolve.resolve` ->
       `commitments.build_row`, tagged `parsed_by='model'`. No due date stated -> the
       normal end-of-week fallback applies, same as any other untracked `this_week` item
       (`commitments.classify`, proven in `tests/pm/test_commitments.py`). This never
       creates a `pm_standup_responses` row or clears the author from `non_responders` —
       it only appends to `pm_commitments`.
     - **Resolution/approval of a DIFFERENT person's existing item** ("{{HEAD_OF_MARKETING_FIRST}} approves the
       copy {{CONTENT_LEAD_FIRST}} raised"). Fetch the subject person's OPEN `pm_commitments` rows
       (`week_starting, id, commitment, linear_link, project_id, issue_id`) as candidates
       and call `commitments.match_open_commitment(text, candidates)`:
       - `by_ref` / `by_name` (single confident match) -> append a linked note to
         `state/journal/scribe_project_management.md` naming the approver, the quoted
         text, and the matched `pm_commitments.id` — **no `pm_commitments` write**. The
         approval is narrative context for a human/Thursday-agenda read, not a new
         completion-status value (an approval unblocks the item; it doesn't complete it).
       - `needs_model` (ambiguous or no candidate) -> flag in the journal for human
         review. Never guess a link.
   - each `members[].external_deps_needs_model` line -> run the **dep-extraction prompt**. (A bare negative response — "None", "N/A", "No dependencies" — is filtered by `capture.py`'s deterministic pass before this step; it never reaches the model.)
   Validate every model output against its schema; on mismatch, re-ask once, then flag (never write a malformed row). Stamp `parsed_by='model'`.
6. **Write (via `scripts/pm/db.py`):**
   - `pm_standup_responses` — one row per **`members`** entry (`week_starting, owner, slack_user_id, last_week, this_week, blockers, linear_links_present, responded_at, raw_text, parsed_by`). Each **non-responder** (including a `context`-only member) gets a row with `responded_at = NULL` (flagged, never fabricated).
   - `pm_external_dependencies` — rule deps (`parsed_by='rule'`) + model deps (`parsed_by='model'`), each with `internal_owner`, `raw_text`, `week_starting`, `status='pending'`.
7. **Journal + commit** as in the post flow (state-bot identity).

### Fixed prompts (the rigid procedure — change only via commit)

**Section split** (a reply with no recognizable section anchors):
> Extract this stand-up reply into JSON with keys `last_week`, `this_week`, `blockers`, `external_deps` (strings; null if the member did not address that section). Use ONLY the member's own words — copy them; do not summarize, rephrase, or invent. If unsure a section is present, set it null. Return only the JSON.

**Dependency extraction** (a non-`/`-structured external-dep line):
> From this external-dependency text, return JSON: `external_party` (the agency/partner/person, or null), `owner_side_action` (what we owe to unblock them, or null), `expected_delivery` (ISO 8601 date if a date is expressed — resolve relative dates against {stand-up date} — else null). Use only stated information; do not invent. The raw text is stored separately. Return only the JSON.

Schema validation (code): keys present, types correct, `expected_delivery` matches `YYYY-MM-DD` or is null. Reject + re-ask once on mismatch.

### Resolve commitments -> pm_commitments

Run after the responses are written. For each responder, split their `this_week` section
into individual commitment lines (one per non-empty line/bullet). For each line:

1. **Fetch candidates.** From Linear (MCP): the owner's open projects + issues (as lead or
   member), shaped `{id, name, type, due_date}`.
2. **Resolve (deterministic-first)** via `scripts/pm/linear_resolve.py::resolve(commitment, candidates)` -> `{resolution, refs, match, shortlist}`:
   - `by_ref` -> `get_issue`/`get_project` on each ref -> entity type + id + name + due + URL.
   - `by_name` -> use `match`.
   - `needs_model` -> run the **commitment-resolution prompt** (below) over `shortlist`.
3. **Confirm (one-time, via DM call-and-response — gated by `accountability_mode`).** If the
   model returns `null`/low confidence, or there are no candidates, batch the owner's
   unresolved `this_week` commitments into a single **Slack DM** to that owner (not an
   in-thread reply), composed in the **Accountability prompt format** below. This follows
   chief-of-staff's Decision Queue call-and-response (`roster/chief-of-staff/prompt.md` step 10): persist
   the sent DM's permalink to the PM journal so the next sweep can find the reply thread; on
   that sweep, read the reply thread (fall back to DM channel history) and interpret the
   owner's free-text reply — verbose or shorthand, never demand syntax. Per commitment:
   - Owner gives a Linear link/ref -> resolve it (`resolution=confirmed`).
   - Owner picks a listed project/issue -> `resolution=confirmed`.
   - Owner says "track it" / "new ticket" / "new project" and no entity exists -> **create it**
     via the **Linear entity creation** procedure below (direct callout authorizes; a bare/inferred
     "track it" with no kind signal confirms once first). Record `resolution=confirmed` with the
     new `linear_link`.
   - Owner says no / incidental -> `acknowledged_untracked=1`, `resolution=unresolved`, scale incidental.
   One DM per owner per sweep (batches all their open items); hard cap.
4. **Classify + write.** `scripts/pm/commitments.py::build_row(...)` derives scale / horizon /
   effective_due_date; write to `pm_commitments` via `db.py`. Project-scale commitments anchor
   to their entity and carry forward across weeks (dedup by `project_id`/`issue_id`).

**Fixed prompt — commitment resolution (rigid procedure; change only via commit):**
> Given a stand-up commitment and a numbered list of the owner's Linear projects and issues, return JSON `{match_id: <an id from the list, or null>, confidence: "high" | "low"}`. Choose a match only if the commitment is clearly about that project or issue. If none clearly matches, return null. Do not invent ids. Return only the JSON.

Schema validation (code): `match_id` is one of the provided ids or null; `confidence` in {high, low}. Treat `low` or null as 'no match' -> confirm with the owner.

### Accountability prompt format (DM call-and-response)

All accountability prompts — the one-time commitment confirm (above), the C3 close-the-loop
replay (below), and any outstanding-commitments backlog sweep — are delivered as **Slack DMs**
to the owner and resolved by reading their free-text reply (chief-of-staff's Decision Queue pattern,
`roster/chief-of-staff/prompt.md` step 10): never demand a reply syntax; interpret verbose or shorthand
answers. Persist the sent DM's permalink to the PM journal so the next sweep finds the reply thread.

Message style (the fleet standard — keep it scannable):
- **Bold title** naming the check and the week; a short italic tag if it is a test.
- One-line intro: what didn't resolve and the reply contract (give a Linear link/ref to track it,
  or say **incidental** to acknowledge-untracked — recorded once, never re-prompted).
- **Numbered items.** Each: a **bold short label** + a parenthetical of the specifics, then the
  bump result and a single clear ask.
- For a partial/closest match, name the closest Linear entity **as a clickable link**, state what
  it does and does not cover, and offer link / split / incidental.
- Close with an inline-reply example (e.g. `Reply inline, e.g. "1 incidental, 3 link MAR-7075"`).
- Voice: factual, non-accusatory; pragmatic questions about due date / scope / whether it should be
  a Linear task are fine. No em-dashes, no AI-speak. Every Linear ref is a clickable link
  (`docs/linear-reference-formatting.md`).

### Linear entity creation (accountability-driven) — `scripts/pm/linear_create.py` (Block G2)

Fires **only** from a human's accountability reply (the commitment confirm, the C3 close-the-loop,
or the outstanding-commitments sweep) — never autonomously, and only when `accountability_mode` is
on. This is the narrow, human-authorized half of the deferred brief-to-Linear write; the pulse stays
read-only and the content brief→Linear flow (G1) is separate.

1. **Detect intent** (`linear_create.detect_intent` — deterministic keywords; `needs_model` →
   run the fixed classifier below). Per commitment in the reply, classify resolution intent:
   - `link_existing` — reply carries a Linear ref/URL or picks a listed entity → existing resolve path.
   - `roll_in` — "roll into `<hub / other item>`" → link to that entity; create nothing (dedup by target id).
   - `create_issue` — "track it / new ticket / create an issue" with no existing match. **Default for an
     inferred bare "track it" with no kind signal.**
   - `create_project` — explicit "project / new project / track as a project" **only**.
   - `incidental` — no / incidental.
   Direct callout (explicit create/track keywords) → the reply **is** the authorization. Inference (bare
   "track it" / "yes", no entity match) → treat as `create_issue` but **confirm once** (kind + title +
   parent) before writing; **never** create a *project* on inference.

   **Fixed prompt — creation intent + fields (rigid procedure; change only via commit):**
   > Given a stand-up commitment and the owner's reply, return JSON `{intent: "link_existing"|"roll_in"|"create_issue"|"create_project"|"incidental", title: <short title from the commitment's own words, or null>, parent_project: <name/ref if stated, else null>, roll_into: <entity name/ref if intent=roll_in, else null>, subscribers: [names explicitly asked to be looped in, else empty], notes: <dependency / blocked-by / scope text stated, else null>}. Use only what the commitment and reply state; do not invent a title or a parent. Return only the JSON.

   Schema validation (code): `intent` in the enum; `title` null or non-empty string; arrays well-formed.
   Re-ask once on mismatch; on a second failure, fall back to a one-time human confirm.

2. **Build the payload (deterministic).** `linear_create.build_payload(...)` maps the validated
   extraction → a `save_issue` / `save_project` payload with fixed defaults: team = Marketing;
   **orphan issues (no parent stated) → MOPS Inbox and New Requests**; assignee / project lead = the
   commitment owner; subscribers → `@displayName` mentions appended to the description (`save_issue`
   has no subscriber field); stated dependencies/blocked-by → into the description as prose (Linear
   issue relations only when a real issue ref is given); target/priority left unset unless stated.

3. **Idempotency + dedup (no dupes).** Consult `linear_create.creation_action(row)` first:
   `skip` (already `linear_link`ed) → nothing to do; `reconcile` (`create_requested_at` set but no
   link — a prior create was attempted) → search Linear by title and link if found, else retry;
   `create` → proceed. Before any create call, **stamp `pm_commitments.create_requested_at`**
   (`db.update(conn, 'pm_commitments', {'create_requested_at': now}, {'id': row_id})`) so a re-run
   reconciles instead of duplicating. Then run `linear_create.dedup_match(title, candidates)` against
   open entities; an exact-title match links instead of creating (report "found existing `<ref>` —
   linked"). `roll_in` always links, never creates.

4. **Gate.** Direct-callout creation: the owner's reply authorizes it (Tier 2 per-run, satisfied by the
   human in the loop) → create, then post a one-line confirmation in the DM thread ("Created `<ref>` —
   linked"). Inferred creation (`detect_intent` returned `inferred=True`): confirm once before writing,
   and never create a *project*. Creation never fires outside an accountability reply and never in
   `state_only`.

5. **Write back.** The commitment row already exists (captured this week as `unresolved`), so this is an
   UPDATE: `commitments.build_resolution_update(week_starting, 'confirmed', entity_type=..., entity_due_date=...,
   linear_link=..., project_id=.../issue_id=...)` → the column dict → `db.update(conn, 'pm_commitments',
   <dict>, {'id': row_id})`. (`build_resolution_update` shares build_row's classify, so a created-and-linked
   commitment matches a name/ref-resolved one.) The next pulse picks the entity into `pm_projects`/`pm_issues`.

### Evaluate prior commitments (C3) — at Monday start

Before posting the new stand-up, evaluate last week's open `pm_commitments`
(`completion_status` in pending/in_flight/carried):

1. **Linked commitments** (project_id or issue_id set) — deterministic via
   `scripts/pm/commitments.py::evaluate_completion`. Build `entity = {closed, canceled,
   original_due_date}` per commitment, then update `completion_status` (completed / dropped /
   missed / in_flight / carried) + `evaluated_at` via `db.py`. **Runs every cycle** (a Tier 0
   DB update — no DM).

   - **Issue-linked**: always live. `get_issue(issue_id)` is on every caller's Linear
     allowlist and cheap by exact id, so call it every run — no cache dependency, no
     staleness question.
   - **Project-linked**: `get_project` is not universally allowlisted, so resolve
     cache-first with a live fallback (`scripts/pm/commitments.py::cache_is_fresh` /
     `project_entity_from_cache` / `refresh_project_from_live`):
     1. **Part A (cache).** If the linked `pm_projects` row exists and
        `cache_is_fresh(row.last_synced_at, now)` (within `STALE_HOURS` = 48h — the
        Tue–Fri pulse keeps this current in normal weeks), build the entity from that
        row via `project_entity_from_cache`. No live call.
     2. **Part B (live fallback).** Otherwise — no cached row, or `last_synced_at` older
        than 48h — call `list_projects(query=<cached name, or the commitment's Linear
        project name if no cached row>, team="Marketing")` (already-allowlisted). Score
        the results with `scripts/pm/linear_resolve.py::resolve` (deterministic name
        match, no model) against the target name:
        - **Single confident match** (`resolution == "by_name"`): normalize it with
          `pulse.normalize_project`, build the patch + entity via
          `refresh_project_from_live(cached_row, live_project, now=now)`, write the
          patch back to `pm_projects` (`db.update`/`db.upsert`, stamping
          `last_synced_at`), and use the refreshed entity. This also self-heals the
          cache for the next run.
        - **No match or ambiguous** (`resolution == "needs_model"` or zero results):
          treat as vanished — `entity = None` (`evaluate_completion` returns `carried`)
          — and note it in the journal as "no confident Linear match — human check."
          Do not run a model here; this is an internal cache-refresh, not a
          user-facing resolution, so ambiguity gets flagged, not guessed.
     Note each row's provenance (cache-fresh / live-refreshed / flagged) in the journal
     entry.

2. **Incidental commitments** (unlinked) — **gated by `accountability_mode`** (off in cycle 1):
   - **Close-the-loop replay:** **DM the member** (call-and-response, **Accountability prompt
     format** above — not an in-thread reply) listing their open incidentals verbatim, and accept
     an explicit **"Done"** and/or a **✅** (`:white_check_mark:`) to mark `completed` (deterministic
     done-signal detection). Never accusatory; it is fine to ask pragmatic questions about a due
     date or scope ("still relevant? when do you expect it? should this be a Linear task?").
   - **Model-match:** for incidentals not explicitly closed, run the fixed prompt below against
     the member's new "last week" report -> completed / partial / carried (raw preserved,
     `parsed_by='model'`). If there is no clear signal, leave it `pending` and surface it Thursday.

**Fixed prompt — incidental completion match (rigid procedure; change only via commit):**
> Given a prior incidental commitment and the member's new "last week" report, return JSON `{status: "completed" | "partial" | "carried"}`. Choose `completed` only if the report clearly says that specific item was finished; `partial` if explicitly partly done; otherwise `carried`. Use only what the report states; do not infer or invent. Return only the JSON.

---

*Block B (post -> capture -> resolution) is complete. C3 (week-over-week completion eval) is wired
here; the Tue-Fri pulse (`linear-pulse-check`) maintains the project/issue state it reads. The
agenda/WBR surfaces (v1.5) consume the captured state.*

## Acceptance

- Master lands within 5 min of the configured time; structure byte-identical to the
  golden (`tests/pm/test_standup_post.py`).
- The consolidated tag posts as a single in-thread reply that @-mentions all members.
- `pm_standup_threads` has exactly one row for the week with the master `ts`.
- No DMs sent in cycle 1.
