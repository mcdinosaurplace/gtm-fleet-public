# Tick Schedule Reference

## Purpose

The fleet's cadence lives in one committed file, **`schedule.yaml`**, and nothing in
the kit installs a schedule. Every entry is `enabled: false`; you render the entry for
your scheduler and install it yourself. This replaces the original arrangement where
schedules lived in two unsynchronized external stores on two people's machines and
could only be recovered from a document.

```bash
python3 scripts/schedule_render.py --list                         # what exists
python3 scripts/schedule_render.py --format crontab               # commented lines for `crontab -e`
python3 scripts/schedule_render.py --format launchd --only revops-watchdog-daily \
    > ~/Library/LaunchAgents/com.gtm-fleet.revops-watchdog-daily.plist      # macOS; then launchctl load
python3 scripts/schedule_render.py --format routine --only chief-of-staff-am   # prompt for a cloud routine
```

Every scheduled entry runs the same thing a human would run by hand:

```bash
python3 scripts/tick.py --agent <agent> --mode <mode>
```

`tick.py` performs Librarian steps 0–5 in Python (sync, identity, last journal entry,
new handoffs, anchor, migrations), starts a headless session —
`claude -p "/gtm-fleet:<agent> <mode> --harness"` — verifies proof-of-work (a new
journal header), runs chief-of-staff's cross-agent audit, and commits through
`scripts/fleet_git.py`. With `--runner stub` the job step is a no-op (tests, machines
without the CLI).

## Cadence (America/Los_Angeles)

| Entry | Cron | Agent · mode | Notes |
|---|---|---|---|
| `chief-of-staff-am` | `0 7 * * 1-5` | chief-of-staff · am | Morning brief. Runs first so overnight handoffs are curated before the humans start. |
| `revops-watchdog-daily` | `0 8 * * 1-5` | revops-watchdog · daily | Funnel snapshot, workflow health, scoring drift, enrichment coverage. Fridays: `weekly`. |
| `performance-marketer-daily` | `30 8 * * 1-5` | performance-marketer · daily | Spend + ranking watch. **Wednesday** adds the GTM scorecard pass (before Scribe's WBR); Thursday adds the position pass. |
| `scribe-standup` | `0 9 * * 1` | scribe · standup | Monday async stand-up post. |
| `scribe-pulse` | `0 9 * * 2-5` | scribe · pulse | Tue–Fri Linear health pulse. |
| `scribe-standup-sweep` | `15 0 * * 2` | scribe · standup | Tuesday 00:15 capture of Monday's thread. |
| `scribe-wbr` | `0 9 * * 3` | scribe · weekly | Wednesday WBR draft; section owners pinged with the Thursday 07:00 deadline. |
| `content-researcher-weekly` | `30 9 * * 1` | content-researcher · weekly | Monday voice-of-market sweep → topic backlog. |
| `content-producer-daily` | `0 10 * * 1-5` | content-producer · daily | Weekday queue check (creation pod is Phase 2). |
| `chief-of-staff-pm` | `0 16 * * 1-5` | chief-of-staff · pm | Evening wrap: carry-forward, cross-agent audit, meditation. |

```
07:00  chief-of-staff AM ──► 08:00 revops-watchdog ──► 08:30 performance-marketer ──► 09:00 Scribe (Mon stand-up / Tue–Fri pulse / Wed WBR)
       ──► 09:30 content-researcher (Mon) ──► 10:00 content-producer ──► 16:00 chief-of-staff PM          Tue 00:15 Scribe sweep
```

Ticks are staggered so the single-writer SQLite database never sees two agents at
once. If a Tick runs past its window, SQLite's default journal mode serializes the
writes; enable WAL only if contention actually appears.

## Environment a scheduled Tick needs

- `FLEET_ROOT` (blank = the repository), `FLEET_CLAUDE_BIN` if `claude` is not on the
  scheduler's PATH, and for multi-machine fleets `FLEET_REMOTE` + `FLEET_BRANCH`.
- Connector credentials for the agent: `.env` in `FLEET_ROOT` (Google/Luma scripts) and
  a project `.mcp.json` built from `mcp/connectors.example.json` so tool names are stable
  (`mcp__slack__…`) and match `.claude/settings.json`'s allowlist. Account-level
  connectors bound in the desktop app do not survive unattended runs — see
  `docs/connector-reauth-runbook.md`.
- Budget and safety: `FLEET_MAX_TURNS` (80), `FLEET_MAX_BUDGET_USD` (5),
  `FLEET_TICK_TIMEOUT_S` (1800), `FLEET_PERMISSION_MODE` (acceptEdits). A session that
  exits without journaling is recorded as a HIGH `ops-incidents.md` entry, never as success.

## Recovering the schedule

`schedule.yaml` is the source of truth. If a scheduler is lost, re-render and reinstall
from it; nothing else needs to be remembered.
