# Negative Keyword Patterns

Common negative keyword categories for the search-terms-miner skill. These
patterns help identify queries that are unlikely to convert for a B2B SaaS
product like {{COMPANY}} (an incident management and on-call platform for
engineering teams).

## Universal Negatives

These apply to almost any B2B campaign:

**Job seekers (not buyers):**
- "jobs," "career," "hiring," "salary," "compensation," "interview,"
  "resume," "apply," "glassdoor," "indeed"
- Watch out: "on call compensation" is a job-seeker query *and* one of our
  strongest organic clusters. Block it in paid, keep ranking for it organically.

**Free/cheap seekers:**
- "cheap," "low cost," "budget," "discount," "coupon," "promo code"
- Exception: "free" is **not** a universal negative for {{COMPANY}} — the free
  tier (up to 5 responders) is the self-serve entry point. "free on call
  scheduling," "free incident management tool," and "free trial" are all valid.
  Block "free" only in combination with a template or DIY modifier.

**Educational/academic:**
- "PDF," "essay," "thesis," "research paper," "wikipedia," "coursera," "udemy"
- Exception: "research" alone may be valid commercial intent
- Exception: definition queries ("what is MTTR," "what is an error budget") are
  valid *organic* targets — block them in paid, not in the content plan

**DIY/template seekers:**
- "template," "spreadsheet," "excel," "google sheets," "DIY," "do it yourself"
- These users want to build a rotation in a spreadsheet rather than pay for one.
  They convert organically through the postmortem and policy template cluster,
  almost never through a click.

**Competitor reviews/complaints:**
- "[competitor] complaints," "[competitor] lawsuit," "[competitor] scam"
- Exception: In conquesting campaigns, you may want these

## Industry-Specific Negatives (Incident Management / On-Call)

### Nonbrand — Incident Mgmt

The word "incident" carries four unrelated commercial meanings. All three of the
non-software senses ship as shared phrase negatives on `Nonbrand — Incident Mgmt`:

- **Paperwork intent:** "incident report," "incident report form," "incident
  report template," "workplace incident," "accident report," "incident log book"
- **Public-safety intent:** "police incident," "traffic incident," "incident
  number," "road incident," "fire incident," "incident command system," "ICS 100"
- **Insurance / claims intent:** "incident claim," "liability incident,"
  "incident insurance"
- **Security-operations intent:** "security incident response," "SIEM," "breach
  notification," "forensics," "CSIRT," "incident response retainer" — adjacent
  but a different buyer and a different budget; {{COMPANY}} does not sell to it
- **Certification / training intent:** "incident commander certification,"
  "ITIL certification," "incident management course," "ICS training"

### On-call (the clinical and trade senses)

"On call" is dominated by healthcare and home services. This is the single
largest source of wasted spend on the category head terms, and the list is worth
auditing monthly rather than quarterly:

- **Clinical:** "doctor on call," "nurse on call," "on call physician," "on call
  pharmacist," "on call nurse triage," "vet on call," "on call room," "on call
  shift differential"
- **Trades and services:** "on call plumber," "on call electrician," "24 hour on
  call," "on call locksmith," "on call HVAC," "emergency on call service"
- **Staffing:** "on call shift," "on call worker," "on call employee rights,"
  "on call scheduling law," "predictive scheduling law"

Note the asymmetry: "on call scheduling software" and "on call rotation" are
core terms, while "on call scheduling" alone skews to workforce scheduling for
shift labor. Keep the unmodified two-word phrase as a negative and bid only on
the qualified variants.

### Wrong product category

- "observability," "APM," "log management," "distributed tracing" — {{COMPANY}}
  ingests from these; it does not replace them
- "ITSM," "service desk," "help desk software," "ticketing system,"
  "change management" — the enterprise suite motion we deliberately do not run
- "uptime monitoring," "website monitor," "ping test," "synthetic monitoring"
- "SMS gateway," "bulk SMS," "voice API" — matches on "alerting" and "paging"
  but is an infrastructure purchase, not ours
