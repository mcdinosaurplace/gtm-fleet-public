-- Migration: 005_pm_block_c
-- Created: 2026-06-08
-- Description: Block C schema prep.
--   (1) pm_projects.owner_source — provenance for the pulse owner mapping, incl.
--       external-led projects defaulted to an internal owner (Maya Lindqvist).
--   (2) Extend pm_commitments.completion_status with 'dropped' (cancelled linked
--       work — neither delivered nor missed). SQLite can't ALTER a CHECK, so the
--       table is rebuilt (it is empty in production at this point). Owner: Scribe.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step 5).

ALTER TABLE pm_projects ADD COLUMN owner_source TEXT
    CHECK (owner_source IN ('lead','member','external_default','external_declared','unassigned'));

-- Rebuild pm_commitments to add 'dropped' to the completion_status CHECK.
CREATE TABLE pm_commitments_new (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                  TEXT    NOT NULL DEFAULT 'scribe',
    week_starting          TEXT    NOT NULL,
    owner                  TEXT    NOT NULL,
    commitment             TEXT    NOT NULL,
    linear_link            TEXT,
    linear_ref_type        TEXT    CHECK (linear_ref_type IN ('project','issue')),
    project_id             TEXT,
    issue_id               TEXT,
    resolution             TEXT    CHECK (resolution IN ('by_ref','by_name','confirmed','unresolved')),
    scale                  TEXT    CHECK (scale IN ('project','task','incidental')),
    acknowledged_untracked INTEGER NOT NULL DEFAULT 0,
    nudged_at              TEXT,
    horizon                TEXT    CHECK (horizon IN ('this_week','multi_week')),
    effective_due_date     TEXT,
    completion_status      TEXT    NOT NULL DEFAULT 'pending'
                                   CHECK (completion_status IN ('pending','in_flight','carried','completed','partial','missed','dropped')),
    evaluated_at           TEXT,
    created_at             TEXT    NOT NULL
);
INSERT INTO pm_commitments_new SELECT * FROM pm_commitments;
DROP TABLE pm_commitments;
ALTER TABLE pm_commitments_new RENAME TO pm_commitments;

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('005_pm_block_c', datetime('now'));
