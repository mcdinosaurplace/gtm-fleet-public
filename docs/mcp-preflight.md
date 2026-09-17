# MCP Preflight

Shared procedure for ensuring required MCP connectors are bound before an
agent's Tick begins MCP-dependent work.

## Why

MCP servers (Slack, Linear, Notion, HubSpot, etc.) bind asynchronously when
a Claude Code session starts. Observed pattern: connectors sometimes finish
binding 1–4 minutes after the session opens. If an agent's Tick fires
immediately on a scheduled run and a connector hasn't bound yet, the agent
falls into degraded paths or skips work that would have succeeded a few
minutes later.

Two late-bind incidents on consecutive mornings both followed this pattern:
- Slack MCP late-bound during chief-of-staff's AM Tick
- Linear MCP late-bound during the next morning's AM Tick

This preflight runs a bounded retry loop so the Tick proceeds when binding
is just slow, and only fails out when a connector is genuinely down.

## Procedure

Each agent that uses MCP tools runs this preflight as a Librarian Protocol
step, before any step that calls an MCP tool. The agent specifies its own
list of required connectors when invoking the procedure.

### Step 1 — Probe (t = 0)

For each required connector, call `ToolSearch` with a keyword query. Run all
queries in parallel.

Recommended queries:
- Linear → `+linear list_issues`
- Slack → `+slack send_message`
- HubSpot → `+hubspot crm_objects`
- Notion → `+notion search`
- Google Calendar → `+calendar list_events`
- Gmail → `+gmail search_threads`
- Grain → `+grain list_meetings`

Each query must return at least one matching tool schema. If every required
connector returns a match, MCP is healthy → proceed to the next Librarian
Protocol step.

### Step 2 — First retry (t ≈ 60s)

If any required connector did not match in Step 1, wait 60 seconds, then
re-run `ToolSearch` for the missing connectors only.

```bash
sleep 60
```

If all missing connectors now match → proceed.

### Step 3 — Final retry (t ≈ 4 min)

If any connector is still missing after Step 2, wait an additional ~3
minutes (≈4 minutes total since Step 1), then re-run `ToolSearch` for the
remaining missing connectors one more time.

```bash
sleep 180
```

If all now match → proceed. Note the late binding in the journal entry.

### Step 4 — Fail state

If any required connector is still missing after Step 3:

1. Append a structured incident to `state/journal/ops-incidents.md` with
   severity `LOW` (degrade path) or `MED` (essential connector missing):

   ```
   ## YYYY-MM-DDTHH:MM:SSZ | MCP_BIND_FAILURE | {agent} | {severity}

   Required connectors: {list}
   Bound: {list}
   Missing after 3 attempts (~5 min): {list}

   Action: {degraded | aborted}
   ```

2. Append a handoff to `state/journal/handoffs.md` addressed to chief-of-staff.
   If chief-of-staff itself is the failing agent, address it to Scott.

