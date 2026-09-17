-- Migration: 001_init
-- Created: 2026-04-14
-- Description: Initialize Phase 1 schema — all 12 tables for chief-of-staff, revops-watchdog, and performance-marketer.
-- Run: sqlite3 state/working/fleet.db < state/working/migrations/001_init.sql

-- ============================================================
-- revops-watchdog TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS funnel_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT    NOT NULL DEFAULT 'revops-watchdog',
    snapshot_date TEXT  NOT NULL,
    mqls        INTEGER,
    sals        INTEGER,
    sqls        INTEGER,
    pipeline_value REAL,
    mql_to_sal_rate REAL,
    sal_to_sql_rate REAL,
    notes       TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT    NOT NULL,
    detected_at TEXT    NOT NULL,
    surface     TEXT    NOT NULL,
    metric      TEXT    NOT NULL,
    value       REAL,
    baseline    REAL,
    deviation_pct REAL,
    severity    TEXT    NOT NULL CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved')),
    resolved_at TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_health (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'revops-watchdog',
    check_date      TEXT    NOT NULL,
    workflow_id     TEXT    NOT NULL,
    workflow_name   TEXT,
    enrollments_24h INTEGER,
    exits_24h       INTEGER,
    first_step_exit_rate REAL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    flag            TEXT,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS scoring_drift (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'revops-watchdog',
    snapshot_date   TEXT    NOT NULL,
    median_score    REAL,
    top_decile_count INTEGER,
    top_decile_pct  REAL,
    distribution_json TEXT,
    drift_flag      INTEGER NOT NULL DEFAULT 0,
    drift_note      TEXT,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS opsos_signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'revops-watchdog',
    check_date      TEXT    NOT NULL,
    new_contacts_7d INTEGER,
    enriched_count  INTEGER,
    coverage_pct    REAL,
    field_coverage_json TEXT,
    flag            TEXT,
    created_at      TEXT    NOT NULL
);

-- ============================================================
-- performance-marketer TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS paid_creative (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'performance-marketer',
    platform        TEXT    NOT NULL,
    campaign_name   TEXT,
    ad_group        TEXT,
    creative_id     TEXT,
    headline        TEXT,
    description     TEXT,
    impressions     INTEGER,
    clicks          INTEGER,
    ctr             REAL,
    spend           REAL,
    conversions     INTEGER,
    cpl             REAL,
    status          TEXT,
    snapshot_date   TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'performance-marketer',
    name            TEXT    NOT NULL,
    platform        TEXT,
    hypothesis      TEXT,
    variant_a       TEXT,
    variant_b       TEXT,
    start_date      TEXT,
    end_date        TEXT,
    status          TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    outcome         TEXT,
    notes           TEXT,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS spend_alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'performance-marketer',
    detected_at     TEXT    NOT NULL,
    platform        TEXT    NOT NULL,
    campaign_name   TEXT,
    metric          TEXT    NOT NULL,
    value           REAL,
    baseline        REAL,
    deviation_pct   REAL,
    severity        TEXT    NOT NULL CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    description     TEXT,
    status          TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved')),
    resolved_at     TEXT,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS keyword_rankings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'performance-marketer',
    snapshot_date   TEXT    NOT NULL,
    keyword         TEXT    NOT NULL,
    position        INTEGER,
    prior_position  INTEGER,
    position_delta  INTEGER,
    search_volume   INTEGER,
    url             TEXT,
    flag            TEXT,
    created_at      TEXT    NOT NULL
);

-- ============================================================
-- chief-of-staff / SHARED TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL,
    context         TEXT    NOT NULL,
    decision        TEXT    NOT NULL,
    approved_by     TEXT    NOT NULL DEFAULT 'scott',
    approved_at     TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS handoffs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent      TEXT    NOT NULL,
    to_agent        TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    body            TEXT,
    severity        TEXT    CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    status          TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'resolved')),
    created_at      TEXT    NOT NULL,
    acknowledged_at TEXT,
    resolved_at     TEXT
);

CREATE TABLE IF NOT EXISTS approvals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL,
    tier            INTEGER NOT NULL CHECK (tier IN (2, 3)),
    draft_type      TEXT    NOT NULL,
    draft_content   TEXT,
    draft_path      TEXT,
    slack_channel   TEXT,
    slack_thread_ts TEXT,
    approver        TEXT,
    approved_at     TEXT,
    status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'approved', 'rejected', 'needs_edit', 'expired')),
    edit_notes      TEXT,
    created_at      TEXT    NOT NULL
);

-- Record that this migration was applied
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT    PRIMARY KEY,
    applied_at  TEXT    NOT NULL
);

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('001_init', datetime('now'));
