---
name: content-producer:brief-builder
description: >
  Turns a {{HEAD_OF_MARKETING_FIRST}}-approved topic_backlog row into a build-ready content brief.
  Bundles the exact verbatim evidence behind the topic via topic_evidence →
  voice_bank, picks primary/secondary keywords from keyword_rankings (absorbing
  performance-marketer keyword-research §7), pulls the AEO question set from the canonical
  register, re-checks content_inventory so a covered topic becomes a refresh
  brief instead of a duplicate, and writes the brief file plus its content_briefs
  row. Stops rather than drafting when a topic has fewer than 2 evidence sources.
---

# Brief Builder

## When This Runs

- **Tick integration:** Daily queue check (weekdays 10:00 PT), stage 2 — after gate
  outcomes are processed. One brief per `topic_backlog` row with `status='approved'`
  that does not already have a `content_briefs` row, oldest `approved_at` first.
- **Standalone:** `/gtm-fleet:content-producer brief-builder [topic_uid]` — with a `topic_uid`,
  build that topic only (it must still be `approved`); with no argument, work the
  same queue the Tick works.

Standalone runs load `state/identity/content-producer.md` and the last entry of
`state/journal/content-producer.md` for context, then skip the rest of the Librarian Protocol.

content-producer never writes `topic_backlog` except the single `status` flip in step 8. Topic
selection, scoring, and evidence linking are content-researcher's
(`roster/content-researcher/skills/topic-synthesizer.md`).

## Inputs

| Source | Table / File | What To Read |
|--------|--------------|--------------|
| Approved topic | `topic_backlog` | The row: `topic_uid`, `topic`, `target_persona`, `funnel_stage`, `content_type`, `score_total`, `evidence_summary`, `evidence_sources`, `review_notes` |
| Evidence bundle | `topic_evidence` → `voice_bank` | Verbatim `content`, `entry_type`, `persona`, `theme`, `funnel_stage`, `trust_tier`, `source_ref` for every linked entry |
| Keyword state | `keyword_rankings` | Latest `position`, `prior_position`, `search_volume`, `url` per keyword (performance-marketer-owned, read-only) |
| AEO register | `docs/aeo-tracked-prompts.md` | Tracked prompts in the topic's area: prompt text, platform, bucket, ICP, journey phase (read-only, Scott-owned) |
| Tone | `context/personas/aaron-platform-engineer.md` (Aaron) · `context/editorial-tone-context.yaml` (Erin, Hannah) | Humor code per channel — see step 5 |
| Internal links + refresh | `content_inventory` | `status='live'` rows: `url`, `title`, `primary_topic`, `persona`, `top_queries`, `query_source`, `published_at`, `last_modified` |
| Dedup | `content_briefs` | Existing `topic_id` values (a topic is briefed once) |
| Brief structure | `templates/content-brief.md` | The output template — every section, no invented ones |
| Guardrails | `state/identity/content-producer.md` | Aaron hard-fail terms, blocked competitor rule, fear-framing ban |

All DB reads and writes are against `state/working/fleet.db`.

## Workflow

### 1. Pick the Topic(s)

```sql
SELECT t.id, t.topic_uid, t.topic, t.target_persona, t.funnel_stage,
       t.content_type, t.score_total, t.evidence_summary, t.evidence_sources,
       t.review_notes, t.approved_at
  FROM topic_backlog t
 WHERE t.status = 'approved'
   AND t.id NOT IN (SELECT topic_id FROM content_briefs WHERE topic_id IS NOT NULL)
 ORDER BY t.approved_at ASC;
```

Dedup is by `content_briefs.topic_id` — never by title match. For a standalone run
add `AND t.topic_uid = ?`; if that row is not `approved`, say which status it holds
and stop (a `needs_edit` or `submitted` topic is content-researcher's work, not content-producer's).

If the queue is empty, that is a valid run: journal one line and stop.

A topic excluded by that `NOT IN` whose `content_briefs` row is `status='draft'` with
`brief_path IS NULL` is an **interrupted build**, not a finished one (see Failure
Modes). It is correctly out of the queue — dedup is by `topic_id`, and re-running
would mint a second row — but say so in the journal rather than letting it look like
an empty queue:
`interrupted: {topic_uid} has content_briefs id={id} draft/no-path — needs a rebuild decision`.

