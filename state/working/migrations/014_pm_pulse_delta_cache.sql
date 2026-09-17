-- Migration: 014_pm_pulse_delta_cache
-- Created: 2026-07-01
-- Description: linear-pulse-check moves from a full list_projects/list_issues pull every
--   Tue-Fri run to an updatedAt-delta pull merged with cached state (see
--   roster/scribe/skills/linear-pulse-check.md Steps 1-2 and scripts/pm/pulse.py
--   denormalize_project/denormalize_issue/merge_projects/merge_issues). Health and
--   missed-deadline detection are date-driven (pace vs. today, original_due_date vs.
--   today) and must still run against every active project/issue each day even when
--   nothing changed in Linear, so unchanged rows are reconstructed from cache rather
--   than skipped. That reconstruction needs a few raw Linear fields the existing
--   columns don't carry: project status_type + start_date + lead_name, and issue
--   status_type (pm_issues.status already held the human-readable label, not the
--   type enum used by percent_complete/issue_state/issues_to_fetch_blockers).
--   Owner: Scribe.
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step), or
--   manually: sqlite3 state/working/fleet.db < state/working/migrations/014_pm_pulse_delta_cache.sql

ALTER TABLE pm_projects ADD COLUMN status_type TEXT;  -- raw Linear project status type (backlog/planned/started/paused/completed/canceled)
ALTER TABLE pm_projects ADD COLUMN start_date  TEXT;  -- YYYY-MM-DD; raw Linear start date (pace calc input)
ALTER TABLE pm_projects ADD COLUMN lead_name   TEXT;  -- raw Linear lead name (owner mapping input; distinct from resolved `owner`)

ALTER TABLE pm_issues ADD COLUMN status_type TEXT;    -- raw Linear issue status type (backlog/unstarted/started/completed/canceled)

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('014_pm_pulse_delta_cache', datetime('now'));
