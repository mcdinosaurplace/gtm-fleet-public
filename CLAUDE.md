# GTM Agent Fleet — workspace instructions

A portable GTM / marketing-operations agent fleet for Claude Code. The repository is
simultaneously the **plugin** (`gtm-fleet`: `skills/`, `agents/`, `hooks/`,
`.claude-plugin/`) and the **workspace** that holds its state (`state/`, `wbr/`). Read
`README.md` for the tour and `docs/onboarding.md` to get running.

## Agent Registry

| Agent | Status | Invoke | What it does |
|---|---|---|---|
| chief-of-staff | Live | `/gtm-fleet:chief-of-staff am\|pm` | Chief-of-staff: AM brief (calendar, inbox per `roster/chief-of-staff/references/gmail-classification.md`, handoffs, decision queue) and PM synthesis; Notion durable copy per `references/notion-brief-template.md` (absorbed the retired weekly-concierge); routes cross-agent handoffs; audits the other journals. |
| revops-watchdog | Live | `/gtm-fleet:revops-watchdog daily\|weekly\|<audit>` | Read-only `~~crm` watchdog: daily funnel snapshot, workflow health, scoring drift, enrichment coverage → anomalies → handoffs. 13 audit skills on demand. |
| performance-marketer | Live (execution shadow-only) | `/gtm-fleet:performance-marketer daily\|weekly\|<skill>` | Paid media + SEO/GEO: spend watch, ranking watch, Wednesday GTM scorecard, Thursday optimization dossier; reversible ad changes gated by `PERFORMANCE_MARKETER_EXECUTE`. |
| scribe | Live | `/gtm-fleet:scribe weekly\|standup\|pulse` | Wednesday WBR draft from revops-watchdog/performance-marketer state, Monday stand-up, Tue–Fri Linear pulse, Notion topic-backlog sync. |
| content-researcher | Live | `/gtm-fleet:content-researcher weekly\|<skill>` | Voice-of-market research: sales calls, communities, competitor content → evidence-backed topic backlog. |
| content-producer | Live (M4 partial) | `/gtm-fleet:content-producer daily\|<skill>` | Content creation & distribution. `brief-builder` and `use-case-builder` are built (rebuilt Phase 2); `creation-pod`, `publish-package`, `derivative-spinner` remain planned — the router stops cleanly on those. |
| brand-designer | Nascent | `/gtm-fleet:brand-designer dither-pack <image>` | Visual identity custodian; brand dither/halftone channel packages (1 of 7 skills). |
| funnel-stats | Capability | `/gtm-fleet:funnel-stats` | MTD funnel block from `~~crm`; also a plugin subagent pinned to a smaller model. |
| luma-events | Capability | `/gtm-fleet:luma-events <op>` | Front door to `~~events` via the in-repo Luma MCP server; gated writes. |
| triage / help-me | Operator tools | `/gtm-fleet:triage`, `/gtm-fleet:help-me` | Decision-queue sweep; setup check + command list. |

Seventeen one-shot marketing skills (`draft-content`, `campaign-plan`, `brand-review`,
`competitive-brief`, `performance-report`, `email-sequence`, `email-qa`,
`linear-task-capture`, `diagram-generator`, `utm-builder`, `sop-gen`, `lifecycle-map`,
`sprint-plan`, `workflow-spec`, `lead-score-doc`, `attribution-brief`,
`campaign-forecaster`, plus the auto-loaded `brand-voice`, `content-creation`,
`campaign-planning`, `competitive-analysis`, `performance-analytics`, `gtm-ops`
knowledge skills) need no fleet state.

Agent prompts live in `roster/<agent>/prompt.md` (procedure skills in
`roster/<agent>/skills/`); every agent has a router skill at `skills/<agent>/SKILL.md`.
Headless runs: `python3 scripts/tick.py --agent <a> --mode <m>`; schedules are declared
(not installed) in `schedule.yaml`.

## Folder Structure

