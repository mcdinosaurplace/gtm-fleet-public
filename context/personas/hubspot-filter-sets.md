---
revision: 2
purpose: Property filter sets to match HubSpot contacts to each of {{COMPANY}}'s four personas. Use these as the definition layer for HubSpot lists, workflows, and the existing `hs_persona` enum values.
---

# HubSpot Persona Filter Sets

Filter definitions for matching HubSpot contacts to Erin, Hannah, Anna, and Jake. Built from the HubSpot Contact and Company schemas. Geography intentionally omitted per request.

## Existing `hs_persona` enum mapping

The HubSpot `hs_persona` field already has four values that map almost directly to the four personas in this file. Recommend updating labels and using filter sets below to populate the field via workflow.

| `hs_persona` value | Current label | New label (recommended) | Persona file |
|---|---|---|---|
| `persona_3` | CTO at company under 100 people | Erin the Technical Founder | `erin-technical-founder.md` |
| `persona_1` | Most senior Engineering member | Hannah the VP Engineering | `hannah-vp-engineering.md` |
| `persona_2` | Most senior Finance member | Anna the Finance Leader | `anna-finance-leader.md` |
| `persona_4` | Most senior IT / Security member | Jake the IT & SecOps Leader | `jake-ops-leader.md` |

`persona_5` ("Can't match") and `persona_6` ("Don't contact") stay as-is.

## Available property reference (verified live)

**Contact properties used in filters:**

- `jobtitle` — free text (CONTAINS_TOKEN)
- `hs_seniority` — enum: `executive`, `vp`, `director`, `manager`, `senior`, `partner`, `owner`, `employee`, `entry`
- `hs_role` — enum: `finance`, `engineering`, `information_technology`, `operations`, `entrepreneurship`, `product`, `human_resources`, `accounting`, etc.
- `hs_sub_role` — enum: `founder`, `chief_executive_officer`, `chief_technology_officer`, `chief_financial_officer`, `chief_information_officer`, `chief_information_security_officer`, `software_engineer`, `devops_engineer`, `system_administrator`, `financial_controller`, etc.
- `hs_buying_role` — enum (decision_maker, influencer, blocker, champion, etc.)
- `hs_persona` — enum (`persona_1` … `persona_6`)

**Company properties used in filters:**

