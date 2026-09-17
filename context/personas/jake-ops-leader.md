---
persona: Jake the IT & SecOps Leader
status: speculative
buyer_role: influencer_blocker
revision: 2
sources:
  - {{company_slug}}-on-call-buyer-research.docx
  - {{COMPANY}}-Positioning.docx
  - Synthesized for the {{COMPANY}} demo profile
notes: Speculative draft. Validate inferred fields against HubSpot data before publishing.
---

# Jake the IT & SecOps Leader

Speculative persona. HubSpot persona blocks below are formatted to paste field-by-field. Items marked **[INFERRED]** are not stated directly in the source documents and should be validated against HubSpot contact data before publishing.

## Name

Jake the IT & SecOps Leader

## Description

The identity, security, and internal-systems owner who shows up as an influencer in {{COMPANY}} deals — most often at Series B and later, but in lighter forms earlier. Jake doesn't sign the contract, but he can stop one by flagging a missing SSO tier, an unanswered security questionnaire, or a tool that creates another unmanaged identity surface. His job is to make sure new tools inherit the company's access model and produce evidence an auditor will accept. If {{COMPANY}} can't be provisioned, de-provisioned, and logged like everything else, Jake will say so — and he says it in writing.

## Internal Notes

### Roles — What kinds of jobs does this persona have?

- Head of IT, Director of IT, Head of Security, Director of Security Operations, CISO, Security Engineering Lead
- At pre-Series A: often combined with another role — a platform engineer who "owns SSO," or absorbed into Aaron's remit entirely
- At Series A–B: typically a dedicated IT lead or a first security hire, often ex-consulting or ex-MSP
- **[INFERRED]** Common adjacent titles: "Head of Corporate Engineering," "GRC Lead," "Manager, Security Operations"

### Goals — What is this persona trying to do?

- Put every SaaS tool behind SSO with SCIM provisioning, so an offboarding is one action instead of eleven
- Keep the audit evidence trail intact: who had access, who changed the escalation policy, who acknowledged the page, and when
- **[INFERRED]** Drive adoption of a single incident process across Engineering, Support, and Security so a security event and a service outage don't run on separate rails
- Manage vendor risk and security review: SOC 2 Type II report, data residency, subprocessor list, retention policy, breach notification terms
- **[INFERRED]** Reduce the tax of "identity debt" — each tool with local accounts is an account he will have to clean up during an access review
- Make sure the data leaves the platform cleanly: audit logs into the SIEM, incident records into the ticketing system, no manual export step

### Challenges — What gets in this persona's way?

- Tools that look great in a demo but put SSO behind the top pricing tier and SCIM behind a sales call
- Notification platforms that phone, text, and push to personal devices with no policy controls and no retention story
- Security review is slow; vendors that can't produce a SOC 2 report or answer an infosec questionnaire in under a week stall procurement past the quarter
- Audit data trapped in a vendor console — he can't get access-change history into the SIEM without a person exporting a CSV
- **[INFERRED]** Cross-functional pressure: Engineering wants speed, Support wants a shared process, Legal wants retention limits. Tools that solve for one and ignore the others fail his review
- **[INFERRED]** Allergic to vendors that answer a security question with a marketing page instead of a document

## Demographics

### Age

**[INFERRED]** 30–48, modal 35–42. Most IT and security leaders at this stage are mid-career — typically 8–18 years of experience.

### Income range

**[INFERRED]** $160K–$260K base + equity at Series A–B; CISO comp spreads higher. References: *Strata Comp* and *Rung* security-leadership data.

### Education

**[INFERRED]** Bachelor's degree common, often in CS, information systems, or an unrelated field followed by a career switch. Certifications carry more weight than degrees in this population: CISSP, CISM, Security+, and cloud-provider security certifications. Not stated in source docs.

### Location

**[INFERRED]** Predominantly US-based at HQ; sometimes in the operating heart of a remote-first company (NYC, Austin, Toronto, London). Confirm via HubSpot data.

## Story (details)

Jake's information diet is dense with practitioner content. He reads *Lockbox Weekly*, *Blastradius*, the national cyber agency's advisory feed, **[INFERRED]** the Fleet & Endpoint and IT-leadership Slacks, GRC Commons and detection-engineering communities on Slack/Discord, and vendor postmortems whenever a peer company has an incident. His tool stack: Warden ID for identity, Anchorpoint for endpoints, a SIEM he complains about, Relayworks for security automation, a compliance-automation platform that generates his SOC 2 evidence, and Linear for the work.

In free time **[INFERRED]** he reads incident and failure analysis across industries (aviation, medicine, industrial) and is the person at the company who actually maintains the access-review spreadsheet.

Marketing that lands with Jake leads with two things: access-model proof (SSO/SAML on every paid tier, SCIM provisioning, scoped API tokens, immutable audit log — these are *exactly* his language) and evidence he can file (a SOC 2 Type II report available under NDA, a public trust center, a written retention and subprocessor policy). The "ownership as code" framing is a near-perfect fit for him too, for a different reason than Aaron: a rotation defined in Terraform is a rotation with a reviewable change history, which is the artifact his auditor asks for. He is the persona most likely to convert from blocker to advocate once the security file is clean — and the most likely to kill the deal quietly if it isn't.
