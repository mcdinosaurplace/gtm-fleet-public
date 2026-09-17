-- pm_open_blockers: unresolved blockers with age in days.
-- Used by pulse + thursday-agenda-draft (blockers older than 5 business days). Read-only.
SELECT id, project_id, issue_id, description, opened_at,
       CAST(julianday('now') - julianday(opened_at) AS INTEGER) AS age_days
FROM pm_blockers
WHERE resolved_at IS NULL
ORDER BY opened_at;
