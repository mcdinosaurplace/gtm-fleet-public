# Claude Desktop / Cowork Setup & Fleet Plugin Installation — Team SOP

**Version:** 2.0 (gtm-fleet) · **Owner:** Marketing / GTM Ops · **Applies to:** anyone on
the team who will use the one-shot marketing skills or run a fleet agent interactively.

## What this covers

1. Installing Claude (desktop app) and Claude Code
2. Loading the `gtm-fleet` plugin
3. Authorizing connectors (`~~crm` HubSpot, `~~knowledge base` Notion, `~~chat` Slack, `~~issue tracker` Linear)
4. Verifying everything works

**Time to complete:** 10–15 minutes.

## Section 1 — Install Claude

1. Download the desktop app from [claude.ai/download](https://claude.ai/download) and sign in
   with your company account.
2. For the fleet's headless runs (schedules, `scripts/tick.py`) you also need the CLI:
   `curl -fsSL https://claude.ai/install.sh | bash`, then `claude --version` and `claude /login`.

## Section 2 — Load the plugin

The plugin **is** this repository — there is no separate `.plugin` file to download.

```bash
git clone <your fleet repo> ~/claude_code/gtm-agent-fleet
cd ~/claude_code/gtm-agent-fleet && make setup && make seed
claude plugin marketplace add .          # registers the bundled marketplace manifest
```

Then in any Claude Code session: `/plugin install gtm-fleet@gtm-fleet-local`, or start
Claude Code with `--plugin-dir ~/claude_code/gtm-agent-fleet`. Opening the repository
itself as a workspace also loads everything.

### What's in the plugin

| Group | Commands |
|---|---|
| Fleet agents | `/gtm-fleet:chief-of-staff` `revops-watchdog` `performance-marketer` `scribe` `content-researcher` `content-producer` `brand-designer` |
| Capabilities & operator tools | `/gtm-fleet:funnel-stats` `luma-events` `triage` `help-me` |
| Content & campaigns | `/gtm-fleet:draft-content` `campaign-plan` `brand-review` `competitive-brief` `performance-report` `email-sequence` `email-qa` `diagram-generator` |
| GTM ops | `/gtm-fleet:utm-builder` `sop-gen` `lifecycle-map` `sprint-plan` `workflow-spec` `lead-score-doc` `attribution-brief` `campaign-forecaster` `linear-task-capture` |

Knowledge skills (`brand-voice`, `content-creation`, `campaign-planning`,
`competitive-analysis`, `performance-analytics`, `gtm-ops`) load automatically when a
task needs them; they are not invoked by name.

## Section 3 — Authorize connectors

Desktop app: **Settings → Connectors** → connect HubSpot, Notion, Slack, Linear (and Grain,
Google Calendar/Gmail if you run chief-of-staff or content-researcher). Each opens the vendor's OAuth
screen; approve read access. Account connectors appear to the agents with opaque ids and
are discovered at runtime.

Headless runs cannot use account connectors. For those, copy `mcp/connectors.example.json`
to `.mcp.json` in the fleet root and authenticate each server once — tool names become
stable (`mcp__slack__…`) and match `.claude/settings.json`.

## Section 4 — Verify

Run `/gtm-fleet:help-me`. It reports: plugin loaded, `FLEET_ROOT`, database present,
git mode, which connectors are bound, and whether `DEMO_MODE` is on. Then try
`/gtm-fleet:draft-content` (no connectors needed) and `/gtm-fleet:funnel-stats`
(needs `~~crm`).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/gtm-fleet:*` commands missing | the plugin is not loaded — `claude plugin marketplace add .` + `/plugin install`, or `--plugin-dir` |
| "database missing" in help-me | `make seed` |
| connector shows *not bound* | Settings → Connectors (interactive) or `.mcp.json` (headless); `docs/mcp-preflight.md` |
| `claude -p` says "Not logged in" | `claude /login` once in a terminal |
| permissions ignored warning | open the repo interactively once and accept the workspace trust dialog |
