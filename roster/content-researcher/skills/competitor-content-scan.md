---
name: content-researcher:competitor-content-scan
description: >
  Weekly organic/content competitive intelligence sweep. Scans competitor
  blog and content pages for new posts, identifies content and keyword gaps,
  and captures positioning angles relevant to {{COMPANY}}'s topic strategy.
  Paid competitive intelligence stays with performance-marketer. Writes voice_bank entries
  (competitor_gap type) and one research_packets row.
---

# Competitor Content Scan

## When This Runs

- **Tick integration:** Weekly (Mon), before `topic-synthesizer`.
- **Standalone:** `/content-researcher competitor-content-scan`

## Scope Boundary

This skill owns **organic and content** competitive intelligence only:

| This skill covers | performance-marketer owns |
|------------------|-------------|
| Competitor blog, resources, guides | Paid auction intelligence |
| Content topic gaps and keyword gaps | Auction insights, impression share |
| Positioning angles and messaging shifts | Ad copy and landing page paid analysis |
| Content freshness and publishing cadence | SERP paid feature changes |

When reading performance-marketer's `keyword_rankings` table (read-only), use it only to
understand organic search context — do not modify it.

Reference `roster/performance-marketer/references/competitor-methodology.md` for
triangulation rules and confidence-level guidance. Apply those rules to all
findings from third-party `~~SEO` tools.

## Competitor List

Primary competitors to scan each week. These are the platforms most commonly
named in Aaron's, Hannah's, and Erin's pain points and migration stories:

