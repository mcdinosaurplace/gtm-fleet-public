# The composer — bespoke client fleets

`scripts/compose_fleet.py` turns this kit plus a `fleet.yaml` selection into a standalone,
installable plugin for one client: the profile rendered, everything the client did not buy
pruned away, the plugin renamed, state seeded, and (optionally) the zero-leak gate run over
the result.

The composed tree is a complete kit — it carries its own `scripts/`, `state/`,
`profiles/<profile>/` and `fleet.yaml`, so it can reseed and run itself with no reference
back to this repository.

## CLI

```bash
python3 scripts/compose_fleet.py --fleet fleet.yaml \
    [--out build/<plugin-name>] [--seed empty|demo] [--terms <private terms.yaml>]
```

| Flag | Default | Meaning |
|---|---|---|
| `--fleet` | (required) | The selection file. This repo's own `fleet.yaml` is a valid input (the full fleet). |
| `--out` | `build/<plugin-name>/` | Output directory. **Deleted and rebuilt** if it exists (same as `profile_render.py`). |
| `--seed` | `empty` | `empty` = migrated DB + header-only journals. `demo` = the full Orrery demo state. |
| `--terms` | (none) | Private terms yaml. When given, runs `scripts/sanitize/verify.py` over the composed tree; when absent the gate is skipped and the manifest records `gate.ran = false`. |
| `--terms2` | (none) | Second-tier terms yaml (vocabulary gate). Runs a second verify pass over the composed tree; the manifest adds `gate.terms2` / `gate.findings2`, and a finding in either pass exits 2. |

Exit `0` on success, `2` on a validation error, an unresolved profile token, a failed seed,
or a gate finding. Every failure names what to fix.

## fleet.yaml

```yaml
name: acme                      # slug → plugin acme-fleet
profile: acme                   # must exist under profiles/
agents: [chief-of-staff, revops-watchdog, scribe]
capabilities: [funnel-stats]
skills: [draft-content, utm-builder]
connectors: {crm: project, chat: account}
runner: {permission_mode: acceptEdits, max_turns: 80, max_budget_usd: 5}
schedule: {enabled_entries: [revops-watchdog-daily]}
```

| Key | Required | Default | Rules |
|---|---|---|---|
| `name` | yes | — | Slug (`[a-z0-9-]`). Plugin name is `name` when it already ends in `-fleet`, else `name + "-fleet"`. |
| `profile` | yes | — | A directory under `profiles/`. |
| `agents` | yes | — | Non-empty subset of chief-of-staff, revops-watchdog, performance-marketer, scribe, content-researcher, content-producer, brand-designer. |
| `capabilities` | no | `[]` | Subset of `funnel-stats`, `luma-events`. |
| `skills` | no | `all` | The string `all`, or a list of one-shot skill names. |
| `connectors` | no | `{}` | Recorded in the composed `fleet.yaml` and the manifest; **not** enforced. |
| `runner` | no | `{}` | Same — recorded, not enforced. |
| `schedule` | no | `{enabled_entries: []}` | Entry names from `schedule.yaml`; the entry's agent must be selected. |

Unknown agents, capabilities, skills or schedule entries exit 2 naming the offender and the
valid options.

## Overlay precedence

Highest first: `profiles/<p>/overrides/<relpath>` (whole file) → `profiles/<p>/identity-notes/<agent>.md`
(appended to the constitution after a `---` rule) → `profile.yaml` / `connectors.yaml` tokens → base kit.

An identity note is appended only when the profile does **not** ship a whole-file override for
that same constitution — an override replaces the file outright, so appending to it would
contradict the operator's intent. Identity notes are optional; no profile ships them today.

## What gets pruned

Everything below is removed from the output tree, never from this repository.

- `roster/<x>/` and `skills/<x>/` for every unselected agent **and** capability.
- `state/identity/<agent>.md` for unselected agents, along with any companion identity
  files matching `<agent>-*` (e.g. `scribe-pm.md`, `scribe-pm-cadence.yaml`).
- `agents/funnel-stats.md` when `funnel-stats` is not selected.
- `scripts/luma_mcp.py` and `mcpServers.luma` in `.claude-plugin/plugin.json` when
  `luma-events` is not selected (`mcpServers` is dropped entirely if it becomes empty).
