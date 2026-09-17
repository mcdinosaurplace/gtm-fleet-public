---
name: content-researcher:social-listening
description: >
  Weekly sweep of external communities where Aaron the Platform Engineer (and
  secondary personas Erin and Hannah) live. Captures verbatim questions,
  pain points, and quote language with source URLs. Writes voice_bank entries
  and one research_packets row. Read-only on every external platform — no
  posting, no commenting, no engagement.
---

# Social Listening

## When This Runs

- **Tick integration:** Weekly (Mon), early in the sweep — before `topic-synthesizer`.
- **Standalone:** `/content-researcher social-listening`

## Inputs

- `context/personas/aaron-platform-engineer.md` — primary ICP; defines communities to sweep
- `context/personas/erin-technical-founder.md` — secondary; Hacker News, YC, founder Slack signals
- `context/personas/hannah-vp-engineering.md` — secondary; LinkedIn, engineering-leadership newsletters, conference trip reports
- Prior `voice_bank` rows (for dedup — avoid inserting exact-duplicate content)

## Tracked Sources and Queries

Run one or more web searches per source cluster. Capture the most recent
results (past 7 days when date filtering is available).

### Cluster A — LinkedIn (Aaron + Hannah primary)

**Hashtag sweeps** (search LinkedIn hashtag pages or run web search with
`site:linkedin.com`):

| Hashtag | Signal type | Primary persona |
|---------|------------|----------------|
| `#SRE` | Practice debates, war stories, role identity | Aaron |
| `#PlatformEngineering` | Tooling choices, internal-platform builds, "should the platform team own paging" | Aaron |
| `#oncall` | Rotation pain, fairness and comp complaints, handoff stories | Aaron, Hannah |
| `#incidentmanagement` | Severity-level arguments, process rollouts, migration stories | Hannah |
| `#DevOps` | Broad: toolchain frustration, automation gaps, webhook plumbing | Aaron |
| `#observability` | Where monitoring stops and paging starts — the boundary argument | Aaron |
| `#postmortem` | Review culture, template sharing, "we stopped writing them" | Hannah |

**What to capture:** opinions, questions, complaints, verbatim phrases that
name a pain point or describe a workflow problem. Ignore job postings and
vendor announcements.

**Search pattern:** `site:linkedin.com/posts "{query}" on-call OR incident OR
paging OR escalation` — vary the query per hashtag.

`#oncall` is the highest-yield hashtag and the one most polluted by clinical and
staffing posts. Filter on the presence of a second technical term (service,
alert, rotation, escalation, deploy) before capturing anything from it.

### Cluster B — Hacker News (Erin + Aaron)

Run searches against `hn.algolia.com` or `site:news.ycombinator.com`:

| Query | Signal type |
|-------|------------|
| `on-call` | Rotation design, handoff friction, "how does your team do this" |
| `incident management` | Tool evaluation and migration threads |
| `alert fatigue` | Signal-to-noise debates; the densest source of quotable language |
| `pager` OR `paged at 3am` | Burnout and attrition language, first-person |
| `terraform on-call` OR `incident management API` | Provider gaps and API gating — Aaron's exact frustration |
| `status page` | Incident comms; where the buying boundary gets drawn |
| `blameless postmortem` | Review practice, template shares, "does this actually work" |

Focus on threads with meaningful replies (>10 comments). Capture the
original question and the most-upvoted replies that name specific frustrations.
"Ask HN" threads about on-call rotations recur roughly quarterly and are worth
reading in full when one appears.

### Cluster C — Reddit

Target subreddits:

| Subreddit | Primary persona | What to look for |
|-----------|----------------|-----------------|
| `r/sre` | Aaron | SLO and error-budget questions, alert-hygiene practice, tool complaints |
| `r/devops` | Aaron | Alert routing, webhook plumbing, "how do you handle escalation" |
| `r/sysadmin` | Aaron | Paging setups at smaller shops; legacy escalation chains and phone trees |
| `r/kubernetes` | Aaron | Noisy default alerts, operator-generated pages, cluster-event floods |
| `r/ExperiencedDevs` | Hannah | Whether on-call should be mandatory, how to staff it, leadership framing |
| `r/startups` | Erin | First-rotation questions — "we're six engineers and one of us is always on" |
| `r/cscareerquestions` | Hannah, Erin | On-call compensation and burnout from the responder's side |

**Search pattern:** `site:reddit.com/r/{subreddit} on-call OR incident OR
escalation OR paging` for the past week.

`r/cscareerquestions` is included for one reason only: it is where on-call
compensation gets discussed in numbers. Do not capture career advice from it.

### Cluster D — Communities (public only)

These are public or publicly-indexed spaces; use web search for indexed
discussions:

- `site:sreweekly.com` — the editor's commentary around each link, and the
  threads that link back to it
- `"Rands Leadership Slack" #incident-response` — recaps, screenshots, and
  summaries shared publicly on LinkedIn or HN
