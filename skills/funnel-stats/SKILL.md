---
name: funnel-stats
description: Generate the current month-to-date GTM funnel metrics (MEL/MQL/SAL/SQL/pipeline) from ~~crm (HubSpot) as a fixed metrics block. Use when asked for funnel stats, MTD funnel numbers, or when revops-watchdog/Scribe need the funnel block.
argument-hint: "[month YYYY-MM]"
model: sonnet
allowed-tools: Bash(python3 *) Read ToolSearch
---

Paths for this session (absolute; use them for every script call and state read/write):

- PLUGIN_ROOT = ${CLAUDE_PLUGIN_ROOT}
- FLEET_ROOT  = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --root`
- Status      = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --status`

First command: `cd "$FLEET_ROOT"`. Relative `state/...` paths in the roster prompt resolve
from there; `scripts/...` paths resolve under PLUGIN_ROOT (identical in workspace mode).

Generate the current month-to-date GTM funnel metrics from ~~crm (HubSpot). Follow the
instructions in `${CLAUDE_PLUGIN_ROOT}/roster/funnel-stats/prompt.md`. Deterministic,
spec-driven query runner — pinned to a smaller model on purpose (first model pin in the
fleet); validate output parity against a larger run before dropping further.

Arguments: $ARGUMENTS
