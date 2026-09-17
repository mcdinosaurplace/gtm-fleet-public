---
name: luma-events
description: The fleet's front door to ~~events (Luma) via the in-repo MCP server — list/get events, registrant counts (counts only, guest PII never stored), and the gated create/update write path. Use when any agent or the user needs Luma data.
argument-hint: "list [upcoming|past|all] | get <evt-id|url> | registrants <evt-id> | health | create … | update <evt-id> …"
allowed-tools: Bash(python3 *) Read ToolSearch mcp__plugin_gtm-fleet_luma__*
---

Paths for this session (absolute; use them for every script call and state read/write):

- PLUGIN_ROOT = ${CLAUDE_PLUGIN_ROOT}
- FLEET_ROOT  = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --root`
- Status      = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --status`

First command: `cd "$FLEET_ROOT"`. Relative `state/...` paths in the roster prompt resolve
from there; `scripts/...` paths resolve under PLUGIN_ROOT (identical in workspace mode).

Run the Luma Events capability. Follow the instructions in `${CLAUDE_PLUGIN_ROOT}/roster/luma-events/prompt.md`.
The MCP server ships with this plugin (`mcp__plugin_gtm-fleet_luma__*`, `scripts/luma_mcp.py`); it reads
`LUMA_API_KEY` from the environment or FLEET_ROOT/.env. Healthcheck: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/luma_mcp.py --smoke`.

Operation is selected by the argument: `list [upcoming|past|all]`, `get <evt-id|luma-url>`,
`registrants <evt-id>`, `health`, or a write — `create …`, `update <evt-id> …`, `cover [content_type]`.

Writes require `LUMA_ENABLE_WRITES=1` and always hit an interactive approval prompt — that is
intended. Still attempt the operation and surface the gate if it is disabled.

Arguments: $ARGUMENTS