| Competitor | Blog / Content URL | Relevant content areas |
|------------|-------------------|----------------------|
| {{COMPETITOR_A}} | `{{COMPETITOR_A_DOMAIN}}/blog` | Incident response practice, MTTR benchmarks, enterprise readiness |
| {{COMPETITOR_B}} | `{{COMPETITOR_B_DOMAIN}}/blog` | On-call scheduling, rotation fairness, shift handoffs |
| {{COMPETITOR_D}} | `{{COMPETITOR_D_DOMAIN}}/blog` `{{COMPETITOR_D_DOMAIN}}/resources` | Alerting and paging, alert fatigue, notification reliability |
| {{COMPETITOR_F}} | `{{COMPETITOR_F_DOMAIN}}/blog` | Blameless postmortems, incident review, learning practice |
| {{COMPETITOR_B}} | `{{COMPETITOR_B_DOMAIN}}/resources` | Platform / SRE ownership convergence ({{COMPETITOR_B}}'s differentiated angle) |

Check each week whether new competitors have entered performance-marketer's `keyword_rankings`
data as ranking URLs to add to this list.

Reporting notes: competitor names are factual in internal intelligence outputs.
They must NOT appear in external content (existing brand rule; enforced at
content-producer's creation-pod stage, not here).

## Workflow

### Step 1 — Scan for New Content

For each competitor, identify posts published in the past 7 days:

```
site:{competitor_domain}/blog after:{YYYY-MM-DD}
```

Supplement with a direct fetch of the competitor's blog index page if
accessible to confirm freshness. Look for:
- New blog posts or guides
- New resource pages (checklists, reports, templates)
- Updated pillar pages or comparison pages

Record: title, URL, publish date, estimated topic.

### Step 2 — Content Gap Analysis

Compare competitor content topics against {{COMPANY}}'s current topic footprint:
- Topics well covered by competitors that {{COMPANY}} has **no published content on**
  → `gap` signal (high priority for backlog if Aaron-relevant)
- Topics covered by competitors where {{COMPANY}} has published content but with a
  weaker angle → `differentiation` signal
- Topics covered by competitors that are not Aaron/Erin/Hannah relevant →
  log but do not score highly (breadth over depth is not {{COMPANY}}'s strategy)

Cross-reference with performance-marketer's `keyword_rankings` to find competitor-owned
keywords where {{COMPANY}} has no position:
```sql
SELECT keyword FROM keyword_rankings
WHERE position IS NULL OR position > 50
ORDER BY search_volume DESC;
```
If this query returns no rows (table empty), note the gap and proceed with
web-based gap analysis only.

### Step 3 — Positioning and Messaging Scan

For each new competitor piece, extract:
1. **Core claim / headline angle** — what is the leading value prop?
2. **Target persona** — is this aimed at an Aaron, Hannah, or Erin equivalent?
3. **Differentiation angle against {{COMPANY}}** — does this piece implicitly or
   explicitly address a capability {{COMPANY}} has or lacks?
4. **Language patterns** — are they using new vocabulary or framing the
   category differently? ("AI incident commander", "autonomous remediation",
   "reliability platform", etc.)

This is observation, not a threat assessment. Note what is being said;
do not overinterpret.

### Step 4 — Classify Each Finding

Each finding is either:

| Finding type | voice_bank entry_type | What to record |
|-------------|----------------------|---------------|
| Content gap (topic with no {{COMPANY}} equivalent) | `pain_point` | The topic itself + competitor URL as source_ref |
| Positioning angle (new messaging direction) | `quote` | Verbatim headline or key claim + URL |
| Competitor-owned keyword cluster | `pain_point` | Keyword cluster + evidence it targets Aaron/Hannah |
| Vocabulary/category-creation signal | `quote` | Exact phrase + URL (signals emerging language we may want to own) |

### Step 5 — Write voice_bank Rows

For each qualifying finding:

```sql
INSERT INTO voice_bank (
  agent, entry_type, source, trust_tier, persona, theme, content,
  source_ref, funnel_stage, captured_at, created_at
)
VALUES (
  'content-researcher', ?, 'community', 'attributed', ?, ?,  -- source='community' for competitor content
  ?, ?, ?, ?, datetime('now')
);
```

**`trust_tier` is `attributed`, and only for the competitor's own published pages.**
A post on {{COMPETITOR_B_DOMAIN}} is written by {{COMPETITOR_B}}, under their name, and they are
accountable for it — that is what `attributed` means. It does not mean true or
neutral; a competitor's framing of their own product is marketing, and it is
still fine to store because we know exactly whose words they are.

Two things that are **not** `attributed` and must be stored `open_ugc` if stored
at all: comment sections on those pages, and third-party comparison/review sites
(the "best incident management tools 2026" and "on-call alternatives" listicles
that surface in search). Anyone can author those,
including the vendors being ranked. See `docs/agent-content-trust-policy.md`.

**`source` field:** use `'community'` for competitor content (nearest valid
enum value for external platform signals; not `'social'` or `'sales_call'`).

**Persona tagging:** tag to the competitor's apparent target persona, not
{{COMPANY}}'s. A {{COMPETITOR_B}} post arguing that the platform team should own paging likely maps to `aaron`.

**Theme tagging:** use same theme taxonomy as `social-listening`, plus:
- `competitor_gap` — topic with no {{COMPANY}} equivalent and clear demand signal
- `competitor_positioning` — messaging or framing angle shift worth noting
- `category_vocabulary` — new terminology a competitor is seeding

### Step 6 — Write research_packets Row

```sql
INSERT INTO research_packets (
  agent, packet_type, week_starting, source_count,
  quiet_week, summary, payload_path, created_at
)
VALUES (
  'content-researcher', 'competitor_content',
  date('now', 'weekday 1', '-7 days'),
  ?,     -- count of competitor domains scanned
  ?,     -- 0 or 1; quiet_week=1 if <5 new findings
  ?,     -- one-paragraph summary
  NULL,
  datetime('now')
);
```

**Summary paragraph format:** `"Scanned {N} competitor domains. {N} new posts
found. {N} content gaps identified. Notable: {competitor} published
'{title}' targeting [{persona description}] — [{gap/positioning/vocab note}]."`

**Quiet week threshold for competitor scan:** < 5 new findings across all
competitors. Quieter than social listening by nature (competitors don't publish
daily). A quiet week here is normal; flag only for awareness.

## Confidence Levels

Apply the confidence framework from `roster/performance-marketer/references/competitor-methodology.md`:

- **High confidence:** Direct fetch of competitor blog confirms new post with
  visible publish date
- **Medium confidence:** Appears in web search results with date metadata, but
  page not directly fetched
- **Low confidence:** Inferred from a third-party `~~SEO` tool's content-gap
  data — directional only; not treated as a "new piece" for the weekly count

Always state confidence level in the `evidence_summary` field when the signal
reaches `topic_backlog`.

## Specific Watch List

Beyond the weekly cadence, flag immediately (HIGH severity handoff to chief-of-staff)
if a competitor:
- Publishes a dedicated "open API on every tier," "Terraform provider," or
  "ownership as code" post that directly addresses {{COMPANY}}'s core
  differentiation — the ownership graph and the routing that falls out of it,
  which is the whole reason the pages stop arriving. This is a category race
  signal, not a routine content gap
- Launches a tool, integration, or product that matches a topic currently in
  {{COMPANY}}'s `topic_backlog` with `status = 'approved'` (brief-stage urgency bump)
- Starts ranking in top 10 for a tracked keyword where {{COMPANY}} currently ranks
  1–5 (competitive threat to a content moat — write handoff immediately)

For routine findings (content gaps, new posts, positioning shifts), write to
`voice_bank` and let `topic-synthesizer` surface them through the normal
scoring process.

## Output to Journal

In the Tick journal entry, under `### Research Sweep`, include:

```
[competitor_content] → {N} competitor domains, {N} new posts, {N} voice_bank entries
{quiet_week flag if <5 findings}
Top gap: {topic area — one line}
Watch list triggers: {none | competitor + what they published}
```

## Boundary Rules

- **Organic/content only.** Do not analyze auction insights, ad copy,
  or paid SERP data. Those signals belong to performance-marketer.
- **Read-only.** Do not interact with competitor platforms in any way.
- **No fabrication.** If a competitor domain returns no new content this
  week, record `source_count` accurately; do not invent gaps.
- **Name competitors factually** in internal state (voice_bank, journal,
  research_packets). Names must not flow into external-facing content —
  content-producer's creation-pod enforces this at draft stage.
