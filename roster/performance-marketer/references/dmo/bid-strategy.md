# Bid Strategy Decision Framework

## The Core Principle

Bid strategy is a signal about what you value, not just what you want to pay. Changing
a bid strategy mid-campaign has a cost — the algorithm resets its learning, and you'll
see performance instability for 1–2 weeks. Don't recommend bid strategy changes lightly.
Recommend them when the current strategy is structurally wrong for the objective, not
just because performance dipped.

---

## Decision Tree by Objective Mode

### Efficiency Mode

Goal: Spend less (or the same) while maintaining or improving qualified output.

```
1. Is there conversion tracking set up?
   └─ No → Fix tracking first. Bid strategy is irrelevant without this.
   └─ Yes → Continue.

2. Does the campaign have 30+ conversions in the last 30 days?
   └─ No → Use Maximize Conversions (Google) or Maximum Delivery (LinkedIn)
            to accumulate data. Don't set Target CPA yet — you don't have enough
            data for the algorithm to work with.
   └─ Yes → Consider Target CPA (Google) or Target Cost (LinkedIn).

3. Is current CPA more than 30% above target?
   └─ Yes → Don't lower Target CPA dramatically in one step. Reduce by ~10-15%
            increments. Aggressive Target CPA reduction starves the campaign.
   └─ No → Current strategy may be fine. Check for budget waste elsewhere
           (low-quality keywords, poor landing page match, broad match overexposure).

4. Are there campaigns with zero conversions for 14+ days AND >$200 spend?
   └─ Yes → These are 🔴 Act Now. Pause or significantly reduce budget before
            addressing bid strategy.
```

**Efficiency-specific budget moves:**
- Identify the cost-per-conversion of each campaign. Rank them.
- Bottom 20% by cost-efficiency with >10% of total budget → flag for reallocation
- Top 20% by cost-efficiency with <10% of total budget → flag as underinvested

---

### Pipeline Mode

Goal: Generate more qualified leads, demos, or MQLs.

```
1. What's the conversion bottleneck?
   a. Low impressions → Audience is too narrow or budget is too low.
      → Expand audience, increase budget, or shift to Maximize Clicks temporarily.
   b. High impressions, low CTR → Creative problem, not bid problem.
      → Fix creative first. Don't increase bids on bad ads.
   c. Good CTR, low conv. rate → Landing page or offer problem.
      → Check landing page relevance and CTA. Bid changes won't fix this.
   d. Good conv. rate, just want more volume → This is a scale problem.
      → Increase budget on proven campaigns, or shift to Maximize Conversions.

2. Is Search Impression Share (Google) below 40% on high-intent campaigns?
   └─ Yes → This campaign is losing auctions. Either bids are too low or
            budget is running out mid-day. Check "Lost IS (rank)" vs "Lost IS (budget)":
            - Lost to rank → increase bids or improve Quality Score
            - Lost to budget → increase daily budget

3. Is LinkedIn campaign in learning phase (<2 weeks old)?
   └─ Yes → Don't change anything. Let it learn. Note in analysis but don't flag as
            underperforming yet.
```

**Pipeline-specific bid adjustment logic:**
- Campaigns with Conv Rate >3% and budget utilization >90%: recommend 20–30% budget increase
- Campaigns with Target CPA set below historical CPA average: recommend raising Target CPA by 15% to unshackle the algorithm
- For new campaigns: always start with Maximize Conversions (Google) or Maximum Delivery (LinkedIn) — let the platform find its footing before applying constraints

---

### Awareness Mode

Goal: Maximize reach, brand recall, and engagement.

```
1. Is CPM running above benchmark?
   LinkedIn:
   - Founder titles (CEO/Founder/CTO): $18–$30 CPM normal
   - Senior managers: $12–$20 CPM normal
   - Broad B2B: $8–$15 CPM normal

   Google Display:
   - $2–$8 CPM normal; above $10 = investigate audience overlap or frequency

2. Is frequency above 5x per week?
   └─ Yes → Audience fatigue. Expand audience, refresh creative, or add frequency cap.

3. Is engagement rate (LinkedIn) below 0.5%?
   └─ Yes → Creative problem. The message isn't landing with this audience.
            Try founder POV / removal-first framing before adjusting bids.
```

**Awareness bid recommendation:**
- Google: Switch to Target Impression Share for brand campaigns (target 85%+ for branded terms)
- Google Display: CPM bidding with a sensible cap (set at 1.5x your current average CPM)
- LinkedIn: Maximum Delivery is usually fine for awareness; only use Target Cost if CPM is running >2x benchmark

---

## Budget Reallocation Framework

### When to reallocate budget across campaigns

Reallocate when the data shows a **structural imbalance** — not just weekly noise.

| Signal | Recommendation |
|--------|---------------|
| Campaign A: CPA 50%+ below average + budget constrained | Move 10–20% of budget from underperformers to Campaign A |
| Campaign B: 14+ days, zero conversions, >1% of total spend | Pause Campaign B, redistribute budget |
| Campaign C: Impression Share lost to budget >20% | Increase Campaign C's daily budget by at least the lost impression share × expected value |
| LinkedIn CPL >3x Google CPL for same bottom-funnel objective | Shift 15–20% of LinkedIn budget to Google; keep LinkedIn for awareness/top-funnel only |
| Google CPA climbing week-over-week for 3+ weeks straight | Don't add more budget; investigate Quality Score, landing page, or keyword match issues first |

### Cross-channel budget allocation heuristics

For {{COMPANY}}'s marketing at current scale (founder-first, B2B SaaS, US-primary):

- **Pipeline mode:** ~70% Google (high-intent search) / ~30% LinkedIn (founder awareness + retargeting). Can flex to 60/40 if LinkedIn Lead Gen Forms are performing.
- **Awareness mode:** ~40% Google (branded + display) / ~60% LinkedIn (targeted founder reach). LinkedIn wins on audience precision.
- **Efficiency mode:** Follow the data. Concentrate budget on the channel with the lowest verified CPL. Don't maintain channel balance for its own sake.

---

## Signals That Bid Strategy Should NOT Change

Changing bid strategy is sometimes the right call — but these are common false alarms:

- **Week 1–2 after a campaign launch or bid strategy change:** The algorithm is learning. Don't intervene.
- **One bad week in an otherwise consistent campaign:** Wait for a second confirming data point.
- **Low impressions on a new campaign:** This might be audience size, not bid level. Check estimated audience reach first.
- **CTR drop without conversion rate change:** Could be seasonal, competitor activity, or ad fatigue. Not necessarily a bid problem.
- **Conversion spike that then normalizes:** Could be a tracking issue or genuine anomaly. One week isn't a trend.

The best bid strategy decision is often: wait one more week and look again.

---

## Change Log Discipline

Every bid strategy recommendation should include:
1. The specific change (e.g., "Switch Campaign X from Maximize Conversions to Target CPA: $85")
2. The reason (e.g., "Campaign has 45 conversions in 30 days, CPA has stabilized at $72 — ready for constraint")
3. What to watch (e.g., "Monitor for 2 weeks; if CPA climbs >$110, dial back Target CPA to $95")

This goes into the hypothesis log so next week's analysis can verify whether the change worked.
