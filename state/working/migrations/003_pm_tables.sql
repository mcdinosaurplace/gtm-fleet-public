-- Migration: 003_pm_tables
-- Created: 2026-06-08
-- Description: Marketing PM data layer (Scribe extension). Tables for stand-up
--   capture, commitment classification + tracking, Linear project/issue health,
--   blockers, external dependencies, missed-deadline docs, and the RCA index.
--   House conventions: TEXT dates (YYYY-MM-DD), ISO-8601 TEXT timestamps, 0/1
--   INTEGER booleans, CHECK enums, no enforced foreign keys (relationships noted
--   in comments), created_at + agent on every table. Owner agent: Scribe.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step 5),
--   or manually: sqlite3 state/working/fleet.db < state/working/migrations/003_pm_tables.sql

-- ============================================================
-- SCRIBE — MARKETING PM TABLES
-- ============================================================

-- Canonical project list + current state. Keyed by Linear project ID.
CREATE TABLE IF NOT EXISTS pm_projects (
    id                        TEXT    PRIMARY KEY,        -- Linear project ID
    agent                     TEXT    NOT NULL DEFAULT 'scribe',
    name                      TEXT    NOT NULL,
    owner                     TEXT    NOT NULL,           -- marketing team member
    outcome                   TEXT,                       -- GTM Fleet Way: the result being delivered
    quality_bar               TEXT,                       -- GTM Fleet Way: standard not to be compromised
    original_due_date         TEXT,                       -- YYYY-MM-DD; IMMUTABLE once set (no-reschedule rule)
    current_target_date       TEXT,                       -- YYYY-MM-DD; may shift via milestones (communication only)
    health                    TEXT    CHECK (health IN ('on_track','at_risk','off_track')),
    health_source             TEXT    CHECK (health_source IN ('owner','agent_suggested')),
    brief_link                TEXT,                       -- Google Doc URL
    linear_link               TEXT,                       -- Linear project URL
    short_description         TEXT    CHECK (short_description IS NULL OR length(short_description) <= 280),
    closed_at                 TEXT,                       -- ISO 8601
    off_track_acknowledged_at TEXT,                       -- ISO 8601 (GTM Fleet Way off-track playbook step 1)
    off_track_decision        TEXT    CHECK (off_track_decision IN ('recover','reduce_scope','cancel')),
    rca_required              INTEGER NOT NULL DEFAULT 0, -- 0/1
    rca_link                  TEXT,
    last_synced_at            TEXT,                       -- ISO 8601; last pulse-check sync
    created_at                TEXT    NOT NULL            -- ISO 8601 (row creation)
);

-- All marketing-labeled Linear issues, including orphans (no parent project).
-- Keyed by Linear issue ID.
CREATE TABLE IF NOT EXISTS pm_issues (
    id                TEXT    PRIMARY KEY,                -- Linear issue ID
    agent             TEXT    NOT NULL DEFAULT 'scribe',
    project_id        TEXT,                               -- -> pm_projects.id (not enforced); NULL for orphans
    title             TEXT    NOT NULL,
    owner             TEXT,                               -- nullable; flagged if missing
    status            TEXT,                               -- raw Linear status
    state             TEXT    CHECK (state IN ('active','stale','blocked','closed')),  -- computed
    due_date          TEXT,                               -- YYYY-MM-DD; nullable
    linear_link       TEXT    NOT NULL,
    short_description TEXT    CHECK (short_description IS NULL OR length(short_description) <= 280),
    last_activity_at  TEXT,                               -- ISO 8601 (from Linear)
    closed_at         TEXT,                               -- ISO 8601
    last_synced_at    TEXT,                               -- ISO 8601; last pulse-check sync
    created_at        TEXT    NOT NULL                    -- ISO 8601 (row creation)
);

-- Blocker history. Links to either a project or a standalone issue.
CREATE TABLE IF NOT EXISTS pm_blockers (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    agent            TEXT    NOT NULL DEFAULT 'scribe',
    project_id       TEXT,                                -- -> pm_projects.id (not enforced)
    issue_id         TEXT,                                -- -> pm_issues.id (not enforced)
    opened_at        TEXT,                                -- ISO 8601
    resolved_at      TEXT,                                -- ISO 8601
    description      TEXT,
    resolution_notes TEXT,
    created_at       TEXT    NOT NULL,                    -- ISO 8601
    CHECK (project_id IS NOT NULL OR issue_id IS NOT NULL)
);

-- One row per Monday stand-up. Anchors the thread so later Ticks can re-read it.
CREATE TABLE IF NOT EXISTS pm_standup_threads (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    agent            TEXT    NOT NULL DEFAULT 'scribe',
    week_starting    TEXT    NOT NULL,                    -- YYYY-MM-DD (Monday)
    channel_id       TEXT    NOT NULL,                    -- resolved #team-marketing id
    master_ts        TEXT    NOT NULL,                    -- Slack ts of the master post (thread anchor)
    master_posted_at TEXT    NOT NULL,                    -- ISO 8601
    sweep_done_at    TEXT,                                -- ISO 8601
    created_at       TEXT    NOT NULL,
    UNIQUE (week_starting)
);