- `skills/` — plugin entry points (`/gtm-fleet:<name>`): agent routers + marketing skills
- `agents/` — plugin subagents (`funnel-stats`) — Claude Code's reserved directory
- `roster/` — the agents' prompts, procedure skills, references (read by path)
- `scripts/` — Python: `fleet_paths.py` (roots), `fleet_git.py` (transport), `tick.py` (runner),
  `seed_demo_state.py`, `profile_render.py`, `compose_fleet.py` (client fleets),
  `schedule_render.py`, `sanitize/`, data pulls, `pm/`, `paid/`, `luma_mcp.py`
- `state/` — FLEET_ROOT: `identity/` (constitutions), `journal/` (append-only), `pending/`,
  `working/` (`fleet.db`, `migrations/`, `schema.sql`, `queries/`)
- `profiles/` — `_template/` + `orrery/` (the fictional demo company); `build/` is the rendered output
- `context/` — tokenized company/brand/persona context; `context/visual-identity.yaml` for anything visual
- `docs/` — knowledge base (index below) · `sops/` — human procedures · `templates/` · `buyer-journey/`
- `fixtures/` + `scripts/demo/` + `mcp/demo.json` — DEMO_MODE: fixture MCP servers and the outbox (`state/demo-outbox/`); runbook `docs/demo-runbook.md`
- `tests/` — pytest (`make test`)
- `mcp/` — `connectors.example.json` (stable-named MCP servers) · `CONNECTORS.md` — the `~~category` convention

## Git Workflow

- Ticks sync with `python3 scripts/fleet_git.py sync` and commit with
  `fleet_git.py commit --agent <a> --action "<action>"` as `state-bot`; `push` is a no-op
  unless `FLEET_REMOTE` is set. Rules: `docs/state-commit-convention.md`.
- Human changes: small, descriptive commits; never amend or force-push state-bot commits.

## Language

- Python for every script (`scripts/`), SQL for migrations, Markdown for prompts and docs,
  YAML for profiles and schedules.

## Documentation (`docs/`)

Fetch the relevant doc for the task at hand — don't load everything upfront.

| Path | What it is | When to use |
|---|---|---|
| `docs/agent-content-trust-policy.md` | **Binding, fleet-wide.** Four trust tiers for text the fleet did not write; prompt-injection and exfiltration invariants. | Before ingesting, storing, or acting on any external text; before adding a data source or outbound write. |
| `docs/conventions.md` | Operational rules: naming, execution order, routers, git, record ids, decision queue, human-feedback weighting. | Running agents; any agent operation. |
| `docs/linear-reference-formatting.md` | Every Linear id / project name in agent output is a clickable link; surface-specific syntax. | Any time an agent writes a Linear reference anywhere. |
| `docs/notion-markdown-syntax.md` | Notion enhanced-markdown reference. | Before creating or updating a Notion page. |
| `docs/mcp-preflight.md` | Connector binding procedure + per-agent required connectors. | Start of every MCP-dependent Tick; adding a connector. |
| `docs/connector-reauth-runbook.md` | Restoring Google (Calendar/Gmail) connectors in scheduled runs. | `MCP_BIND_FAILURE` on Calendar/Gmail; "offline" briefs. |
| `docs/tick-schedule.md` | Cadence reference for `schedule.yaml`, the runner, and what a scheduled Tick needs. | Scheduling or recovering a schedule. |
| `docs/state-commit-convention.md` | state-bot identity, local-commit vs multi-writer modes, DB archive rule. | Anything touching commits of `state/`. |
| `docs/triage-protocol.md` | Weekly decision-queue sweep runbook (`/gtm-fleet:triage`). | Resolving agent-surfaced decisions. |
| `docs/gtm-scorecard-definitions.md` | Locked metric definitions (v1.5), projection methodology, restatement protocol. | Any scorecard / WBR funnel number work. |
| `docs/lead-lifecycle-model.md` | Canonical lifecycle model + glossary; frozen snapshot `docs/lifecycle-map-2026-06-30.md` (consumed by `revops-watchdog:lifecycle-audit`). | What MEL/MQL/SAL/SQL mean; stage criteria. |
| `docs/agent-fleet-diagram.mermaid` | Current fleet diagram (render with `/gtm-fleet:diagram-generator`). | Decks, onboarding. |
| `docs/onboarding.md` | Clone → plugin → seed → first Tick. | New machine or teammate. |
| `docs/composer.md` | The composer: CLI, `fleet.yaml` schema, overlay precedence, pruning semantics, manifest. | Composing a client fleet; acceptance checks. |
| `docs/demo-runbook.md` | The hero-loop demo: reset, three ticks, the reveal, failure recovery. | Before any interview/client demo. |
| `docs/brand-designer-scope.md` | brand-designer plan of record (M1 shipped, M2–M5 roadmap). | Design-agent work. |
| `docs/google-api-setup.md` | One-time GA4 / Search Console / Google Ads API setup. | Bootstrapping the Google pull scripts. |
| `docs/aeo-tracked-prompts.md` | The AEO prompt register (re-skin per profile). | performance-marketer GEO/AEO work. |

