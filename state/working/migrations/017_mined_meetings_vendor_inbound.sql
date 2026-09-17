-- 017_mined_meetings_vendor_inbound.sql
-- Adds a `vendor_inbound` class to the mined_meetings.call_type CHECK.
--
-- DEFECT — `call_type` has no class for an inbound vendor pitch.
--   A call where the only external participant is a consultant pitching tooling TO
--   GTM Fleet's own leadership team scopes as participant_scope='external' and clears
--   the call-miner 1.5(b) unknown-path host gate whenever a founder sits in, so it
--   would be mined and the vendor's own pitch language stored as market voice. The
--   1.3 bot-only filter does not catch it (the pitcher is a genuine external human).
--   Adding 'vendor_inbound' gives step 1.4 somewhere to classify it so 1.5 can skip
--   it. Found live on 2026-07-27 against a consultant pitching an internal tooling
--   product to GTM Fleet's leadership team.
--
-- History: this fix was originally authored alongside the `outcome` / 'deferred'
-- CHECK fix in PR #19 as a combined migration 016. That PR was superseded — the
-- 'deferred' half landed independently as 016_mined_meetings_deferred_outcome.sql
-- while #19 sat open, and #19's binary db conflicted against 45 state-bot commits.
-- This migration carries forward only the half that never landed.
--
-- SQLite cannot ALTER a CHECK constraint, so this rebuilds the table and copies rows
-- forward. Column order, types, defaults and the meeting_id UNIQUE idempotency key
-- are preserved exactly. Owned by content-researcher (mined_meetings is content-researcher's table).

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
                            ('prospect_sales','customer','partner_reseller','recruiting',
                             'vendor_inbound','unknown')
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
VALUES ('017_mined_meetings_vendor_inbound', datetime('now'));
