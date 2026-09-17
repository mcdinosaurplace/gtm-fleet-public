# fixtures/google — the DEMO_MODE Google pull set

performance-marketer's Tick shells four Google pull commands before it does any work
(`roster/performance-marketer/prompt.md` → *Run the Job*). Live, they hit the GA4,
Search Console, and Google Ads APIs and fail without credentials. With `DEMO_MODE=1`
each script serves the CSV below through the **same command**, so the agent's procedure
is unchanged and a demo needs no Google account.

The branch lives in the pull scripts themselves and runs before any credential import:
it reads the mapped file, renders its date tokens (`scripts/demo/dates.py`), writes to
`--output` (or stdout for `-`), prints `[demo] served fixture <relpath>`, and exits 0.
A missing fixture exits non-zero naming the path it looked for.

## Invocation → fixture

| Command (from the prompt) | Fixture | Feeds |
|---|---|---|
| `google_ads_pull.py --mode spend-watch --range 14d` | `ads/spend-watch-14d.csv` | `google_to_sqlite.py ads-spend` → `paid_creative` → `spend-watch` |
| `gsc_pull.py --range 7d --dimensions query,page` | `gsc/query-page-7d.csv` | `google_to_sqlite.py gsc-rankings` → `keyword_rankings` → `ranking-watch` |
| `google_ads_pull.py --mode dmo --range 14d --by-day` | `ads/dmo-14d-by-day.csv` | `creative-optimizer` (the DMO CSV schema, read directly) |
| `ga4_pull.py --range 7d --by-day --metrics sessions,engagedSessions,conversions --dimensions pagePath,sessionSourceMedium` | `ga4/date-pagepath-sessionsourcemedium-7d.csv` | `landing-page-review` (read directly) |

Mapping is by script plus the arguments that change the **shape** of the output —
`--mode`, `--by-day`, `--dimensions`, `--format`. Window arguments (`--range`,
`--row-limit`, `--limit`), `--search-type`, and `--metrics` do **not** select a
fixture: every variation gets the canonical file, and the `[demo]` line says which
arguments were ignored. Ask for a shape that has no file — `--format json`, an
un-fixtured dimension set, `--mode dmo` without `--by-day` — and the script exits 2
naming the path it wanted, which is also how you add one.

## The planted story

Coherent with the Orrery narrative `scripts/seed_demo_state.py` already seeded, and
sized to trip the documented thresholds rather than to sit near them.

| Signal | Where | The numbers |
|---|---|---|
| **Spend spike** | `ads/spend-watch-14d.csv`, `Nonbrand — Incident Mgmt`, today | $9,860.07 against the fixture's own trailing-7 daily mean of $4,020.59 (spend-watch baselines on the 14-day series it just loaded into `paid_creative`) → **+145%** (spend-watch flags >25% as MED). Conversions barely move, so CPL goes $152 → $318, **+109%** (>20% is also MED). Brand and Competitor stay inside ±0.5%. |
| **Ranking drop** | `gsc/query-page-7d.csv`, `sidereal on call` | Position 27.4 today against a seeded prior of 14 → Δ **−13**. That is both a >10 drop (MED) and an exit from the top 20 (HIGH). The legacy-brand-bleed term, per the tracked-keywords file — the retired Sidereal name giving up the last of its SERP. |
| **Ranking drop's page** | `ga4/…-7d.csv`, `/blog/sidereal-on-call` under `google / organic` | Sessions slide 118 → 64 across the week as the retired name gives up its SERP — the page evidence behind the keyword drop; direct traffic stays flat. |
| **Landing-page sag** | `ga4/…-7d.csv`, `/product/incident-response` under `google / cpc` | Sessions 268 → 611 across the week (**+128%**, the paid spike landing) while conversions fall 14 → 7 (**−50%**) and engagement rate slides 62.9% → 48.7%. One dossier bullet: traffic bought, conversion lost. |

`/product/incident-response` is the Final URL of the spiking campaign's ads in the DMO
fixture, so the three signals read as one incident rather than three coincidences.
Everything else in all four files is deliberately boring.

## Content rules

- **Orrery-world only.** Every value belongs to the fictional company in
  `profiles/orrery/`; domains end `.example`. No real company is named anywhere.
- **Already rendered, not tokenized.** These are demo payloads, not kit files: no
  profile tokens (`{{COMPANY}}`, `{{company_slug}}`) appear, so `make render` has
  nothing to resolve here.
- **Dates are offset tokens.** `{{T-13d}}` … `{{T+0d}}`, substituted at read time so a
  fixture written months ago still ends today. Use the `T±Nd` form only — the braced
  `TODAY` / `NOW` / `MONDAY` forms render correctly but collide with
  `scripts/profile_render.py`'s uppercase-token scan and break `make render`
  (`fixtures/README.md`).
- **Keywords are joinable.** The 15 rows are exactly the 15 literal lines among the
  first 20 of `roster/performance-marketer/references/tracked-keywords.txt` — the window
  the seeder reads (`keywords[:20]`) and the same file the ETL filters on — so all 15
  survive `--keywords-file` and land with a real `prior_position`. The five tokenized
  brand lines are skipped by design: the ETL matches the file literally, so
  `{{company_slug}} …` never joins in DEMO_MODE. Every position sits within one place of
  its last seeded reading except the planted drop, so nothing else crosses a threshold.
  Campaign names match the ones the seeder writes to `paid_creative`.
- **Columns are the consumers' columns.** They match what `scripts/google_to_sqlite.py`
  parses and what the live scripts emit, down to number formatting.

Coverage lives in `tests/demo/test_google_fixtures.py`.
