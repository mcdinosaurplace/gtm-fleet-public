# {{COMPANY}} Persona Context: Aaron the Platform Engineer (PRIMARY ICP — Content Engine)

> **Status: Primary ICP for the content engine.** Renamed from "Erin the Platform
> Engineer" to avoid collision with the existing `erin-technical-founder.md` persona.
> The three content-targeting personas are Aaron the Platform Engineer (primary for
> content topic scoring), Erin the Technical Founder, and Hannah the VP Engineering.
> Hannah remains the business buyer; Aaron is the technical champion — and at many
> companies, the person who actually runs the trial. All content agents read this doc alongside
> the brand pack before acting.
>
> **Pending:** HubSpot `hs_persona` enum value + `hubspot-filter-sets.md` row (needs the
> standard validation checklist in `README.md` before publishing in HubSpot).

## Who he is

The engineer who owns the paging stack at a mid-market B2B SaaS company (50–500 engineers)
and thinks in systems, not seats. He evaluates incident tools by reading the Terraform provider
docs before he books a demo. He has tried to codify an escalation policy in a competitor's product
and hit a partner-program wall. He wants a platform he can **declare**, not one he has to click.

**Core belief:** on-call is infrastructure, and infrastructure belongs in version control.

**Titles:** Staff Platform Engineer, Site Reliability Engineer, SRE Lead, Infrastructure Engineer,
Platform Team Lead, Developer Experience Lead, Head of Platform. Emerging: Reliability Engineer,
Production Engineering Lead, Internal Developer Platform Owner.

**Two origin stories, same mindset:** backend engineer who inherited the rotation, or an ops/sysadmin
who taught himself Terraform, Go, and Kubernetes. Age 27–41 (modal ~33), mostly US-based.

## The content mandate for this persona

**This is a role with no settled name.** Half of the Aarons carry an SRE title, half don't, and most
of the audience is one step behind him on tooling maturity. The job of {{COMPANY}}'s content is therefore:

1. **Make the complex feel less complex.** Signal correlation, ownership graphs, escalation
   semantics, error budgets, alert SLOs — explained clearly, never dumbed down. Assume
   intelligence, not prior knowledge.
2. **Lead with education.** Teach the practice before selling the product. Define the discipline,
   name the patterns, give people the vocabulary ("ownership as code", "signal-to-page ratio",
   "the 3 a.m. tax").
3. **Approachable and engaging.** {{COMPANY}} voice pillars apply in full: Clear, Authoritative,
   Approachable. Education-first does not mean dry — it means the reader leaves more
   capable than they arrived.
4. **Close loops.** Every piece should leave Aaron able to *do* something: a working `.tf` file,
   a routing rule, an alert-hygiene checklist, a mental model.

## Goals (what content should help him do)

- Build one ownership map — service to team to responder — that Engineering, Support, and Security all trust
- Define rotations, escalation policies, and routing rules as code, reviewed in a pull request like everything else
- Cut the page volume his team receives by 50%+ without losing a real incident
- Wire incident response into the tools the team already lives in — chat, the issue tracker, the deploy pipeline
- Stop being the human router who forwards pages to the right person at 3 a.m.
- Make the internal case that reliability tooling is platform work, not a line item Support owns

## Pain points / challenges

- **Clicked-together config:** rotations and escalation policies live in a web UI nobody reviews;
  the on-call setup drifts from the service catalog within a quarter.
- **Alert fatigue is measured in resignations:** his team receives far more pages than incidents,
  and the ratio is the reason two people left last year.
- **The automation chain breaks** at the moments that matter: a page fires, and acknowledging,
  reassigning, or suppressing it still requires a login.
- **Shadow tooling:** a cron job, a chat bot, and a spreadsheet rotation, because the official
  product can't express what his team actually does.
- **Internal skepticism:** must justify "another reliability tool" in business terms — hours
  reclaimed, incidents shortened, attrition avoided.
- **Trust anxiety about automation:** auto-resolve and auto-suppress need an audit trail,
  a dry-run mode, scoped tokens, and a way to explain what the system did and why.

## {{COMPANY}}'s differentiator for Aaron

**Ownership as code:** every rotation, escalation policy, routing rule, and service owner is a
Terraform resource, an API object, and a CLI command — on every plan, including the free tier.
Reads and writes. No partner program, no enterprise gate, no waitlist. (Competitors gate the API,
restrict it to read-only, or ship a provider that covers a third of the product — referenced in
content only as "traditional platforms" / "legacy tools".)

## Messaging rules

### What to say
- Lead with technical capability: provider docs, API examples, CLI snippets, a real `.tf` file
- Use systems language: correlate, route, declare, reconcile, ownership as code
- Reference the market shift: infrastructure and CI went declarative; on-call is the last click-ops holdout
- Acknowledge that most alert rules are bad and that this is a design problem, not a discipline problem — he knows; saying it earns respect
- Show the competitive gap without naming competitors: "Most incident platforms put the API behind
  an enterprise tier. {{COMPANY}} doesn't."

### What NOT to say (hard fails for the brand-voice editing stage)
- "Easy-to-use", "all-in-one" — signals {{COMPANY}} doesn't understand him
- "Never miss an alert again" — his problem is the opposite; this phrase loses him in one line
- "AI will triage your incidents for you" — triggers trust anxiety, alienates Hannah
- Feature checklists — invites breadth comparisons larger competitors win
- Competitor names in external content (existing rule; unchanged)

### Key messages
1. "Your on-call rotation should live in version control. Period."
2. "Stop being the human router between your monitors and your team."
3. "Most incident tools tell you something is wrong. {{COMPANY}} tells you whose it is."
4. "Declared by engineers. Trusted at 3 a.m."
5. "Reliability isn't heroics. Build it like infrastructure."

## Where he lives (research agent targets)

- LinkedIn: #SRE, #PlatformEngineering, #DevEx
- Communities: SRE Slack/Discord, r/sre and r/devops, CNCF and platform-engineering Slack channels
- Developer-adjacent: Hacker News incident-tooling threads, GitHub, Lobsters, changelog feeds
- Reads: the Google SRE books, incident write-ups and public postmortems, provider changelogs, engineering blogs
- Events: SREcon, KubeCon platform tracks, incident-response and reliability webinars

## Tone calibration

- **Tone priority:** educational confidence — technical precision without gatekeeping
- **Blog/guides:** humor A–B; engaging, concrete, example-led
- **Social/LinkedIn:** humor B; opinionated, pattern-naming, never snarky
- **Always:** assume he'll open the docs and check — never overclaim a technical capability

## Content strategy by funnel stage

- **Top (feels the pain, hasn't named it):** "State of On-Call" research report; the signal-to-page
  ratio benchmark; #PlatformEngineering LinkedIn campaign; open-source alert-hygiene recipes
- **Mid (researching):** "The platform engineer's incident stack" blog; alert-hygiene audit checklist;
  a reliability roundtable webinar; escalation-policy design patterns
- **Bottom (evaluating):** API docs + sandbox; "Your first routed page in nine minutes" tutorial;
  Terraform provider quickstart; migration guide off a click-ops incumbent

## Relationship to Hannah

Hannah feels the cost — MTTR on the board slide, two resignations citing on-call, an SLA credit
issued last quarter — and makes the business case. Aaron diagnoses the root cause and validates
the technical claim (reads the provider docs, runs a shadow rotation, pipes a real service through
in an afternoon). Reach both: Hannah with the business case, Aaron with the technical proof.
At companies under ~80 engineers they are frequently the same conversation.
