---
name: performance-marketer:creative-optimizer
description: >
  Weekly WoW creative performance analysis with brand-compliant variation
  generation. Runs the week-over-week creative pass end to end, adding
  hypothesis tracking, creative memory, and A/B variant management.
  Generates Google RSA headlines (<=30 chars) and descriptions (<=90 chars) and
  LinkedIn Sponsored Content variations. Writes to paid_creative table and
  docs/publications/pending/performance-marketer/creative_variations/ for Tier 2 approval.
---

# Creative Optimizer

## When This Runs

- **Tick integration:** Weekly Tick (Fridays, after daily checks)
- **Standalone:** `/performance-marketer creative-optimizer`

## Inputs

Same inputs as the weekly position pass:
- Google Ads performance data (14-day export recommended)
- LinkedIn Campaign Manager performance data (14-day export recommended)
- Objective mode (Efficiency / Pipeline / Awareness / Custom)

If the user doesn't state an objective, ask before running anything — the
objective decides which metric a delta is judged against.

## Relationship to optimization-dossier

`performance-marketer:optimization-dossier` forms the week's position and owns:
- WoW delta analysis
- Campaign tiering
- Bid and budget recommendations
- Cross-channel reallocation
- Dossier assembly and move classification

It invokes this skill for every move in the `creative` bucket. creative-optimizer
owns the creative half and adds:
- State persistence (writes to `paid_creative`, `experiments` tables)
- Hypothesis scoring (reads prior hypotheses, scores against new data)
- Creative memory (tracks which variations were approved/rejected/flagged)
- Pending draft management (writes to `docs/publications/pending/performance-marketer/creative_variations/` for approval flow)
- Handoff generation (notifies chief-of-staff for Tier 2 approval)

## Workflow

### 1. Load Brand Context

Read these before generating any creative:
- `context/marketing-project-context.yaml`
- `context/founder-pov-context.yaml`
- `context/buyer_persona_context_profile.yaml`

### 2. Load Prior Context

Read the prior week's trail out of the paid tables: open rows in `experiments`,
the last dossier's `paid_change_proposals` rows, and any `applied_changes`
since. Score open hypotheses from the prior week:
- **CONFIRMED** — predicted outcome materialized
- **DISPROVEN** — opposite or null result
- **INCONCLUSIVE** — insufficient data to determine

### 3. Run the WoW Analysis

Work the pass in order, grounded in the channel references under
`roster/performance-marketer/references/dmo/`:

1. **Objective** — confirm the mode (Efficiency / Pipeline / Awareness / Custom).
2. **WoW deltas** — this week against the prior week on spend, impressions,
   clicks, CTR, CPC, conversions and CPL, per campaign and ad group, read
   against the benchmarks in `dmo/google-ads-channel.md` and
   `dmo/linkedin-channel.md`.
3. **Tiering** — sort every campaign into 🔴 Act Now / 🔍 Research Spike /
   🟡 Watch / 🟢 Performing on the size and direction of those deltas.
4. **Bid and budget** — note the bid and reallocation reads per
   `dmo/bid-strategy.md`. They belong to the dossier; carry them here only so
   the creative read has the spend context.
5. **Creative** — for the Act Now and Watch campaigns, diagnose the ad-level
   cause (headline set, landing-page match, asset strength) and draft the
   variations per **Generate Creative Variations** below.
6. **Hypotheses** — one testable statement per variation, naming the metric
   that should move.

This produces the WoW snapshot, campaign tiering, and creative variations.

### 4. Persist to State

For each ad unit analyzed, UPSERT into `paid_creative`:

```sql
INSERT INTO paid_creative (
  agent, platform, campaign_name, ad_group, creative_id,
  headline, description, impressions, clicks, ctr, spend,
  conversions, cpl, status, snapshot_date, created_at
) VALUES (...);
```

For new A/B tests proposed, INSERT into `experiments`:

```sql
INSERT INTO experiments (
  agent, name, platform, hypothesis, variant_a, variant_b,
  start_date, status, created_at
) VALUES (...);
```

### 5. Generate Creative Variations

For campaigns in the Act Now or Watch tiers, generate variations following the
field limits in `dmo/google-ads-format.md` and the guardrails in
`dmo/paid-ads-brand-guardrails.md`:

**Google RSAs:**
- Headlines: max 30 characters (hard limit — count carefully)
- Descriptions: max 90 characters (hard limit)
- 3-5 new headlines + 2 new descriptions per flagged ad group
- Apply persona: Erin for search/founder campaigns, Hannah for engineering-leadership campaigns

**LinkedIn Sponsored Content:**
- Intro text: 150 chars ideal, 600 max
- Headline: 70 chars max
- 2-3 variations per flagged campaign

**Brand guardrails (always enforced):**
- No fear-based language
- Outcome-first, mechanism-second
- No competitor names (except in explicit conquesting campaigns)
- No corporate jargon padding

For each variation, document the hypothesis: what change is being proposed,
what behavioral or messaging lever it pulls, and what metric should move.

### 6. Write Pending Draft

Supersede the prior pending draft, then write the new variations:

```bash
python3 scripts/paid/publish.py creative_variations
```

Write all creative variations to:
`docs/publications/pending/performance-marketer/creative_variations/YYYY-MM-DD-creative-variations.md`

Format:

```markdown
# Creative Variations — YYYY-MM-DD

**Objective:** {mode}
**Channels:** {Google Ads / LinkedIn / Both}

---

## {Campaign Name} — {Ad Group}

**Tier:** {Act Now / Watch}
**Issue:** {diagnosis — e.g., CTR dropped 32% WoW}

### Variation 1
- **Headline:** {text} ({char count})
- **Description:** {text} ({char count})
- **Hypothesis:** {what this tests}

### Variation 2
...

---

*These drafts need copywriter review before going live.*
*Route to {{CONTENT_LEAD_FIRST}} or run through /draft-content for a full pass.*
```

### 7. Write Handoff

Append to `state/journal/handoffs.md`:

```
## YYYY-MM-DDTHH:MM:SSZ | performance-marketer → chief-of-staff | Tier 2: Creative variations ready

**Severity:** n/a (scheduled weekly output)
**Surface:** docs/publications/pending/performance-marketer/creative_variations/YYYY-MM-DD-creative-variations.md
**Summary:** {N} variations across {M} campaigns. Key changes: {1-line summary}.
**Action required:** Post to Slack for thread-reply approval.
**Tier gate:** 2
```

INSERT into `handoffs` and `approvals` tables.

## Copy-Review Delegation (C3)

When an optimization position is greenlit, every move performance-marketer classified as
`creative` is **blocked on copy review** — it never auto-applies. For each such
greenlit proposal, open a routable copy-review task rather than waiting on any
one person:

1. Create a Linear issue via `gtm-fleet:linear-task-capture` in the
   Marketing team. **Default assignee: {{CONTENT_LEAD_FIRST}}; explicitly reassignable** — the task
   gates on copy *approval*, not on {{CONTENT_LEAD_FIRST}}, so anyone with copy authority can clear
   it and {{CONTENT_LEAD_FIRST}} backed up never freezes the pipeline.
2. The issue body carries the full brief so the reviewer edits rather than
   authors: campaign / ad group, the diagnosis, the **pre-drafted variations**
   from this skill, the hypothesis each tests, and a reference to the dossier.
3. Capture the new issue ref and mark the proposal:
   ```python
   from scripts.paid import db
   conn = db.connect()
   db.set_proposal_status(conn, proposal_id, "awaiting_creative", linear_ref="MAR-XXXX")
   conn.commit(); conn.close()
   ```
   We store the **issue ref**, not the assignee — so reassigning the task in
   Linear never breaks the link back to the proposal.
4. The dependent ad change stays blocked until the copy clears Tier 2 review.

Render the issue ref as a clickable link wherever it appears
(`docs/linear-reference-formatting.md`). chief-of-staff surfaces the standing count of
`awaiting_creative` proposals in the AM brief so the queue stays visible and
Scott can reassign.

## Output

- `paid_creative` table rows (performance snapshots)
- `experiments` table rows (new tests proposed)
- Pending creative draft in `docs/publications/pending/performance-marketer/creative_variations/`
- Handoff entry for chief-of-staff
- Updated hypothesis scores in journal

## Creative Memory

Track approval outcomes over time. When chief-of-staff reports back on creative
variations (via handoff):
- `approved` → note the variation ID and what resonated
- `rejected` → note the reason; avoid similar patterns in future
- `needs_edit` → capture edit notes; incorporate in next pass

Over time, this builds a feedback loop that shapes future generation.
The `experiments` table tracks this at the hypothesis level;
performance-marketer's `paid_creative` table tracks it at the individual creative level.
