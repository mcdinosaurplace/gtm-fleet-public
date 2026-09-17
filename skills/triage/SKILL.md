---
name: triage
description: Weekly decision-queue triage sweep — load open handoffs, anomalies, and recent decisions; build a numbered queue; collect the operator's rulings; apply the resolution playbooks. Use when asked to triage, sweep the decision queue, or resolve agent-surfaced decisions.
argument-hint: "[--since YYYY-MM-DD]"
disable-model-invocation: true
allowed-tools: Bash(python3 *) Bash(git *) Bash(sqlite3 *) Bash(ls *) Bash(cat *) Bash(head *) Bash(tail *) Bash(wc *) Bash(date *) Read Edit Write Glob Grep ToolSearch
---

Paths for this session (absolute; use them for every script call and state read/write):

- PLUGIN_ROOT = ${CLAUDE_PLUGIN_ROOT}
- FLEET_ROOT  = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --root`
- Status      = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --status`

First command: `cd "$FLEET_ROOT"`. Relative `state/...` paths in the roster prompt resolve
from there; `scripts/...` paths resolve under PLUGIN_ROOT (identical in workspace mode).

Run the weekly decision-queue triage sweep. Follow the runbook in `${CLAUDE_PLUGIN_ROOT}/docs/triage-protocol.md`.

Before starting, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fleet_git.py sync`.

Load all open handoffs (`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/handoffs.py list`), open anomalies, and
recent decisions; build a numbered queue collapsing superseded re-flags into one item per thread;
propose a resolution per item and collect the operator's ruling before applying any playbook.

Rulings collected here are architect rulings — ground truth for the fleet. Teammate feedback
(the head of marketing, content lead, design lead) in the queue is weighed just as heavily as
input; the operator is the tie-breaker on operational calls.

Arguments: $ARGUMENTS
