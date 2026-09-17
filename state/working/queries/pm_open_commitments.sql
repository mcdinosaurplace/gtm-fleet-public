-- pm_open_commitments: stand-up commitments not yet completed, by owner.
-- Used by the week-over-week completion eval + thursday-agenda-draft. Read-only.
SELECT owner, week_starting, commitment, scale, horizon, completion_status,
       linear_link, effective_due_date
FROM pm_commitments
WHERE completion_status IN ('pending', 'in_flight', 'carried', 'partial')
ORDER BY owner, week_starting;