3. Decide:
   - **Degrade and continue** if the missing connector is non-essential
     for this Tick's primary deliverable. Skip dependent steps and note
     the gap in the final output.
   - **Abort the Tick** if the missing connector is essential to the
     deliverable itself (e.g. Slack for a Slack-delivered brief, Notion for a
     Notion write). Do not fabricate data. Do not commit partial state. The
     incident is the output for this run.
   - **Escalate loudly and degrade** for a *content-source* connector that is
     chronically unbound in the run environment (e.g. chief-of-staff's Calendar/Gmail):
     file the `MCP_BIND_FAILURE` every run it is missing, flag it prominently in
     the output, and continue with the sources that bound.

**Do not rationalize a chronic outage as expected.** A connector that fails to
bind run after run is a standing defect to be fixed at its source — usually
reauthorization in the run environment (see
[`docs/connector-reauth-runbook.md`](connector-reauth-runbook.md)) — not a
normal condition to narrate around. Cautionary precedent: chief-of-staff's Calendar
connector lost auth in a scheduled run (`ops-incidents.md`); the outage was relabeled
"expected — security rollover" and copied forward daily for months while the
real reauth went undone. If you find yourself writing the same "expected"
explanation for the same connector on consecutive runs, stop — that is the
anti-pattern. Re-file the bind failure and point at the runbook instead.

## Operating notes

- Total worst-case delay: ~5 minutes (60s + 180s wait + probe overhead).
  Acceptable because Ticks run before Scott's working day.
- Do not poll on intervals shorter than 60s. MCP binding is async; frequent
  polls do not bind faster — they just waste cache and tokens.
- Use a single `sleep` per retry. Do not chain shorter sleeps
  to fake a long wait — the harness blocks that pattern.
- Record per-connector binding time in the Tick's journal entry under a
  `### MCP Preflight` subsection. Over time we can detect whether the
  late-bind window is shrinking, growing, or correlating with specific
  connectors.

## Per-agent required connectors

Each agent declares its own list. Listed essentiality determines whether
a missing connector aborts vs. degrades the Tick.

| Agent | Connector (category · default) | Essentiality | Used for |
|---|---|---|---|
| revops-watchdog | `~~crm` · HubSpot | essential | funnel queries, workflow audits |
| revops-watchdog | `~~knowledge base` · Notion | essential | funnel-stats post |
| revops-watchdog | `~~issue tracker` · Linear | optional | ticket cross-references |
| revops-watchdog | `~~chat` · Slack | optional | escalations only |
| chief-of-staff | `~~chat` · Slack | essential | brief delivery, handoffs, decision queue |
| chief-of-staff | `~~issue tracker` · Linear | essential | cross-agent audit, issue snapshot |
| chief-of-staff | `~~calendar` · Google Calendar | source | meeting pull (AM); script fallback `scripts/gcal_pull.py` |
| chief-of-staff | `~~email` · Gmail | source | inbox signals (AM); script fallback `scripts/gmail_pull.py` |
| chief-of-staff | `~~knowledge base` · Notion | optional | meditation / brief writes |
| performance-marketer | `~~ads` · Google Ads (`scripts/google_ads_pull.py`) | essential (scripts) | spend watch, DMO creative data, execute-approved |
| performance-marketer | `~~web analytics` · GSC + GA4 (`scripts/gsc_pull.py`, `ga4_pull.py`) | essential (scripts) | ranking watch, traffic scorecard, landing-page review |
| performance-marketer | `~~crm` · HubSpot | optional | campaign analytics, attribution review |
| performance-marketer | `~~issue tracker` · Linear | optional | copy-review delegation issues |
| performance-marketer | `~~SEO` · Ahrefs / Similarweb | optional | seo-audit, competitor scan enrichment |
| Scribe | `~~knowledge base` · Notion | essential | WBR write, topic-backlog sync |
| Scribe | `~~chat` · Slack | essential | channel notify, stand-up post + sweep |
| Scribe | `~~crm` · HubSpot | essential | funnel fallback (when the revops-watchdog snapshot is absent) |
| Scribe | `~~issue tracker` · Linear | essential (pulse) / optional (WBR) | PM pulse, project updates |
| content-researcher | `~~meeting notes` · Grain | essential | sales-call mining (degrade-and-log if unbound) |
| content-researcher | WebSearch / WebFetch | essential | social listening, competitor content |
| content-researcher | `~~crm` · HubSpot | optional | deal context for ICP-weighting call signals |
| content-producer | `~~issue tracker` · Linear | optional | clickable refs in review packets |
| content-producer | `~~knowledge base` · Notion | optional | use-case library reads |
| brand-designer | `~~design` · Figma | optional (M3) | design-board bridge — log absence at M1 |
| brand-designer | `~~issue tracker` · Linear | optional | clickable refs |
| funnel-stats | `~~crm` · HubSpot | essential | the metrics block |
| luma-events | `~~events` · Luma (plugin MCP `mcp__plugin_gtm-fleet_luma__*`) | essential | all operations |

In `DEMO_MODE=1` (Phase 2) every row above is served by fixtures and the preflight is
skipped; see `CONNECTORS.md` → *Three ways a connector gets bound*.

**Essentiality `source`** (chief-of-staff Calendar/Gmail): a content-source connector,
not on the deliverable's delivery path. If unbound, do NOT abort and do NOT
narrate it as "expected" — file `MCP_BIND_FAILURE` every run and degrade with a
loud flag (see Step 4 → "Escalate loudly and degrade", and
`docs/connector-reauth-runbook.md`).

When an agent's required-connector list changes, update both this table and
the agent's prompt.
