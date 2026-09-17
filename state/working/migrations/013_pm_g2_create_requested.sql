-- Migration: 013_pm_g2_create_requested
-- Created: 2026-06-30
-- Description: G2 (accountability-driven Linear creation) idempotency stamp. When a
--   create intent is parsed from a human's accountability reply, the agent stamps
--   create_requested_at BEFORE issuing the Linear write. On a re-run, a row with
--   create_requested_at set but linear_link still NULL means a create was already
--   attempted -> reconcile (search + link), never blind re-create. Prevents dupes.
--   Owner: Scribe.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step), or
--   manually: sqlite3 state/working/fleet.db < state/working/migrations/013_pm_g2_create_requested.sql

ALTER TABLE pm_commitments ADD COLUMN create_requested_at TEXT;  -- ISO 8601

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('013_pm_g2_create_requested', datetime('now'));
