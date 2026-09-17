# WBR Prep — Team SOP

**Version:** 1.0
**Owner:** Marketing / GTM Ops
**Applies to:** Marketing ops team members using Claude Code
**Tool:** Claude Code Agent → `/wbr-prep`

---

## What This Is

The WBR Prep agent builds the Marketing Weekly Business Review page in Notion. It finds last week's WBR, duplicates it as a new page for the current week, pulls fresh funnel metrics from HubSpot, and fills in the Summary section automatically. All other sections (Project Updates, Content and Product Marketing, Website and Design, GTM Ops) are left intact for their owners to fill in manually.

**Time to complete:** ~5 minutes (mostly waiting for HubSpot queries and Notion API)

---

## Section 1: Prerequisites

Before running the agent, confirm the following:

- **Claude Code installed and working.** You should be able to open the `~/claude_code/marketing` project and run slash commands.
- **Marketing repo cloned.** The agent reads from and writes to the local `wbr/` directory for previews.
- **Notion connector authorized.** The agent reads from and writes to the Marketing Updates database (`collection://{{NOTION_UPDATES_DB_ID}}`). If Claude Code prompts you to connect Notion, follow the OAuth flow.
- **HubSpot connector authorized.** The funnel-stats sub-agent queries HubSpot for MQL, SAL, SQL, and pipeline numbers. Authorize when prompted.
- **Slack connector authorized.** Used at the end of the workflow to notify section owners. Not required for the prep and publish steps, only for notifications.

If any connector is missing, Claude Code will tell you which one it needs and pause until you authorize it.

---

## Section 2: Running the Agent

1. Open Claude Code in the `~/claude_code/marketing` project.
2. Type `/wbr-prep` and press Enter.
3. The agent runs the following steps automatically:
   - Searches the Marketing Updates database in Notion for the most recent WBR page.
   - Duplicates that page as the starting point for this week.
   - Calls the `funnel-stats` sub-agent, which queries HubSpot for month-to-date funnel metrics (MQLs, SALs, SQLs, pipeline generated).
   - Populates the Summary section with those metrics.
   - Sets the page properties: name (format: "WBR YYYY-MM-DD"), date, and status.
   - Carries forward all other sections from last week's page unchanged.
4. You will see terminal output as each step completes. The agent logs what it finds, what it duplicates, and what metrics it pulls.

You do not need to provide any input during the run. The agent handles everything from invocation through preview.

---

## Section 3: Reviewing the Preview

Before anything is posted to Notion, the agent saves a local Markdown preview to `wbr/YYYY-MM-DD.md` and prints it in the terminal.

### What to check

- **Funnel metrics accuracy.** Compare the MQL, SAL, SQL, and pipeline numbers against what you see in HubSpot. The agent pulls MTD figures, so confirm the date range matches your expectation.
- **Page properties.** The name should follow the format "WBR YYYY-MM-DD" using the upcoming Friday's date. The date property and status should be set correctly.
- **Section structure.** All sections from last week's page should be present and intact. The Summary section should contain the updated metrics. Everything else should be unchanged.
- **Formatting.** Scan for broken Markdown, missing headers, or table alignment issues.

### Requesting changes

If something looks wrong, tell the agent what to fix in the chat. Common requests:

- "The MQL number looks off, can you re-pull for this date range?"
- "Change the page date to next Friday instead of this Friday."
- "The Summary formatting is broken, fix the table."

The agent will make the correction and regenerate the preview. Repeat until you're satisfied.

---

## Section 4: Publishing to Notion

Once you approve the preview, tell the agent to publish (e.g., "looks good, post it" or "publish to Notion").

The agent then:

1. Creates the new WBR page in the Marketing Updates database.
2. Sets the page properties: name, date, status, department relation (Marketing), and review relation (Business Review).
3. Populates the page content with the previewed Markdown, including the auto-filled Summary section and all carried-forward sections.

The new page appears in Notion immediately. You can verify it by opening the Marketing Updates database and finding the newest entry.

---

## Section 5: Slack Notifications

After the page is posted to Notion, the agent asks if you want to notify section owners in Slack. If you confirm, it sends a message to each owner asking them to fill in their section before the WBR meeting.

### Who gets notified

| Section | Owner | What they need to do |
|---------|-------|---------------------|
| Summary (funnel metrics) | Scott McKeighen | Already auto-populated. Review only. |
| Project Updates | {{HEAD_OF_MARKETING}} | Fill in manually before the meeting. |
| Content and Product Marketing | {{CONTENT_LEAD_FIRST}} | Fill in manually before the meeting. |
| Website and Design | {{DESIGN_LEAD_FIRST}} | Fill in manually before the meeting. |
| GTM Ops (MOPs / RevOps) | Scott McKeighen | Fill in manually before the meeting. |

### What the message says

Each owner receives a Slack DM with a link to the new Notion page and a request to complete their section. The agent resolves Slack handles at runtime via user search.

### Customizing the deadline

The default message references the Friday WBR meeting. If your meeting is on a different day, tell the agent before it sends notifications (e.g., "notify owners but the deadline is Thursday EOD").

---

## Section 6: Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Can't find last week's WBR page" | The Notion search didn't match any page in the Marketing Updates database. This happens if the previous page was renamed, moved, or deleted. | Open Notion, find the most recent WBR page, and confirm it exists in the correct database. Re-run the agent. |
| HubSpot query returns zeros or errors | The HubSpot connector token may have expired, or the query filters don't match current lifecycle stage definitions. | Re-authorize HubSpot in Claude Code. If the token is valid, check that MQL/SAL/SQL lifecycle stages in HubSpot haven't been renamed. |
| Metrics look wrong compared to HubSpot dashboards | The agent pulls raw contact counts by lifecycle stage for the current month. Dashboard numbers may use different filters, attribution models, or date ranges. | Compare the agent's query logic (in `roster/scribe/skills/wbr-prep.md`) against your dashboard filters. Adjust your review expectations or update the agent prompt if the source of truth has changed. |
| Slack user search fails for an owner | The owner's display name or email doesn't match what Slack returns. This can happen if someone changed their Slack profile. | Tell the agent the correct Slack handle directly (e.g., "notify @mark.{{HEAD_OF_MARKETING_FIRST_LOWER}} instead"). |
| Notion page creates but properties are missing | The database schema may have changed, or a relation target was moved. | Check the Marketing Updates database in Notion for renamed or removed properties. Update the database IDs in `CLAUDE.md` if needed. |
| Preview file not generated | The `wbr/` directory may not exist locally, or there's a file permission issue. | Run `mkdir -p ~/claude_code/marketing/wbr` and re-run the agent. |

---

## Quick Reference

| Item | Detail |
|------|--------|
| **Command** | `/wbr-prep` |
| **Prerequisites** | Claude Code, Notion connector, HubSpot connector, Slack connector |
| **Output** | Local preview at `wbr/YYYY-MM-DD.md`, Notion page in Marketing Updates database |
| **Cadence** | Weekly, before the Friday WBR meeting |
| **Auto-populated sections** | Summary (funnel metrics from HubSpot) |
| **Manual sections** | Project Updates, Content and Product Marketing, Website and Design, GTM Ops |
| **Notifications** | Slack DMs to section owners after publishing |

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
