-- 009_paid_applied_changes.sql
-- performance-marketer paid-execution rollback ledger.
-- One row per auto-applied (live) or simulated (shadow) Tier-3a change. prior_value
-- is the JSON snapshot needed to reverse it. Owned by performance-marketer.

-- ============================================================
-- performance-marketer — APPLIED CHANGES (rollback ledger, migration 009)
-- ============================================================

CREATE TABLE IF NOT EXISTS applied_changes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    agent          TEXT    NOT NULL DEFAULT 'performance-marketer',
    proposal_id    INTEGER NOT NULL,                -- -> paid_change_proposals.id (not enforced)
    approval_ref   TEXT,                            -- greenlight record: decisions/approvals id or Scott->performance-marketer handoff
    platform       TEXT    NOT NULL CHECK (platform IN ('google_ads','linkedin')),
    entity         TEXT    NOT NULL,                -- resource_name acted on
    op_type        TEXT    NOT NULL                 -- 3a allowlist (scripts/paid/config.py)
                           CHECK (op_type IN ('add_negative','set_bid','match_type_promotion','create_experiment')),
    prior_value    TEXT    NOT NULL,                -- JSON snapshot for rollback
    new_value      TEXT    NOT NULL,                -- JSON of the applied state
    mode           TEXT    NOT NULL CHECK (mode IN ('shadow','live')),
    applied_at     TEXT    NOT NULL,                -- ISO 8601
    rolled_back_at TEXT,                            -- ISO 8601; set when reversed
    created_at     TEXT    NOT NULL                 -- ISO 8601
);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005/007/008; tick.py also INSERT OR IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('009_paid_applied_changes', datetime('now'));
