# Linear Reference Formatting

Fleet-wide standing rule. Applies to **every** agent in `/roster/*`.

## The Rule

**Every** reference to a Linear issue or project in **any** agent-authored
output — no exceptions — must be rendered as a clickable link. This covers
Slack DMs, Slack channel posts, Notion pages, journal entries, handoff files,
ops-incidents logs, fallback briefs preserved in the journal, carry-forward
notes, meditations, WBR sections, intelligence briefs, and anything else an
agent produces.

Bare issue IDs (e.g. a naked `MAR-7076`) and bare project names are not
permitted in any artifact produced by the fleet.

If you find yourself about to type an issue ID or project name without a URL
behind it, **stop and link it**.

## HARD-AND-FAST PRE-SEND GATE

This is the rule with teeth. Every agent that ships output to an external
surface (Slack send, Notion write, file commit) must run this self-check
**immediately before** the publish call:

1. **Scan** the composed payload for any token matching the issue-ID pattern
   `[A-Z]+-\d+` (e.g. `MAR-7076`, `OPS-91`). For each match, verify it sits
   inside a markdown link of the form
   `[MAR-XXXX](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/…)`.
2. **Scan** for any Linear project name that came from a `project` field on
   a Linear MCP response. For each match, verify it sits inside a markdown
   link to `https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/project/…/overview`.
3. **If ANY unlinked Linear reference is found, DO NOT publish.** Stop, link
   it using the `url` field from the Linear MCP response, re-run the scan,
   and only proceed when it returns clean.
4. **revops-watchdog handoff IDs** (`id=78`, `ids 98–99`, etc.) and any other integer
   row references are **NOT** Linear references and must NOT be linked.

The gate is binding. A brief, post, page, or commit that names a bare Linear
ID is a defect. The only allowed bypass is the MCP-unreachable fallback
below — and even then, the agent must explicitly state that links were
omitted.

## Surface determines syntax

{{COMPANY}}'s Slack workspace exposes Slack via `slack_send_message` (MCP server
`00000000-…`), which accepts **standard markdown** and renders `[label](URL)`
as a clickable link in Slack DMs and channels. The legacy Slack mrkdwn
`<URL|label>` form is NOT required for this MCP — and in fact will render
as literal text. Use standard markdown everywhere.

| Surface | Format | Example |
|---------|--------|---------|
| Slack DM via `slack_send_message` (chief-of-staff AM brief, Tier 1 escalations) | Standard markdown: `[label](URL)` | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Slack channel post via `slack_send_message` (Scribe WBR ping, any channel send) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Notion page (WBR, Intelligence Brief, Digital Marketing Brief, Updates row) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Journal files (`state/journal/*.md`) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Handoff file (`state/journal/handoffs.md`) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Ops-incidents log (`state/journal/ops-incidents.md`) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Meditations (`state/journal/*-meditations.md`) | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Brief content preserved in journal as fallback for later retry-send | Standard markdown — same form, send-ready as-is | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |
| Any other state file or agent-authored artifact | Standard markdown | `[MAR-7076](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/MAR-7076)` |

**Single rule:** standard markdown `[label](URL)` everywhere. One format
covers Slack, Notion, and every flat file. No surface-specific syntax
switching.

If an agent ever needs to call Slack's Web API directly (bypassing the MCP
— rare, but possible for some integrations), that path requires the legacy
mrkdwn `<URL|label>` form. Note it explicitly in the calling code; do not
let raw Web-API calls quietly leak Slack mrkdwn into the rest of the fleet.

## Label rules

- **Issues**: label is the issue ID exactly as Linear returns it
  (e.g. `MAR-7076`). Do not include the issue title in the label — keep it
  tight. If you want the title for context, write it outside the link:
  `[MAR-7076](URL) — Register user_type custom dimension`.
- **Projects**: label is the project name as Linear returns it (e.g.
  `MOps Inbox and New Requests`). Do not include the slug or UUID in the
  label.
- **Priority tags** (Urgent / High / Medium): when an issue carries a
  priority tag in the brief, the tag stays **outside** the link, not inside:
  `[MAR-7076](URL) (H)`, not `[MAR-7076 (H)](URL)`.

## URL rules

- **Prefer the canonical `url` field returned by the Linear MCP response.**
  `list_issues`, `get_issue`, `save_issue`, and the equivalent project tools
  all return a `url` per record. Use that value verbatim — it already
  contains the slug and is guaranteed correct.
- **If the MCP response does not include a URL** (older payloads, partial
  data), construct the minimal form. Linear redirects both to the slugged
  canonical:
  - Issue: `https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/issue/{ID}` (e.g. `…/issue/MAR-7076`)
  - Project: `https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/project/{slug-id}/overview` only when
    you already have the slug-id pair; otherwise omit the link, write the
    project name plain, and log a LOW ops-incident noting the missing URL.
- **Never invent or guess a slug.** A wrong slug still routes correctly via
  Linear's redirect, but a fabricated slug in the label is misleading.

## Fallback — MCP unreachable

If the Linear MCP is unreachable for the whole run (e.g. the "requires
approval" pattern observed across the fleet), the pre-send gate above
allows one — and only one — bypass: write issue IDs plain (no link) AND
add this single line at the bottom of any section that lists issues:

> _Issue links omitted — Linear MCP unavailable this run._

Do not fabricate URLs from a previous session's data. Do not silently ship
bare IDs without the disclaimer.

## Workspace

{{COMPANY}}'s Linear workspace slug is `pilot`. All canonical URLs begin with
`https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/`. Do not hardcode any other workspace.
