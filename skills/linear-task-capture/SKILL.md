---
name: linear-task-capture
description: >
  Creates, queues, and pushes Linear issues into the {{COMPANY}} Marketing team. Use any time the user wants to
  create, log, push, or track tasks in Linear — even without saying "Linear" explicitly. ALWAYS use when
  the user says: "create tasks", "log this", "push to Linear", "create a Linear issue", "note that for
  later", "assign this to X", "create issues for all of that", or "push these". Also use proactively during
  campaign planning, content briefs, HubSpot work, paid search, and marketing ops sessions where follow-ups
  emerge — e.g. "we need to set up X", "someone should write Y", or "{{HEAD_OF_MARKETING_FIRST}} needs to sign off". Use at
  session wrap-up ("log everything and push") and whenever tasks need routing to the team ({{CONTENT_LEAD_FIRST}} for copy,
  {{DESIGN_LEAD_FIRST}} for design, Scott for ops/tracking, {{HEAD_OF_MARKETING_FIRST}} for approvals). Full workflow: detect → queue → review
  table → push to Linear in one batch.
---

## What This Skill Does

This skill lets you capture Linear issues from inside a Claude session — whether you explicitly ask for them
or Claude notices action items emerging from the work. Tasks collect in a session queue and are pushed to
Linear in a single reviewed batch.

**Core workflow:**
1. Tasks are added to the session queue (explicitly or proactively detected)
2. When ready to push, Claude shows a review table for approval
3. On approval, all issues are created in Linear in one shot

---

## {{COMPANY}} Marketing Linear Context

**Team:** Marketing | Key: `MAR` | ID: `{{NOTION_COLLECTION_ID}}`

### Issue Statuses
| Status | Use for |
|--------|---------|
| `Todo` | Ready-to-start tasks — **default for all new issues** |
| `Ideas` | Early-stage, not yet scoped or prioritized |
| `In Progress` | Already underway |

Always default to **Todo** unless the user explicitly asks for a different status. Include status in the review table so it's visible before push.

### Labels
| Label | Use when |
|-------|---------|
| `MOPS` | Marketing ops, HubSpot, RevOps, data, tooling, tracking setup, campaign execution |
| `HubSpot` | HubSpot-specific configuration, workflow, or property tasks |
| `Content` | Blog posts, newsletters, copy, case studies, guides, email sequences |
| `Website` | Framer pages, landing pages, web updates |
| `Advertising` | Paid search strategy, ad copy, LinkedIn ads, display |

Apply labels based on context — don't over-label. One or two is usually right. Some tasks span multiple labels — for example, "set up conversion tracking for a paid campaign" earns both `MOPS` (it's ops/technical work) and `Advertising` (it serves the paid channel). Use your judgment on overlap.

### Active Projects
Reference these when tasks clearly belong to an existing project. This roster mirrors the
`pm_projects` table Scribe maintains — re-read it rather than trusting memory:
- **Website repositioning** — the site rebuild and messaging refresh
- **Q3 webinar series** — the quarterly live-session program
- **Lead scoring model 2.0** — the scoring rebuild
- **Use-case library** — the use-case content library
- **Brand refresh** — visual identity refresh
- **Partner co-marketing** — joint campaigns with partners
- **Event telemetry → CRM** — wiring event registrations into `~~crm`
- **SEO content sprint** — the organic content push
- **Customer stories program** — customer proof and reference program
- **Paid search restructure** — account and campaign restructure
- **MOPS Inbox and New Requests** — marketing ops requests and backlog; the default home for
  an issue with no other parent

If a task clearly belongs to one of these, suggest associating it. If uncertain, leave project blank.

---

## Smart Assignee Routing

The team has clear functional ownership. When the user doesn't specify an assignee, use these defaults.
This isn't just a lookup table — it's the mental model for who owns what at {{COMPANY}} Marketing.

| Functional domain | Default assignee |
|-------------------|-----------------|
| Copywriting, content writing, editorial, email copy, messaging, linguistic tasks | **{{CONTENT_LEAD}}** |
| Design, visual production, Framer builds, page layout, graphic assets | **{{DESIGN_LEAD}}** |
| Marketing ops, RevOps, HubSpot, campaign execution, tracking, UTMs, data work | **Scott McKeighen** |
| Approvals, go/no-go decisions, launch reviews, strategic sign-offs | **{{HEAD_OF_MARKETING}}** |
| {{ENRICHMENT_VENDOR}} platform, technical site infrastructure, deep SEO implementation | **{{CEO}}** |

**How to apply this:**
- "write copy for the hero section" → {{CONTENT_LEAD_FIRST}}
- "design the Framer layout" → {{DESIGN_LEAD_FIRST}}
- "set up UTM tracking" or "configure HubSpot workflow" → Scott
- "update keyword targeting doc" or "update ad campaign brief" → Scott (campaign ops, not {{CEO_FIRST}})
- "review and approve before launch" → {{HEAD_OF_MARKETING_FIRST}}
- "fix a {{ENRICHMENT_VENDOR}} integration" or "update technical SEO config on the site" → {{CEO_FIRST}}

