---
name: content-researcher:topic-synthesizer
description: >
  Synthesizes all voice_bank research signals with performance-marketer's keyword_rankings
  and the canonical AEO register into a scored, ranked topic backlog.
  Deduplicates against published content. Submits top candidates (≥2 evidence
  sources, score ≥50) as a Tier 2 pending draft for {{HEAD_OF_MARKETING_FIRST}}'s batch approval.
  Runs last in the weekly Tick, after all research skills have written to voice_bank.
---

# Topic Synthesizer

## When This Runs

- **Tick integration:** Weekly (Mon), last step — runs after `call-miner`,
  `social-listening`, and `competitor-content-scan` have all written their
  `voice_bank` entries for the week.
- **Standalone:** `/content-researcher topic-synthesizer`

## Inputs

| Source | Table / File | What To Read |
|--------|-------------|--------------|
| Voice bank | `voice_bank` | All entries since last `topic_backlog` synthesis run (count distinct `source_ref` for evidence) |
| Keyword state | `keyword_rankings` | Latest position + volume per keyword (performance-marketer-owned, read-only) |
| AEO register | `docs/aeo-tracked-prompts.md` | Full prompt list: platform, topic, bucket, ICP, journey phase |
| Existing backlog | `topic_backlog` | Current `candidate` / `approved` rows for dedup |
| Content inventory | `content_inventory` | Published {{COMPANY}} content for net-new/refresh/duplicate dedup (Step 6); maintained by `content-researcher:content-inventory` |
| Personas | `context/personas/` | Aaron (primary), Erin, Hannah (secondary) |

## Workflow

### 1. Load Prior State

Query `topic_backlog` for all non-rejected rows to build the dedup set, and pull
{{HEAD_OF_MARKETING_FIRST}}'s review state at the same time:

```sql
SELECT topic_uid, topic, status, review_notes FROM topic_backlog
WHERE status != 'rejected';
```

**Rows with `status='needs_edit'` are instructions, not new work.** `review_notes`
holds {{HEAD_OF_MARKETING_FIRST}}'s own words about what to change. Re-cluster and re-title that topic
*using* his note, keep its existing `topic_uid`, and move it back to `submitted` —
do not mint a new row, or the same topic re-enters the backlog twice under two
phrasings and his ruling is orphaned on the old one.

**Rows with `status='rejected'` stay excluded from the dedup set but their
`review_notes` are worth reading** — a rejection reason is the calibration signal
described under Scoring Calibration below. If a cluster you are about to score
matches a rejected topic, say so in the journal rather than silently re-submitting it.

Also note the most recent `created_at` timestamp in `topic_backlog` —
this is your "synthesized since" marker for clustering new voice_bank entries.

### 2. Cluster Voice Bank Signals

**Use the `theme` tag as a clustering prior.** call-miner and social-listening
stamp each entry with a shared `theme` label (same vocabulary across sources).
Group within each theme tag first, then refine into specific topics — do not
re-cluster from scratch. This keeps clusters consistent week-to-week and scales to
the higher entry volume call-miner produces.

Then refine. Do not invent theme names beyond the shared vocabulary — derive
specific topics from the actual content. Clustering rules:

- Entries sharing the same pain point or question axis → one theme cluster
- Entries from different sources (sales call, social, competitor gap) that
  describe the same underlying need → merge; the count of distinct `source_ref`s
  is the evidence score (see step 5)
- `competitor_mention` entries cluster toward comparison/positioning topics;
  cross-link any matching gap from `competitor-content-scan` as corroborating
  evidence
- `vocabulary` entries (the market reaching for words) flag a category-creation
  opportunity — they lift the education score in step 5