```sql
SELECT b.id, t.topic_uid FROM content_briefs b
  JOIN topic_backlog t ON t.id = b.topic_id
 WHERE b.status = 'draft' AND b.brief_path IS NULL;
```

`review_notes` on an approved row is {{HEAD_OF_MARKETING_FIRST}}'s own instruction about the angle.
Read it before writing titles and honour it — it outranks the topic string.

### 2. Bundle the Evidence

The link is persisted, not re-derived. Pull the exact rows behind the topic:

```sql
SELECT vb.id, vb.entry_type, vb.source, vb.trust_tier, vb.persona, vb.theme,
       vb.content, vb.source_ref, vb.funnel_stage, vb.captured_at
  FROM topic_evidence te
  JOIN voice_bank vb ON vb.id = te.voice_bank_id
 WHERE te.topic_id = ?
 ORDER BY vb.trust_tier, vb.id;
```

Quote `content` **verbatim**. Never paraphrase it, never compose a representative
quote from two entries, never write a quote that is not in this result set. Each
quote carries its `source_ref` and `trust_tier` into the brief so the editorial gate
can check the claim rather than the prose.

Count the sources:

```sql
SELECT COUNT(DISTINCT vb.source_ref) AS sources,
       SUM(CASE WHEN vb.trust_tier IN ('first_party','attributed') THEN 1 ELSE 0 END) AS corroborated
  FROM topic_evidence te
  JOIN voice_bank vb ON vb.id = te.voice_bank_id
 WHERE te.topic_id = ?;
```

**Evidence rule — hard stop.** `sources < 2`, or `corroborated = 0`, and the brief
does not get written. This is the same bar the topic cleared at submission
(`docs/agent-content-trust-policy.md` → tier floors; `topic-synthesizer` → the
provenance floor), and a topic that no longer meets it has lost evidence, not gained
a shortcut. Leave `topic_backlog.status` at `approved`, write no `content_briefs`
row, and report:

```
brief-builder STOPPED — {topic_uid} "{topic}": {N} distinct source_ref(s),
{M} first_party/attributed. Needs ≥2 sources with ≥1 first_party/attributed.
Evidence is content-researcher's to add (topic_evidence).
```

Journal it under `### Skipped` and, if the topic has sat approved for more than one
Tick, write a LOW handoff to content-researcher naming the topic and the gap.

Trust-tier handling inside the brief: `first_party` and `attributed` quotes may be
used in the published piece (`attributed` only *with* its attribution). `open_ugc`
quotes stay in the brief as direction for the writer and are marked
`[open_ugc — do not publish]` in the evidence bundle. They never reach a
customer-facing surface — the T3 publication ban in
`docs/agent-content-trust-policy.md` is not negotiable at brief stage.

### 3. Refresh Detection

Run this **before** drafting anything, and run it regardless of the topic's status —
a topic can be approved as net-new and still turn out to be covered.

```sql
SELECT url, title, primary_topic, persona, top_queries, query_source,
       published_at, last_modified
  FROM content_inventory
 WHERE status = 'live'
 ORDER BY published_at DESC;
```

Match each live row against the topic on **both** axes:

- **Title / `primary_topic` / `headings` overlap** with the topic string and its theme.
- **`top_queries` overlap** with the candidate keywords from step 4. A live page
  already ranking for the primary keyword is the strongest "already covered" signal.
  When `query_source = 'none'`, fall back to title/topic overlap only and note the
  reduced confidence in the brief.

Then classify:

- **No strong match → net-new brief.** Template `Type` row = `net-new`; delete the
  `Refresh delta` section.
- **Strong match → refresh brief.** Template `Type` row = `refresh`; keep the
  `Refresh delta` section and fill it with the existing `url` and what this piece
  adds that the existing one lacks (new angle, different persona, an AEO format,
  freshness against `last_modified`). The brief specs the *delta*, not a rewrite of
  the whole page. Say the same thing in one line under `Content type` so a reader of
  the brief cannot miss it.
- **Fully covered, no new angle → stop.** Do not write a duplicate brief. Report
  `deduped: {topic_uid} already covered by {url}`, leave the topic `approved`, and
  hand it back to content-researcher (LOW) so the backlog row can be retired or rescoped.

`content_briefs` has **no** `content_type` column — the net-new/refresh marker and
the existing URL live in the brief file (`Type`, `Content type`, `Refresh delta`) and
in the handoff body. Do not invent a column for it.

