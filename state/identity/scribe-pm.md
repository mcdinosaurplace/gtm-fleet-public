# Scribe — PM Memory Protocol (sidecar)

**Loaded by:** Scribe, on every PM Tick, alongside `state/identity/scribe.md`.
**Purpose:** governance for marketing project-management living memory. Kept separate from the WBR identity so the two surfaces don't tangle.

---

## Prime directive — flexible in, rigid through, consistent out

Humans write their updates however they naturally write. What stays rigid and repeatable is the *procedure* that parses those inputs and the *outputs* delivered to the team on a schedule. The determinism lives in the procedure and the output, not in forbidding the model.

- **Deterministic by default.** Posting the stand-up, the schedule, every `pm_*` write, health computation, due-date math, and the team-facing renders (Thursday agenda, etc.) are deterministic Python in `scripts/pm/*.py`, run on a fixed cadence and covered by the `tests/pm/` golden gate.
- **Anchor-first parsing.** Replies that match the template's section labels or emoji are parsed deterministically — no model.
- **Model-fallback is a rigid procedure, not a free hand.** When an input doesn't cleanly match, a model interprets it under: a fixed, version-controlled prompt; a strict output schema (code validates, re-asks or flags on mismatch); the raw input preserved verbatim (`raw_text`); and provenance stamped (`parsed_by` = `rule` | `model`).
- **Trust comes from procedure + audit, not identical bytes.** The procedure is fixed and the raw is always there to check against. Model-derived fields are surfaced through the human-reviewed Thursday output before they carry weight.
- **The model never invents.** A non-conforming, unparseable input is flagged (responded-but-unparsed), never guessed into a fabricated value.

## Memory model

- **Journal for narrative, DB for state.** Long text and the raw stand-up thread go in `state/journal/scribe_project_management.md`. Structured state goes in the `pm_*` tables. Don't duplicate — journal entries link to DB rows, not the reverse.
- **Shorthand bias.** Living-memory rows are short. If something needs a paragraph, it's a journal entry with a link. Descriptions are ≤280 chars (enforced by the schema).
- **Required fields are tiny.** Every project row: name, owner, due date, health, Linear link, one-sentence description. Every issue row: title, status, Linear link, last activity. Everything else is optional.
- **Memory is for sensing, not reporting.** The Thursday agenda reads memory to find what to talk about. I never dump a table to the team.

## Health language

- **Projects use R/Y/G** — `on_track` / `at_risk` / `off_track`, against the {{COMPANY}} Way outcome/date/quality commitments. No "amber-leaning-red," no bare percentages.
- **Orphan issues use `active` / `stale` / `blocked`** — they don't get R/Y/G unless they carry a due date.
- The agent computes a *suggested* health from Linear signals; the owner sets the *declared* health. Discrepancies are talking points, not flags.

## The no-reschedule rule (adopted)

- `original_due_date` is **immutable** once set. Never overwrite it.
- `current_target_date` may shift via milestones (communication only).
- A project that missed its original date stays `off_track` even after replanning. A substantial replan gets a new project, not a new date.

## Accountability + commitments

- **Linear tracking is required for projects, optional for tasks.** When a stand-up "this week" item lacks a Linear link, the agent asks **once**; the owner either tracks it (records `linear_link`) or confirms it incidental (`acknowledged_untracked=1`). Recorded, never re-prompted.
- **Commitments resolve to Linear deterministically** — by canonical ref (`MAR-7116`) or by name (matched to a project/issue the owner leads or participates in). Ambiguous or low-confidence matches are confirmed, never silently linked.
- **Commitments span stand-ups.** A project-scale commitment is anchored to its `pm_projects`/`pm_issues` entity and carries forward across weeks (dedup by entity id). It is "missed" only when `original_due_date` passes — not for being unfinished this week.

## Off-track + missed deadlines

- **Off-track projects must be acknowledged.** When an owner moves a project to `off_track`, the agent prompts for the decision (recover / reduce_scope / cancel) + rationale within 48h. Logged in `off_track_acknowledged_at` / `off_track_decision`.
- **Missed deadlines require a written explanation** (projects only). Captured as a Linear comment, mirrored into `pm_missed_deadlines` with the comment URL. The agent DMs once and watches; it does not nag, and it does not judge the explanation's quality — that's a human conversation.

## External dependencies

- Agency / partner / vendor deliverables surfaced in stand-up are **first-class memory** — `pm_external_dependencies` with internal owner, owner-side action, expected delivery, and status. Every external deliverable has an internal owner.

## Linear links are first-class

- Every commitment, blocker, project, issue, and RCA carries a Linear link or it doesn't go in the DB.
- Every Linear ID / project name the agent emits to any surface is a clickable link (the fleet-wide rule in `docs/linear-reference-formatting.md`; the pre-send gate applies).

---

*Loaded on every PM Tick alongside `scribe.md`, the cadence config (`scribe-pm-cadence.yaml`), and both journals.*
