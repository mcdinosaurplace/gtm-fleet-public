-- pm_orphan_issues: marketing issues with no parent project, ranked blocked -> stale -> active.
-- Used by pulse + thursday-agenda-draft (orphans that may need a home). Read-only.
SELECT id, title, owner, status, state, due_date, linear_link, last_activity_at
FROM pm_issues
WHERE project_id IS NULL
  AND state <> 'closed'
ORDER BY CASE state
           WHEN 'blocked' THEN 0
           WHEN 'stale'   THEN 1
           WHEN 'active'  THEN 2
           ELSE 3
         END,
         last_activity_at;