- One-shot skills not in the `skills` list. **Always kept regardless of the list:** the six
  auto-loaded knowledge skills (`brand-voice`, `content-creation`, `campaign-planning`,
  `competitive-analysis`, `performance-analytics`, `gtm-ops`), the operator tools
  (`triage`, `help-me`), and the routers of the selected agents and capabilities.
  `skills: all` prunes nothing.
- `schedule.yaml` entries whose agent was pruned; the survivors get `enabled: true` for
  exactly the names in `schedule.enabled_entries` and `enabled: false` otherwise.
- `docs/mcp-preflight.md` — rows of the "Per-agent required connectors" table whose first
  cell names a pruned agent or capability (matched case-insensitively, so the `Scribe` rows
  are found).
- `CLAUDE.md` — Agent Registry rows for pruned agents/capabilities, and (when `skills` is a
  list) the backticked names of pruned one-shot skills in the paragraph after the table.
- `docs/agent-fleet-diagram.mermaid` — every line naming a pruned agent, then any `subgraph`
  whose body became empty (with its `end`). Two consequences worth knowing: a relationship
  line naming several agents is dropped whole as soon as one of them is pruned, and an edge
  pointing at a subgraph that was removed becomes a dangling reference (mermaid renders it as
  a bare node). Redraw the diagram by hand (or with `diagram-generator`, when the fleet kept
  it) before putting it in front of a client.

Then, when the plugin name differs from `gtm-fleet`, the exact string `gtm-fleet` is replaced
throughout every text file of the output: `/gtm-fleet:` command prefixes,
`mcp__plugin_gtm-fleet_luma__` tool prefixes, `plugin.json`, `marketplace.json`, the README,
the Makefile and the docs. Binary files (null-byte sniff, plus `.db`) are skipped.

### Caveats

- **YAML comments are lost.** `schedule.yaml` is round-tripped through PyYAML, so its header
  comment block and the quoting of cron expressions do not survive. The data does: entries
  keep their order, the `defaults` block stays first, and `schedule_render.py` reads the
  result unchanged.
- Prose the composer does not rewrite can go stale for a subset fleet: the `plugin.json`
  description and the CLAUDE.md "Seventeen one-shot marketing skills" count still describe the
  full kit, and `skills/help-me/SKILL.md` still lists commands for pruned agents. Edit them by
  hand (or via a profile override) before handing the fleet over.

## Seeding

`--seed empty` (default) creates `state/working/fleet.db` by applying the **composed kit's own**
migrations, then writes a header-only journal for each selected agent plus the shared journals:
`handoffs.md` and `ops-incidents.md` always, `chief-of-staff-meditations.md` only when
chief-of-staff is selected, `scribe_project_management.md` only when scribe is selected.

`--seed demo` runs the composed kit's `scripts/seed_demo_state.py --as-of yesterday --force`.
It is **allowed only when all seven agents are selected** — the demo story is a cross-agent
loop, and a partial roster would produce journals and handoffs referring to agents the client
does not have. A subset fleet with `--seed demo` exits 2 with
`demo seed requires the full roster; use --seed empty`.

## The manifest

`<out>/compose-manifest.json`, plus a readable summary on stdout. It holds no absolute paths:

`plugin_name` · `profile` · `composed_at` (UTC ISO) · `source_commit` (this repo's `HEAD`, or
`unknown` without git) · `seed` · `agents` · `capabilities` · `skills` ·
`identity_notes_applied` · `pruned` (`roster` / `skills` / `identity` / `other` — relative
paths) · `schedule` (`entries` kept, `enabled`) · `connectors` · `runner` ·
`gate` (`ran`, `terms` basename or null, `findings`) · `files` (total in the composed tree).

The summary ends by reminding you to run `claude plugin validate <out>`. The composer never
shells out to the `claude` CLI itself.

## Acceptance

The composer is done when two different `fleet.yaml` files produce two plugins that both validate
and both pass the gate with their own terms:

```bash
python3 scripts/compose_fleet.py --fleet fleet.yaml --seed demo --out build/gtm-fleet-full \
    --terms ../private/terms-source.yaml
claude plugin validate build/gtm-fleet-full

python3 scripts/compose_fleet.py --fleet clients/acme/fleet.yaml --seed empty --out build/acme-fleet \
    --terms ../private/terms-acme.yaml
claude plugin validate build/acme-fleet
```

The gate is also runnable on its own afterwards:
`python3 scripts/sanitize/verify.py --root build/acme-fleet --terms <terms.yaml>`.
