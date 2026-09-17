# Onboarding — running the fleet on your machine

This kit is a Claude Code **plugin** (`gtm-fleet`) that is also a runnable workspace.
Ten minutes gets you from clone to a first Tick against synthetic demo data; connecting
real systems is a separate, optional step.

## 1. Prerequisites

- Claude Code CLI (`claude --version`) — desktop app alone is not enough for headless runs.
  Run `claude` once in this directory and accept the workspace trust dialog; run
  `claude /login` once if the CLI is not signed in.
- Python 3.10+ (`python3.12 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt -r scripts/pm/requirements.txt pytest`),
  or simply `make setup`.
- git. No remote is required (local-commit mode); see `docs/state-commit-convention.md`.

## 2. Load the plugin

Pick one:

```bash
# a) as a workspace — open the repo and everything loads from CLAUDE.md + .claude/settings.json
claude

# b) as a plugin into ANY other project (agents + skills only; state stays here via FLEET_ROOT)
FLEET_ROOT=/path/to/gtm-agent-fleet claude --plugin-dir /path/to/gtm-agent-fleet

# c) via the bundled marketplace manifest
claude plugin marketplace add /path/to/gtm-agent-fleet     # then /plugin install gtm-fleet@gtm-fleet-local
```

Then `/gtm-fleet:help-me` — it checks paths, the database, git mode, and which
connectors are bound, and lists every command.

## 3. Seed demo state

```bash
make seed            # = python3 scripts/seed_demo_state.py --profile orrery --force
python3 scripts/fleet_paths.py --check
python3 scripts/handoffs.py list
```

The seed rebuilds `state/working/fleet.db` from the migrations, writes synthetic journals
in the formats the prompts parse, and plants a story (a three-day SAL→SQL conversion dip,
one HIGH workflow flag, a stale content-producer journal) so every agent has something to say.
Re-run it with `--as-of $(date +%F)` before a demo so chief-of-staff's staleness audit reads the
right dates.

## 4. Run a Tick

Interactive: `/gtm-fleet:revops-watchdog daily`, then `/gtm-fleet:chief-of-staff am`, then
`/gtm-fleet:scribe weekly --dry-run`. Headless:

```bash
python3 scripts/tick.py --agent revops-watchdog --mode daily --dry-run     # prints the exact claude -p command
python3 scripts/tick.py --agent revops-watchdog --mode daily               # runs it (needs the CLI signed in)
```

Scheduling is opt-in: `python3 scripts/schedule_render.py --list` (see `docs/tick-schedule.md`).

## 5. Connect real systems (optional)

1. Copy `.env.example` → `.env` for the script-based connectors (Google Ads/GA4/GSC, Luma).
2. Copy `mcp/connectors.example.json` → `.mcp.json` for stable-named MCP servers
   (`mcp__slack__…`, `mcp__hubspot__…`) that match `.claude/settings.json`'s allowlist —
   or bind account connectors in the desktop app and let ToolSearch find them.
3. Create `profiles/<you>/` from `profiles/_template/`, fill in ids and people, and
   `python3 scripts/profile_render.py --profile <you>` → `build/<you>/` is your fleet.

`CONNECTORS.md` explains the `~~category` convention; `docs/mcp-preflight.md` lists what
each agent needs and what happens when it is missing.

## 6. Which entry point should I use?

| You want to… | Use |
|---|---|
| see what the fleet can do | `/gtm-fleet:help-me` |
| draft content, plan a campaign, review brand voice, build UTMs, write an SOP | the one-shot skills: `/gtm-fleet:draft-content`, `campaign-plan`, `brand-review`, `utm-builder`, `sop-gen`, … (no fleet state needed) |
| run the operations loop | `/gtm-fleet:revops-watchdog`, `chief-of-staff`, `performance-marketer`, `scribe`, `content-researcher`, `content-producer`, `brand-designer` |
| resolve what the agents surfaced | `/gtm-fleet:triage` |
| funnel numbers right now | `/gtm-fleet:funnel-stats` |

## Getting help

`docs/` is indexed in `CLAUDE.md`. Operational rules: `docs/conventions.md`.
