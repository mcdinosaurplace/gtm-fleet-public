-- 016_mined_meetings_deferred_outcome.sql
-- Fixes schema drift: the live mined_meetings table (created by migration 010)
-- was left with a CHECK constraint that never included 'deferred', even though
-- 010_call_miner_ledger.sql on disk documents 'deferred' as a valid outcome and
-- the call-miner skill (roster/content-researcher/skills/call-miner.md, Step 1.7) depends
-- on it for cap-overflow rows. SQLite can't ALTER a CHECK constraint in place,
-- so recreate the table with the corrected constraint and copy existing rows.
-- Owned by content-researcher (mined_meetings is content-researcher's table).

CREATE TABLE mined_meetings_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'content-researcher',
    meeting_id      TEXT    NOT NULL UNIQUE,
    title_redacted  TEXT,
    meeting_date    TEXT,
    outcome         TEXT    NOT NULL
                            CHECK (outcome IN ('mined','mined_empty','skipped_offtarget','deferred')),
    skip_reason     TEXT,
    call_type       TEXT    CHECK (call_type IN
                            ('prospect_sales','customer','partner_reseller','recruiting','unknown')
                            OR call_type IS NULL),
    icp_persona     TEXT    CHECK (icp_persona IN ('aaron','erin','hannah','unknown')
                            OR icp_persona IS NULL),
    funnel_stage    TEXT    CHECK (funnel_stage IN ('top','mid','bottom') OR funnel_stage IS NULL),
    host            TEXT,
    company_size    TEXT,
    entries_written INTEGER NOT NULL DEFAULT 0,
    packet_id       INTEGER,
    mined_at        TEXT    NOT NULL
);

INSERT INTO mined_meetings_new SELECT * FROM mined_meetings;

DROP TABLE mined_meetings;

ALTER TABLE mined_meetings_new RENAME TO mined_meetings;

CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('016_mined_meetings_deferred_outcome', datetime('now'));