**Note on {{CEO_FIRST}}:** Only route to {{CEO_FIRST}} for tasks that directly involve the {{ENRICHMENT_VENDOR}} platform or hands-on technical site/SEO work. General keyword strategy, paid campaign docs, and ad-related work are campaign ops — they belong to Scott or should be left unassigned if ownership isn't clear.

When the user says "assign to me", always resolve their identity via `get_user` with query `"me"` rather than assuming.
If the domain is ambiguous, leave unassigned and add a note in the review table rather than guessing.

---

## Proactive Task Detection

While working with the user, stay alert for language that signals a task needing follow-up. When you
detect this, add it to the queue and briefly surface it with a short inline note. Keep it lightweight —
one line is enough.

**Signals to watch for:**
- Action verbs with future intent: "we need to", "someone should", "we'll need to", "let's make sure"
- Delegation language: "farm this out", "pass this to", "have [name] handle"
- Output gaps: "we're missing a brief", "we need a landing page for this", "there's no tracking set up"
- Explicit logging requests: "log this", "note that", "add this to the backlog", "create a task"

**When you detect tasks, say something natural like:**
> 📋 It looks like there are a couple of tasks worth pushing to Linear from this session — I'll add them to the queue. Let me know when you want to review and push.

Or inline when a single task emerges:
> 📋 Noted for Linear — I'll queue "Update the pricing page CTAs" for review before we push.

Don't interrupt the flow. A brief one-line note is enough. Save the full review for when the user is ready.

---

## Session Queue Management

Maintain a running queue of issues to be created. Each queued issue has:

| Field | Required? | Notes |
|-------|-----------|-------|
| Title | Yes | Short, action-oriented. Start with a verb. |
| Description | Optional | 1–3 sentences of context. What, why, any links. |
| Assignee | Optional | Use smart routing defaults; blank if truly ambiguous |
| Priority | Optional | Urgent / High / Normal / Low (default: Normal) |
| Status | Yes | Default: **Todo** |
| Labels | Optional | 1–2 from the labels table |
| Project | Optional | Link to existing project if clearly applicable |

Good issue titles: "Draft the nurture sequence for the webinar series", "Set up UTM tracking for the paid search restructure", "Update lead scoring model doc with new MQL thresholds"

---

## Review and Push Workflow

When the user is ready to push (or asks to review), present a clean summary table that includes Status:

```
Here's what I have queued for Linear. Review and say "push" to create them all, or call out anything to adjust:

| # | Title | Assignee | Status | Priority | Labels | Project |
|---|-------|----------|--------|----------|--------|---------|
| 1 | Write hero copy for the new homepage | {{CONTENT_LEAD}} | Todo | Normal | Content | Website repositioning |
| 2 | Design the new homepage layout in Framer | {{DESIGN_LEAD}} | Todo | Normal | Website | Website repositioning |
| 3 | Set up UTM tracking for paid campaigns | Scott McKeighen | Todo | High | MOPS, Advertising | — |
| 4 | Approve launch before paid traffic goes live | {{HEAD_OF_MARKETING}} | Todo | Urgent | — | Website repositioning |
```

Wait for explicit approval ("push", "looks good", "go ahead") before creating any issues.

**On approval:**
1. Resolve all assignees to Linear user IDs (via `get_user` or `list_users` if not already resolved)
2. For any project associations, fetch the project ID via `get_project` or confirm from the known list above
3. Call `save_issue` for each issue in sequence — always include `team: "Marketing"` and `state: "Todo"`
4. After all are created, confirm with a brief summary:

> ✅ Created 4 issues in Linear (Marketing team). Here they are:
> - MAR-### — Write hero copy for the new homepage
> - MAR-### — Design the new homepage layout in Framer
> - MAR-### — Set up UTM tracking for paid campaigns
> - MAR-### — Approve launch before paid traffic goes live

If any issue fails to create, report it clearly and offer to retry rather than silently skipping.

---

## Creating New Projects

If a batch of tasks clearly belongs to a new effort that doesn't have a project yet, offer to create one:

> These tasks seem to be part of a new initiative — want me to create a project for them and link the issues?

If yes, ask for: project name, optional target date, optional lead. Then call `save_project` before creating the issues.

---

## Edge Cases

- **Duplicate detection**: If a task description sounds identical to one already in the queue, flag it before adding again.
- **Ambiguous assignee**: If the domain is unclear, leave unassigned and note this in the description so it's easy to assign manually in Linear.
- **No project match**: If a task doesn't fit any active project, leave project blank. Don't force-fit to the wrong project.
- **Empty queue**: If the user asks to push but the queue is empty, say so clearly and ask if they'd like to create issues directly.
- **Partial approval**: If the user says "push 1 and 3 but not 2", respect that — only create the approved issues and keep the rest in queue.
- **User overrides smart routing**: If the user explicitly assigns someone different from the default, always honor their explicit instruction over the smart defaults.