- Public DevOps and platform-engineering Slack/Discord communities that publish
  open archives
- SREcon hallway threads — conference hashtags and public trip reports in the
  two weeks around an event

Capture any public threads discussing tooling, routing, ownership, or API access.

**Vendor communities are out of scope.** Do not sweep a competitor's user forum,
Slack, or community site. The signal there is shaped by their support motion and
by our own presence in the room, and the trust policy treats it as adversarial
input rather than market evidence.

### Cluster E — Product Hunt + GitHub (Aaron primary)

- Product Hunt: `site:producthunt.com "on-call" OR "incident" OR "alerting"` —
  new launches and comments from the past 30 days. Comments are richer than
  launch copy.
- GitHub: search for repos tagged `oncall`, `incident-response`,
  `alert-deduplication`, and incident/on-call Terraform providers — look at
  README content and open issues for verbatim user pain language.
- Issue threads on alert-dedup and routing tools are the single best source of
  *specific* technical complaint language anywhere in this sweep. A reproduction
  case with a "this is why we built our own" comment attached is worth ten
  LinkedIn posts.

### Cluster F — Publications (Hannah signal)

Scan recent articles for pain-point language (not vendor content):

- `site:sreweekly.com` — the commentary lines, not the linked articles
- `site:infoq.com` — architecture and reliability-practice coverage
- `site:thenewstack.io` — platform engineering and incident tooling coverage
- Public engineering-blog postmortems — the write-up itself is the artifact;
  what we want is the sentence where the team says what made the night hard
- DORA reports and the Google SRE books — practice authority for citation, not
  weekly signal; do not sweep them for verbatims

These are secondary signal; include only if a piece contains verbatim
community language (e.g., quotes from practitioners, survey data).

## Signal Capture Rules

### What qualifies for voice_bank

Include if it meets **all three criteria:**

1. **Verbatim:** The exact phrasing is preserved, not paraphrased.
   A question or complaint is more valuable than a summary.
2. **Pain or aspiration:** Describes a problem the persona has, a question
   they're asking, or a capability they wish existed.
3. **Source-referenceable:** Has a URL or at minimum a platform + date.

Exclude: vendor blog posts, press releases, job descriptions, general
industry news without practitioner voice.

### Anonymization

Social posts are public, so anonymization is not required. However:
- Do not store the author's full name if the post is from a small community
  where attribution could be sensitive (e.g., private-ish Slack archives shared
  online). Use role + company stage instead: "SRE lead at a 200-person startup."
- Public LinkedIn posts by named professionals: store verbatim with source URL.
  The author made the statement publicly.

### Persona tagging

Tag each entry to the best-fit persona:
- `aaron` — platform engineer, SRE, infrastructure engineer, head of platform;
  focused on APIs, Terraform, routing rules, alert hygiene
- `erin` — founder, CTO/CEO at an early-stage team; is the rotation herself, has
  no SRE hire yet, wants the thing to run without her
- `hannah` — VP/Head/Director of Engineering; owns MTTR, the on-call policy,
  retention, and the tooling budget; multi-system patchwork, stakeholder ROI
- `unknown` — cannot determine from context; use sparingly

### Theme tagging

Assign a `theme` label from the emerging clusters. Common starting themes:
- `api_access_gating` — frustration with platforms blocking, read-only-ing, or charging for API and provider access
- `automation_chain_breaks` — automation that works until a page fires and the ack, reassign, or suppress still needs a login
- `multi_system_patchwork` — rotation in one tool, escalation in another, the service catalog in a third
- `alert_noise_ratio` — far more pages than incidents; signal-to-page complaints, muted channels, ignored severities
- `oncall_fairness_burnout` — compensation, rotation equity, weekend load, resignations that cite the pager
- `shadow_it_workarounds` — a cron job, a chat bot, and a spreadsheet rotation standing in for the product
- `stakeholder_trust_anxiety` — selling auto-resolve and auto-suppress internally; audit trails, dry runs, approval gates
- `role_definition` — "who should own on-call," "what is a platform engineer" category-creation signals

Add new themes as they emerge. Do not force a theme if none fits — leave
`theme` as NULL and note it in the journal.

## Quiet Week Detection

Count `voice_bank` entries written in this run at the end of the sweep.
If the count is **< 10**, set `quiet_week = 1` on the `research_packets` row.
Log: `quiet_week = 1 — {N} entries captured, below 10-entry threshold.`

A quiet week is a finding, not a failure. Common causes: news cycle
dominated by unrelated events, all sources swept recently with no new threads,
communities on a holiday cycle.

## DEMO_MODE

When `DEMO_MODE=1` this skill does not run. The live sweeps are **skipped, never
simulated**: there is no fixture corpus for open-web search, and inventing plausible
community quotes would write fabricated verbatims into `voice_bank`, where
`topic-synthesizer` reads them as evidence and the fleet starts asserting market signal
nobody ever said. The no-fabrication boundary rule below is not suspended for a demo.

