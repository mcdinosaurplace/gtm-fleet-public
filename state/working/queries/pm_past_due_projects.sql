-- pm_past_due_projects: open projects past their IMMUTABLE original_due_date.
-- Feeds missed-deadline-capture. Read-only.
SELECT id, name, owner, original_due_date, current_target_date, health, linear_link
FROM pm_projects
WHERE closed_at IS NULL
  AND original_due_date IS NOT NULL
  AND original_due_date < date('now')
ORDER BY original_due_date;
