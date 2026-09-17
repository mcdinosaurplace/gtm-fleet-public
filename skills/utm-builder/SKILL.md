---
name: utm-builder
description: Generate UTM parameters and a standardized campaign name for {{COMPANY}} marketing campaigns. Applies {{COMPANY}}'s naming conventions and outputs copy-paste-ready UTM strings compatible with the {{COMPANY}} V0 marketing toolkit.
allowed-tools: Read
disable-model-invocation: true
---

# /utm-builder

Load the `gtm-ops` skill and read the UTM Naming Convention section of `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/stack.md` before proceeding.

## What to Ask

Collect the following from the user. Ask for all at once in a single message:

1. **Campaign theme / angle**: What is this campaign about? (e.g., "ownership as code for platform teams", "on-call rotation guide launch", "alert-hygiene audit")
2. **Campaign type**: paid / organic / email / event / content / partner
3. **Target audience**: founders / platform / eng-leaders / security / general
4. **Quarter and year**: (e.g., Q2 2026)
5. **Source(s)**: Which platform(s)? (e.g., LinkedIn, Google, newsletter, Hacker News)
6. **Medium(s)**: cpc / social / email / content / referral
7. **Destination URL(s)**: The base URL(s) to append UTM parameters to
8. **Content variant** (optional): Specific asset or creative name (e.g., "on-call-rotation-guide", "ad-variant-a")
9. **Paid keyword** (optional, paid search only): Primary keyword being targeted (e.g., `incident-response-platform`, `on-call-scheduling-software`)

## What to Produce

### 1. Campaign Name

Generate a standardized campaign name following {{COMPANY}}'s convention:
`{year}-{quarter}-{type}-{audience}-{theme}`

Example: `<year>-q2-paid-platform-ownership-as-code`

Provide 1–3 campaign name options if the theme could be interpreted multiple ways, and let the user confirm.

**Keep the UTM campaign aligned to the ad account.** The live campaigns are
`Brand — Core`, `Nonbrand — Incident Mgmt`, and `Competitor — Conquest`; their UTM
counterparts are `<year>-q2-paid-general-brand-defense`,
`<year>-q2-paid-eng-leaders-incident-management`, and
`<year>-q2-paid-eng-leaders-competitor-conquest`. A campaign name that cannot be
traced back to an ad group is a reporting problem later, not a naming preference.

### 2. UTM Parameter Set

For each source/medium combination, produce the full parameter set:

```
utm_source    = {source}
utm_medium    = {medium}
utm_campaign  = {campaign-name}
utm_content   = {content-identifier}  (if provided)
utm_term      = {keyword}             (paid search only)
```

### 3. Full UTM URLs

For each destination URL + source/medium combination, produce the complete tagged URL:

```
{destination-url}?utm_source={source}&utm_medium={medium}&utm_campaign={campaign-name}&utm_content={content}
```

Format as a clean list, one URL per line.

### 4. Campaign Tracking Summary

A copy-paste-ready summary block:

```
Campaign Name:   {campaign-name}
Quarter:         {Q# YYYY}
Type:            {type}
Audience:        {audience}
Theme:           {theme}

UTM Parameters:
  Source:     {source}
  Medium:     {medium}
  Campaign:   {campaign-name}
  Content:    {content}

Tagged URLs:
  {url-1}
  {url-2}
```

### 5. Naming Notes

Call out any deviations from {{COMPANY}}'s naming convention that the user should be aware of, and flag if any parameter values are non-standard.

## V0 Compatibility Note

These UTM parameters follow {{COMPANY}}'s standard naming convention and are designed to be compatible with the {{COMPANY}} marketing toolkit in Vercel's V0. If the V0 tool has specific input field names or format requirements that differ, let Scott know and adjust accordingly.
