# roster/ — the agents' procedure library

Each directory is one agent. This tree is read **by path** from the router skills
(`skills/<agent>/SKILL.md` → `roster/<agent>/prompt.md`); it is deliberately *not* the
plugin's `agents/` directory, which Claude Code reserves for subagent definitions.

```
roster/<agent>/
  prompt.md            the agent: Mode → Runtime Configuration → Librarian Protocol → job → Skills table → Reference Files
  skills/<skill>.md    procedure skills the prompt invokes by path (front-matter: name: <agent>:<skill>, description)
  references/          lookup material the skills cite (catalogs, taxonomies, keyword lists)
  runtime-profiles.yaml (content-producer only) model/runtime intent per platform — policy, not configuration
```

## Conventions

- **No front-matter on `prompt.md`.** It starts with `# <Name> — <Role>`. Model pins and
  tool allowlists live on the router skill, not here.
- **Runtime Configuration** sits before the Librarian Protocol and lists only keys; values
  are profile tokens (`{{HUBSPOT_PIPELINE_ID}}`) resolved by `scripts/profile_render.py`.
  Connector categories (`~~crm`, `~~chat`, …) are defined in `CONNECTORS.md`.
- **Librarian Protocol** (every stateful agent): 0 sync (`scripts/fleet_git.py sync`) →
  1 identity (`state/identity/<agent>.md`) → 2 last journal entry → 3 new handoffs →
  4 anchor → 5 migrations → 6 MCP preflight → 7 job → 8 handoffs → 9 journal entry →
  10 commit (`fleet_git.py commit`). With `--harness`, `scripts/tick.py` performs 0, 5, 10.
- **Journal format** is parsed: `## YYYY-MM-DDTHH:MM:SSZ | <label>` headers, `###` sections.
  `scripts/tick.py::parse_last_tick_timestamp` reads the last header as the "since" marker.
- **A declared skill must exist as a file.** content-producer's `prompt.md` lists skills whose files
  are being rebuilt (Phase 2); the router says so and stops rather than improvising.
- **Stateless members** (`funnel-stats`, `luma-events`) have a `prompt.md` only — no
  identity, journal, or commit step.

| Agent | Skills on disk | Status |
|---|---|---|
| chief-of-staff | (monolith prompt) | live |
| revops-watchdog | 13 | live |
| performance-marketer | 14 (+ `references/`, `references/dmo/`) | live, execution shadow-only |
| scribe | 4 (+ `scribe-pm` identity) | live |
| content-researcher | 5 (`performance-learning` planned) | live |
| content-producer | 0 of 5 — `brief-builder`, `use-case-builder` rebuilt in Phase 2 | partial |
| brand-designer | 1 of 7 (`dither-pack`) | nascent |
| funnel-stats | — | capability (also a plugin subagent with a model pin) |
| luma-events | — | capability over the in-repo Luma MCP |
