# Profiles

A profile is everything that makes the fleet *someone's* fleet: company name and
domains, the humans decisions route to, competitors and customers named in
examples, and the ids of the live systems the connectors talk to.

```
profiles/
  _template/            this directory — copy it to start a new profile
    profile.yaml        company + people + market tokens
    connectors.yaml     live-system ids (~~crm, ~~chat, ~~knowledge base, ...)
    README.md
  orrery/               the default demo company (fictional)
    profile.yaml
    connectors.yaml
    overrides/          whole files that replace base files at render time
      context/personas/aaron-platform-engineer.md   (example — overrides use the BASE file's exact relpath; the persona slug is stable even when the persona's role changes)
```

## How it is used

1. **Base kit** — prompts, context, docs and skills carry `{{TOKENS}}`. Only the
   UPPER_CASE tokens (and `company_slug`) are profile tokens; lowercase
   `{{placeholders}}` are template variables the skills fill at runtime.
2. **Render** — `python3 scripts/profile_render.py --profile <name>` writes a fully
   substituted copy to `build/<name>/`, copies `overrides/` over it, and fails if
   any profile token is left unresolved. Point `claude --plugin-dir build/<name>`
   at it, or ship it to a client.
3. **Seed** — `python3 scripts/seed_demo_state.py --profile <name>` regenerates
   `state/` (identity notes, synthetic journals, the SQLite DB) using the same
   names, so the demo data and the prompts agree.

Tokens live in flat `tokens:` maps on purpose: the renderer treats the two files
as one dictionary, and a client-facing profile stays greppable.
