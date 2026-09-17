---
name: performance-marketer:optimization-dossier
description: >
  Forms performance-marketer's weekly paid-media POSITION and packages it as a dossier. Runs
  the full paid analysis (objective, WoW, tiering, bid, budget,
  cross-channel), enumerates every proposed move, then sorts each move
  into 3a (auto on greenlight) / 3b (human-applied) / creative (copy-review)
  via the deterministic classifier scripts/paid/classify.py. Produces the
  dossier that chief-of-staff shares with the team and surfaces for greenlight.
  Gives the bid/budget half of the paid analysis an output home.
---

# Optimization Dossier

## When This Runs

- **Tick integration:** Weekly Tick (**Thursday**, so the dossier lands in
  Friday's chief-of-staff AM brief for greenlight). See `roster/performance-marketer/prompt.md`.
- **Event-driven:** Off-cycle on a HIGH (or clustered-MED) spend/ranking anomaly
  (decided deterministically by `scripts/paid/trigger.py`) — a scoped mini-dossier
  rather than waiting for Thursday; pass the trigger's reason as `trigger_reason`.
- **Standalone:** `/performance-marketer optimization-dossier`.

## Relationship to the other paid skills

| Skill | Role |
|-------|------|
| `performance-marketer:optimization-dossier` (this) | Forms the **position**. Runs the full paid analysis, classifies every move, emits the dossier. |
| `performance-marketer:creative-optimizer` | Generates the brand-compliant **copy variations** for moves in the `creative` bucket. Invoked by this skill; still standalone-invocable. |
| `performance-marketer:execute-approved` (Block F2) | Applies the greenlit `auto_3a` moves; packages `human_3b`; delegates `creative`. |

This skill runs the analysis itself (§2) and adds the position framing, the
deterministic bucket classification, and the dossier artifact.

## Inputs

- Google Ads + LinkedIn performance data (14-day) — pull per the Export
  Instructions in `roster/performance-marketer/references/dmo/google-ads-channel.md`
  and `dmo/linkedin-channel.md`.
- Objective mode (Efficiency / Pipeline / Awareness / Custom) — confirm before
  running if not stated; it decides which metric a delta is judged against.
- Prior context: open rows in `paid_change_proposals`, the `applied_changes`
  since the last dossier, open `spend_alerts`, and open `experiments`.

## Workflow

### 1. Load context

- Brand: `context/marketing-project-context.yaml`,
  `context/founder-pov-context.yaml`,
  `context/buyer_persona_context_profile.yaml`.
- Prior hypotheses: open rows in `experiments`, plus the prior dossier's
  `paid_change_proposals` and any `applied_changes` since — score open
  hypotheses against current data (CONFIRMED / DISPROVEN / INCONCLUSIVE).

### 2. Run the analysis

Work the pass in order, grounded in the channel references under
`roster/performance-marketer/references/dmo/`:

1. **Objective** — confirm the mode; it sets which metric a delta is judged
   against and which direction bids move.
2. **WoW deltas** — this week against the prior week on spend, CTR, CPC,
   conversions and CPL, per campaign and ad group, read against the benchmarks
   and significance thresholds in `dmo/google-ads-channel.md` and
   `dmo/linkedin-channel.md`.
3. **Tiering** — sort every campaign into 🔴 Act Now / 🔍 Research Spike /
   🟡 Watch / 🟢 Performing.
4. **Bid, budget, cross-channel** — form the recommendations per
   `dmo/bid-strategy.md`, including its list of signals that mean bid strategy
   should *not* change and its cross-channel reallocation heuristics.
5. **Creative** — where the cause is ad-level, raise a `creative` move and let
   `performance-marketer:creative-optimizer` draft the copy (step 4 below);
   never draft ad copy in this skill.
6. **Hypotheses** — one testable statement per proposed move, naming the metric
   that should move and the window it should move in.

This produces the raw analysis; it does **not** decide what is auto-executable.

### 3. Enumerate proposed moves

Express each recommendation as one structured move. The classifier reads these
fields (see `scripts/paid/classify.py`):

```python
{
  "platform": "google_ads" | "linkedin",
  "op_type": "add_negative" | "set_bid" | "match_type_promotion"
             | "create_experiment" | "pause_ad" | "budget"
             | "bid_strategy" | "cross_channel" | "creative",
  "campaign_name": "...",
  "campaign_tier": "act_now" | "research_spike" | "watch" | "performing",
  "summary": "human-readable description of the move",
  "involves_new_copy": false,        # true if new/changed ad copy goes live
  "bid_change_pct": 12.0,            # signed %, for set_bid
  "budget_delta_weekly": 0.0,        # for budget
  "pauses_source": false,            # for match_type_promotion
  "reversal_if": "condition that should trigger rollback"
}
```

Be precise with `op_type`, `campaign_tier`, `involves_new_copy`, and
`bid_change_pct` — these drive the bucket. When unsure, leave a field off; the
classifier defaults unknowns to the safe side (`human_3b`).

### 4. Classify — deterministically, not by judgment

Run the moves through the classifier. **You do not assign buckets yourself** —
the module does, and its rules are the safety contract (plan §2, §7):

```python
from scripts.paid.classify import classify_moves, bucket_counts
results = classify_moves(moves)        # each -> {summary, op_type, campaign_name, bucket, reason}
counts  = bucket_counts(results)       # {auto_3a, human_3b, creative}
```

Buckets:
- **`auto_3a`** — mechanical, reversible, capped Google Ads change; auto-applied
  after greenlight.
- **`human_3b`** — budgets, pauses, bid-strategy switches, cross-channel,
  LinkedIn, out-of-envelope bids, or anything on a 🔍 Research-Spike campaign.
- **`creative`** — needs new/changed copy live; blocked on copy review.

For every `creative` move, invoke `performance-marketer:creative-optimizer` to generate the
pre-drafted variations that will ride along on the copy-review task.

### 5. Assemble and write the dossier

Build the dossier object (position, WoW snapshot, campaign health, the classified
`moves`, budget view, rollback, hypotheses — shape documented in
`scripts/paid/dossier.py`) and write it deterministically:

```python
from scripts.paid.dossier import write_dossier
path = write_dossier(dossier)   # -> docs/publications/pending/performance-marketer/optimization_dossiers/<date>-optimization-dossier.md
```

`dossier.py` renders the fixed §5 sections byte-stably and formats Linear refs as
clickable links per
[docs/linear-reference-formatting.md](../../../docs/linear-reference-formatting.md) —
do not hand-format the page. It also **supersedes** the prior pending dossier,
moving it to `docs/publications/published/performance-marketer/optimization_dossiers/` so
`pending/` always holds only the current one.

### 6. Persist the proposals

Record each classified move as a `paid_change_proposals` row so downstream blocks
(greenlight, copy-delegation, execute) can track its lifecycle. Merge each
move's `bucket` + `reason` from step 4 onto the move, then:

```python
from scripts.paid import db
conn = db.connect()
ids = db.insert_proposals(conn, moves, dossier["dossier_date"], created_at)  # created_at = this Tick's ISO ts
conn.commit(); conn.close()
```

`db.py` is the only writer to the paid tables; it requires `platform`, `op_type`,
`bucket`, and `summary` on every move and supplies nothing implicitly (you pass
the timestamp). Rows start at `status='proposed'`.

### 7. Hand off to chief-of-staff (team-share + greenlight)

Append one entry to `state/journal/handoffs.md` so chief-of-staff shares the dossier
with the team and surfaces the greenlight ask. chief-of-staff keys on the subject prefix
**"Optimization dossier"** (see chief-of-staff's *Specialist Optimization Dossiers*
section). Format:

```
## {ISO ts} | performance-marketer → chief-of-staff | Optimization dossier — {date range} ({objective})

**Severity:** MED   (HIGH if event-driven)
**Surface:** paid-optimization
**Dossier:** docs/publications/pending/performance-marketer/optimization_dossiers/{date}-optimization-dossier.md
**Summary:** {N} moves — {a} auto_3a, {b} human_3b, {c} creative. Position: {thesis}.
**Triggered by:** {trigger_reason, or omit for the weekly Thursday pass}
**Team-share:** #team-marketing (context, before greenlight)
**Greenlight ask:** approve the position? auto_3a applies on greenlight; human_3b packaged for the operator; creative → copy-review tasks.
**Proposal ids:** {paid_change_proposals ids from step 6}
**Tier gate:** 2
```

Also INSERT the matching row into the `handoffs` table (`status='pending'`) so
the lifecycle is tracked (`docs/conventions.md` → Handoff Lifecycle). chief-of-staff
picks this up on its next AM Tick.

## Outputs

- A bucketed move list (`auto_3a` / `human_3b` / `creative`) with a `reason` per
  move, produced deterministically by `scripts/paid/classify.py`.
- A dossier rendered per §5 and written to `docs/publications/pending/performance-marketer/optimization_dossiers/`.
- A `paid_change_proposals` row per move (`status='proposed'`).
- A `performance-marketer → chief-of-staff` handoff for team-share + greenlight.

## Status of dependent blocks

Done and usable now:
- **A1** — `scripts/paid/classify.py` (the deterministic bucketing in step 4).
- **A2** — `scripts/paid/dossier.py` (the deterministic render + write in step 5).
- **A3** — `paid_change_proposals` table exists (migration 008).
- **Proposal persistence** — `scripts/paid/db.py` (step 6).
- **C1/C2** — chief-of-staff team-shares the dossier to `#team-marketing` and surfaces
  the greenlight in the AM brief (step 7 handoff → chief-of-staff's *Specialist
  Optimization Dossiers* section).

Not built yet (don't rely on these):
- **C3** — Linear copy-review tasks for `creative` moves (default {{CONTENT_LEAD_FIRST}},
  reassignable); proposals marked `awaiting_creative`.
- **F2** — `performance-marketer:execute-approved` applies greenlit `auto_3a` moves.

Until C3/F2 land: `creative` moves are surfaced in the dossier but their copy
tasks are created manually, and greenlit `auto_3a` moves are applied by a human.