- `hs_employee_range` — string range. Verified live values: `1 - 10`, `11 - 50`, `51 - 250`, `251 - 1K`
- `hs_revenue_range` — string range. Verified live values: `$0 - $1M`, `$1M - $10M`, `$10M - $50M`, `$50M - $100M`, `$100M - $250M`
- `numberofemployees` — number
- `industry` — enum (~150 options); tech-relevant: `COMPUTER_SOFTWARE`, `INTERNET`, `INFORMATION_TECHNOLOGY_AND_SERVICES`, `COMPUTER_NETWORK_SECURITY`, `BIOTECHNOLOGY`, `COMPUTER_GAMES`, `MOBILE_GAMES`, `SEMICONDUCTORS`, `CONSUMER_ELECTRONICS`
- `lifecyclestage` — enum
- `{{company_slug}}_responders` — number (responder seats on the customer's {{COMPANY}} account, where known)
- `opsos_score_prospect`, `opsos_score_signup`, `opsos_score_usage`, `opsos_score_mrr` — {{ENRICHMENT_VENDOR}} enrichment scores

## Filter set 1 — Erin the Technical Founder

**Goal**: Match founders/CTOs/technical co-founders at small (under 50) software companies. Refines the current overly broad `persona_3` definition (which today includes presidents of trucking companies, real estate principals, etc.).

**Required match (all conditions, AND logic):**

- **`jobtitle`** CONTAINS_TOKEN ANY OF: `Founder`, `Co-Founder`, `CTO`, `Chief Technology Officer`, `CEO`, `Chief Executive Officer`, `Founder & CTO`, `Founding Engineer`
  - **OR** `hs_sub_role` IN: `founder`, `chief_technology_officer`, `chief_executive_officer`, `chief_product_officer`, `owner`
- **`hs_seniority`** IN: `executive`, `owner`, `partner`
- **Associated company `hs_employee_range`** IN: `1 - 10`, `11 - 50`
  - **OR** `numberofemployees` LTE `50`

**Strongly preferred (boost qualification confidence):**

- **Associated company `industry`** IN: `COMPUTER_SOFTWARE`, `INTERNET`, `INFORMATION_TECHNOLOGY_AND_SERVICES`, `COMPUTER_NETWORK_SECURITY`, `COMPUTER_GAMES`, `MOBILE_GAMES`, `SEMICONDUCTORS`, `BIOTECHNOLOGY`, `CONSUMER_ELECTRONICS`, `FINANCIAL_SERVICES`
- **`hs_role`** IN: `entrepreneurship`, `engineering`, `information_technology`, `product`
- **Associated company `hs_revenue_range`** IN: `$0 - $1M`, `$1M - $10M`

**Disqualifiers (NOT_IN):**

- `hs_sub_role` NOT IN: `realtor`, `property_manager`, `medical_doctor`, `nurse`, `attorney`, `lawyer`, `professor`, `teacher`, `retired`, `student`
- Associated company `industry` NOT IN: `LAW_PRACTICE`, `LEGAL_SERVICES`, `HOSPITAL_HEALTH_CARE`, `MEDICAL_PRACTICE`, `RELIGIOUS_INSTITUTIONS`, `RESTAURANTS`, `REAL_ESTATE` (validate — {{COMPANY}} has selective fit in regulated verticals that run their own software)
- Associated company `hs_employee_range` NOT IN: `251 - 1K`, `1K - 10K`, `10K+`

**HubSpot list logic (paste-ready):**
```
[Contact] hs_seniority IS ANY OF: executive, owner, partner
AND
([Contact] jobtitle CONTAINS ANY OF: founder, cto, chief technology, ceo, chief executive, founding engineer
 OR [Contact] hs_sub_role IS ANY OF: founder, chief_technology_officer, chief_executive_officer, chief_product_officer)
AND
[Company] hs_employee_range IS ANY OF: 1 - 10, 11 - 50
AND
[Contact] hs_sub_role IS NONE OF: realtor, property_manager, medical_doctor, nurse, attorney, lawyer, retired, student
```

## Filter set 2 — Hannah the VP Engineering

**Goal**: Match the most senior engineering leader at 250–1000 person companies, where the role is senior enough to own the on-call policy and the tooling budget. Refines current `persona_1` (which includes Engineering Managers and Senior Engineers who are champions, not buyers).

**Required match (all conditions, AND logic):**

- **`hs_role`** IS `engineering`
  - **OR** `hs_sub_role` IN: `chief_technology_officer`, `vice_president_of_engineering`
  - **OR** `jobtitle` CONTAINS_TOKEN ANY OF: `VP Engineering`, `VP of Engineering`, `Vice President of Engineering`, `Head of Engineering`, `Director of Engineering`, `Senior Director of Engineering`, `Head of Platform`, `Head of Infrastructure`, `Director of Platform Engineering`, `Head of Reliability`, `Director of SRE`, `VP Platform`
- **`hs_seniority`** IN: `executive`, `vp`, `director`
- **Associated company `hs_employee_range`** IN: `51 - 250`, `251 - 1K`
  - **OR** `numberofemployees` BETWEEN `150` AND `1000`

**Strongly preferred:**

- **Associated company `industry`** IN: `COMPUTER_SOFTWARE`, `INTERNET`, `INFORMATION_TECHNOLOGY_AND_SERVICES`, `COMPUTER_NETWORK_SECURITY`, `FINANCIAL_SERVICES`, `MARKETING_AND_ADVERTISING`, `BIOTECHNOLOGY`, `MEDIA_PRODUCTION`
- **Associated company `hs_revenue_range`** IN: `$10M - $50M`, `$50M - $100M`

**Disqualifiers:**

- `hs_seniority` NOT IN: `entry`, `employee`, `manager` (Engineering Managers are champions, not buyers — route them to Aaron once that persona ships)
- `jobtitle` NOT CONTAINS_TOKEN ANY OF: `Sales Engineer`, `Solutions Engineer`, `Support Engineer`, `QA`, `Test`, `Recruiter`, `Technical Recruiter`, `Engineering Coordinator`, `Program Manager` (adjacent titles that match on the word "engineering" but are not the buyer)

**HubSpot list logic:**
```
[Contact] hs_seniority IS ANY OF: executive, vp, director
AND
([Contact] hs_role IS: engineering
 OR [Contact] jobtitle CONTAINS ANY OF: vp engineering, vice president of engineering, head of engineering, director of engineering, head of platform, head of infrastructure, director of platform engineering, head of reliability, director of sre, vp platform)
AND
[Company] hs_employee_range IS ANY OF: 51 - 250, 251 - 1K
AND
[Contact] jobtitle DOES NOT CONTAIN ANY OF: sales engineer, solutions engineer, support engineer, qa, test, recruiter, coordinator, program manager
```

## Filter set 3 — Anna the Finance Leader

**Goal**: Match the most senior finance person at companies where {{COMPANY}} is closing annual contracts. Per interview: most common once the deal crosses ~75 responder seats, but exists across stages — under ~40 engineers, "Anna" is often the CTO wearing the finance hat. Filter accommodates that flexibility with two paths.

**Required match — Path A (dedicated finance leader):**

- **`hs_role`** IS `finance`
  - **OR** `hs_sub_role` IN: `chief_financial_officer`, `financial_controller`, `financial_analyst`, `accounting_manager`
  - **OR** `jobtitle` CONTAINS_TOKEN ANY OF: `CFO`, `Chief Financial Officer`, `VP Finance`, `VP of Finance`, `Head of Finance`, `Director of Finance`, `Controller`, `Head of Accounting`, `Finance Lead`
- **`hs_seniority`** IN: `executive`, `vp`, `director`
- **Associated company `hs_employee_range`** IN: `11 - 50`, `51 - 250`, `251 - 1K`

**Required match — Path B (CTO wearing finance hat at small co):**

- Already qualifies as Erin (filter set 1) AND
- Associated company `hs_employee_range` IN: `1 - 10`, `11 - 50` AND
- No other contact at the same company has `hs_persona` = `persona_2`
  - In HubSpot list logic, this is approximated by also tagging Anna on Erin records when company size is `1 - 10` or `11 - 50`. Mark these in a separate list (`Anna-via-CTO`) to avoid double-counting.

**Strongly preferred:**

- **Associated company `industry`** IN: tech-relevant industries (same list as Erin) plus `FINANCIAL_SERVICES`, `MANAGEMENT_CONSULTING`, `ACCOUNTING`
- **`hs_buying_role`** IS `decision_maker` or `economic_buyer`

**Disqualifiers:**

- `hs_seniority` NOT IN: `entry`, `employee`, `manager` (excludes "Assistant Manager - Finance Operations - P2P - AP" which currently appears mistagged)
- `jobtitle` NOT CONTAINS_TOKEN ANY OF: `Accounts Payable`, `Accounts Receivable`, `Bookkeeper`, `Junior`, `Associate`, `Analyst` (unless title also contains `Senior`)
- Exclude contacts where `jobtitle` contains `Operations` without a finance modifier (e.g., "Finance Operations" coordinators get caught here)

**HubSpot list logic — Path A:**
```
[Contact] hs_seniority IS ANY OF: executive, vp, director
AND
([Contact] hs_role IS: finance
 OR [Contact] jobtitle CONTAINS ANY OF: cfo, chief financial, vp finance, head of finance, director of finance, controller, head of accounting, finance lead)
AND
[Company] hs_employee_range IS ANY OF: 11 - 50, 51 - 250, 251 - 1K
AND
[Contact] jobtitle DOES NOT CONTAIN ANY OF: accounts payable, accounts receivable, bookkeeper, junior, associate
```

## Filter set 4 — Jake the IT & SecOps Leader

**Goal**: Match senior IT and security leaders who are influencer-blockers in the deal motion. Refines current `persona_4` (which today is grossly broad — currently catches "Senior CX Operations Manager", "Field Service Technician", "Desktop Support Lead", "Operations Manager – Data Furnishing" — none of which are the right Jake).

**Required match (all conditions, AND logic):**

- **`hs_role`** IS `information_technology`
  - **OR** `hs_sub_role` IN: `chief_information_officer`, `chief_information_security_officer`
  - **OR** `jobtitle` CONTAINS_TOKEN ANY OF: `CISO`, `Chief Information Security Officer`, `CIO`, `Chief Information Officer`, `Head of Security`, `Head of IT`, `Director of IT`, `VP IT`, `VP of Information Technology`, `Director of Security`, `Director of Security Operations`, `Head of Information Security`, `Security Engineering Manager`, `Head of Corporate Engineering`, `GRC Lead`
- **`hs_seniority`** IN: `executive`, `vp`, `director`
- **Associated company `hs_employee_range`** IN: `51 - 250`, `251 - 1K` (Jake mostly doesn't exist as a dedicated role under 50 people — his review is absorbed by Aaron)

**Strongly preferred:**

- **Associated company `industry`** IN: `COMPUTER_SOFTWARE`, `INTERNET`, `INFORMATION_TECHNOLOGY_AND_SERVICES`, `COMPUTER_NETWORK_SECURITY`, `FINANCIAL_SERVICES`, `BIOTECHNOLOGY`
- **`hs_buying_role`** IS `influencer` or `blocker`

**Disqualifiers (critical — current persona_4 is heavily polluted by these):**

- `jobtitle` NOT CONTAINS_TOKEN ANY OF:
  - `Customer`, `CX`, `Customer Experience`, `Customer Success` (excludes CX Ops Managers)
  - `Help Desk`, `Service Desk`, `Desktop Support`, `Technician`, `Field Service` (excludes IT support ICs — not the reviewer)
  - `Sales Operations`, `Revenue Operations`, `RevOps`, `Marketing Operations`, `MOps` (different personas)
  - `Logistics`, `Warehouse`, `Manufacturing`, `Production`, `Plant`, `Clinical` (industry-specific ops)
  - `Physical Security`, `Facilities`, `Guard` (wrong kind of security)
  - `Talent Operations`, `Workplace Operations` (wrong function)
  - `Trading Operations`, `Treasury Operations` (finance-adjacent, not Jake)
- `hs_sub_role` NOT IN: `customer_success`, `customer_service_specialist`, `sales_operations`, `support_specialist`, `technical_support_specialist`, `production_manager`, `logistics_manager`, `office_manager`, `office_management`, `facilities`, `quality_assurance_manager`, `quality_assurance_specialist`

**HubSpot list logic:**
```
[Contact] hs_seniority IS ANY OF: executive, vp, director
AND
([Contact] jobtitle CONTAINS ANY OF: ciso, chief information security, cio, chief information officer, head of security, head of it, director of it, vp it, director of security, director of security operations, head of information security, security engineering manager, head of corporate engineering, grc lead)
AND
[Company] hs_employee_range IS ANY OF: 51 - 250, 251 - 1K
AND
[Contact] jobtitle DOES NOT CONTAIN ANY OF: customer, cx, help desk, service desk, desktop support, technician, field service, sales operations, revenue operations, marketing operations, logistics, warehouse, manufacturing, production, plant, clinical, physical security, facilities, talent operations, workplace operations, treasury, trading
```

## Implementation notes

- **Pollution check first.** Sample data confirms the existing `persona_4` enum value contains a large amount of IT-adjacent noise (CX Ops, Desktop Support, Field Service Technician). Recommend a one-time cleanup workflow that re-evaluates all current `persona_4` contacts against the new filter and drops mismatches to `persona_5`.
- **Anna Path B is intentionally narrow.** Only run this when explicitly needed for finance-leader campaigns; the default `persona_2` should remain dedicated finance leaders.
- **`hs_employee_range` boundaries.** Erin caps at `11 - 50`. Hannah starts at `51 - 250`. There is no overlap by design — an Erin at a 300-person company is no longer Erin; she's a CTO who now has a Hannah reporting to her.
- **Aaron sits inside Hannah's companies, not beside them.** When the Aaron filter ships, expect a large share of Aaron contacts to share an associated company with a Hannah contact. That is correct and should not be de-duplicated — they are two roles in one buying group.
- **Keep `jobtitle` CONTAINS_TOKEN logic case-insensitive.** HubSpot's CONTAINS_TOKEN matching is case-insensitive by default, so the lowercase examples in the list logic blocks will match correctly.
- **Refresh quarterly.** Job titles drift, especially in platform and reliability roles where the vocabulary is still settling. Re-run sample audits against filter sets each quarter and prune `jobtitle` keyword lists.

## Suggested next steps

- Update `hs_persona` enum labels in HubSpot to reflect the new persona names
- Build active lists in HubSpot using the four filter sets above to size each persona accurately
- Build a Sales Ops workflow that re-evaluates `hs_persona` on contact create + on jobtitle change, applying these filters
- Run a one-time cleanup audit on existing `persona_2` and `persona_4` contacts (highest pollution risk based on samples)
- Validate Anna and Jake company-size cutoffs against actual closed-deal data (interview noted Anna shows up across stages with flexibility — confirm with closed-won analysis)
