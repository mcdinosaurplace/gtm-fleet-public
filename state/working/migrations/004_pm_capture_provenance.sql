-- Migration: 004_pm_capture_provenance
-- Created: 2026-06-08
-- Description: Provenance + raw-input columns for the flexible-in / rigid-through
--   capture procedure. Stores the member's verbatim text (raw_text) and how each
--   row was parsed (parsed_by: anchor 'rule' vs 'model' fallback). Owner: Scribe.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step 5),
--   or manually: sqlite3 state/working/fleet.db < state/working/migrations/004_pm_capture_provenance.sql

ALTER TABLE pm_standup_responses ADD COLUMN raw_text TEXT;
ALTER TABLE pm_standup_responses ADD COLUMN parsed_by TEXT
    CHECK (parsed_by IN ('rule', 'model'));

ALTER TABLE pm_external_dependencies ADD COLUMN raw_text TEXT;
ALTER TABLE pm_external_dependencies ADD COLUMN parsed_by TEXT
    CHECK (parsed_by IN ('rule', 'model'));

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('004_pm_capture_provenance', datetime('now'));
