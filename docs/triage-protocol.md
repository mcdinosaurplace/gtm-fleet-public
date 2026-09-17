# Triage Protocol — Weekly Decision Sweep

Operator-facing runbook for `/triage`. Run weekly (suggested: Wednesday,
alongside the WBR cycle) or whenever the Decision Queue backs up. The reference
run is a housecleaning sitting: the whole queue in one pass — on the order of a
hundred backlog items plus the handful of aged decisions (two to four weeks
old) sitting behind them — rather than a trickle of one-off rulings.

This is a working session between Scott and the assistant — not an agent Tick.
Rulings collected here are architect rulings — ground truth for the fleet
(see `docs/conventions.md` → Decision Queue). Teammate feedback ({{HEAD_OF_MARKETING_FIRST}}, {{CONTENT_LEAD_FIRST}},
{{DESIGN_LEAD_FIRST}}) routed into the queue is weighed just as heavily as input; Scott is
the tie-breaker on operational decisions and implementation. When a triage
item originated from teammate feedback, present it with attribution so the
ruling can engage with it directly.

## Steps

### 1. Pull current state

```
git pull
python3 scripts/handoffs.py list
```

Also query for context:
- `SELECT * FROM decisions ORDER BY id DESC LIMIT 10` — recent rulings, avoid
  re-asking anything already decided
- Open `anomalies` rows (status='open') not represented by a live handoff
- Skim the newest entries in `state/journal/handoffs.md` for carry-forward
  threads that never became handoff rows (e.g., journal-only asks)

### 2. Build the queue

One numbered item per *thread*, not per row — collapse superseded daily
re-flags into their latest entry. For each item present:

- The ask, in one line
- Age, severity, and what the agents have already observed
- A **proposed resolution playbook** (see below) with a recommendation

### 3. Collect rulings

Scott responds per item — verbose or shorthand, both valid. Interpret free
text; ask a sharpening question only if a ruling genuinely cannot be mapped
to an action.

### 4. Apply the fan-out

For every ruling, in this order:

1. INSERT a `decisions` row (agent, context, decision verbatim-ish,
   approved_by='scott', timestamps).
2. Append a `Scott → {agent}` entry to `state/journal/handoffs.md` with the
   full reasoning — the fleet reads this, not the DB, for context.
3. `python3 scripts/handoffs.py resolve <ids> --note "..."` (or `ack` if the
   ruling is "seen, keep open").
4. Apply file changes per the playbook.
5. Commit and push (normal operator identity, not state-bot).

### 5. Close

Confirm `scripts/handoffs.py list` shows only intentionally-open items.
Note in the session summary anything routed onward (e.g., a business decision
that became a Linear issue).

## Resolution playbooks

| Ruling type | Fan-out beyond DB + journal |
|---|---|
| **Accept / explained** ("this is fine, here's why") | None. Resolve with the explanation in the note — agents stop re-flagging. |
| **Baseline break** ("new level is the new normal") | State the break date and post-break reference level in the handoffs entry so the watcher stops comparing against the stale baseline while the trailing window normalizes. |
| **Filter / exclusion update** | Edit the owning skill file (e.g., `roster/revops-watchdog/skills/opsos-watch.md` exclusion list) with the rationale and decision date inline. |
| **Threshold recalibration** | Edit all encodings — identity file (canonical), agent prompt, skill file. Cite observed ranges that justify the new band. |
| **Defer** | Re-ack with a new decide-by date; eligible items may get a default-on-silence. Two deferrals = the ask is wrong — reframe it. |
| **Route to human owner** | Create a Linear issue (per `gtm-fleet:linear-task-capture` conventions) and resolve the handoff with the issue link. |
| **Standing guidance** ("from now on, always/never X") | Also append to the affected agent's Identity Notes section — this is the durable form of architect feedback. |

## Guardrails

- Never bulk-resolve without distinguishing "issue closed" from "flag
  superseded" — say which in the journal entry.
- Tier 3 surfaces (HubSpot writes, external publishes) are never part of
  triage fan-out; they get their own approval flow.
- If a ruling changes agent behavior, the affected agent must be able to
  discover it from `handoffs.md` alone on its next Tick — the journal entry,
  not this session, is the delivery mechanism.
