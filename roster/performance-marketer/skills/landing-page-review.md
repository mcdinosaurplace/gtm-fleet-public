---
name: performance-marketer:landing-page-review
description: >
  Landing page quality assessment through a search performance lens. Evaluates
  message match (ad copy to LP alignment), Quality Score LP experience factors,
  Core Web Vitals impact on ad performance, mobile UX, and form friction. Scoped
  to what affects search performance — not a full CRO audit.
---

# Landing Page Review

## When This Runs

- **Standalone:** `/performance-marketer landing-page-review`
- **Typical cadence:** Ad hoc, triggered by Quality Score issues, high bounce
  rates on ad traffic, or CPA spikes with no obvious ad-side cause

## Inputs

- Landing page URL(s) to review
- Associated ad copy (headlines, descriptions) pointing to the page
- Google Ads Quality Score data for the relevant ad groups (specifically the
  LP Experience component)
- PageSpeed Insights / Core Web Vitals data
- Optional: GA4 behavior data (bounce rate, time on page, conversion rate
  for paid traffic vs. organic)

## Analysis Framework

### 1. Message Match

The strongest signal for LP experience and conversion rate is alignment between
what the ad promises and what the page delivers.

**Check:**
- Does the LP headline reinforce the ad headline? (Exact match not required,
  but semantic alignment is critical)
- Does the LP lead with the same benefit/outcome the ad promises?
- Is the CTA on the LP consistent with the ad's implied next step?
- Does the LP address the same persona the ad targets?

**Scoring:**
| Score | Criteria |
|-------|---------|
| Strong | Headline echoes ad, benefit reinforced above fold, CTA matches |
| Moderate | Benefit present but buried, or headline is generic |
| Weak | LP content doesn't reflect ad promise, or is a generic homepage |

### 2. Quality Score LP Experience Factors

Google evaluates LP experience based on:

| Factor | What Google Checks | How to Diagnose |
|--------|-------------------|----------------|
| **Relevance** | Does LP content match the keyword intent? | Check if the target keyword or synonyms appear in headline, H1, body |
| **Transparency** | Is it clear what the business does? | About info, contact details, privacy policy |
| **Navigation** | Can users find what they need easily? | Clear nav, no interstitials blocking content |
| **Load speed** | Does the page load fast? | Core Web Vitals — see section 3 |
| **Mobile UX** | Is the page usable on mobile? | Responsive design, tap targets, text readability |

If the QS LP Experience component shows "Below Average":
- Prioritize the weakest factor (often load speed or relevance)
- Specific fix recommendations for each

### 3. Core Web Vitals

These directly impact both QS and ad rank:

| Metric | Good | Needs Improvement | Poor |
|--------|------|------------------|------|
| **LCP** | <2.5s | 2.5-4.0s | >4.0s |
| **INP** | <200ms | 200-500ms | >500ms |
| **CLS** | <0.1 | 0.1-0.25 | >0.25 |

For each LP:
- Run PageSpeed Insights (mobile + desktop)
- Identify the largest contributors to poor scores
- Prioritize fixes by impact: LCP is usually the highest-leverage for ads

### 4. Mobile Experience

>60% of search traffic is mobile. For ad landing pages:

- Does the page render correctly on mobile?
- Is the CTA visible without scrolling?
- Are form fields easy to tap and fill?
- Are there interstitials or popups that block content on mobile?
- Is text readable without zooming?

### 5. Form Friction (if applicable)

For lead gen landing pages with forms:

| Factor | Low Friction | High Friction |
|--------|-------------|---------------|
| **Fields** | 3-5 fields | 8+ fields |
| **Required fields** | Name, email, company | Name, email, phone, company, title, size, revenue... |
| **Layout** | Single column, above fold | Multi-step, below fold, complex validation |
| **Submit CTA** | Action-oriented ("Get a demo") | Generic ("Submit") |
| **Trust signals** | Privacy note, social proof near form | No trust signals |

### 6. Paid vs. Organic Traffic Behavior

If GA4 data is available, compare behavior metrics for the same LP:

| Metric | Paid Traffic | Organic Traffic | Delta |
|--------|-------------|----------------|-------|
| Bounce rate | | | |
| Avg. session duration | | | |
| Conversion rate | | | |
| Scroll depth | | | |

A large gap (paid bounce rate much higher than organic) suggests the LP
isn't meeting the expectations set by the ad copy — revisit message match.

## Output Format

```markdown
## Landing Page Review — {URL} — {Date}

### Summary
- **Message match:** {Strong / Moderate / Weak}
- **QS LP Experience:** {Above Average / Average / Below Average}
- **Core Web Vitals:** {Good / Needs Improvement / Poor}
- **Mobile UX:** {Pass / Issues Found}
- **Form friction:** {Low / Medium / High} (if applicable)

### Message Match Assessment
- **Ad headline(s):** {text}
- **LP headline:** {text}
- **Alignment:** {assessment}
- **Recommendation:** {specific changes}

### Core Web Vitals
| Metric | Mobile | Desktop | Status |
|--------|--------|---------|--------|
| LCP | {value} | {value} | {Good/NI/Poor} |
| INP | {value} | {value} | {Good/NI/Poor} |
| CLS | {value} | {value} | {Good/NI/Poor} |

### Issues Found
| Issue | Impact | Fix | Effort |
|-------|--------|-----|--------|
| {issue} | {how it affects QS/conversion} | {specific fix} | {Quick/Medium/Involved} |

### Recommendations (Priority Order)
1. {Highest-impact fix}
2. ...
```

## Scope Boundaries

This skill evaluates LPs from a **search performance perspective** — what
affects Quality Score, ad rank, and conversion from search traffic.

**In scope:** Message match, QS factors, page speed, mobile UX, form friction
for paid traffic.

**Out of scope:** Full CRO audit (heat maps, multivariate testing, UX research),
design review, brand consistency (use `/brand-review` for that), content quality
beyond search relevance.
