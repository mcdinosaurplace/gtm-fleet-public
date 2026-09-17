-- 006: GTM Scorecard frozen weekly snapshots.
-- Append-only: one row per metric per period per snapshot_date. Rows are
-- never updated; restatement detection compares across snapshot_dates.
-- Shared table: revops-watchdog writes funnel rows, performance-marketer writes traffic rows.

CREATE TABLE IF NOT EXISTS gtm_scorecard (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent              TEXT    NOT NULL,          -- 'revops-watchdog' | 'performance-marketer'
    snapshot_date      TEXT    NOT NULL,          -- YYYY-MM-DD (Friday run date)
    metric             TEXT    NOT NULL,          -- see docs/gtm-scorecard-definitions.md
    period             TEXT    NOT NULL,          -- YYYY-MM
    value              REAL,                      -- actual (complete month) or MTD
    is_complete        INTEGER NOT NULL DEFAULT 0,-- 1 = month closed at snapshot time
    projected          REAL,                      -- projection for incomplete months
    flag               TEXT,                      -- e.g. 'import_polluted', 'low-sample'
    definition_version TEXT    NOT NULL DEFAULT 'v1.0',
    created_at         TEXT    NOT NULL           -- ISO 8601
);

CREATE INDEX IF NOT EXISTS idx_gtm_scorecard_lookup
    ON gtm_scorecard (metric, period, snapshot_date);
