---
name: performance-marketer:execute-approved
description: >
  Processes a greenlit optimization dossier. Applies the Tier-3a moves via the
  constrained Google Ads mutate tool (shadow unless PERFORMANCE_MARKETER_EXECUTE=live), packages
  the Tier-3b moves as a human change-list, routes creative moves to copy-review,
  and writes an execution-summary handoff. Nothing is applied without a matching
  Scott→performance-marketer decision; caps and the kill switch are enforced in code.
---

# Execute Approved

## When This Runs

- **Tick integration:** triggered from the Librarian Protocol (step 3) when a new
  `Scott → performance-marketer` decision approving a dossier is read.
- **Standalone:** `/performance-marketer execute-approved`.

Default posture is **safe**: with `PERFORMANCE_MARKETER_EXECUTE` unset, this runs in shadow only
(validate-only, nothing applied). It never acts without a greenlit decision.

## Inputs

- A greenlit `Scott → performance-marketer` decision (from `handoffs.md` / the `decisions`
  table) naming the dossier (by `dossier_date`).
- `PERFORMANCE_MARKETER_EXECUTE` mode (`config.execution_mode()`): `off` | `shadow` | `live`.

## Workflow

### 1. Load the greenlit proposals

```python
from scripts.paid import db, execute, config
conn = db.connect()
proposals = db.list_proposals(conn, dossier_date=DOSSIER_DATE)  # the greenlit dossier
```
Mark them greenlit (`db.set_proposal_status(..., 'greenlit', decided_at=now, approval_ref=...)`)
if not already. Then partition:
```python
parts = execute.partition_proposals(proposals)   # {auto_3a, human_3b, creative}
```

### 2. Auto_3a — apply via the mutate tool

```python
from scripts import google_ads_mutate as gm
ops = execute.proposals_to_ops(parts["auto_3a"])
result = gm.execute(ops, conn=conn, approval_ref=DECISION_REF, now=now)  # mode from PERFORMANCE_MARKETER_EXECUTE
```
`gm.execute` guards every op (caps RAISE, never clamp), validate-only-first, and
applies **only** in `live`. It logs each acted op to `applied_changes` (mode
`shadow`/`live`) with a `prior_value` snapshot.
- **live** → set each applied proposal `status='applied'`.
- **shadow** → leave `status='greenlit'` (the `applied_changes` row records the
  simulation; nothing changed in Google Ads).
- **off** → `result["note"]` says disabled; nothing applied.
- Ops the mutate tool doesn't yet implement (`match_type_promotion`,
  `create_experiment`) come back under `result["deferred_to_human"]` — fold them
  into the 3b change-list below.

### 3. Human_3b — package a change-list

```python
md = execute.render_human_change_list(parts["human_3b"] + result["deferred_to_human"], DOSSIER_DATE)
# supersede the prior pending change-list, then write the new one:
#   python3 scripts/paid/publish.py change_lists
# write md to docs/publications/pending/performance-marketer/change_lists/<DOSSIER_DATE>-change-list.md
```
Leave these proposals `status='greenlit'` (awaiting human apply). performance-marketer never
applies 3b itself.

### 4. Creative — route to copy review

For each `creative` proposal, run the **Copy-Review Delegation** procedure in
`performance-marketer:creative-optimizer`: create a Linear task (default {{CONTENT_LEAD_FIRST}}, reassignable)
carrying the pre-drafted variations, then
`db.set_proposal_status(conn, pid, 'awaiting_creative', linear_ref=...)`.

### 5. Execution-summary handoff

Append a `performance-marketer → chief-of-staff` handoff (and the `handoffs` row) summarizing the run
for the next AM brief:
- mode (shadow/live), counts applied / validated-only / deferred,
- the 3b change-list path (what a human must apply),
- the `awaiting_creative` Linear refs,
- the rollback window (`config.ROLLBACK_WATCH_HOURS`) and that each applied change
  has a `prior_value` snapshot in `applied_changes`.

Then `conn.commit()`, journal the run, and commit state (the Tick handles commit).

## Safety invariants

- Nothing applies without a matching `decisions` row (a real greenlight).
- The 3a allowlist, the ±20% bid envelope, the per-run op cap, and the kill switch
  live in `scripts/paid/config.py` and are enforced in `scripts/google_ads_mutate.py`
  — a violated cap raises.
- `live` is the only mode that writes; it requires the explicit `PERFORMANCE_MARKETER_EXECUTE=live`
  flip, which is an operator decision after a shadow review.

## Output

- `applied_changes` rows (mode `shadow`/`live`) with rollback snapshots.
- Updated `paid_change_proposals` statuses (`applied` / `greenlit` / `awaiting_creative`).
- `docs/publications/pending/performance-marketer/change_lists/<date>-change-list.md` (human change-list).
- An execution-summary handoff to chief-of-staff.
