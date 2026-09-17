# Google Ads Format Reference

## Responsive Search Ads (RSA) — Field Limits

| Field | Max Characters | Max Count per Ad |
|-------|---------------|------------------|
| Headline | 30 | 15 |
| Description | 90 | 4 |
| Final URL | 2048 | 1 |
| Display path (path 1) | 15 | 1 |
| Display path (path 2) | 15 | 1 |

Google recommends: at least 5 unique headlines, 2 unique descriptions. More assets = more combinations to test.

## Character Counting Rules
- Count spaces, punctuation, and special characters. "The pages stop arriving." = 24 characters including the period; "On-Call Without the Noise" = 25; "Clear Ownership, Fast Fixes" = 27. All three clear the 30-character headline limit with room for a hyphenated variant.
- Dynamic keyword insertion tokens like `{KeyWord:Default}` count as the token itself for limit purposes, but Google renders the actual keyword at serving time
- Emojis count as 2 characters each — avoid in search copy unless explicitly tested
- The em dash in a campaign name (`Nonbrand — Incident Mgmt`) is one character, but it is not a copy field — campaign and ad group names have no limit that matters here. Keep the spelling identical to the account, or the bulk upload creates a second campaign.

## Pinning
Headlines and descriptions can be "pinned" to specific positions (Pin to H1, Pin to H2, etc.). Avoid over-pinning — Google's machine learning optimizes combinations, but only when it has freedom to test. Pin only when a specific message must always appear (e.g., a legal disclaimer, a brand name).

## Asset Strength Rating
Google rates each ad's "Ad Strength" from Poor → Average → Good → Excellent based on:
- Number of unique headlines and descriptions
- Distinctiveness (avoid repeating the same keywords across all headlines)
- Relevance to the ad group's keywords

Aim for Good or Excellent. Excellent typically requires 8–10 unique, varied headlines.

## Bulk Upload Column Spec (Google Ads Editor / CSV Import)

Required columns for bulk upload:

```
Campaign,Ad group,Headline 1,Headline 2,Headline 3,Headline 4,Headline 5,
Description 1,Description 2,Final URL,Path 1,Path 2
```

Optional (for full RSA):

```
Headline 6 through Headline 15,Description 3,Description 4
```

Row format (taken from the live {{COMPANY}} account, so the campaign and ad group strings match on import):
```csv
"Nonbrand — Incident Mgmt","Nonbrand — Incident Response","Incident Management Tool","Cut MTTR in Half","On-Call Without the Noise","Route Pages to the Owner","Free 14-Day Trial","Cut mean time to resolution without paging half the company.","Ownership, routing, and review in one place. Free for 14 days.","https://{{COMPANY_DOMAIN}}/product/incident-response","Incident","Response"
```

## Quality Score Components

| Component | Weight | How to Improve |
|-----------|--------|----------------|
| Expected CTR | High | Better headline relevance to keyword intent |
| Ad Relevance | Medium | Match headline language to keyword theme |
| Landing Page Experience | High | Fast load, relevant content, clear CTA on landing page |

Quality Score is per keyword, not per ad. An ad may score differently across the keywords in an ad group.

## Common Optimization Mistakes
- **Too-similar headlines**: All 15 headlines saying the same thing in slightly different words. Google has little to test.
- **Over-pinning**: Pinning 10 of 15 headlines removes Google's ability to learn.
- **Keyword stuffing**: Repeating the keyword in every headline looks spammy and Google penalizes it.
- **Ignoring landing page match**: Low Quality Score is often a landing page problem, not a copy problem. Check that the landing page mirrors the ad's promise.
- **One ad per ad group**: RSAs benefit from 2–3 ads per ad group so Google can compare performance across different copy directions.
