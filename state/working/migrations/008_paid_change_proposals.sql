-- 008_paid_change_proposals.sql
-- performance-marketer paid-execution loop.
-- One row per proposed paid-media move in an optimization dossier. Records the
-- deterministic bucket from scripts/paid/classify.py, the move's lifecycle
-- status, and the prior/target values needed to execute and later roll back.
-- Owned by performance-marketer.

-- ============================================================
-- performance-marketer — PAID CHANGE PROPOSALS (migration 008)
-- ============================================================

CREATE TABLE IF NOT EXISTS paid_change_proposals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent         TEXT    NOT NULL DEFAULT 'performance-marketer',
    dossier_date  TEXT    NOT NULL,                 -- YYYY-MM-DD (the dossier this move belongs to)
    platform      TEXT    NOT NULL CHECK (platform IN ('google_ads','linkedin')),
    campaign_name TEXT,
    bucket        TEXT    NOT NULL                  -- from scripts/paid/classify.py
                          CHECK (bucket IN ('auto_3a','human_3b','creative')),
    op_type       TEXT    NOT NULL                  -- recognized move kinds (classify.py contract)
                          CHECK (op_type IN ('add_negative','set_bid','match_type_promotion',
                                             'create_experiment','pause_ad','budget',
                                             'bid_strategy','cross_channel','creative')),
    summary       TEXT    NOT NULL,                 -- human-readable description of the move
    reason        TEXT,                             -- classifier's rationale for the bucket
    prior_value   TEXT,                             -- JSON snapshot of current state (for execution + rollback)
    target_value  TEXT,                             -- JSON of the proposed new state
    reversal_if   TEXT,                             -- abort condition that should trigger rollback
    linear_ref    TEXT,                             -- creative bucket only: copy-review issue (e.g. MAR-7076)
    approval_id   INTEGER,                          -- -> approvals.id once greenlit (not enforced)
    status        TEXT    NOT NULL DEFAULT 'proposed'
                          CHECK (status IN ('proposed','greenlit','applied',
                                            'awaiting_creative','rejected','rolled_back')),
    decided_at    TEXT,                             -- ISO 8601; set when status leaves 'proposed'
    created_at    TEXT    NOT NULL                  -- ISO 8601
);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005/007; tick.py also INSERT OR IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('008_paid_change_proposals', datetime('now'));
