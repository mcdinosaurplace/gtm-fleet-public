---
name: content-researcher:content-inventory
description: >
  Refreshes content_inventory — {{COMPANY}}'s published-content source of truth — by
  running scripts/blog_inventory_crawl.py over {{COMPANY_DOMAIN}}/blog and enriching each
  post with search queries via a degradation ladder (GSC API → GSC CSV → `~~SEO` →
  none). topic-synthesizer reads this table to classify candidate topics as
  net-new / refresh / duplicate. Runs MONTHLY and on-demand — NOT in the weekly
  Tick (a crawl is too slow to couple into every run). Read-only on the live site;
  writes only content_inventory.
---

# Content Inventory

Maintains the inventory the content engine dedups against. Without it,
`topic-synthesizer` can't tell a genuinely new topic from one {{COMPANY}} already
published — so this skill is what makes the refresh-vs-net-new decision real.

## When This Runs

- **Cadence:** Monthly (first Tick of the month) **and** on-demand.
- **Standalone:** `/content-researcher content-inventory`
- **Not** part of the weekly Tick. The synthesizer reads the table read-only each
  week and logs `MED` if it is >30 days stale — that staleness flag is the prompt
  to run this skill.

When invoked standalone, load the identity file and read the last journal entry
for context, then run the workflow below (no full Librarian Protocol).

## Dependencies

- **`scripts/blog_inventory_crawl.py`** — the crawler (stdlib only). Run via
  subprocess.
- **GSC** — optional, for query enrichment. The API path
  (`scripts/gsc_pull.py`) is **not permissioned yet**; degrade down the ladder.
- **`~~SEO` MCP** (Ahrefs / Similarweb) — optional proxy (plugins installed, need auth).

## Inputs / Outputs

| | |
|---|---|
| **Reads** | `{{COMPANY_DOMAIN}}/blog` sitemap + pages (read-only); a GSC CSV export if provided |
| **Writes** | `content_inventory` (upsert; `source='crawl'`, query_source per ladder) |
| **Journals** | counts (new / updated / stale) + query-source coverage |

## Workflow

### 1. Confirm the blog domain

The crawler defaults to `https://{{COMPANY_DOMAIN}}` and walks `/blog` from the
sitemap. Confirm the live blog path before the first seed crawl — a site that
serves posts from a CMS subdomain rather than `/blog` will yield an empty crawl
rather than an error — and pass `--base-url` if it differs.

### 2. Resolve the query-enrichment source (ladder — best available wins)

1. **GSC API** — if `scripts/gsc_pull.py` is permissioned and returns page-level
   queries, write them to a CSV and pass it as `--gsc-csv`. *(Not live yet.)*
2. **GSC CSV** — GSC's "Performance on Search" export is an xlsx with separate
   Queries and Pages sheets (no per-page join). Convert it first:
   `python scripts/gsc_xlsx_to_pagequeries.py --xlsx <export.xlsx> --out state/working/google/<name>.csv`
   — this assigns each top query to the best slug-matching blog page (a topical
   heuristic, not true per-page GSC attribution). Then pass that CSV as
   `--gsc-csv`. **Works today.** Real per-page queries arrive with the GSC API (rung 1).
3. **`~~SEO` MCP** — if authed, pull per-URL organic keywords as a
   query proxy and stage them as a CSV in the same format.
4. **None** — run the crawl without enrichment; rows get `query_source='none'`
   and the synthesizer falls back to title/topic overlap. Note the gap.

### 3. Run the crawl

```bash
python scripts/blog_inventory_crawl.py --gsc-csv <path-if-available>
```

(Add `--dry-run` first on the seed run to eyeball extraction before writing.)
The script discovers blog URLs from the sitemap, extracts title/excerpt/headings/
dates (preferring Article JSON-LD), enriches with queries, and upserts
`content_inventory`. Re-runs are idempotent (`ON CONFLICT(url)`); a non-`none`
query source never gets overwritten by a later `none` run.

### 4. Staleness reconciliation

The crawl flags `source='crawl'` rows not seen this run as `status='stale'`
(likely unpublished or moved). Review the count; if a stale row is genuinely
removed, leave it `stale` (the synthesizer only dedups against `status='live'`).
Do not delete rows — content-producer-authored rows (`source='content-producer'`) and history stay.

### 5. Journal

Append to `state/journal/content-researcher.md` under a `### Content Inventory` block:

```
[content_inventory] → {live} live posts ({new} new, {updated} updated, {stale} flagged stale)
Query coverage: {N} with queries ({source}); {M} query_source='none'
Domain crawled: {base_url}
[note any ladder degradation, e.g. "GSC API unavailable — used CSV export from {date}"]
```

## Framer Seam

`blog_inventory_crawl.py` includes a `framer_adapter()` stub (`source='framer'`).
No Framer connector exists in the MCP registry today, so it is a no-op. When a
Framer MCP/API is connected, implement the adapter to pull the CMS collection
directly — the table and `source` enum already accommodate it, no migration needed.

## Boundary Rules

- **Read-only on the live site.** Crawl politely (the script rate-limits and sets
  a descriptive User-Agent); never POST or submit anything.
- **Writes only `content_inventory`.** No voice_bank, no topic_backlog, no
  external surfaces.
- **Shared table.** content-producer's `publish-package` also writes here (`source='content-producer'`) on
  publish. Never overwrite or delete content-producer-authored rows.
- **No fabrication.** If the sitemap is unreachable, log it and stop — never
  invent inventory rows.
