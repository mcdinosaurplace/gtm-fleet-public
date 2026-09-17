---
name: revops-watchdog:data-hygiene-audit
description: >
  Monthly HubSpot data quality audit. Detects duplicate contacts and
  companies, missing required fields, malformed data (invalid emails,
  phones, country codes), orphan records (deals without contacts, contacts
  without companies), and stale records (>12mo no activity). References
  data entry SOPs for required field definitions.
---

# Data Hygiene Audit

## When This Runs

- **Standalone:** `/revops-watchdog data-hygiene-audit`
- **Typical cadence:** Monthly

## Inputs

- HubSpot contact, company, and deal records (via MCP or API)
- Email validation status fields (if populated)
- Last activity date fields

## Cross-Agent Input: SOPs

Search for SOPs that define required fields and data entry standards:
- `outputs/sop-mops-*.md` (lead routing, data entry, contact creation)
- Any SOP with `required_fields` or `data_entry` in the frontmatter

Extract from SOPs:
- Required fields per object type (contact, company, deal)
- Format standards (e.g., phone format, country code normalization)
- Allowed vs. disallowed property values

Fall back to a conservative required-field set if no SOPs found:
- Contact: email, first_name, last_name, lifecyclestage
- Company: name, domain
- Deal: dealname, pipeline, dealstage, amount (for non-existing-business)

## Audit Checks

### 1. Duplicate Detection

**Contacts:**
- Exact email match (should be impossible if email is unique, but check)
- Near-match: same first_name + last_name + company (different emails)
- Same phone number across multiple contact records

**Companies:**
- Exact domain match
- Near-match: same name (normalized: lowercase, strip common suffixes like
  "Inc", "LLC", "Ltd")
- Same website URL across multiple company records

### 2. Missing Required Fields

For each object type, count records missing any required field (from SOP
or fallback set). Output per-field counts.

### 3. Malformed Data

**Email validation:**
- Regex check: invalid format → flag
- Email validation status (if populated): `invalid`, `hard bounce`,
  `unknown` → flag

**Phone validation:**
- Check for phone number length in expected range (7-15 digits after
  country code)
- Flag entries that are clearly not phone numbers (e.g., "TBD", "N/A",
  alphanumeric strings)

**Country codes / geography:**
- Country field should be a standardized code or full name
- Flag contacts with country in one format and company in another
- Flag impossible combinations (e.g., timezone offset vs. country)

### 4. Orphan Records

**Contacts without companies:**
- Lifecycle stage >= Lead (i.e., not raw Subscriber)
- No `associated_company_id`
- For a B2B context, this is usually a data error

**Deals without contacts:**
- Deal has no associated contact
- This breaks attribution and is always a data error

**Contacts without email:**
- `email IS NULL` on a non-bouncing contact
- Indicates import error or stripped field

### 5. Stale Records

Contacts with no activity (no engagement, no property change, no
notes) in the past 12 months. Not always a problem — but in aggregate,
a signal that the database is accumulating dead weight.

Output: count and distribution by lifecycle stage.

## Output Format

```markdown
## Data Hygiene Audit — {Date}

### SOPs Loaded
- {list of SOP files referenced, or "No SOPs loaded — using fallback required-field set"}

### Summary
| Category | Records Flagged | Severity |
|----------|----------------|----------|
| Duplicates (contacts) | {N} | {MED if >0.5% of total, LOW otherwise} |
| Duplicates (companies) | {N} | {MED if >0.5% of total, LOW otherwise} |
| Missing required fields | {N} | {severity by %} |
| Malformed data | {N} | LOW |
| Orphan records | {N} | MED if >50, LOW otherwise |
| Stale records | {N} | LOW (informational) |

### Duplicates

**Contacts (exact email match — should be zero):**
| Email | Record Count | Contact IDs |
|-------|-------------|-------------|

**Contacts (near-match):**
| Name | Company | Email Variants |
|------|---------|---------------|

**Companies:**
| Domain / Name | Record Count | Company IDs |
|--------------|-------------|-------------|

### Missing Required Fields
| Field | Object | Records Missing | % of Total |
|-------|--------|----------------|-----------|

### Malformed Data
| Type | Example | Count |
|------|---------|-------|
| Invalid email format | {example} | {N} |
| Invalid phone | {example} | {N} |
| Malformed country | {example} | {N} |

### Orphan Records
| Type | Count | Sample IDs |
|------|-------|-----------|
| Contacts without companies (Lead+ stage) | {N} | {3-5 IDs} |
| Deals without contacts | {N} | {3-5 IDs} |

### Stale Records
- Total inactive 12+ months: {N}
- Distribution: Subscriber {N}, Lead {N}, MQL {N}, SAL {N}, SQL {N}
- Recommendation: {consider recycle workflow, archive, or leave}

### Recommended gtm-ops action
{If significant data quality drift: "Run /sop-gen to formalize data
entry rules"}
{If orphan deals: "Run /workflow-spec to design a deal association
enforcement workflow"}
```

## Anomaly Table Writes

One anomaly row per issue category exceeding threshold:

| Category | MED Threshold | HIGH Threshold |
|----------|--------------|---------------|
| Duplicate contacts (exact email) | >0 | >10 |
| Orphan deals (no contact) | >50 | >200 |
| Malformed email >0.5% of contacts | ✓ | — |
| Missing required field >5% of object | ✓ | — |

INSERT with `surface='data_hygiene'`.

## Handoff

One consolidated handoff to chief-of-staff with:
- Summary counts
- Top 3 urgent fixes
- Path to full audit output
- Recommended gtm-ops follow-up
