# Skill: notion-topic-sync

Two-way sync between content-researcher's `topic_backlog` and the Notion review database
where {{HEAD_OF_MARKETING_FIRST}} rules on content topics. Pulls his decisions into local state, then
pushes current repo state back out.

Runs on **every** Scribe tick (Monday stand-up, Tue–Fri pulse, Wednesday WBR) and
standalone via `/scribe notion-topic-sync`. The point of the per-tick cadence is
latency: content-researcher only runs Mondays, so if decisions were only harvested weekly a
Thursday approval would wait until the following Monday before content-producer could build
against it. Running here puts it at roughly a day, or immediately on a manual
invocation.

## Surfaces

| Thing | ID |
|---|---|
| Parent page | `{{NOTION_COLLECTION_ID}}` (Marketing → Content Engine) |
| Database | `{{NOTION_TOPIC_BACKLOG_PAGE_ID}}` (Topic Backlog) |
| Data source | `collection://{{NOTION_TOPIC_BACKLOG_DB_ID}}` |

## Preflight

- Scribe Librarian steps per `roster/scribe/prompt.md`, including pending migrations.
  This skill requires migration `018_topic_backlog_notion_sync` (adds `topic_uid`,
  `review_notes`, `notion_page_id`, `notion_synced_at`, and the `needs_edit` status).
  If it has not been applied, abort — do not attempt the sync against the old schema.
- **MCP: Notion essential.** Abort before any write if it fails to bind after the
  three preflight attempts; log `MCP_BIND_FAILURE` per `docs/mcp-preflight.md`. A
  skipped sync is recoverable (next tick catches up); a half-applied one is not.
- Slack is **optional** here. It carries only the "new topics to review" pointer;
  if Slack is down, sync anyway and note the un-sent pointer.

## Order of operations is load-bearing

**Pull first, then push.** Both directions touch `Status`. If push ran first it
would overwrite a decision {{HEAD_OF_MARKETING_FIRST}} made since the last tick with the repo's stale
value, silently discarding his ruling. Pull, then push. Never the reverse.

## Who wins on conflict

One `Status` property is shared, so precedence has to be explicit. The two sets
are disjoint, which is what makes this safe:

| Status value | Authority | Direction |
|---|---|---|
| `Approved`, `Needs revision`, `Rejected` | **Notion ({{HEAD_OF_MARKETING_FIRST}})** | Notion → repo |
| `Pending review`, `Candidate`, `Briefed`, `Published`, `Refresh` | **Repo (agents)** | repo → Notion |

Consequence: the push pass **must not write `Status`** for any row whose Notion
value is currently one of {{HEAD_OF_MARKETING_FIRST}}'s three. `Comments` is {{HEAD_OF_MARKETING_FIRST}}'s alone — never written
by the push pass, in any circumstance.

---

## Pass 1 — Pull decisions (Notion → repo)

1. **Query the data source** for rows whose `Status` is one of `Approved`,
   `Needs revision`, `Rejected`. Read `Topic UID`, `Status`, `Comments`, and the
   page id.

2. **Discard rows with an empty or malformed `Topic UID`.** A blank UID means the
   row was hand-created in Notion rather than synced from the repo, or someone
   edited the key despite the warning. Do not guess the match by title — titles
   are editable and duplicated titles are possible. Log each discarded row and
   surface it in the journal; if any appear, include them in the handoff so
   content-researcher knows a decision was made that never reached local state.

3. **Apply via the shared core.** Do not write `topic_backlog` by hand — it is
   content-researcher's table and the decision semantics live in one place:

   ```bash
   python3 scripts/topic_review.py apply --json '[{"uid": "...", "status": "Approved",
     "comments": "...", "notion_page_id": "..."}, ...]'
   ```

   It is idempotent — re-applying an unchanged decision reports `unchanged` and
   writes nothing, which is why running this every tick is safe. It stamps
   `approved_at`, writes `review_notes`, and inserts one `approvals` row per
   decision as the Tier 2 gate record. Exit 2 means bad input (stop and log);
   exit 1 means nothing matched.

4. **Read the returned JSON** and count `applied` vs `unchanged` vs `no_match`.
   Only `applied` rows are news.

## Pass 2 — Push state (repo → Notion)

5. **Select rows to push.** Every row in `topic_backlog`. Rows with
   `notion_page_id IS NULL` are created; the rest are updated. Full-set push is
   deliberate — it needs no `updated_at` column and is self-healing if a prior
   tick died mid-run. Log a cap note if the table ever exceeds 100 rows so the
   batching question surfaces before it becomes a timeout.

6. **On create** — one page per row, properties from the table below, plus the
   body template. Record the returned page id:

   ```sql
   UPDATE topic_backlog SET notion_page_id = ?, notion_synced_at = datetime('now')
    WHERE topic_uid = ?;
   ```

