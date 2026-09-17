# scripts/sanitize — re-skinning a fleet without leaking its origin

Two tools, one rule: **the map and the terms list are private; the repo ships only examples.**

| Tool | What it does |
|---|---|
| `apply.py --map <map.yaml> --root <dir>` | ordered, idempotent find/replace with renames, per-rule review lists, code-vs-prose variants, YAML-safe quoting. Re-runnable: a second run reports `0 changes`. |
| `verify.py --root <dir> --terms <terms.yaml>` | the zero-leak gate: text, filenames, archive members, every SQLite cell + raw bytes, YAML parse, git history. Exit 0 only at zero findings. `--skip-history` scans trees only — it exists for second-tier vocabulary terms that legitimately live in the canonical repo's history; a red full-history scan against such terms is expected there forever and must never be "fixed" by rewriting history. Fresh-history public cuts and composed kits are always scanned in full. |

## Workflow (what produced this kit)

1. `rsync` the source with an exclude list (secrets, scratch, history).
2. Write `replace_map.<source>.yaml` **outside the repo** (copy `replace_map.example.yaml`):
   renames first, then literals longest-first, identifiers, people (tokens in prose,
   concrete names under `concrete_paths` such as tests), competitors/customers, brand last.
3. `apply.py` → read the review list → add rules → re-run until idempotent.
4. Rebuild anything binary instead of editing it (SQLite via migrations + `seed_demo_state.py`, zips by re-zipping sources).
5. `verify.py --terms terms.<source>.yaml` → fix → repeat until `OK: 0 findings`.
6. Only then `git init`: history is scanned too, so nothing leaks via an early commit.

## Gotchas the tooling already handles

- Some company, product, and first names are also ordinary English words (a verb, a
  direction, a math term) — such rules carry `review: true` and verify terms can be
  `case_sensitive: true` so the gate does not flag the English use.
- `{{TOKENS}}` at the start of a YAML scalar or inside `[flow, lists]` must be quoted.
- Catch-all id regexes must exclude their own zero-filled placeholders or the pass never converges.
- `grep` on macOS may be `ugrep`, which honours `.gitignore` by default — use `--no-ignore-files`.
