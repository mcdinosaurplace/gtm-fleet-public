# state-bot Commit Convention

## Purpose

Agent-generated commits are written by `state-bot`, a synthetic git identity used
exclusively for autonomous Tick activity. This keeps agent commits visually separate
from code commits and out of the code-review flow.

## Identity and transport

`state-bot` is never configured globally. `scripts/fleet_git.py` applies it per commit:

```bash
python3 scripts/fleet_git.py commit --agent revops-watchdog --action "Daily Tick"
python3 scripts/fleet_git.py push          # no-op unless FLEET_REMOTE is set
```

which runs `git commit --author="state-bot <state-bot@fleet.local>"` with the message
`[state-bot] {AgentName} | {Action} | {ISO 8601 UTC}`.

Two modes, chosen by environment:

| Mode | Env | Behaviour | Use |
|---|---|---|---|
| **Local-commit** (default) | `FLEET_REMOTE` unset | Commits land on the checked-out branch; `sync` only confirms the branch; `push` is a no-op. Commits are the audit trail. | One machine, demos, client pilots |
| **Multi-writer** | `FLEET_REMOTE=origin`, `FLEET_BRANCH=main` | `sync` fetches + fast-forwards `FLEET_BRANCH` before every Tick (hard stop on failure); `push` retries 4× (2/4/8/16 s). An unpushed commit is treated as a Tick that never ran. | Two operators, a cloud routine, any second clone |

Never substitute a session-assigned or "more complete"-looking branch: work committed
there is invisible to the rest of the fleet and to the agent's own next Tick.

## Commit message format

```
[state-bot] {AgentName} | {Action} | {ISO 8601 timestamp (UTC)}
```

```
[state-bot] chief-of-staff | AM Tick complete | 2026-01-05T14:20:00Z
[state-bot] revops-watchdog | Daily Tick | 2026-01-05T13:44:00Z
[state-bot] performance-marketer | Daily Tick (Wed) + Scorecard Pass | 2026-01-07T15:30:00Z
[state-bot] Scribe | Weekly Tick | WBR posted | 2026-01-07T17:05:00Z
```

## Rules

1. **One commit per Tick.** Every Tick ends with exactly one commit.
2. **Atomic commits.** Everything a single Tick produced — journal entries, DB writes,
   pending drafts, incident appends — is in that one commit. Never commit partial state.
3. **No code-review flow.** `state-bot` commits are the operational record, not code.
4. **state-bot commits only touch `state/` and `wbr/`.** Anything else is a bug.
5. **DB size.** `state/working/fleet.db` is committed as a binary. Above 5 MB, copy it to
   `state/working/archive/` (create the directory), rebuild from migrations
   (`scripts/seed_demo_state.py --force` for demo fleets; `scripts/tick.py` applies
   migrations to an empty file for live ones), and note the archive in the commit message.
6. **Never force-push, never amend** a state-bot commit. Corrections are new commits.
7. **Text ids.** `anomalies`, `handoffs`, `spend_alerts` mint ids via `scripts/ids.py` so
   two writers never collide; integer-PK tables re-read `MAX(id)` after `sync`, never cache it.
