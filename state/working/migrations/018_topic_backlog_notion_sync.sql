-- 018_topic_backlog_notion_sync.sql
-- Prepares topic_backlog to be mirrored into a Notion review database (parent:
-- Marketing teamspace -> Content Engine -> Topic Backlog), where Maya sets a
-- review status and leaves comments that flow back into this table.
--
-- Two fixes and four additions:
--
-- 1. status CHECK gains 'needs_edit'. The constraint has never included it, yet
--    roster/content-researcher/prompt.md (Librarian step 3) instructs content-researcher to handle
--    `needs_edit` on topic_backlog rows, and the approvals table has carried a
--    'needs_edit' status since migration 007. The first "Needs Revision" ruling
--    from Maya would have hard-failed on this constraint. Same defect class as
--    016 (mined_meetings could not store 'deferred' though call-miner required
--    it) — caught here before it could fail mid-Tick rather than after.
--
-- 2. topic_uid TEXT UNIQUE — the Notion sync key. topic_backlog was NOT covered
--    by migration 015_textual_ids, so its id is still INTEGER AUTOINCREMENT.
--    docs/conventions.md forbids MAX(id)+1 ids precisely because uncoordinated
--    writers collide and then get renumbered by hand on merge. A renumber is
--    survivable while ids live only in this repo; once Notion pages are keyed to
--    them it would silently re-point rows at the wrong topics with nothing to
--    surface the error. Observed live on 2026-08-03: a content-researcher Tick and a
--    Scribe Tick raced on main, content-researcher's DB writes were
--    discarded and replayed onto Scribe's, and the replayed topic rows landed on
--    new integer ids. Ids minted via scripts/ids.py ("content-researcher topic") are
--    unique without coordination and survive that replay unchanged.
--    Left nullable here (SQL cannot mint); backfilled immediately after apply,
--    and topic-synthesizer mints one per INSERT going forward.
--
-- 3. review_notes TEXT — Maya's free-text reaction, pulled back from Notion as
--    *instruction for the next synthesis*, never as an in-place overwrite of
--    `topic`. topic-synthesizer dedups on the `topic` string (step 1), so
--    letting a human rewrite silently replace it would make the next run compare
--    clusters against the new phrasing and re-mint the original as "net-new".
--
-- 4. notion_page_id / notion_synced_at TEXT — the mirrored page and last
--    successful push, so the sync is resumable and can detect drift.
--
-- Integer `id` is preserved verbatim (INSERT ... SELECT with an explicit column
-- list) because topic_evidence.topic_id references it — 139 rows as of this
-- migration. Owned by content-researcher (topic_backlog is content-researcher's table); the
-- recurring Notion read/write is Scribe's, which already holds Notion as an
-- essential connector.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step), or
--   manually: sqlite3 state/working/fleet.db < state/working/migrations/018_topic_backlog_notion_sync.sql

CREATE TABLE topic_backlog_new (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    agent            TEXT    NOT NULL DEFAULT 'content-researcher',
    topic_uid        TEXT    UNIQUE,       -- scripts/ids.py mint; Notion sync key, never edited in Notion
    topic            TEXT    NOT NULL,
    target_persona   TEXT    NOT NULL DEFAULT 'aaron'
                             CHECK (target_persona IN ('aaron','erin','hannah')),
    funnel_stage     TEXT    CHECK (funnel_stage IN ('top','mid','bottom')),
    content_type     TEXT,
    score_total      INTEGER,
    score_icp        INTEGER,
    score_search     INTEGER,
    score_aeo        INTEGER,
    score_evidence   INTEGER,
    score_education  INTEGER,
    evidence_summary TEXT,
    evidence_sources INTEGER NOT NULL DEFAULT 0,
    status           TEXT    NOT NULL DEFAULT 'candidate'
                             CHECK (status IN ('candidate','submitted','approved','rejected',
                                               'needs_edit','briefed','published','refresh')),
    review_notes     TEXT,                 -- Maya's prose, as instruction for next synthesis
    approved_at      TEXT,
    notion_page_id   TEXT,                 -- mirrored Notion page
    notion_synced_at TEXT,                 -- last successful push
    created_at       TEXT    NOT NULL
);

INSERT INTO topic_backlog_new (
    id, agent, topic, target_persona, funnel_stage, content_type,
    score_total, score_icp, score_search, score_aeo, score_evidence, score_education,
    evidence_summary, evidence_sources, status, approved_at, created_at
)
SELECT
    id, agent, topic, target_persona, funnel_stage, content_type,
    score_total, score_icp, score_search, score_aeo, score_evidence, score_education,
    evidence_summary, evidence_sources, status, approved_at, created_at
FROM topic_backlog;

DROP TABLE topic_backlog;

ALTER TABLE topic_backlog_new RENAME TO topic_backlog;

CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('018_topic_backlog_notion_sync', datetime('now'));
