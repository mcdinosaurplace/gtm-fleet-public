---
persona: Erin the Technical Founder
status: primary
buyer_role: primary_buyer_and_user
revision: 2
sources:
  - {{company_slug}}-on-call-buyer-research.docx
  - {{COMPANY}}-Positioning.docx
---

# Erin the Technical Founder

HubSpot persona blocks below are formatted to paste field-by-field. Items marked **[INFERRED]** are not stated directly in the source documents and should be validated against HubSpot contact data before publishing.

## Name

Erin the Technical Founder

## Description

A technical founder or first CTO at a Series A or earlier company, shipping a product with a small engineering team that is already carrying production traffic. Lives in code, Claude/Cursor, and the terminal. Is the on-call rotation today — her phone is the escalation policy — because she hasn't hired a platform person and won't for at least six months. Doesn't want to learn incident management. She wants pages to reach the right person without her, ideally inside the tools her team already uses.

## Internal Notes

### Roles — What kinds of jobs does this persona have?

- Technical Founder / CTO / Co-founder of a Series A-or-earlier startup
- De facto Head of Platform, Head of Security, and Head of Support until the team grows past ~25 engineers
- Hands-on builder: ships product, reviews code, still carries the pager
- Buyer, evaluator, and end-user of every infrastructure tool in her stack — the same person makes the decision and gets woken up by the consequences
- Other titles this persona maps to: Founder, Co-founder, CTO, VP Engineering (at a company small enough that the title is aspirational). Common at companies with 5–40 engineers, pre-seed through Series A.

### Goals — What is this persona trying to do?

- Ship product. Everything else is overhead.
- Get off the "everything routes to me" pattern before the next hire quits over it
- Have one place where an alert becomes an incident with an owner, instead of a monitor firing into a chat channel nobody is watching at 2 a.m.
- Answer a customer's "what happened?" with a real timeline, not a scroll through three channels
- Stand it up in an afternoon — sign up, connect the monitoring, route one real service, done
- Treat incident response the way she treats everything else: declarable, callable from the terminal, reviewable in a pull request — not a browser tab she resents
- Avoid having to "become a part-time SRE" to keep the product up

### Challenges — What gets in this persona's way?

- Incident response is the last manual thing in an otherwise automated stack — deploys, tests, infrastructure, and reviews are all codified; who gets paged is a Slack channel and a shared calendar
- Fragmented signals: uptime checks in one tool, application errors in another, customer reports arriving by email, and nothing correlating them into a single incident
- No one to delegate to: hasn't hired a platform or SRE person and won't for 6+ months
- Reliability questions she can't answer confidently ("what's our actual MTTR?", "how many pages did we send last month, and how many were real?") — the data exists in four places and agrees in none
- The first enterprise prospect just sent a security questionnaire asking about her incident-response process, and the honest answer is "me"
- Allergic to long sales cycles and heavyweight implementations — she needs this working before the next launch
- Switching costs feel high once a tool is "working," even when it's paging the wrong person weekly — status quo bias is a competitor

## Demographics

### Age

**[INFERRED]** 28–42, with the modal Erin around 32–36. Source docs don't state an age; inference is from "Series A or earlier technical founder" demographic norms (recent technical co-founders are most commonly in their early-to-mid 30s).

### Income range

**[INFERRED]** Founder cash comp typically $120K–$220K base at seed/Series A, with the bulk of expected comp in equity. Net worth and income vary widely. Reference points: standard YC/SaaS founder comp benchmarks.

### Education

Bachelor's degree, often in CS, EE, math, or a related technical field. Some are dropouts (YC pattern) or self-taught engineers. Less commonly: MS/PhD in CS or a stint in a Big Tech infrastructure role (Google, Meta, Stripe, etc.) before founding.

### Location

Distributed across US tech hubs (SF Bay Area, NYC, Austin, Seattle) and remote-first founder hubs globally; engineering team is frequently distributed across time zones, which is exactly why the rotation problem shows up early. Buying decision typically made from US time zones.

## Story (details)

Erin uses Claude or Cursor every day and lives in Slack, Linear, Notion, GitHub, and the terminal. Information sources: Hacker News, X/Twitter (founder and infrastructure accounts), Lobsters, GitHub trending, podcasts like Lenny's, Acquired, and Latent Space, **[INFERRED]** founder Slack/Discord communities and YC alumni networks. She reads public postmortems for entertainment and treats new developer infrastructure (MCP, agent SDKs, CLI wrappers, Terraform providers) as worth a Saturday afternoon to wire up.

In her free time she's building — a side project, a hardware tinker, a weekend AI experiment — or recovering from building. **[INFERRED, but consistent with the doc's portrayal]** She reads founder-voice content (essays, not vendor reports) and is more persuaded by an honest "here's what's live now vs. what's coming" post than by polished marketing.

The thing the docs make explicit and worth restating: **Erin doesn't think about incident management. She thinks about shipping.** Marketing that lands with her leads with the outcome ("stop being the escalation policy") and explains the mechanic (Terraform provider, CLI, API) second. Marketing that leads with the mechanism loses her. She is also the clearest self-serve entry point {{COMPANY}} has: she signs up, routes one service, and either it works that afternoon or she closes the tab.
