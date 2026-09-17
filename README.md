# GTM Agent Fleet (`gtm-fleet`)

A portable, company-agnostic **marketing-operations agent fleet for Claude Code**: seven
stateful agents that share one memory model, two capability layers, seventeen one-shot
marketing skills, and the tooling to re-skin the whole thing for a new company in an
afternoon. It runs as a plugin inside any project, as a workspace on its own, or headless
on a schedule you choose to install.

Built from a fleet that ran a real B2B SaaS marketing org for five months, then
sanitized, tokenized, and reseeded with a fictional company (**Orrery**, incident
management for engineering teams) so it can be demoed with no credentials at all.

## What's in the fleet

| Agent | Role | Loop |
|---|---|---|
| **chief-of-staff** | Chief of staff | AM brief → decision queue → PM synthesis; routes every cross-agent handoff; audits the others' journals |
| **revops-watchdog** | `~~crm` watchdog (read-only) | Daily funnel snapshot, workflow health, scoring drift, enrichment coverage → anomalies → handoffs; 13 on-demand audits |
| **performance-marketer** | Paid media + SEO/GEO | Spend & ranking watch → weekly optimization dossier → GTM traffic scorecard; reversible ad changes behind a gate |
| **Scribe** | Reporting & PM | Weekly business review from fleet state, Monday stand-up, Linear pulse, Notion topic sync |
| **content-researcher** | Voice-of-market research | Sales calls + communities + competitor content → evidence-backed topic backlog |
| **content-producer** | Content creation | Approved topics → build-ready briefs + smoke-tested use-case articles (the drafting loop stays planned) |
| **brand-designer** | Design systems | Brand dither/halftone channel packages; visual-identity custodian |

Plus `funnel-stats` (a model-pinned subagent), `luma-events` (an in-repo MCP server for
`~~events`), `triage` and `help-me` for the operator, and the marketing skills:
`draft-content`, `campaign-plan`, `brand-review`, `competitive-brief`, `performance-report`,
`email-sequence`, `email-qa`, `linear-task-capture`, `diagram-generator`, `utm-builder`,
`sop-gen`, `lifecycle-map`, `sprint-plan`, `workflow-spec`, `lead-score-doc`,
`attribution-brief`, `campaign-forecaster`.

The design: every stateful agent runs the same **Librarian Protocol** — load its
constitution, read its last journal entry, read new handoffs, verify the date, apply
migrations, do the job, write handoffs, journal, commit. Memory is three-tiered
(`state/identity/` immutable constitutions, `state/journal/` append-only, `state/working/fleet.db`
queried by code). Agents never message each other directly; git is the bus. Humans gate
every outbound write.

## Five-minute start

```bash
git clone <this repo> gtm-agent-fleet && cd gtm-agent-fleet
make setup                 # python venv + requirements
make seed                  # synthetic demo state as of today (Orrery profile)
make claude                # Claude Code with the plugin loaded
```

Then `/gtm-fleet:help-me`, `/gtm-fleet:revops-watchdog daily`, `/gtm-fleet:chief-of-staff am`,
`/gtm-fleet:scribe weekly --dry-run`. Prerequisites: Python 3.10+, git, the Claude Code
CLI signed in (`claude /login`) — details in `docs/onboarding.md`.

## Using it from another project

```bash
FLEET_ROOT=/path/to/gtm-agent-fleet claude --plugin-dir /path/to/gtm-agent-fleet
# or register the bundled marketplace: claude plugin marketplace add /path/to/gtm-agent-fleet
```

Code (`skills/`, `roster/`, `scripts/`, migrations) lives in the plugin; mutable state
(`state/`, `wbr/`) lives wherever `FLEET_ROOT` points. `scripts/fleet_paths.py --check`
shows the resolution.

## Headless runs and schedules

```bash
python3 scripts/tick.py --agent revops-watchdog --mode daily --dry-run   # shows the exact claude -p command
python3 scripts/tick.py --agent revops-watchdog --mode daily             # runs the Librarian Protocol + a headless session
python3 scripts/schedule_render.py --list                      # the cadence in schedule.yaml (nothing installed)
python3 scripts/schedule_render.py --format launchd --only revops-watchdog-daily
```

`tick.py` does steps 0–5 in Python, starts `claude -p "/gtm-fleet:<agent> <mode> --harness"`,
checks that the session actually journaled, runs chief-of-staff's cross-agent audit, and commits
via `scripts/fleet_git.py` (local commits by default; set `FLEET_REMOTE` + `FLEET_BRANCH`
for multi-machine fleets). `schedule.yaml` declares the cadence; you install it.

## Re-skinning for a company

```
profiles/_template/   → copy to profiles/<client>/ and fill in profile.yaml + connectors.yaml
scripts/profile_render.py --profile <client>   → build/<client>/ (fails on any unresolved token)
scripts/seed_demo_state.py --profile <client>  → state/ that agrees with the profile
```

Prompts and docs carry `{{TOKENS}}`; connectors are referenced by category (`~~crm`,
`~~chat`, `~~issue tracker` — see `CONNECTORS.md`) with HubSpot / Slack / Linear / Notion
as the tested defaults. Whole-file `overrides/` carry the prose tokens cannot (personas,
brand voice, keyword lists). A bespoke client fleet is composed from a `fleet.yaml`
selection with `scripts/compose_fleet.py` — profile rendered, unselected agents/skills
pruned, plugin renamed, state seeded, zero-leak gate run, manifest written
(`docs/composer.md`).

## Repository map

```
.claude-plugin/   plugin + marketplace manifests        skills/      /gtm-fleet:* entry points
agents/           plugin subagents (funnel-stats)        roster/      agent prompts, procedure skills, references
scripts/          runner, git transport, seeder, renderer, sanitizer, data pulls, pm/, paid/, luma_mcp.py
state/            identity · journal · pending · working/fleet.db + migrations    profiles/   _template, orrery
context/          tokenized company / brand / persona context                     docs/       knowledge base (indexed in CLAUDE.md)
sops/  templates/  buyer-journey/  assets/visual-identity/  tests/  mcp/  schedule.yaml  fleet.yaml
```

## Status

Phases 1–2 shipped: sanitized, tokenized, plugin-packaged, runner + schedule manifest,
synthetic state, fixture-backed `DEMO_MODE` (`make demo-run`, `docs/demo-runbook.md`),
content-producer's skills rebuilt, chief-of-staff absorbed the briefing agent, 380+ tests, zero-leak gate.
Phase 3 shipped: the client-fleet composer (`scripts/compose_fleet.py`, `docs/composer.md`).

## License

Apache-2.0 (`LICENSE`). Several one-shot skills derive from Anthropic's open-source
knowledge-work marketing plugin — see `NOTICE`.
