---
name: brand-designer
description: Run brand-designer — design & visual systems: brand dither/halftone treatment → channel graphics packages (dither-pack), visual-identity custodian. Use only when explicitly asked to run brand-designer or dither-pack.
argument-hint: "[queue|dither-pack <source> [instructions]|<skill>|help]"
disable-model-invocation: true
allowed-tools: Bash(python3 *) Bash(git *) Bash(sqlite3 *) Bash(ls *) Bash(cat *) Bash(head *) Bash(tail *) Bash(wc *) Bash(date *) Read Edit Write Glob Grep ToolSearch
---

Paths for this session (absolute; use them for every script call and state read/write):

- PLUGIN_ROOT = ${CLAUDE_PLUGIN_ROOT}
- FLEET_ROOT  = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --root`
- Status      = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --status`

First command: `cd "$FLEET_ROOT"`. Relative `state/...` paths in the roster prompt resolve
from there; `scripts/...` paths resolve under PLUGIN_ROOT (identical in workspace mode).

Run brand-designer. Follow the instructions in `${CLAUDE_PLUGIN_ROOT}/roster/brand-designer/prompt.md`.

Mode is determined by the argument:
- No argument or `queue` → queue check (process handoffs addressed to brand-designer, report state)
- `dither-pack <source> [instructions]` → apply the brand dither treatment and emit the channel graphics package (`roster/brand-designer/skills/dither-pack.md`, engine `scripts/brand_designer_dither.py`)
- Another skill name → skills land M2–M5; if the skill file does not exist yet, say so and stop


Flags:
- `help` — print the modes above and stop; do not start a Tick.
- `--harness` — invoked by `scripts/tick.py`: skip Librarian steps 0 (sync), 5 (migrations)
  and the Commit step; the harness did/does them. Everything else runs exactly as written.

Connector resolution: when Status shows `DEMO_MODE=1` the connector tools are fixture-backed
(registered from `mcp/demo.json`) — call them normally: reads return synthetic Orrery data, and
writes land in `state/demo-outbox/` and never reach a live surface. Skip the MCP-preflight retry
loop; one probe is enough. If a needed tool is not bound, use
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/demo/connector.py <connector> <tool>` instead. Otherwise bind
connectors as the roster prompt's MCP Preflight step describes (`CONNECTORS.md` lists the categories).

Finish line: a Tick counts only once the timestamped journal entry is appended to the
agent's `state/journal/` file, its `##` header stamped with the CURRENT UTC time — run
`date -u +%Y-%m-%dT%H:%M:%SZ` for it; never copy or infer the time from prior entries
(a header older than the tick start fails the check). The harness verifies exactly that
and records a session that ends without it as a failed Tick. How to write so the
harness accepts it on the first try — this is the ONLY write path that works in a
harness run, because the fleet's files live inside the plugin directory and skill runs
refuse the Edit and Write tools and shell redirection (`>>`) there as "sensitive":
get the timestamp in its own `date -u` call, then write with ONE Bash call that is a
single `python3 - <<'EOF' … EOF` heredoc (or one `python3 -c "…"`) whose body opens the
file with `open(path, 'a')` to append (journal, `handoffs.md`, `ops-incidents.md`) or
`open(path, 'w')` to create (a brief, a pending submission, an outbox page), writes the
text, and closes it. Nothing else in that call: no `cd`, no `&&`, no `;`, no `$( )`. A
denied Edit/Write/redirect burns the turn — do not retry them, go straight to python3. Journals, handoffs, and
incident entries cite repo-relative paths only — never absolute machine paths (the
zero-leak gate bans them and a red gate blocks every push). Deliverables are writes (files, DB rows, outbox
messages via the connector tools), never only chat output; in DEMO_MODE the brief/page
"send" IS the corresponding write tool call, which lands in `state/demo-outbox/`.

Arguments: $ARGUMENTS
