---
name: lead-score-doc
description: Document {{COMPANY}}'s lead scoring model — behavioral signals, firmographic weights, MQL/SAL thresholds, decay rules, and HubSpot property mapping.
allowed-tools: Read Write
disable-model-invocation: true
---

# /lead-score-doc

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/funnel.md` before proceeding.

## What to Ask

If the user hasn't provided the scoring model, ask:
- Do they want to **document an existing model** (in which case ask them to describe it or paste the logic) or **design a new one from scratch**?
- What are the current MQL and SAL score thresholds (if known)?
- Are there any negative scoring signals in use?

If designing from scratch, use {{COMPANY}}'s known buyer personas (Aaron the Platform Engineer, Erin the Technical Founder, Hannah the VP Engineering) and funnel context to propose sensible defaults. The job-title lists in `context/personas/hubspot-filter-sets.md` are the source of truth for every title-match row below — do not invent a second list here.

## What to Produce

Generate a lead scoring documentation with these sections:

### 1. Model Overview

- Model name and version
- Scoring tool: HubSpot contact score property
- Threshold summary table: Score range → Stage

| Score Range | Designation |
|-------------|-------------|
| 0–24 | Unqualified |
| 25–49 | Nurture |
| 50–74 | MQL candidate |
| 75+ | MQL — route to Sales |

(Adjust thresholds to match what the user provides.)

### 2. Behavioral Signals

| Signal | Points | Notes |
|--------|--------|-------|
| Content download | +N | Gated asset — high intent |
| Webinar / event registration | +N | |
| Webinar / event attendance | +N | Attended > Registered |
| Demo request | +N | Highest intent signal on the sales-led path |
| Pricing page visit | +N | |
| Docs, API reference, or Terraform provider page visit | +N | Aaron's evaluation starts here, not on the pricing page |
| Blog visit | +N | Low weight |
| Email click | +N | |
| Campaign conversion event ({{ENRICHMENT_VENDOR}}) | +N | Marketing signal via {{ENRICHMENT_VENDOR}} |

**Product-usage signals (self-serve path).** These are the highest-signal
behaviors {{COMPANY}} has and the ones the CRM cannot see yet — the product
telemetry integration is the open dependency. Document them now so the model is
ready when the pipeline lands; until then, score them as 0 and flag the gap.

| Signal | Points | Notes |
|--------|--------|-------|
| Free-tier workspace created | +N | The primary self-serve entry point |
| First routed page within 7 days (activated workspace) | +N | The activation metric; strongest leading indicator of expansion |
| API token or Terraform provider configured | +N | Aaron is in the account, not just the docs |
| Responder seats crossed 5 (free-tier ceiling) | +N | The Detour trigger — jumps straight to SAL |
| Second team or service onboarded | +N | Expansion signal |
| No routed page 14 days after signup | 0 | Not negative — an unactivated workspace is a nurture case, not a disqualification |

### 3. Firmographic Signals

| Attribute | Criteria | Points |
|-----------|----------|--------|
| Company size | `1 - 10` / `11 - 50` | +N (Erin band) |
| Company size | `51 - 250` / `251 - 1K` | +N (Aaron and Hannah band) |
| Company size | Above `1K` | +N (or 0 — outside ICP; the enterprise ITSM motion is not ours) |
| Engineering headcount band | 50–500 engineers | +N — the single most predictive firmographic, and the one most often missing |
| Geography | US-based | +N |
| Funding stage | Pre-seed → Series A | +N (Erin ICP) |
| Funding stage | Series B–C | +N (Hannah ICP) |
| Industry | `COMPUTER_SOFTWARE` / `INTERNET` / `INFORMATION_TECHNOLOGY_AND_SERVICES` / `COMPUTER_NETWORK_SECURITY` | +N |
| Job title match | Founder / CEO / CTO / Founding Engineer | +N (Erin) |
| Job title match | Site Reliability Engineer / SRE Lead / Staff Platform Engineer / Infrastructure Engineer / Head of Platform | +N (Aaron) |
| Job title match | VP Engineering / Head of Engineering / Director of Engineering / Director of Platform Engineering / Head of Reliability / Director of SRE | +N (Hannah) |
| `{{company_slug}}_responders` | Known seat count on an existing {{COMPANY}} account | +N — a free-tier workspace with an unlinked company record is the most common cause of a false-negative score |

### 4. Negative Signals

| Signal | Points | Reason |
|--------|--------|--------|
| Unsubscribed from email | −N | Disengaged |
| Marked spam | −N | Hard disqualifier |
| Competitor domain | −N | Competitive account |
| Adjacent "engineer" title (Sales Engineer, Solutions Engineer, Support Engineer, QA, Technical Recruiter) | −N | Matches on the word, not the role — the largest source of persona pollution |
| Freemail domain with no company association | −N | Usually a free-tier signup that has not been unified with its company record; suppress the score, do not disqualify the person |
| Inactivity (N days no engagement) | −N | Score decay |

### 5. Score Decay Rules

- Behavioral score decays: −N points per [X days] of no engagement
- Decay applies to behavioral signals only; firmographic score is static
- HubSpot implementation: workflow fires on last engagement date > N days

### 6. HubSpot Property Mapping

| Score Component | HubSpot Property | Notes |
|----------------|-----------------|-------|
| Total score | `hs_lead_score` (or custom) | |
| Behavioral score | Custom property | |
| Firmographic score | Custom property | |
| Last score update | Custom date property | |
| MQL threshold crossed date | `hs_lifecyclestage` transition date | |

### 7. {{ENRICHMENT_VENDOR}} Integration Notes

Note any behavioral signals that flow into HubSpot scoring via {{ENRICHMENT_VENDOR}} (e.g., campaign conversion events, content downloads triggered through a campaign). These should be documented as {{ENRICHMENT_VENDOR}}-sourced signals with the relevant {{ENRICHMENT_VENDOR}} event name.

### 8. Known Issues and Gaps

Flag data completeness issues (e.g., firmographic properties not consistently populated), decay logic not yet implemented, or signals not currently tracked.

## Output

Save as `lead-score-doc-v{version}-{date}.md` in the user's outputs folder and present the file link. Display the Model Overview threshold table and Behavioral Signals table inline in chat.