## Google Data Pulls

`scripts/google_auth.py` (auth), `ga4_pull.py`, `gsc_pull.py`, `google_ads_pull.py`,
`google_to_sqlite.py` (→ `paid_creative`, `keyword_rankings`). Outputs land in
`state/working/google/` (gitignored). Credentials in `FLEET_ROOT/.env` — template
`.env.example`; runbook `docs/google-api-setup.md`.

## Luma MCP (events)

`scripts/luma_mcp.py` ships with the plugin (`.claude-plugin/plugin.json` → `mcpServers.luma`)
as `mcp__plugin_gtm-fleet_luma__*`. Reads are always registered; writes only with
`LUMA_ENABLE_WRITES=1` and an interactive approval. Guest PII never reaches committed
state, `~~chat`, `~~knowledge base`, or journals (trust policy §4). Healthcheck:
`python3 scripts/luma_mcp.py --smoke`. Front door: `/gtm-fleet:luma-events`.

## Profiles, connectors, people

Every company-specific value is a profile token (`profiles/<name>/profile.yaml`,
`connectors.yaml`) rendered by `scripts/profile_render.py`; connector categories are
defined in `CONNECTORS.md`. Section owners, Notion/Slack/HubSpot ids, and the humans
who gate decisions are read from the profile and from
`state/identity/scribe-pm-cadence.yaml` — never hard-coded in prompts. The standing
Notion-write exception (Scribe's `notion-topic-sync` mirrors the topic backlog both ways)
is documented in `docs/conventions.md`; every other outbound write asks a human first.

## Coding Principles (Karpathy Skills)

> Behavioral guidelines to reduce common LLM mistakes. This file is the source of truth
> for every session that opens this repository (headless runs included).
> Source: [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).
> Scope: apply to all substantive work. For **code** (scripts, automation, agent
> tooling), verification means tests; for **content / agent output** (reports,
> Notion, Slack, briefs), verification means adversarial validation — see Principle 4.
> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

**Non-code work (content, reports, agent output): verify by adversarial validation.**
There are no unit tests for a WBR, a Notion page, or a Slack post, so default to
trying to *break* the output before shipping it — not just confirming it looks right:
- Render and inspect the real surface (the published Notion block, the Slack
  message, the Linear issue), not the draft.
- Re-derive every number from its source; assume a metric is wrong until traced.
- Red-team the claim: ask "what would make this false?" and go check that.
- For agent runs, dry-run first and treat the output as suspect until you have
  actively looked for the failure mode.

Bias toward disconfirmation: a check that can only pass is not a verification step.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

**Review checklist (`/code-review`, `/simplify`).** These passes enforce the
principles above. Flag, in order: (1) changes that don't trace to the request
(Surgical Changes); (2) speculative complexity (Simplicity First); (3) unstated
assumptions or unsurfaced tradeoffs (Think Before Coding); (4) claims or outputs
shipped without verification — tests for code, adversarial validation for
content / agent output (Goal-Driven Execution).