- Cap theme name at 6 words. Prefer noun phrases ("managing contractor
  compliance at scale") over verbs ("how to manage…")
- Retain each cluster's member `voice_bank.id`s — step 7 persists them to
  `topic_evidence` so `content-producer:brief-builder` can pull the exact quotes behind a topic

Minimum viable cluster: 1 entry. Single-source clusters are `candidate`
status; they do NOT qualify for Tier 2 submission but appear in the backlog
for accumulation.

### 3. Cross-Reference Keyword State

For each theme cluster, scan `keyword_rankings` for matching or related terms:

```sql
SELECT keyword, position, search_volume
FROM keyword_rankings
ORDER BY snapshot_date DESC;
```

Match heuristically (substring, semantic overlap). Record:
- Best matching keyword for the topic
- Current position (if present — table may be empty early on)
- Search volume estimate (if available)

If `keyword_rankings` is empty, note the gap and score `search_opportunity`
at 5/15 (low but not zero — topic may still have search value not yet tracked).

### 4. Cross-Reference AEO Register

For each theme cluster, scan `docs/aeo-tracked-prompts.md` for:
- Prompts in the same topic area → `aeo_covered` flag (reduce AEO opportunity
  score if {{COMPANY}} is already tracking this prompt and citation rate is healthy)
- Topic areas with NO matching AEO prompts → strong AEO opportunity
- Bucket classification (1 = Existing Commercial Demand, 2 = Category Narrative
  Ownership, 3 = Technical / Infrastructure Authority, 4 = Operator / Workflow
  Intent) to guide education/category-creation scoring

### 5. Score Each Topic (0–100)

Apply the canonical scoring split:

| Dimension | Weight | Scoring Logic |
|-----------|--------|---------------|
| **Aaron-fit (ICP)** | /25 | How well does this topic serve Aaron the Platform Engineer's primary goals and pain points — ownership mapped service to team to responder, rotations and escalation policies declared in version control and reviewed in a pull request, page volume cut without losing a real incident, response wired into the tools the team already lives in, and an end to being the human router at 3 a.m.? The pains that score highest: clicked-together config that drifts from the service catalog, alert fatigue measured in resignations, an automation chain that breaks at the moment a page fires, and trust anxiety about anything that auto-resolves without an audit trail. 20–25 = direct pain/goal match with technical depth (a `.tf` file, a routing rule, a real config); 10–19 = adjacent; 0–9 = primarily Hannah or Erin territory or too generic |
| **AEO opportunity** | /20 | Is there an unmet or weakly-met AEO prompt in this topic area? 16–20 = no current prompt + LLM answer gap visible; 8–15 = adjacent prompt exists, differentiation possible; 0–7 = {{COMPANY}} already tracking, citation rate healthy |
| **Evidence** | /20 | Count **distinct `source_ref`s** (one call = one source, no matter how many rows it produced) plus cross-channel diversity. Call-frequency counts strongly on its own; a second channel is a bonus, not a requirement. 18–20 = 5+ distinct calls, or 3+ calls with social/competitor corroboration; 15–17 = 5+ distinct calls single-channel, or 3–4 calls; 12–14 = 3–4 distinct calls; 8–11 = 2 distinct sources (clears the Tier 2 floor); 4–7 = 1 source (stays `candidate`); 0–3 = inferred, no direct quote |
| **Education / category-creation** | /20 | Does this topic name an emerging pattern or define the role/category Aaron is building? 16–20 = introduces new vocabulary or frames the category (e.g., "ownership as code", "signal-to-page ratio", "the 3 a.m. tax") — a cluster backed by `vocabulary` voice_bank entries (the market visibly reaching for words) sits in this band; 8–15 = educates on an established concept (error budgets, blameless postmortems, MTTA vs MTTR); 0–7 = product feature explanation only |
| **Search opportunity** | /15 | Volume × difficulty proxy. 11–15 = tracked keyword with meaningful volume, position >20 (can improve); 6–10 = related keyword present, mid-competition; 0–5 = no matching keyword data yet or very low estimated volume |

**Score floor for Tier 2 submission:** ≥50 total AND ≥2 evidence sources
(distinct `source_ref`s — the same question in 2+ distinct calls qualifies)
**AND at least one source at `trust_tier` in (`first_party`, `attributed`)**.
Topics scoring 30–49 stay as `candidate` in the backlog for accumulation.
Topics scoring <30 are logged but not inserted (or inserted with a note).

### The provenance floor

A topic evidenced **only** by `open_ugc` stays `candidate` regardless of score or
source count. Check it before submitting:

```sql
SELECT COUNT(DISTINCT vb.source_ref) AS corroborating
  FROM topic_evidence te
  JOIN voice_bank vb ON vb.id = te.voice_bank_id
 WHERE te.topic_id = ?
   AND vb.trust_tier IN ('first_party', 'attributed');
-- 0 -> not submittable, no matter what the score says
```

The reasoning is adversarial, not editorial. Distinct `source_ref` counts as
independent evidence only if the sources are independently authored — true of two
sales calls, not true of eight forum posts, which one person can write in an
afternoon. Once content-researcher can read LinkedIn, Reddit and Hacker News, "how many
distinct URLs said this" becomes a number an outsider can manufacture, and that
number currently drives 20/100 of the score and gates submission to {{HEAD_OF_MARKETING_FIRST}}.

So: `open_ugc` is real signal for **what to look into**, never sufficient proof of
**what the market thinks**. When a cluster is blocked by this rule, say so plainly
in the journal — `"{topic} — {N} sources, all open_ugc; held as candidate pending
first-party corroboration"` — rather than quietly dropping it or promoting a
source's tier to get it through. A blocked cluster is a lead for `call-miner` to
listen for, not a defeat.

Full policy and the fleet-wide tier definitions: `docs/agent-content-trust-policy.md`.

### 6. Dedup Against Published Content (content_inventory)

Search `content_inventory` — {{COMPANY}}'s published-content source of truth, maintained
by `content-researcher:content-inventory` — for overlap with each candidate topic:

```sql
SELECT url, title, primary_topic, persona, top_queries, query_source,
       published_at, last_modified
FROM content_inventory WHERE status = 'live';
```

Match each candidate on **both** axes:
- **Title / topic / headings** semantic overlap with the candidate topic + its theme.
- **`top_queries` overlap** — if a live page already ranks for the candidate's
  keywords (from step 3) or AEO phrasings, that is the strongest "already covered"
  signal. If the matched page's `query_source = 'none'`, fall back to title/topic
  overlap only and note the reduced confidence.

Classify (balanced policy):
- **net-new** — no strong match → insert as a new row.
- **refresh** — covered, but the candidate adds a distinct angle, a different
  persona, or an AEO format the existing piece lacks → set `status='refresh'` and
  note the gap + the existing `url` in `evidence_summary`.
- **duplicate** — fully covered, no new angle → do not insert; log
  `deduped: "{topic}" already covered by {url}`.

If `content_inventory` is empty (not yet seeded), skip dedup, insert as net-new,
and note `MED`: content inventory unseeded — dedup skipped this run.

### 7. Write to topic_backlog

For each clustered topic, INSERT or UPDATE.

**Mint `topic_uid` on every INSERT.** It is the key the Notion review database syncs
on, so a row without one cannot reach {{HEAD_OF_MARKETING_FIRST}}:

```python
from scripts.ids import mint
topic_uid = mint("content-researcher", "topic")   # content_researcher_topic_01kz4j20ha_bq5m9p
```

Never derive it from `MAX(id)+1` or the integer `id` — `docs/conventions.md` forbids
that, and a renumber on branch merge would silently re-point Notion pages at the
wrong topics. Rescoring an existing topic keeps its original `topic_uid` unchanged;
that is what lets {{HEAD_OF_MARKETING_FIRST}}'s decision on it survive a rescore.

```sql
INSERT INTO topic_backlog (
  agent, topic_uid, topic, target_persona, funnel_stage, content_type,
  score_total, score_icp, score_search, score_aeo,
  score_evidence, score_education, evidence_summary,
  evidence_sources, status, created_at
)
VALUES (
  'content-researcher', ?, ?, ?, ?, ?,
  ?, ?, ?, ?, ?, ?,
  ?, ?, ?, datetime('now')
);
```

Do not write `review_notes`, `notion_page_id`, or `notion_synced_at` here — those are
written by the review loop (`scripts/topic_review.py` and
`roster/scribe/skills/notion-topic-sync.md`), not by synthesis.

**Persist the evidence link.** Immediately after each topic INSERT, capture its id
(`last_insert_rowid()`) and write one `topic_evidence` row per `voice_bank` entry in
that cluster — this is what lets `content-producer:brief-builder` bundle the exact verbatim
quotes behind a topic instead of re-deriving them by theme match:

```sql
INSERT OR IGNORE INTO topic_evidence (topic_id, voice_bank_id, created_at)
VALUES (?, ?, datetime('now'));
```

Use the cluster's `voice_bank.id`s retained from step 2. On a rescore/refresh that
re-clusters an existing topic, `UNIQUE(topic_id, voice_bank_id)` keeps re-inserts
idempotent.

**target_persona:** `aaron` if Aaron-fit score ≥15; `hannah` or `erin` if
the theme is primarily theirs. One row per topic — if it scores well for
multiple personas, use the primary and note the secondary in `evidence_summary`.

**content_type:** infer from evidence and AEO bucket:
- Top-of-funnel, category-creation → `educational guide`
- Tactical, how-to, with code/config examples → `tutorial`
- Data-driven, cites research → `report`
- Common Q&A cluster with AEO match → `faq`
- Comparative framing → `comparison`

**evidence_summary:** one line, ≤20 words. Format: `"{N} [sources]; {keyword} vol
{V}; {AEO note if relevant}"`. Example: `"4 sales calls, 2 LinkedIn threads;
'terraform on call rotation' 1.1k vol; no AEO prompt tracked"`.

### 8. Write Pending Draft

If any topics qualify for Tier 2 (score ≥50, evidence_sources ≥2), write a
draft to `state/pending/YYYY-MM-DD/content-researcher-topic-backlog.md`:

```markdown
# content-researcher Topic Backlog — {Date}

**Submitted for batch approval (Tier 2). {{HEAD_OF_MARKETING_FIRST}}: approve / reject / needs_edit per topic.**

## Submission Summary
- Topics submitted: {N}
- Score range: {min}–{max}
- New this week: {N} / Rescored: {N} / Refresh: {N}

---

## Topic {rank}: {topic title}

**Score:** {total}/100 (ICP {icp}/25 · AEO {aeo}/20 · Evidence {ev}/20 · Education {edu}/20 · Search {srch}/15)
**Persona:** {primary} {secondary if applicable}
**Funnel stage:** {top / mid / bottom}
**Content type:** {type}
**Evidence:** {evidence_summary}
**Evidence sources ({N}):**
- [{source_type}] "{verbatim quote or signal}" ({source_ref})
- ...

**Suggested angle:** {one sentence on the editorial hook — what makes this distinct}

---

[repeat for each qualifying topic, ranked by score desc]

## Candidate Pool (score 30–49, not submitted)

| Topic | Score | Missing |
|-------|-------|---------|
| {topic} | {score} | {what's needed to qualify — more evidence, keyword data, etc.} |

## Candidate Keywords & AEO Prompts (surfaced from call signal)

- **Keywords → performance-marketer:** {comma-separated phrasings not yet in keyword_rankings}
- **AEO prompts → Scott:** {newline list of proposed register prompts}

```

### 9. Write Handoff to chief-of-staff

After writing the pending draft, append a handoff entry to
`state/journal/handoffs.md`:

```
## {timestamp} | content-researcher → chief-of-staff | Tier 2: Topic backlog ready for batch approval

**Severity:** n/a (scheduled weekly output)
**Surface:** state/pending/{date}/content-researcher-topic-backlog.md
**Summary:** {N} topics submitted for {{HEAD_OF_MARKETING_FIRST}}'s batch approval. Top topic:
"{title}" (score {N}/100). Candidate pool: {N} topics pending more evidence.
**Action required:** Post to approval thread; {{HEAD_OF_MARKETING_FIRST}} batch-approves via
thread-reply (approve / reject / needs_edit per topic).
**Tier gate:** 2
```

If no topics qualify (all below 50 or all single-source), skip the pending
draft and handoff. Note in journal: `Backlog delta — no qualifying topics
this week; [N] candidates accumulating.`

### 10. Candidate Keywords & AEO Prompts (handoffs)

From the `question` and `vocabulary` voice_bank entries in each submitted cluster,
extract the market's own phrasings as proposals. content-researcher **proposes** — it never
edits performance-marketer's keyword state or Scott's AEO register.

- **Candidate keywords → performance-marketer.** Distinct search-shaped phrasings not already in
  `keyword_rankings`. Skip if none. Append to `handoffs.md`:

```
## {timestamp} | content-researcher → performance-marketer | Candidate keywords from call signal

**Severity:** LOW (informational)
**Surface:** topic_backlog (this week's submission)
**Summary:** {N} candidate keywords surfaced from sales-call language, not yet in
keyword_rankings. e.g. "{phrase}" ({M} distinct calls).
**Action required:** Consider for tracking in the next ranking sweep.
**Tier gate:** n/a
```

- **Candidate AEO prompts → Scott.** Question phrasings that read like prompts a
  buyer would put to an LLM, absent from `docs/aeo-tracked-prompts.md`. Route to
  Scott's rebalance-memo process (Tier 2 register-addition proposal). Skip if none:

```
## {timestamp} | content-researcher → Scott | Proposed AEO prompts (register addition)

**Severity:** n/a (Tier 2 proposal)
**Surface:** docs/aeo-tracked-prompts.md (proposed additions — I do not edit the register)
**Summary:** {N} candidate prompts from call signal. e.g. "{question}" (asked in
{M} distinct calls; bucket {1-4}; persona {aaron|hannah|erin}).
**Action required:** Review for the next dated rebalance memo.
**Tier gate:** 2
```

Note the counts surfaced in the journal.

## Scoring Calibration

Approved and rejected outcomes from `handoffs.md` and `topic_backlog.approved_at`
are ground truth. When {{HEAD_OF_MARKETING_FIRST}} rejects a topic, note the stated reason in the
journal and fold the pattern into scoring bias:
- Consistent rejections on a topic type → lower that content_type's default
  education/category score
- Consistent rejections citing "too similar to published X" → tighten dedup
  matching

Do not adjust scoring weights unilaterally. Structural weight changes require
a scope revision (propose via Decision Queue).

## Database Reference

All reads and writes use `state/working/fleet.db`.

**Read-only (performance-marketer's tables):**
- `keyword_rankings` — latest keyword position and volume

**Read-only (shared content inventory):**
- `content_inventory` — published content for dedup (maintained by `content-researcher:content-inventory`)

**Write (content-researcher's tables):**
- `topic_backlog` — one row per synthesized topic
- `topic_evidence` — `topic_id` → `voice_bank_id` links behind each topic (read by `content-producer:brief-builder`)