If `content_inventory` is empty, skip detection, build net-new, and note
`MED: content inventory unseeded — refresh check skipped` in the journal.

### 4. Keywords (absorbs performance-marketer `keyword-research` §7)

```sql
SELECT keyword, position, prior_position, search_volume, url, snapshot_date
  FROM keyword_rankings
 WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM keyword_rankings)
 ORDER BY search_volume DESC;
```

Match heuristically (substring, semantic overlap) against the topic, its theme, and
the market's own phrasings in the evidence bundle.

**Primary keyword.** One per brief. Prefer, in order: a tracked term whose
`position > 20` with meaningful `search_volume` (real upside), then an untracked
term the evidence bank shows the market actually saying, then a tracked term where
we already rank 1–10 *only* if this is a refresh brief consolidating that page.
Classify intent per `roster/performance-marketer/references/search-intent-taxonomy.md`
(informational / navigational / commercial / transactional) and check it matches the
topic's `funnel_stage` — an informational keyword on a bottom-funnel topic is a
mismatch worth naming in the brief rather than papering over.

**Secondary keywords.** 2–5 long-tail and cluster variants of the primary: question
forms, qualifier combinations, and the phrasings that appear verbatim in the evidence
bundle. Do not pad to five.

**Fallback ladder** (`keyword_rankings` is thin early on; use the first rung that
returns something, and record which rung in the brief's `source:` note):

1. `keyword_rankings`
2. content-researcher candidate-keyword handoffs in `state/journal/handoffs.md`
   (`content-researcher → performance-marketer | Candidate keywords from call signal`)
3. `content_inventory.top_queries` for adjacent live pages
4. The topic's theme and the persona's own vocabulary from the evidence bundle

**Cannibalization check.** If any live `content_inventory` row already targets the
chosen primary keyword, either pick a different primary or make this a refresh brief
(step 3) — and write the warning into the template's `Cannibalization` line either
way. Two pages of ours competing for one term is a self-inflicted ranking problem.

### 5. Persona, Tone Code, Word Count

**Persona** comes from `topic_backlog.target_persona` unchanged — `aaron`, `erin`, or
`hannah`. It is a CHECK-constrained value on both tables; do not translate it into a
display name.

**Tone code** is split by persona (locked decision):

- `aaron` → `context/personas/aaron-platform-engineer.md`: blog/guides humor **A–B**,
  social **B**.
- `erin` / `hannah` → `context/editorial-tone-context.yaml` →
  `persona_channel_reference`: e.g. Erin blog `B`, Hannah blog `A–B`.

Write it as `{channel} {code}` — `blog A–B` — matching `templates/content-brief.md`
and the `content_briefs.tone_code` column comment.

**Word count target** (INTEGER, one number): where `keyword_rankings.url` gives a
ranking page to compare against, target its length band. Otherwise use the house band
for the topic's `content_type` — the seeded precedent is guide 1,400 / blog 1,200.
Record the range in the brief file and the single integer in the DB row.

### 6. AEO Question Set

Read `docs/aeo-tracked-prompts.md` (read-only; content-producer never edits the register) and
take every tracked prompt in the topic's area — matching on Topic, ICP, and bucket
(1 Existing Demand · 2 AI Narrative · 3 Technical Authority · 4 Founder Workflow).
Those questions become sections the piece must answer outright.

If no tracked prompt matches, use candidate question targets drawn from the
`entry_type='question'` rows in the evidence bundle — the market's literal phrasing.
Mark them `(candidate — not in register)` so nobody mistakes them for tracked
coverage, and surface them for Scott's rebalance-memo process rather than proposing
a register edit here.

### 7. Write the Brief File and the Row

The file name is derived from the **`content_briefs.id`**, which does not exist until
the row does. So the write is two-phase — insert, learn the id, write the file, then
point the row at it. That ordering is the reason `brief_path` is nullable.

**7a. Insert the row.** Every column below exists in `state/working/schema.sql`:

```sql
INSERT INTO content_briefs (
  agent, topic_id, working_title, target_persona, tone_code,
  primary_keyword, secondary_keywords, aeo_questions, word_count_target,
  brief_path, status, created_at
) VALUES (
  'content-producer', ?, ?, ?, ?,
  ?, ?, ?, ?,
  NULL, 'draft', '{iso_now}'
);
SELECT last_insert_rowid();
```

- `topic_id` is `topic_backlog.id` (the integer), not `topic_uid`.
- `target_persona` ∈ (`aaron`,`erin`,`hannah`) — CHECK-constrained.
- `secondary_keywords` and `aeo_questions` are TEXT holding a **JSON array**
  (`json.dumps([...])`), matching every existing row written by
  `scripts/seed_demo_state.py`. The column comments in `schema.sql` say
  "comma-separated" / "newline-separated" and are stale; the data on disk is JSON.
  Follow the data, and read defensively (accept either) when parsing a row back.
- `status` starts `draft` and becomes `ready` in 7c — the `draft` window is exactly
  the time the file does not exist yet.

**7b. Write the file** to `state/working/briefs/brief-{id:04d}.md`, zero-padded to
four digits from the id returned above (`id=1` → `state/working/briefs/brief-0001.md`,
which is the seeded precedent). Fill `templates/content-brief.md` section by section:

- Replace **every** `{{placeholder}}`. Delete the `Refresh delta` section on net-new.
- Every outline H2 names the AEO question or the educational job it serves **and**
  the evidence it uses. A section with no source does not go in the brief.
- The evidence bundle carries the verbatim quotes from step 2 with `entry_type`,
  `persona`, `funnel_stage`, `source_ref`, and the `[open_ugc — do not publish]`
  marker where it applies.
- `Additional evidence the pod must source + fact-check` names what the brief could
  *not* supply — the stats, code/API examples, and primary sources the pod must go
  get. Naming the gap is the point; leaving it blank invites the pod to invent.
- Working titles carry no Aaron hard-fail term ("easy-to-use", "all-in-one",
  "streamline", "simplify", feature checklists, "AI will replace your team"), no
  blocked competitor name, and no fear-based compliance framing. Check the three
  candidate titles against `state/identity/content-producer.md` before writing them down.

**7c. Point the row at the file and release it:**

```sql
UPDATE content_briefs
   SET brief_path = 'state/working/briefs/brief-{id:04d}.md',
       status     = 'ready'
 WHERE id = ?;
```

`status='ready'` is what makes the brief visible to `creation-pod`. Set it only after
the file is on disk — a `ready` row pointing at a missing file is the one failure the
pod cannot recover from.

**Calibration gate** (locked decision). Count the greenlit briefs:

```sql
SELECT COUNT(*) FROM content_briefs
 WHERE status IN ('ready','in_creation','gated','published');
```

While that count is ≤ `CALIBRATION_N = 3`, the brief is human-reviewed before the pod
picks it up — say so in the handoff (step 9) and in the journal. Past 3, briefs
auto-feed the pod at Tier 0 and the handoff is informational. The `status='ready'`
value is the same either way; what changes is whether a human looks first.

### 8. Flip the Topic

```sql
UPDATE topic_backlog
   SET status = 'briefed'
 WHERE id = ?
   AND status = 'approved';
```

`briefed` is in the `topic_backlog.status` CHECK list. The `AND status = 'approved'`
guard makes the write idempotent and keeps a concurrent content-researcher rescore from being
overwritten. This is the only write content-producer ever makes to `topic_backlog`.

### 9. Handoff to chief-of-staff

Mint the id — never `MAX(id)+1` (`docs/conventions.md` → Record IDs):

```bash
python3 scripts/ids.py content-producer handoff
```

Append to `state/journal/handoffs.md`:

```
## {ISO 8601 UTC} | content-producer → chief-of-staff | LOW: Brief ready — {working_title}

**Severity:** LOW
**Surface:** state/working/briefs/brief-{id:04d}.md (`content_briefs` id={id}, status=ready)
**Topic:** {topic_uid} — "{topic}" ({target_persona}, {funnel_stage})
**Type:** {net-new | refresh of {url}}
**Evidence:** {N} voice-bank entries across {M} distinct sources ({tiers})
**Primary keyword:** "{primary_keyword}" ({position or "untracked"}, vol {volume or "n/a"})
**Editorial gate:** {{HEAD_OF_MARKETING}} (backup {{CONTENT_LEAD}})
**Action required:** {Calibration review — brief {n}/3, {{HEAD_OF_MARKETING_FIRST}} reviews before the pod picks it up | None — calibration complete; brief auto-feeds creation-pod}
**Tier gate:** {2 while calibrating | 0 after}
```

And the row:

```sql
INSERT INTO handoffs (id, from_agent, to_agent, subject, body, severity, status, created_at)
VALUES ('{minted_id}', 'content-producer', 'chief-of-staff',
  'Brief ready — {working_title}',
  '{condensed body text}',
  'LOW', 'resolved', '{iso_now}');
```

LOW handoffs are inserted `resolved` per `docs/conventions.md` → Handoff Lifecycle;
they are informational and never count as stale. The calibration review is tracked by
the brief's own status, not by this row's lifecycle.

`{{HEAD_OF_MARKETING}}` and `{{CONTENT_LEAD}}` are profile tokens — write them as
tokens. `scripts/profile_render.py` fills them; a hard-coded name here is a bug.

## Output to Journal

Under `### Briefs Built` in the Tick entry (or as the body of a standalone-run entry):

```
[brief {id}] {topic_uid} "{working_title}" — {net-new | refresh of {url}}
  persona {persona} · tone {tone_code} · {word_count_target} words
  evidence: {N} entries / {M} distinct sources ({tiers}) · keyword "{primary}" (rung {1-4})
  → state/working/briefs/brief-{id:04d}.md · content_briefs id={id} status=ready
  → topic_backlog {topic_uid} status approved → briefed
```

Under `### Skipped`, one line per topic that did not produce a brief, with the reason
(evidence floor, duplicate of `{url}`, topic not `approved`).

Under `### Handoffs Written`, `- LOW Brief ready — {working_title} → chief-of-staff`.

## Verification (run before you call the brief done)

Adversarial, not confirmatory — try to break the output, and assume it is wrong until
each check has actually run:

1. **Re-read the row you just wrote.** Not the variables you held in memory:
   ```sql
   SELECT id, topic_id, working_title, target_persona, tone_code, primary_keyword,
          secondary_keywords, aeo_questions, word_count_target, brief_path, status
     FROM content_briefs WHERE id = ?;
   ```
   `brief_path` must point at a file that exists on disk, `status` must be `ready`,
   `target_persona` must be one of the three CHECK values, and `topic_id` must be the
   integer id of the topic you actually read — not its `topic_uid`, not its position
   in the queue.
2. **Re-read the topic:** `SELECT status FROM topic_backlog WHERE id = ?` → `briefed`.
   If it is still `approved`, the guard in step 8 rejected the write and the brief is
   orphaned; fix it before journaling.
3. **Grep the brief for `{{`.** Any surviving `{{placeholder}}` means a section was
   skipped. An unfilled template section is worse than an absent one — the pod will
   draft from it.
4. **Trace every quote back to a `voice_bank.id`.** If a quote in the brief is not
   character-for-character in the step-2 result set, it was invented; delete it.
5. **Ask what would make the refresh call wrong** — re-run the step-3 match with the
   primary keyword you finally chose, not the one you started with. Choosing the
   keyword changes the dedup answer, and a duplicate published as net-new is the
   expensive failure.
6. **Read the three working titles against the hard-fail list one at a time.** A
   banned term is easy to miss inside a title you just wrote.

## Failure Modes

- **Evidence below the floor** → stop, report, leave the topic `approved` (step 2).
  Never write a thin brief and flag it; the pod will draft from whatever it is given.
- **Fully covered by a live URL** → stop, hand back to content-researcher (step 3). Never
  write a duplicate brief.
- **`keyword_rankings` empty** → walk the fallback ladder, record the rung used. Never
  invent a search volume or a position.
- **AEO register unmatched** → candidate questions from the evidence bank, marked as
  candidates. Never write a prompt into the register.
- **Row written, file write failed** → the row is `draft` with `brief_path` NULL,
  which is the correct resting state. Log to `state/journal/ops-incidents.md`, do not
  commit partial state, and do not flip the topic to `briefed`.

## Database Reference

**Read-only:** `topic_backlog`, `topic_evidence`, `voice_bank` (content-researcher) ·
`keyword_rankings` (performance-marketer) · `content_inventory` (shared) · `handoffs` (chief-of-staff).

**Write:** `content_briefs` (one row per brief) · `handoffs` (one LOW row per brief) ·
`topic_backlog.status` only, `approved` → `briefed`.
