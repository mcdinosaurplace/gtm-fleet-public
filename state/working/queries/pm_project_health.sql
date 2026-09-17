-- pm_project_health: open projects ranked off_track -> at_risk -> on_track.
-- Used by linear-pulse-check + thursday-agenda-draft. Read-only.
SELECT id, name, owner, health, health_source,
       original_due_date, current_target_date, linear_link, short_description
FROM pm_projects
WHERE closed_at IS NULL
ORDER BY CASE health
           WHEN 'off_track' THEN 0
           WHEN 'at_risk'   THEN 1
           WHEN 'on_track'  THEN 2
           ELSE 3
         END,
         original_due_date;
