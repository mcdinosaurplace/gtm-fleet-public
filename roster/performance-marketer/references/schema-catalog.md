# Schema Markup Catalog

JSON-LD schema types for the seo-audit and serp-analysis skills. Covers the
most impactful schema types for a B2B SaaS site.

## Priority Schema Types

### Organization (homepage)

Establishes brand entity. Required for knowledge panel and AI entity recognition.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{{COMPANY}}",
  "url": "https://{{COMPANY_DOMAIN}}",
  "logo": "https://{{COMPANY_DOMAIN}}/logo.png",
  "description": "...",
  "foundingDate": "...",
  "sameAs": [
    "https://linkedin.com/company/{{company_slug}}",
    "https://twitter.com/{{company_slug}}"
  ]
}
```

### Article / BlogPosting (blog content)

Signals authorship, publish date, topic. Helps AI citation.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "...",
  "author": { "@type": "Person", "name": "..." },
  "datePublished": "2026-01-15",
  "dateModified": "2026-03-01",
  "publisher": { "@type": "Organization", "name": "{{COMPANY}}" }
}
```

### FAQ (FAQ pages, blog posts with Q&A)

Directly feeds featured snippets, PAA boxes, and AI Overviews.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is an error budget?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "An error budget is the amount of unreliability a service is allowed to spend in a period — the inverse of its SLO..."
      }
    },
    {
      "@type": "Question",
      "name": "How does {{COMPANY}} pricing work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{{COMPANY}} is priced per responder seat, plus a usage component on signal ingest. Teams of up to 5 responders use the free tier."
      }
    }
  ]
}
```

Definition questions carry the category cluster; pricing and capability questions
carry the commercial one. Keep both kinds on the same page only when the visible
page actually answers both — schema that outruns the copy is a manual action
waiting to happen.

### BreadcrumbList (all pages)

Signals site hierarchy. Helps search engines understand page relationships.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://{{COMPANY_DOMAIN}}" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://{{COMPANY_DOMAIN}}/blog" },
    { "@type": "ListItem", "position": 3, "name": "Article Title" }
  ]
}
```

### HowTo (tutorial/guide content)

Step-by-step structure that AI systems can parse and display.

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to set up your first on-call rotation",
  "step": [
    { "@type": "HowToStep", "name": "Map services to owners", "text": "..." },
    { "@type": "HowToStep", "name": "Define the rotation", "text": "..." },
    { "@type": "HowToStep", "name": "Write the escalation policy", "text": "..." },
    { "@type": "HowToStep", "name": "Route a real signal end to end", "text": "..." }
  ]
}
```

### Product (product/pricing pages)

Use the `SoftwareApplication` subtype rather than bare `Product` — it is the
shape search engines expect for SaaS, and it is the only one that carries
`featureList`, which is where the surfaces and the integration story land.

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "{{COMPANY}}",
  "applicationCategory": "DeveloperApplication",
  "applicationSubCategory": "Incident Management",
  "operatingSystem": "Web",
  "description": "Incident management and on-call for engineering teams: clear ownership, fast response, and a review after every page.",
  "featureList": [
    "Signal Grouping",
    "Ownership Graph",
    "Rotation Studio",
    "Response Rooms",
    "Learning Loops",
    "Fairness Report",
    "Terraform provider",
    "Open API on every tier",
    "SSO and SCIM"
  ],
  "offers": [
    {
      "@type": "Offer",
      "name": "Free",
      "priceCurrency": "USD",
      "price": "0",
      "description": "Up to 5 responders. Open API and Terraform provider included."
    },
    {
      "@type": "Offer",
      "name": "Team",
      "priceCurrency": "USD",
      "price": "...",
      "priceSpecification": {
        "@type": "UnitPriceSpecification",
        "unitText": "responder / month"
      }
    }
  ]
}
```

Two rules that keep this block out of trouble: the `price` must match the
pricing page on the day it renders, and `featureList` names surfaces that exist
on the tier being described — the open API and the Terraform provider are on
every tier, so they can sit in the free offer without qualification.

## Audit Checklist

When auditing schema coverage:

| Page Type | Required Schema | Optional Schema |
|-----------|----------------|----------------|
| Homepage | Organization | WebSite (with SearchAction) |
| Blog post | Article + BreadcrumbList | FAQ (if Q&A present) |
| Product page | BreadcrumbList | SoftwareApplication, FAQ |
| Pricing page | BreadcrumbList | SoftwareApplication + Offer |
| FAQ page | FAQPage + BreadcrumbList | — |
| How-to guide | HowTo + Article + BreadcrumbList | FAQ |
| About page | Organization + BreadcrumbList | — |
| Integration page | BreadcrumbList | FAQ, HowTo, SoftwareApplication |

## Validation

- Test implementation with Google Rich Results Test
- Check for errors in GSC Enhancement reports
- Ensure schema matches visible page content (no hidden schema)
- Validate JSON-LD syntax (no trailing commas, proper nesting)
