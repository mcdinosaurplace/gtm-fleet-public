-- 010_call_miner_ledger.sql
-- content-researcher call-miner intake ledger (Step 1 of the call-mining workflow;
-- see roster/content-researcher/skills/call-miner.md).
-- One row per Grain meeting call-miner has *decided on* — mined, mined-but-empty,
-- or skipped as off-target — so a meeting is never re-fetched or re-mined across
-- Ticks. The watermark (max research_packets.created_at for call_mining) and this
-- ledger together make ingestion idempotent. Overflow beyond the per-run cap is
-- ledgered as 'deferred' and re-merged into the candidate pool every run
-- (regardless of the watermark) until it is mined — so first-run backfill overflow
-- is never lost when the watermark advances. Owned by content-researcher.

-- ============================================================
-- content-researcher — CALL-MINER MEETING LEDGER (migration 010)
-- ============================================================

CREATE TABLE IF NOT EXISTS mined_meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'content-researcher',
    meeting_id      TEXT    NOT NULL UNIQUE,        -- Grain meeting id (idempotency key)
    title_redacted  TEXT,                           -- anonymized title for human scan
    meeting_date    TEXT,                           -- ISO 8601 start_datetime of the call
    outcome         TEXT    NOT NULL                -- what call-miner did with this meeting
                            CHECK (outcome IN ('mined','mined_empty','skipped_offtarget','deferred')),
    skip_reason     TEXT,                           -- partner_reseller | recruiting | internal_only |
                                                    --   bot_only | too_short | no_transcript |
                                                    --   no_host_gate | unknown_offtarget
    call_type       TEXT    CHECK (call_type IN
                            ('prospect_sales','customer','partner_reseller','recruiting','unknown')
                            OR call_type IS NULL),
    icp_persona     TEXT    CHECK (icp_persona IN ('aaron','erin','hannah','unknown')
                            OR icp_persona IS NULL),
    funnel_stage    TEXT    CHECK (funnel_stage IN ('top','mid','bottom') OR funnel_stage IS NULL),
    host            TEXT,                           -- matched internal host: ae | ceo | other
    company_size    TEXT,                           -- micro | smb | mid | unknown (ICP weight, not a gate)
    entries_written INTEGER NOT NULL DEFAULT 0,     -- voice_bank rows produced from this call
    packet_id       INTEGER,                        -- -> research_packets.id (not enforced)
    mined_at        TEXT    NOT NULL                -- ISO 8601
);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005/007/008/009; tick.py also INSERT OR IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('010_call_miner_ledger', datetime('now'));