- "pager," "pager rental," "pager repair" — the physical device still has real
  search volume; block it as a broad negative everywhere

### Wrong company size or shape

- "enterprise ITSM," "for MSPs," "for hospitals," "for manufacturing," "NOC
  outsourcing," "managed service provider" — services-heavy motions
- "open source" — valid for a content play, negative for paid; these searchers
  are building it themselves this quarter

### Competitor terms (keyed to the {{COMPETITOR_*}} tokens)

Competitor names live in one campaign only. Add them as **phrase negatives on
every nonbrand and brand campaign** so `Competitor — Conquest` owns the auction
and the match data stays readable:

| Pattern | Where it is negative | Where it is a keyword |
|---------|---------------------|----------------------|
| `{{COMPETITOR_A_LOWER}}`, `{{COMPETITOR_B_LOWER}}`, `{{COMPETITOR_D_LOWER}}`, `{{COMPETITOR_F_LOWER}}` | `Brand — Core`, `Nonbrand — Incident Mgmt` | `Competitor — Conquest` |
| `"{{COMPETITOR_A_LOWER}} login"`, `"{{COMPETITOR_A_LOWER}} status"`, `"{{COMPETITOR_A_LOWER}} support"`, `"{{COMPETITOR_A_LOWER}} docs"` | every campaign, including Conquest | — |
| `"{{COMPETITOR_A_LOWER}} careers"`, `"{{COMPETITOR_A_LOWER}} funding"` | every campaign | — |

Rationale: existing-customer and job-seeker traffic on a competitor brand
converts at roughly a tenth of the rate of `alternative` and `vs` modifiers, and
it is what drags Conquest's quality score down. Keep `alternative`, `vs`,
`competitors`, `pricing`, and `review` modifiers live; block the rest.

### Government/compliance research

- "law," "regulation," "statute," "legal requirement," "government," "SLA
  penalty clause," "uptime guarantee law"
- These are informational queries that rarely convert via paid search
- Exception: Keep these if you have high-quality content targeting them organically

## Pattern-Based Rules

When mining search terms, apply these heuristic rules:

| Pattern | Action | Confidence |
|---------|--------|-----------|
| Contains "template" or "spreadsheet" | Add as phrase negative | High |
| Contains "jobs" or "careers" | Add as phrase negative | High |
| Contains "salary" or "pay" + job-seeker intent | Add as phrase negative | High |
| Contains a clinical or trade modifier ("nurse," "plumber," "physician") next to "on call" | Add as phrase negative | High |
| Contains "report" + "incident" with no software modifier | Add as phrase negative | High |
| Contains "free" + no signups in 14 days | Review — the free tier makes this ambiguous | Low |
| Single-word query with high spend, zero conversions | Review (may be too broad) | Medium |
| Query is a competitor name only (no modifier) | Review — may be valid conquesting | Low |
| Contains "how to" + informational intent | Review — may be worth organic, not paid | Medium |

## Negative Match Type Selection

- **Exact match negative** `[term]`: Use when the specific query is off-intent
  but related variants might be valid. Example: [on call pay] is negative, but
  "on call pay policy for engineers" could be valid.

- **Phrase match negative** `"term"`: Use when any query containing the phrase
  is off-intent. Example: "incident report template" — any query with this
  phrase is unlikely to convert.

- **Broad match negative** `term`: Use sparingly. Blocks any query containing
  all the negative words in any order. Can inadvertently block valid queries —
  `pager` is the one term worth this treatment, because the device sense never
  overlaps with ours.

## Maintenance Cadence

- Review and update negative lists weekly (via search-terms-miner)
- Audit the on-call clinical/trade list monthly — it drifts faster than the rest
- Cross-reference negatives across campaigns to avoid inconsistencies
- Audit for false negatives quarterly (are we blocking valid queries?)
- Share negative lists across campaigns using shared negative keyword lists
  in Google Ads