So: skip clusters A–F, write no `voice_bank` rows and no `research_packets` row from
this skill (and therefore no quiet-week flag — there was no sweep to be quiet), and
record the skip in the journal under `### Research Sweep`:

```
social-listening: skipped (DEMO_MODE — live web sweeps disabled)
```

The weekly Tick proceeds without it: `call-miner` runs against the fixture-backed
~~meeting notes (Grain) and the other skills run on the evidence they have. Topics
score lower on evidence breadth, which is the honest result — and the Tier 2 trust
floor is untouched, since this skill's `open_ugc` rows never cleared it anyway.

## Workflow

### Step 1 — Run source sweeps

For each cluster (A–F above), run the search queries via WebSearch. Process
in parallel where possible. Capture the raw results.

### Step 2 — Filter and extract signals

From raw results, select entries that meet the signal capture rules. For each:
- Extract the verbatim quote or question
- Identify the source URL and platform
- Tag persona, theme, entry_type (quote / question / pain_point), funnel_stage

**funnel_stage guidance:**
- `top`: role/category definition, "what is X" questions, aspirational language
- `mid`: solution evaluation, "which tool does X", comparisons
- `bottom`: technical specifics, "how do I connect X to Y", migration questions

### Step 3 — Dedup check

Before inserting, check for near-duplicate content:
```sql
SELECT content FROM voice_bank
WHERE source = ? AND created_at > date('now', '-30 days');
```
Skip entries where `content` is a substring of or near-identical to an
existing row. Paraphrased versions of the same statement from different
sources count as distinct (different source → different evidence signal).

### Step 4 — Write voice_bank rows

For each qualifying signal:

```sql
INSERT INTO voice_bank (
  agent, entry_type, source, trust_tier, persona, theme, content,
  source_ref, funnel_stage, captured_at, created_at
)
VALUES (
  'content-researcher', ?, 'social', ?, ?, ?, ?,
  ?, ?, ?, datetime('now')
);
```

### Trust tier — required, and it varies by cluster

`trust_tier` is NOT NULL with no default: an insert that omits it fails. This skill
is the only one that spans two tiers, so set it per cluster:

| Cluster | Tier | Why |
|---|---|---|
| A — LinkedIn | `open_ugc` | anyone can post |
| B — Hacker News | `open_ugc` | anyone can post |
| C — Reddit | `open_ugc` | anyone can post |
| D — Communities | `open_ugc` | anyone can post |
| E — Product Hunt comments, GitHub issues | `open_ugc` | anyone can author an issue body |
| F — Publications (SRE Weekly, InfoQ, The New Stack, public postmortems) | `attributed` | editorial content published by an identifiable organisation under its own name |

When in doubt, use `open_ugc` — the failure mode of over-trusting is that a
stranger's text becomes something {{COMPANY}} publishes as market evidence; the failure
mode of under-trusting is that a real signal needs one corroborating source.

**Consequence to understand, not to work around:** a topic evidenced *only* by
`open_ugc` cannot clear the Tier 2 submission floor, no matter how many distinct
sources it has — eight forum posts can be eight sock puppets. That is intended.
Surface such a cluster in the journal as a candidate rather than inflating its tier
to get it through. Full rationale: `docs/agent-content-trust-policy.md`.

### Step 5 — Write research_packets row

```sql
INSERT INTO research_packets (
  agent, packet_type, week_starting, source_count,
  quiet_week, summary, payload_path, created_at
)
VALUES (
  'content-researcher', 'social_listening',
  date('now', 'weekday 1', '-7 days'),  -- Monday of current run week
  ?,    -- count of sources scanned
  ?,    -- 0 or 1 quiet_week flag
  ?,    -- one-paragraph summary (see format below)
  NULL, -- no separate payload file; entries live in voice_bank
  datetime('now')
);
```

**Summary paragraph format:** `"Swept {N} source clusters. {N} new voice_bank
entries across {N} themes. Strongest signal: [{theme}] — [{N} entries,
example: '{verbatim snippet}']. {Quiet week note if applicable.}"`

## Output to Journal

In the Tick journal entry, under `### Research Sweep`, include:

```
[social_listening] → {source_count} sources, {voice_bank_count} new voice_bank entries
{quiet_week flag if <10 entries}
Top themes: {comma-separated list of themes with >2 entries}
```

## Boundary Rules

- **Read-only.** Never post, comment, reply, or engage on any platform.
- **External platform scope only.** Do not mine internal Notion pages,
  Slack messages, or Linear issues for voice signals — that is revops-watchdog/chief-of-staff's
  domain for operational intelligence.
- **Grain (sales calls) is call-miner's domain.** Do not pull sales-call
  transcripts from Grain here; those are handled by `content-researcher:call-miner`.
- **No fabrication.** If a source cluster returns zero results, log it.
  Do not invent representative quotes or synthesize composite signals.
