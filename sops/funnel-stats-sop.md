# Funnel Stats -- Team SOP

**Version:** 1.0
**Owner:** Marketing / GTM Ops
**Applies to:** Marketing ops team members using Claude Code
**Tool:** Claude Code Agent -> `/funnel-stats`

---

## What This Is

The Funnel Stats agent queries HubSpot for current month-to-date GTM funnel metrics and produces a formatted metrics block covering MQLs, SALs, SQLs, conversion rates, and active pipeline. It runs seven parallel HubSpot queries, calculates derived metrics, and outputs a clean markdown block you can paste directly into the WBR or share in Slack.

**Time to complete:** ~1-2 minutes (automated HubSpot queries)

---

## Section 1: Prerequisites

Before running the agent, confirm the following:

1. **Claude Code** is installed and running in the marketing repo (`~/claude_code/marketing`).
2. The **HubSpot MCP connector** is authorized in your Claude Code session. If it's not connected, Claude will prompt you to authenticate before the queries can run.
3. You have access to the {{COMPANY}} HubSpot instance (the agent uses pipeline and property IDs specific to our HubSpot account).

No CSV exports, manual data pulls, or other inputs are needed. The agent reads directly from HubSpot.

---

## Section 2: Running the Agent

1. Open Claude Code in the marketing repo.
2. Type `/funnel-stats` and press Enter.
3. The agent determines the current month-to-date date range automatically (first of the month through today).
4. It fires seven HubSpot queries in parallel:
   - Three **contact queries** for MQL counts by type (Inbound Demo Requests, Auto MQLs, Outbound)
   - Two **deal queries** for SAL and SQL counts
   - One **deal query** for in-month SQLs (demos completed on deals also scheduled this month)
   - One **deal query** for active open pipeline (paginated to capture all deals)
5. After all queries return, the agent calculates derived totals and conversion rates.
6. The final output prints directly in your terminal as a formatted markdown block.

There are no prompts or inputs required during the run. The agent is fully autonomous once invoked.

---

## Section 3: Understanding the Output

The output is a single markdown block. Here is what each line means:

### MQL Metrics

| Line | Source | What it measures |
|------|--------|-----------------|
| **MQLs - [total]** | Sum of P1 + P2 + Outbound | Total marketing qualified leads this month |
| Inbound Demo Requests | Contacts where `mql_type_latest` = "MQL Handraiser - P1" | Hand-raisers who requested a demo directly |
| Auto MQLs | Contacts where `mql_type_latest` = "MQL Score Threshold - P2" | Contacts that crossed the lead scoring threshold |
| Outbound | Contacts where `mql_type_latest` = "Outbound" | Outbound-sourced MQLs |

### SAL Metrics

| Line | Source | What it measures |
|------|--------|-----------------|
| **MQL to SAL (Scheduled Demo Calls)** | Deals entering Discovery Scheduled stage this month | Leads that converted to a scheduled demo |
| CVR% | SAL count / MQL total * 100 | MQL-to-SAL conversion rate |

All SALs in the output are in-month by definition (the query filters by in-month stage entry date).

### SQL Metrics

| Line | Source | What it measures |
|------|--------|-----------------|
| **SAL to SQL (Demos Completed)** | Deals with `demo_done_date` this month | Total demos actually completed |
| In-month count | Subset where `demo_done_date` AND `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` are both this month | Demos completed on deals that were also scheduled this month |
| CVR% | SQL total / SAL count * 100 | SAL-to-SQL conversion rate |

The in-month distinction matters because some completed demos this month may have been scheduled last month. The parenthetical "in-month" count isolates same-month velocity.

### Pipeline

| Line | Source | What it measures |
|------|--------|-----------------|
| **Active Open Pipeline** | Sum of `amount` on all deals in pipeline {{HUBSPOT_PIPELINE_ID}}, excluding Closed Won and Closed Lost | Total dollar value of open deals |

Pipeline formatting follows this rule:
- Values at or above $1,000,000 display as `$X.XM` (e.g., $2.3M)
- Values below $1,000,000 display as `$XXX.XK` (e.g., $475.2K)

### Conversion Rates

Both conversion rates (MQL-to-SAL and SAL-to-SQL) are rounded to one decimal place. If the denominator is zero (e.g., zero MQLs in the first days of a new month), the rate displays as "N/A" instead of a number.

---

## Section 4: Using the Output

### In the WBR (automated)

When run as part of `/wbr-prep`, the metrics block is automatically placed into the Summary section of the Weekly Business Review. You do not need to copy it manually.

### Standalone use

When run via `/funnel-stats` directly, copy the output block from your terminal and use it wherever needed:

- **Slack:** Paste into #marketing-ops or a leadership channel for a quick MTD status update.
- **Notion:** Paste into the WBR Summary section or any reporting page.
- **Slides or docs:** The markdown renders cleanly in most tools. Strip the bold markers (`**`) if pasting into a non-markdown context.

### Cadence

- **Weekly (automated):** `/wbr-prep` calls this agent every week as part of WBR preparation.
- **On-demand:** Run `/funnel-stats` any time you need a current MTD snapshot. There is no rate limit or cooldown.

---

## Section 5: Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| HubSpot query returns an error | MCP connector not authorized, or session expired | Re-authorize the HubSpot connector in Claude Code settings and retry |
| A metric shows 0 | Valid result early in the month, or no activity of that type yet | Check the date range (it should be 1st of the month through today). Zero is a real value, not an error. |
| Pipeline total seems low | Pagination may have stopped early | The agent paginates through all pages. If it warns about repeated results after 5 pages, the total may be incomplete. Re-run and check for the warning. |
| Metrics don't match what you see in HubSpot | Date range mismatch, or you're looking at a different pipeline/filter | Confirm you're comparing the same date range (MTD). Confirm the HubSpot view uses the same pipeline (ID {{HUBSPOT_PIPELINE_ID}}) and excludes existing business deals. |
| Conversion rate shows "N/A" | The denominator metric is zero | This is expected behavior. If MQL total is 0, the MQL-to-SAL rate cannot be calculated. |
| Agent asks for HubSpot access | Connector not installed | Search for and connect the HubSpot MCP connector when Claude prompts you |

---

## Quick Reference

| Item | Value |
|------|-------|
| **Command** | `/funnel-stats` |
| **Prerequisites** | Claude Code, HubSpot MCP connector authorized |
| **Output** | Formatted markdown metrics block (printed to terminal) |
| **Cadence** | Weekly via `/wbr-prep`, or on-demand |
| **Date range** | Automatic: 1st of current month through today |
| **Pipeline ID** | `{{HUBSPOT_PIPELINE_ID}}` ({{COMPANY}} sales pipeline) |
| **MQL property** | `mql_type_latest` on contacts |
| **MQL date property** | `mql_date__latest_` on contacts |
| **Demo done property** | `demo_done_date` on deals |
| **Discovery scheduled date** | `hs_v2_date_entered_{{HUBSPOT_STAGE_DISCOVERY_ID}}` on deals |
| **Excluded deal stages** | Closed Won (`{{HUBSPOT_STAGE_CLOSED_WON_ID}}`), Closed Lost (`{{HUBSPOT_STAGE_CLOSED_LOST_ID}}`) |

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
