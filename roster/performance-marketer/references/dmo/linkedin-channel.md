# LinkedIn Campaign Manager Channel Reference

## Why LinkedIn Is Different From Google

Google captures **existing demand** — people searching for a solution they already know they need.
LinkedIn **creates demand** — it reaches people who aren't actively searching but match the
profile of someone who should care about {{COMPANY}}. This distinction shapes everything: bid strategy,
creative angle, success metrics, and how you interpret underperformance.

On LinkedIn, a "bad" CTR (0.3%) might actually be fine if engagement rate and Lead Gen Form
completion are strong. On Google, a 0.3% CTR on a search campaign is a red flag.

---

## Ad Formats

| Format | Best for | Objective mode |
|--------|----------|----------------|
| **Single Image Sponsored Content** | Brand awareness, lead gen, event promotion | Awareness, Pipeline |
| **Carousel Sponsored Content** | Feature comparisons, multi-step storytelling | Pipeline (mid-funnel) |
| **Video Sponsored Content** | Brand storytelling, founder content | Awareness |
| **Message Ads (InMail)** | Direct outreach to high-value targets | Pipeline (bottom-funnel) |
| **Conversation Ads** | Branching outreach sequences | Pipeline |
| **Lead Gen Forms** | Native lead capture without landing page bounce | Pipeline (highest intent) |
| **Dynamic Ads (Follower / Spotlight)** | Personalized ads using member data | Awareness, Followers |
| **Text Ads** | Lowest cost; right-rail placement | Budget-constrained awareness |

**{{COMPANY}}'s highest-ROI formats:** Single Image (awareness + lead gen) and Lead Gen Forms (pipeline).
Message Ads work well for founder-targeting when the sender persona is authentic (e.g., from a real {{COMPANY}} team member).

---

## Creative Character Limits

| Element | Character limit | Notes |
|---------|----------------|-------|
| Introductory text | 600 max; **150 ideal** | Shown in feed above the image; truncates after ~120 chars on mobile |
| Headline | **70 characters** | Shown below the image |
| Description (feed) | **100 characters** | Shown below headline |
| CTA button | Pre-set options only | Learn More, Sign Up, Download, Get Quote, Apply Now, Register, Request Demo |
| Image ratio | 1.91:1 (horizontal) or 1:1 (square) | Square often outperforms horizontal in feed |
| Video length | 3 sec–30 min; **30–90 sec ideal** | Most watch time drops off after 15 sec |

---

## Metric Definitions & Benchmarks

| Metric | What it means | Strong | OK | Weak |
|--------|--------------|--------|----|------|
| CTR (Sponsored Content) | Clicks ÷ Impressions | >0.6% | 0.3–0.6% | <0.3% |
| Engagement Rate | (Clicks + Reactions + Comments + Shares + Follows) ÷ Impressions | >1.5% | 0.5–1.5% | <0.5% |
| Avg. CPM | Cost per 1,000 impressions | <$12 | $12–$25 | >$25 |
| Avg. CPC | Cost per click | <$6 | $6–$15 | >$15 |
| Lead Gen Form Rate | Leads ÷ Opens | >15% | 8–15% | <8% |
| Lead Gen Form Open Rate | Opens ÷ Clicks | >8% | 4–8% | <4% |
| Cost per Lead (LGF) | Spend ÷ Leads | <$50 | $50–$150 | >$150 |

**B2B SaaS context:** LinkedIn CPLs of $50–$150 are typical for mid-market SaaS targeting VP+. For founder audiences (CEO/Founder/Co-founder at 2–100 person companies), expect CPM $18–$30 due to audience competitiveness. A $100–$200 CPL via LinkedIn Lead Gen Form is often comparable to or better than Google's CPL once lead quality is factored in.

---

## Bid Strategy Options

| Strategy | When to use | Objective mode |
|----------|-------------|----------------|
| **Maximum Delivery** | Spend the full budget at LinkedIn's optimized pace | Awareness, new campaigns |
| **Target Cost** | Hit a specific CPC or CPM target | Efficiency |
| **Manual Bidding (CPC)** | Control cost per click; useful for bottom-funnel | Efficiency, Pipeline |
| **Manual Bidding (CPM)** | Control cost per 1,000 impressions; best for awareness | Awareness |

**LinkedIn bid strategy nuance:**
- Maximum Delivery is LinkedIn's version of Smart Bidding — it uses their algorithm to spend your budget optimally. Start here for new campaigns.
- Target Cost is useful for Efficiency mode once you have enough data (2+ weeks, 50+ clicks) to know what a good CPC/CPM looks like for this audience.
- LinkedIn's algorithm needs ~2 weeks to exit the learning phase. Performance in week 1 is often noisy.

---

## Audience Targeting for {{COMPANY}}'s Founder-First Strategy

The most important LinkedIn targeting lever is **Job Title + Company Size** for Erin persona campaigns.
Aaron is the exception: his role has no settled title, so he is reached by **Member Skills + Company Size**
instead. Use the job-title lists in `context/personas/hubspot-filter-sets.md` as the source of truth — the
LinkedIn facets and the `~~crm` filter sets should never drift apart.

