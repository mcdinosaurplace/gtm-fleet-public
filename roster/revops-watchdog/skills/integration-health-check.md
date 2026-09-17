---
name: revops-watchdog:integration-health-check
description: >
  Monthly integration sync health audit. Checks {{ENRICHMENT_VENDOR}}, the `~~enrichment`
  connectors, ad platform → HubSpot syncs for latency, error rates, coverage gaps, and
  webhook failures. References {{company_slug}}-stack.md for the canonical integration
  catalog and expected sync behavior.
---

# Integration Health Check

## When This Runs

- **Standalone:** `/revops-watchdog integration-health-check`
- **Typical cadence:** Monthly, or triggered when `opsos-watch` or
  `attribution-integrity-audit` flags sync-related anomalies

## Inputs

- HubSpot integration status and connected apps list
- Sync logs from connected platforms (where accessible via MCP or API)
- Error rates and last-sync timestamps per integration

## Cross-Agent Input: {{company_slug}}-stack.md

Reference `skills/gtm-ops/references/stack.md` (gtm-fleet
plugin) for the integration catalog. Expected integrations at {{COMPANY}}:

| Integration | Direction | Expected Cadence | Critical? |
|-------------|-----------|-----------------|-----------|
| {{ENRICHMENT_VENDOR}} → HubSpot | Inbound | Near real-time | Yes |
| `~~enrichment` (workflow) → HubSpot | Inbound | Daily batch | Yes |
| `~~enrichment` (contact data) → HubSpot | Inbound | Daily | Medium |
| {{ENRICHMENT_DATA_PROVIDER}} → HubSpot | Inbound (via the `~~enrichment` cascade) | Weekly | Medium |
| Google Ads ↔ HubSpot | Bidirectional (gclid + offline conv) | Daily | Yes |
| LinkedIn ↔ HubSpot | Bidirectional (conversion import) | Daily | Medium |
| GA4 → HubSpot | Reference | Real-time (tag-based) | Medium |
| Zapier / webhooks | Varies | Varies | Varies |

If `{{company_slug}}-stack.md` isn't accessible, fall back to surveying HubSpot's
connected integrations list and categorizing by user role.

## Audit Checks

### 1. Connection Status

For each integration in the catalog:
- Is the connection active (not disconnected, not in an error state)?
- Last successful sync timestamp
- Hours since last sync vs. expected cadence

Flag:
- Disconnected integration → HIGH
- Last sync >2x expected cadence → MED
- Auth errors / reauthentication needed → HIGH

### 2. Error Rate

For each integration with accessible logs:
- Error rate over past 30 days
- Trend (rising / stable / falling)
- Specific error types (auth, rate limit, data format, timeout)

Flag:
- Error rate >5% → MED
- Error rate >15% → HIGH
- Rising error rate trend (3-month slope positive) → MED even if under threshold

### 3. Coverage Gaps

For inbound syncs ({{ENRICHMENT_VENDOR}} and the `~~enrichment` sources feeding its cascade):
- What % of HubSpot contacts in the past 30 days received enrichment
  from this source?
- Is coverage stable month-over-month, or dropping?

This overlaps with `opsos-watch` — use integration-health-check to go
deeper when opsos-watch flags field dropout.

### 4. Bidirectional Flow Health (Ads → HubSpot)

For Google Ads and LinkedIn integrations:
- Gclid / LinkedIn fbc capture rate on paid-source new contacts
- Offline conversion import success rate (deal closed-won → Ads)
- Time lag between deal close and ad platform conversion registration

Flag:
- Offline conversion imports failing → HIGH (breaks Smart Bidding)
- Gclid capture rate <80% on paid contacts → MED
- Import lag >48 hours → LOW (informational)

### 5. Webhook / Zap Health

If Zapier or custom webhooks are in use:
- Active zaps / webhooks
- Run count and success rate over past 30 days
- Any zaps in "paused" or "errored" state

Flag:
- Critical-path zap in error state → HIGH
- Non-critical zap error → LOW

## Output Format

```markdown
## Integration Health Check — {Month Year}

### Catalog Source
{`skills/gtm-ops/references/stack.md` § Integration Catalog, or "Fallback: enumerated HubSpot connected apps"}

### Summary
| Integration | Status | Last Sync | Error Rate | Severity |
|-------------|--------|-----------|-----------|----------|
| {{ENRICHMENT_VENDOR}} → HubSpot | {OK/Degraded/Down} | {timestamp} | {pct}% | {LOW/MED/HIGH} |
| `~~enrichment` → {{ENRICHMENT_VENDOR}} | ... | | | |
| {{ENRICHMENT_DATA_PROVIDER}} → {{ENRICHMENT_VENDOR}} | ... | | | |

### Connection Status
{Per-integration connection detail: auth state, reauth needed, last sync}

### Error Rate Trends
| Integration | 30d Error Rate | 3mo Trend | Top Error Types |
|-------------|---------------|-----------|----------------|

### Enrichment Coverage (Inbound Syncs)
| Source | 30d Contact Coverage | MoM Change | Fields Affected |
|--------|---------------------|-----------|----------------|

### Paid Ads Bidirectional Flow
- Gclid capture rate (paid source, 30d): {pct}%
- Offline conversion import success: {pct}%
- Average import lag: {hours}
- Issues: {list}

### Webhook / Zap Status
| Item | State | 30d Runs | Success Rate |
|------|-------|----------|-------------|

### Recommended gtm-ops action
**Immediate:**
- {list of HIGH-severity issues needing investigation}

**Review:**
- {MED issues to investigate this month}

**Document:**
- {If {{company_slug}}-stack.md lacks current integration detail: "Update
  {{company_slug}}-stack.md integration catalog to reflect current tool set"}

### Notes for Other Agents
- performance-marketer: {any issues affecting attribution-review — gclid, offline conv}
- chief-of-staff: {summary one-liner for AM brief}
```

## Anomaly Table Writes

INSERT into `anomalies` with `surface='integration'`:
- One row per failing integration
- Set severity per the thresholds above

## Handoff

Monthly handoff to chief-of-staff. If any HIGH severity issue is detected,
write an immediate handoff (don't wait for monthly cadence). Include:
- Which integration is affected
- Downstream impact (e.g., "{{ENRICHMENT_VENDOR}} sync down affects all new contact
  enrichment, which affects lead scoring quality")
- Who should investigate (Scott; may need RevOps Admin for reauth)
