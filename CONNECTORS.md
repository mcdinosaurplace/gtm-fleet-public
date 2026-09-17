# Connectors

## How tool references work

Fleet files use `~~category` as a placeholder for whatever tool is connected in that
category. `~~crm` might mean HubSpot, Salesforce, or any CRM with an MCP server;
`~~chat` might mean Slack or Microsoft Teams. The product named in parentheses after a
placeholder (e.g. "`~~chat` (Slack)") is the default this kit was built and tested
against — not a requirement.

Prose describes workflows by category. Procedural steps still name concrete tool names
(`slack_send_message`, `search_crm_objects`) because that is what the agent must call;
the MCP preflight (`docs/mcp-preflight.md`) discovers the bound server at runtime.

## Three ways a connector gets bound

| Mode | Where it is configured | Tool names look like | When to use |
|---|---|---|---|
| **Account connectors** (claude.ai) | Claude settings → Connectors, outside this repo | `mcp__<opaque-id>__slack_send_message` | Interactive sessions on a machine already connected to the team's tools. The permission allowlist cannot name these ids ahead of time; agents find them with ToolSearch. |
| **Project MCP servers** | copy `mcp/connectors.example.json` → `.mcp.json` in FLEET_ROOT | `mcp__slack__slack_send_message` | Headless runs and client fleets — stable names that match `.claude/settings.json`'s allowlist. |
| **Plugin MCP servers** | `.claude-plugin/plugin.json` → `mcpServers` (the in-repo Luma server) | `mcp__plugin_gtm-fleet_luma__list_events` | Servers that ship with the kit. |
| **Demo fixtures** (Phase 2) | `mcp/demo.json` + `DEMO_MODE=1` | same stable names, backed by `fixtures/` | Interviews and demos with no credentials at all. |

## Connectors for this fleet

| Category | Placeholder | Default server | Used by | Other options |
|---|---|---|---|---|
| CRM / marketing automation | `~~crm` | HubSpot | revops-watchdog, funnel-stats, performance-marketer (campaign analytics), Scribe (WBR numbers) | Salesforce, Marketo, Pardot |
| Chat | `~~chat` | Slack | chief-of-staff (briefs, decision queue), Scribe (stand-up, WBR pings), Tier-2 approvals | Microsoft Teams |
| Issue tracker | `~~issue tracker` | Linear | Scribe (PM pulse, stand-up), chief-of-staff (AM snapshot), content-producer/brand-designer (clickable refs) | Jira, Asana |
| Knowledge base | `~~knowledge base` | Notion | Scribe (WBR, topic review sync), chief-of-staff (briefs), content-producer (use-case library) | Confluence, Guru |
| Calendar | `~~calendar` | Google Calendar (MCP or `scripts/gcal_pull.py`) | chief-of-staff AM brief | Outlook |
| Email | `~~email` | Gmail (MCP or `scripts/gmail_pull.py`) | chief-of-staff AM brief | Outlook |
| Meeting notes | `~~meeting notes` | Grain | content-researcher (call-miner) | Gong, Fireflies, Otter |
| Events | `~~events` | Luma (in-repo MCP, `scripts/luma_mcp.py`) | luma-events capability, event telemetry docs | Eventbrite |
| Ads | `~~ads` | Google Ads (`scripts/google_ads_pull.py`), LinkedIn | performance-marketer (spend watch, dossier, execute-approved) | Microsoft Ads, Meta |
| Web analytics | `~~web analytics` | GA4 + Search Console (`scripts/ga4_pull.py`, `gsc_pull.py`) | performance-marketer (ranking watch, traffic scorecard) | Plausible, Matomo |
| SEO | `~~SEO` | Ahrefs, Similarweb (optional) | performance-marketer SEO/GEO skills, seo-audit | Semrush, Moz |
| CMS | `~~cms` | Framer | content-producer (publish packages — humans publish) | Webflow, WordPress |
| Design | `~~design` | Figma, Canva (optional) | brand-designer (M3 Figma bridge — not yet built) | Adobe Creative Cloud |
| Product analytics | `~~product analytics` | Amplitude (optional) | performance-analytics skill | Mixpanel |
| Email marketing | `~~email marketing` | Klaviyo (optional) | email-sequence, email-qa skills | Mailchimp, Customer.io |
| Enrichment / prospecting data | `~~enrichment` | Clay, Apollo (optional) — feeds the {{ENRICHMENT_VENDOR}} cascade | revops-watchdog (integration health, enrichment watch), gtm-ops references, lifecycle model | ZoomInfo, Clearbit, Cognism |
| Business intelligence | `~~BI` | Metabase (optional) | performance-analytics, attribution-brief skills, gtm-ops references | Looker, Mode, Hex |
| AEO / AI-answer insights | `~~AEO insights` | AirOps Prompt Insights (optional); HubSpot AEO rides on `~~crm` | AEO register (`docs/aeo-tracked-prompts.md`), content-researcher topic-synthesizer, content-producer brief-builder | Profound, Peec AI |
| Automation glue | `~~automation` | Zapier (optional) | event telemetry → `~~crm` hand-offs, gtm-ops workflow references | Make, n8n, Workato |
| Support desk | `~~support desk` | none bundled — set the ticket-domain suffix the enrichment watch excludes | revops-watchdog enrichment watch (pseudo-inbox exclusion) | Zendesk, Intercom |
