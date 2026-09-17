-- 012_topic_evidence.sql
-- Links each scored topic to the exact voice_bank rows that drove it, so
-- content-producer:brief-builder can bundle verbatim evidence instead of re-deriving it by
-- theme match. Written by content-researcher:topic-synthesizer during clustering (one row
-- per contributing voice_bank entry per topic); read by content-producer's brief-builder.
-- Owned by content-researcher.

-- ============================================================
-- content-researcher — TOPIC -> EVIDENCE LINK (migration 012)
-- ============================================================

CREATE TABLE IF NOT EXISTS topic_evidence (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id      INTEGER NOT NULL,        -- -> topic_backlog.id (not enforced)
    voice_bank_id INTEGER NOT NULL,        -- -> voice_bank.id (not enforced)
    created_at    TEXT    NOT NULL,        -- ISO 8601
    UNIQUE (topic_id, voice_bank_id)       -- idempotent re-synthesis
);

CREATE INDEX IF NOT EXISTS idx_topic_evidence_topic ON topic_evidence (topic_id);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005/007/008/009/010/011; tick.py also INSERT OR
-- IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('012_topic_evidence', datetime('now'));