7. **On update** — write only agent-owned properties:

   | Notion property | Source | Pushed on update? |
   |---|---|---|
   | `Topic` | `topic` | yes |
   | `Score` | `score_total` | yes |
   | `Persona` | `target_persona` | yes |
   | `Funnel stage` | `funnel_stage` | yes |
   | `Content type` | `content_type` | yes |
   | `Evidence count` | `evidence_sources` | yes |
   | `Evidence summary` | `evidence_summary` | yes |
   | `Topic UID` | `topic_uid` | on create only — never rewritten |
   | `Synced at` | now | yes |
   | `Status` | `status` (mapped) | **only if Notion's current value is agent-owned** |
   | `Comments` | — | **never** |

   Status map, repo → Notion: `candidate`→`Candidate`, `submitted`→`Pending review`,
   `approved`→`Approved`, `rejected`→`Rejected`, `needs_edit`→`Needs revision`,
   `briefed`→`Briefed`, `published`→`Published`, `refresh`→`Refresh`.

   **`Briefed` is derived, not stored.** `content-producer:brief-builder` is forbidden from
   writing `topic_backlog`, so an approved topic keeps `status='approved'` in the repo
   even after content-producer has built its brief. Without the override below, {{HEAD_OF_MARKETING_FIRST}} would see
   "Approved" forever and have no way to tell what had actually been picked up.
   So on push, before mapping status, check for downstream work:

   ```sql
   SELECT topic_id FROM content_briefs WHERE topic_id = ?;   -- read-only
   ```

   If a brief exists, push `Briefed` instead of `Approved`. This keeps the
   read-only boundary intact — Scribe reads `content_briefs`, and nobody writes
   `topic_backlog` to record a fact that is already derivable from it. The
   `briefed` / `published` values in the repo enum stay unused for now; if a future
   agent starts setting them, this override becomes redundant rather than wrong.

8. **Body rewrites are the exception, not the rule.** Write the body on create.
   On update, rewrite it only when the row was rescored — detect by comparing
   repo `score_total` / `evidence_sources` against the Notion property values
   already in hand from pass 1's query. Rewriting an unchanged body every tick
   churns Notion's edit history for nothing and makes real changes hard to spot.

9. **Stamp `notion_synced_at`** for every row successfully pushed.

## Page body template

Follow `docs/notion-markdown-syntax.md` — XML-tag callouts, tab-indented nesting,
`{toggle="true"}` on headings. Never `>` blockquotes or `<details>`.

Sections, in order:
1. Callout: the ask (set `Status`; put reactions in `Comments`, plain language is fine).
2. **What the evidence says** — the pattern in 2–4 sentences, plain language.
3. **Suggested angle** — the editorial hook in one paragraph.
4. **The quotes** — verbatim evidence from `topic_evidence` → `voice_bank`, grouped
   thematically under toggle headings, each group named for what it shows. State the
   total linked count and that the displayed set is the most on-point, whenever it is
   a subset. Quotes are already anonymized in `voice_bank`; do not re-identify.
5. **Score breakdown** — table of the five dimensions with a one-line rationale each.
6. Callout: source of truth (`topic_uid`, and the `state/pending/` submission path).

Note the Search-capped caveat wherever a score is shown, while
`keyword_rankings` remains empty (performance-marketer's GSC 403).

## Slack pointer

If pass 1 or pass 2 produced news — any newly created page, or any `applied`
decision — post one short message to `#team-marketing` with a link to the
**Review Queue** view. Post the pointer, never the topics themselves; the whole
point is that Notion is where review happens.

Suppress the post when there is no news. A recurring "0 new topics" message
trains people to ignore the channel.

## Journal

Append to `state/journal/scribe.md` (or `state/journal/scribe_project_management.md`
on a PM tick, matching that tick's convention):

```
### Notion topic sync
Pulled: {N} applied ({breakdown by decision}), {N} unchanged, {N} unmatched UID
Pushed: {N} created, {N} updated, {N} bodies refreshed
Slack pointer: {sent | suppressed, no news | unsent, Slack unbound}
```

## Handoff to content-researcher

Only when pass 1 applied at least one decision. content-researcher needs it for scoring
calibration and to fold `needs_edit` notes into the next synthesis — the state is
already applied, so this is notification, not a request:

```
## {timestamp} | Scribe -> content-researcher | LOW: {{HEAD_OF_MARKETING_FIRST}}'s topic rulings applied from Notion

**Severity:** LOW (informational; state already applied)
**Surface:** topic_backlog + approvals (via scripts/topic_review.py)
**Summary:** {N} rulings: {N} approved, {N} needs_edit, {N} rejected. {Topics with
review_notes, listed.} Rejection reasons for calibration: {...}
**Action required:** Fold rejection patterns into scoring bias; incorporate
needs_edit notes in next submission. No re-application needed.
**Tier gate:** n/a
```

Write it with `status='resolved'` at insert per the LOW-handoff rule in
`docs/conventions.md`.

## Boundary rules

- **Never write `topic_backlog` directly.** Always through `scripts/topic_review.py`.
- **Never write `Comments`.** It is {{HEAD_OF_MARKETING_FIRST}}'s field. Reading it is the whole point.
- **Never rewrite `Topic UID`** after create. It is the sync key; changing it
  orphans the row from its repo record.
- **Never delete Notion pages.** A topic dropped from `topic_backlog` (which does
  not currently happen) stays in Notion as history; flag the divergence instead.
- **Do not invent topics.** This skill mirrors and harvests. All topic creation is
  `content-researcher:topic-synthesizer`.
- **Do not act on a decision beyond applying it.** Briefing an approved topic is
  `content-producer:brief-builder`, which picks it up on its own from `status='approved'`.

## Acceptance

- Every `topic_backlog` row has a non-null `notion_page_id` and `notion_synced_at`.
- No row's Notion `Status` was overwritten while holding one of {{HEAD_OF_MARKETING_FIRST}}'s three values.
- `Comments` is byte-identical before and after the run.
- Re-running immediately reports all `unchanged` / `0 created` and sends no Slack.
- Every applied decision has exactly one matching `approvals` row.