**Erin persona targeting (founder-first):**
```
Job Titles (include combinations):
  - Founder, Co-Founder, CEO, CTO
  - Chief Technology Officer, Head of Engineering
  - Founding Engineer, Technical Co-Founder

Company Size:
  - 1–10 employees
  - 11–50 employees
  - 51–200 employees (secondary; some budget OK)

Geography: United States (primary); expand with separate campaigns if testing UK, Canada, Australia

Industry (optional refinement):
  - Computer Software, Internet, Information Technology and Services
  - Financial Services (for fintech founders)
  - Computer Network Security
  Avoid: Staffing and Recruiting, Government, Education — they match on "operations" language and never run their own production systems
```

**Aaron persona targeting (platform engineer — skills-led):**
```
Member Skills (the primary facet; titles are unreliable for this persona):
  - Kubernetes, Terraform, Site Reliability Engineering
  - DevOps, Observability, Infrastructure as Code

Job Titles (secondary, OR'd with skills — never AND'd):
  - Site Reliability Engineer, SRE Lead, Staff Platform Engineer
  - Infrastructure Engineer, Platform Team Lead, Head of Platform
  - Developer Experience Lead, Production Engineering Lead

Company Size: 201–500, 501–1,000 employees (the 50–500-engineer band)

Exclude Job Titles: Sales Engineer, Solutions Engineer, Support Engineer,
  Technical Recruiter, QA Engineer — they all match on "engineer" and none of them buy
```

**Hannah persona targeting (VP Engineering):**
```
Job Titles:
  - VP Engineering, VP of Engineering, Vice President of Engineering
  - Head of Engineering, Director of Engineering, Senior Director of Engineering
  - Head of Platform, Head of Infrastructure, Director of Platform Engineering
  - Head of Reliability, Director of SRE, VP Platform

Company Size: 51–200, 201–500, 501–1,000 employees (Series B/C stage)

Seniority: Director, VP, CXO (adds precision on top of title)

Exclude Job Titles: Sales Engineer, Solutions Engineer, Support Engineer,
  Engineering Coordinator, Program Manager, Technical Recruiter
```

**A worked audience (the one that reliably performs):** *Job Title* contains `Site Reliability Engineer` **OR**
*Member Skill* is `Kubernetes` — **AND** *Company Size* is `201–500` — **AND** *Industry* is `Computer Software`.
Estimated reach lands in the low hundreds of thousands in the US, which is the right order of magnitude: wide
enough to deliver, narrow enough that the creative can assume the reader knows what an escalation policy is.
Layering a third facet (seniority *and* skill *and* title) collapses it below 20,000 and the CPM doubles.

**Targeting tips:**
- **Don't layer too many attributes** — LinkedIn audiences shrink fast. Keep Erin campaigns at 50,000+ estimated reach minimum. Below 10,000 is too narrow.
- **Exclude company sizes above 1,000** for Erin and Aaron campaigns to avoid enterprise waste.
- **Skills beat titles for Aaron, titles beat skills for Hannah.** Hannah's title is standardized and her skills list is stale; Aaron's title is whatever his company decided to call the role this year.
- **Lookalike audiences** based on existing customers often outperform manually-defined segments for Pipeline mode.
- **Retargeting** (website visitors, video viewers, Lead Gen Form openers) is extremely high-value for Pipeline mode — these audiences convert 3–5x better than cold audiences. Docs and provider-page visitors are the single best retargeting seed {{COMPANY}} has: Aaron reads before he clicks anything.

---

## Export Instructions (14-Day Performance Report)

1. Log in to linkedin.com/campaignmanager → select account
2. Top nav → **Analyze** → **Campaign Performance**
3. Set date range to **last 14 days**
4. **Group by:** Campaign and Creative (to see individual ad performance)
5. Ensure these columns are visible:
   - Campaign Name, Creative, Status
   - Impressions, Clicks, CTR
   - Avg. CPM, Avg. CPC, Total Spend
   - Engagement Rate, Likes, Comments, Shares
   - Leads (if Lead Gen Forms active), Lead Gen Form Completion Rate
6. Export → **CSV**

**Note on LinkedIn CSV column names:** LinkedIn uses slightly different names than the UI. The optimizer normalizes common variations automatically. If columns are missing, it will flag them and proceed with what's available.

---

## LinkedIn + Google Cross-Channel Interpretation

LinkedIn tends to work as a **top-of-funnel and mid-funnel channel** — it builds awareness and generates leads that later convert through Google search or direct. This means:

- A founder sees a {{COMPANY}} ad on LinkedIn → doesn't click → searches "{{company_slug}} incident management" on Google two weeks later → converts
- LinkedIn gets no credit in last-click attribution, but was the first touch
- This is why LinkedIn CPLs that look high on paper often deliver higher-quality leads than Google's "cheaper" leads

**Practical implication for analysis:**
- Don't kill LinkedIn just because CPL is higher than Google
- Look for **lead quality signals**: Are LinkedIn-sourced leads progressing further in the funnel? (If you have HubSpot data, this helps)
- A reasonable heuristic: LinkedIn CPL can be up to 2x Google CPL and still be justified if the audience quality (founder titles at the right company size) is materially better

Flag any campaign where LinkedIn CPL exceeds 3x the Google CPL for the same objective — that's a signal worth flagging regardless of lead quality arguments.
