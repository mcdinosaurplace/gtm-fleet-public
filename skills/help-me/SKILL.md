---
name: help-me
description: Check the fleet setup (plugin loaded, FLEET_ROOT, database, connectors) and list every /gtm-fleet command with a plain-language description. Use when someone asks what this plugin can do or whether it is set up correctly.
disable-model-invocation: true
allowed-tools: Bash(python3 *) Bash(git *) Read ToolSearch
---

Paths for this session (absolute; use them for every script call and state read/write):

- PLUGIN_ROOT = ${CLAUDE_PLUGIN_ROOT}
- FLEET_ROOT  = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --root`
- Status      = !`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py" --status`

First command: `cd "$FLEET_ROOT"`. Relative `state/...` paths in the roster prompt resolve
from there; `scripts/...` paths resolve under PLUGIN_ROOT (identical in workspace mode).

Check the user's setup and explain what this fleet can do. Keep the language friendly and non-technical.

## Step 1: Check setup

Report pass/fail for each, with a one-line fix when something fails:

1. **Plugin** — this skill ran, so the `gtm-fleet` plugin is loaded. Say so.
2. **Paths** — run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fleet_paths.py --check` and relay its lines.
3. **Database** — if the check reports the DB missing, the fix is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/seed_demo_state.py --force`.
4. **Git** — `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fleet_git.py status`. Local mode (no FLEET_REMOTE) is fine for one machine.
5. **Connectors** — use ToolSearch to probe for `~~crm` (HubSpot), `~~chat` (Slack), `~~issue tracker` (Linear), `~~knowledge base` (Notion) tools. Report each as bound / not bound. Not bound is not a failure — say which agents need which (see `${CLAUDE_PLUGIN_ROOT}/CONNECTORS.md`).
6. **Demo mode** — if Status shows `DEMO_MODE=1`, say the fleet is running on fixtures.

## Step 2: Explain available commands

Present these in plain language with one example each:

- `/gtm-fleet:chief-of-staff am|pm` — the chief-of-staff brief and evening synthesis
- `/gtm-fleet:revops-watchdog daily|weekly|<audit>` — ~~crm funnel and data-health watchdog
- `/gtm-fleet:performance-marketer daily|weekly|<skill>` — paid media + SEO optimizer (recommend → approve → act)
- `/gtm-fleet:scribe weekly|standup|pulse` — weekly business review and project-management pulse
- `/gtm-fleet:content-researcher weekly|<skill>` — voice-of-market research → topic backlog
- `/gtm-fleet:content-producer daily|<skill>` — briefs and content packaging (creation pod is Phase 2)
- `/gtm-fleet:brand-designer dither-pack <image>` — brand-compliant channel graphics
- `/gtm-fleet:funnel-stats`, `/gtm-fleet:luma-events`, `/gtm-fleet:triage` — capabilities and operator tools
- Marketing skills (no fleet state needed): `/gtm-fleet:draft-content`, `campaign-plan`, `brand-review`,
  `competitive-brief`, `performance-report`, `email-sequence`, `email-qa`, `linear-task-capture`,
  `diagram-generator`, `utm-builder`, `sop-gen`, `lifecycle-map`, `sprint-plan`, `workflow-spec`,
  `lead-score-doc`, `attribution-brief`, `campaign-forecaster`
- Scheduling is opt-in: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/schedule_render.py --list`

Arguments: $ARGUMENTS