-- One row per team member per stand-up. Parsed shorthand only; raw -> PM journal.
CREATE TABLE IF NOT EXISTS pm_standup_responses (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                TEXT    NOT NULL DEFAULT 'scribe',
    week_starting        TEXT    NOT NULL,                -- YYYY-MM-DD
    owner                TEXT    NOT NULL,
    slack_user_id        TEXT,                            -- resolved at capture
    last_week            TEXT,
    this_week            TEXT,
    blockers             TEXT,
    linear_links_present INTEGER NOT NULL DEFAULT 0,      -- 0/1
    responded_at         TEXT,                            -- ISO 8601; NULL until they reply
    created_at           TEXT    NOT NULL,
    UNIQUE (week_starting, owner)
);

-- Stand-up commitment tracking. Resolves to Linear (by ref or by name) and spans
-- multiple stand-ups when anchored to a project/issue entity.
CREATE TABLE IF NOT EXISTS pm_commitments (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                  TEXT    NOT NULL DEFAULT 'scribe',
    week_starting          TEXT    NOT NULL,              -- YYYY-MM-DD (stand-up it was stated in)
    owner                  TEXT    NOT NULL,
    commitment             TEXT    NOT NULL,              -- the "this week" item, short
    linear_link            TEXT,                          -- canonical URL once resolved
    linear_ref_type        TEXT    CHECK (linear_ref_type IN ('project','issue')),
    project_id             TEXT,                          -- resolved -> pm_projects.id (not enforced)
    issue_id               TEXT,                          -- resolved -> pm_issues.id (not enforced)
    resolution             TEXT    CHECK (resolution IN ('by_ref','by_name','confirmed','unresolved')),
    scale                  TEXT    CHECK (scale IN ('project','task','incidental')),
    acknowledged_untracked INTEGER NOT NULL DEFAULT 0,    -- 0/1
    nudged_at              TEXT,                           -- ISO 8601; one-time clarify/untracked check
    horizon                TEXT    CHECK (horizon IN ('this_week','multi_week')),
    effective_due_date     TEXT,                           -- YYYY-MM-DD: linked entity's due date, else end-of-week
    completion_status      TEXT    NOT NULL DEFAULT 'pending'
                                   CHECK (completion_status IN ('pending','in_flight','carried','completed','partial','missed')),
    evaluated_at           TEXT,                           -- ISO 8601
    created_at             TEXT    NOT NULL
);

-- External (agency / partner / vendor) dependencies surfaced in stand-up.
CREATE TABLE IF NOT EXISTS pm_external_dependencies (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    agent             TEXT    NOT NULL DEFAULT 'scribe',
    week_starting     TEXT    NOT NULL,                   -- YYYY-MM-DD
    internal_owner    TEXT    NOT NULL,                   -- marketing team member on the hook
    external_party    TEXT,                               -- agency or partner name
    description       TEXT,
    owner_side_action TEXT,                               -- what we owe to unblock
    expected_delivery TEXT,                               -- YYYY-MM-DD
    linear_link       TEXT,
    status            TEXT    NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending','delivered','overdue','cancelled')),
    resolved_at       TEXT,                               -- ISO 8601
    created_at        TEXT    NOT NULL
);

-- Missed-deadline explanations (projects only).
CREATE TABLE IF NOT EXISTS pm_missed_deadlines (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                TEXT    NOT NULL DEFAULT 'scribe',
    project_id           TEXT    NOT NULL,                -- -> pm_projects.id (not enforced)
    original_due_date    TEXT,                            -- YYYY-MM-DD (the missed date)
    detected_at          TEXT,                            -- ISO 8601 (agent noticed the slip)
    prompted_at          TEXT,                            -- ISO 8601 (agent DMed the owner)
    acknowledged_at      TEXT,                            -- ISO 8601 (owner's explanation landed)
    explanation          TEXT,                            -- one-paragraph owner narrative
    linear_comment_link  TEXT,                            -- direct link to the Linear comment
    surfaced_in_thursday INTEGER NOT NULL DEFAULT 0,      -- 0/1 (true if 48h passed without explanation)
    created_at           TEXT    NOT NULL
);

-- RCA index.
CREATE TABLE IF NOT EXISTS pm_rca_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    agent            TEXT    NOT NULL DEFAULT 'scribe',
    project_id       TEXT,                                -- -> pm_projects.id (not enforced)
    rca_trigger      TEXT,                                -- which RCA trigger fired
    rca_link         TEXT,                                -- URL to the RCA doc (Notion)
    process_changes  TEXT,
    owner_of_changes TEXT,
    created_at       TEXT    NOT NULL                     -- ISO 8601
);

-- Record this migration (idempotent; the runner also records it).
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('003_pm_tables', datetime('now'));
