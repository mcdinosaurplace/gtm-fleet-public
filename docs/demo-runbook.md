# Demo runbook — the hero loop, live, with no credentials

**What you show:** the RevOps watchdog loop running end to end on synthetic data —
revops-watchdog finds a funnel anomaly, chief-of-staff curates it into the morning brief with a decision,
Scribe drafts the weekly business review — with every write landing in a local outbox
instead of Slack/Notion, and every run leaving an auditable journal entry and a
`state-bot` git commit.

**Time:** ~2 minutes of setup, then ~3–6 minutes per tick headless (or drive it
interactively and narrate). **Requires:** the Claude Code CLI signed in and this workspace trusted — once, interactively:
`~/.local/bin/claude` from this directory (full path in case `~/.local/bin` is not on your
PATH), sign in if prompted, accept the trust dialog, exit. No connector credentials, no `.env`.

---

## 0. Reset (before every demo)

```bash
make demo-reset
```

This reseeds `state/` as of **yesterday** (so today's ticks are genuinely "the next
ones"), clears `state/demo-outbox/`, and regenerates the fixture MCP config. The seeded
story: SAL→SQL conversion has been below its 35% threshold for three straight days
(revops-watchdog has been counting), one CRM workflow is failing every enrollment at step 1
(HIGH), a performance-marketer scorecard is waiting on a greenlight, and content-producer's journal is quiet —
so every agent has something true to say.

Sanity check:

```bash
python3 scripts/fleet_paths.py --check
python3 scripts/handoffs.py list
```

## 1. The three ticks

Headless (what a scheduler would run):

```bash
make demo-run
```

or one at a time, narrating between:

```bash
DEMO_MODE=1 python3 scripts/tick.py --agent revops-watchdog --mode daily
DEMO_MODE=1 python3 scripts/tick.py --agent chief-of-staff --mode am
DEMO_MODE=1 python3 scripts/tick.py --agent scribe --mode weekly
```

What each one does — and what to say while it runs:

| Tick | What happens | The line that lands |
|---|---|---|
| **revops-watchdog · daily** | Pulls the fixture funnel (fed from the seeded DB, so the numbers agree with history), sees the dip continue a fourth day, writes `funnel_snapshots` + a MED anomaly + a handoff to chief-of-staff, journals, commits. | "Read-only watchdog. It never acts — it counts, journals, and hands off. Day 4 of the same watch item is a *count*, not a re-ask." |
| **chief-of-staff · am** | Reads the new handoffs, runs the cross-agent audit (it will notice anything stale), assembles the brief — meetings, inbox signals, the funnel watch, one decision — and "sends" it: the Slack-shaped DM lands in `state/demo-outbox/slack.md`. | "One place the human looks. The decision travels with its context, and yesterday's reply thread shows the operator already ruled *keep watching*." |
| **Scribe · weekly** | Freezes the scorecard from fleet state, drafts the WBR from revops-watchdog + performance-marketer numbers (never re-deriving them from the CRM), pings section owners, writes the Notion-shaped page to `state/demo-outbox/notion/`. | "The weekly review writes itself from state the specialists already verified — and every number on it traces to a row." |

Interactive variant (same fixtures, you drive):

```bash
make demo          # opens Claude Code with the plugin + fixture servers loaded
# then: /gtm-fleet:revops-watchdog daily   → /gtm-fleet:chief-of-staff am   → /gtm-fleet:scribe weekly --dry-run
```

## 2. The reveal (after the ticks)

```bash
git log --oneline --author=state-bot        # three commits, one per tick
python3 scripts/handoffs.py list            # the anomaly moving through its lifecycle
ls state/demo-outbox/ && cat state/demo-outbox/slack.md
tail -40 state/journal/revops-watchdog.md             # the journal entry the next tick resumes from
```

Points worth making over the output:

- **Auditability** — journal + git log + DB row for every claim; `state-bot` commits are
  the operational record, separate from code.
- **Safety tiers** — nothing touched a live surface; performance-marketer's ad changes ship in shadow
  mode; every outbound write in production has a human gate.
- **Portability** — `profiles/` re-skins the whole fleet for a client; `schedule.yaml`
  declares cadence without installing anything; the same `tick.py` line goes into
  cron/launchd/a cloud routine when it's time.

## 3. Second act — the paid loop (optional)

Run on the same seeded day as the hero ticks — no reset in between:

```bash
make demo-run-paid
```

or one at a time, narrating:

```bash
DEMO_MODE=1 python3 scripts/tick.py --agent performance-marketer --mode daily
DEMO_MODE=1 python3 scripts/tick.py --agent performance-marketer --mode weekly
```

The Google pull commands the prompt shells (`google_ads_pull.py`, `gsc_pull.py`,
`ga4_pull.py`) detect `DEMO_MODE=1` and serve deterministic CSVs from
`fixtures/google/` through the same ETL — no credentials, no Google client imports
(`fixtures/google/README.md` documents the planted story). Three signals that read
as one incident: the `Nonbrand — Incident Mgmt` campaign's spend spikes +145%
against its trailing 7-day baseline with CPL more than doubling, the tracked keyword
`sidereal on call` drops 13 positions (14 → 27) out of the top 20, and that
campaign's landing page shows sessions up / conversions down.

| Tick | What happens | The line that lands |
|---|---|---|
| **performance-marketer · daily** | Serves the fixture spend + GSC CSVs, loads them through `google_to_sqlite.py`, writes the spend alert and the ranking flag, hands off to chief-of-staff. | "Same procedure as production — the fixtures enter through the same pull commands, so nothing in the agent's procedure knows it's a demo." |
| **performance-marketer · weekly** | Adds the DMO creative pass, the optimization dossier (the three signals converge on one campaign), and the GTM traffic scorecard rows Scribe's WBR reads. | "Recommend → approve → act: the dossier proposes reversible changes, and `PERFORMANCE_MARKETER_EXECUTE` stays off — execution is shadow-only by design." |

Reveal: `python3 scripts/handoffs.py list`, the dossier in `state/pending/`, and
`sqlite3 state/working/fleet.db 'SELECT * FROM spend_alerts ORDER BY detected_at DESC LIMIT 3;'`.

## 4. Third act — the content engine (optional)

```bash
make demo-run-content
```

or one at a time:

```bash
DEMO_MODE=1 python3 scripts/tick.py --agent content-researcher --mode weekly
DEMO_MODE=1 python3 scripts/tick.py --agent scribe --mode notion-topic-sync
DEMO_MODE=1 python3 scripts/tick.py --agent content-producer --mode daily
DEMO_MODE=1 python3 scripts/tick.py --agent brand-designer --mode queue
```

| Tick | What happens | The line that lands |
|---|---|---|
| **content-researcher · weekly** | Mines the fixture sales calls (~~meeting notes, Grain) into the voice bank and scores topic candidates. The live-web sweeps are skipped, never simulated (`social-listening.md` §DEMO_MODE). | "Research that refuses to make things up, even in a demo — fabricated quotes would poison the evidence chain." |
| **Scribe · notion-topic-sync** | Mirrors the topic backlog to the Notion-shaped outbox and harvests rulings — the one standing outbound-write exception. | "The only write that doesn't wait for a human, and it's a mirror." |
| **content-producer · daily** | Turns an approved topic from the queue into a build-ready brief, exercising the full DB write path. | "Approved topic in, evidence-cited brief out — the drafting loop stays gated behind milestones." |
| **brand-designer · queue** | Picks up the seeded dither-pack request, runs the halftone treatment on `fixtures/brand/orrery-hero-source.png`, packages the channel assets, files a Tier-2 review packet. | "Even the art ships as a reviewable packet, not a surprise." |

Reveal: `state/pending/` (the brief and the review packet), `localwork/brand-designer/`
(the channel pack — gitignored by design), and `python3 scripts/handoffs.py list`
(the dither request moving to resolved).

## 5. Failure recovery, mid-demo

| Symptom | Fix |
|---|---|
| A tick reports `MCP_BIND_FAILURE` or a missing tool | `state/working/demo-mcp.resolved.json` missing or stale — run `make demo-reset`; confirm `DEMO_MODE=1` is set. |
| chief-of-staff says "no new handoffs" | The seed is from today, not yesterday (clock edge). `make demo-reset` (it always seeds `--as-of yesterday`). |
| `claude` errors "Not logged in" | `~/.local/bin/claude /login`, then rerun the tick. |
| `claude: command not found` | Use the full path `~/.local/bin/claude`, or add `export PATH="$HOME/.local/bin:$PATH"` to your shell profile. The headless runner finds it automatically either way. |
| Permissions warning about untrusted workspace | Open `claude` in the repo once, accept the trust dialog. |
| A session runs long | Ceilings: `FLEET_MAX_TURNS` (80), `FLEET_TICK_TIMEOUT_S` (1800). A session that exits without journaling is recorded as a HIGH incident, never as success — show `state/journal/ops-incidents.md` and call it a feature. |
| You want a clean slate mid-conversation | `make demo-reset` — everything synthetic regenerates in seconds; the git history keeps the aborted run as part of the story if you want it. |

## 6. Cost and ceilings

Headless ticks run under `--max-turns 80` and `FLEET_MAX_BUDGET_USD` (default 5) per
tick; on a subscription login the JSON result reports turns and $0 API cost. The three
hero ticks together typically finish well inside ten minutes; the optional acts add
two and four ticks respectively, and the full nine-tick day stays around half an hour.
