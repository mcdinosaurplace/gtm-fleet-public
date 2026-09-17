-- pm_overdue_external_deps: external (agency/partner) deliverables past expected delivery.
-- Used by thursday-agenda-draft. Read-only.
SELECT internal_owner, external_party, description, owner_side_action,
       expected_delivery, linear_link, status
FROM pm_external_dependencies
WHERE status = 'pending'
  AND expected_delivery IS NOT NULL
  AND expected_delivery < date('now')
ORDER BY expected_delivery;
