---
persona: Hannah the VP Engineering
status: primary
buyer_role: primary_buyer_and_user
revision: 2
sources:
  - {{company_slug}}-on-call-buyer-research.docx
  - {{COMPANY}}-Positioning.docx
---

# Hannah the VP Engineering

HubSpot persona blocks below are formatted to paste field-by-field. Items marked **[INFERRED]** are not stated directly in the source documents and should be validated against HubSpot contact data before publishing.

## Name

Hannah the VP Engineering

## Description

A strategic and stretched VP of Engineering at a Series B or C company (150–400 employees, roughly 90–200 engineers) running eight to twelve teams against contractual uptime commitments. Owns delivery, reliability, and the on-call rota. Shares budget with Platform and Security, and every renewal has to justify itself to Finance, so a tool buy needs three audiences, not one. Wants leverage, not a dashboard — a system that shortens incidents and spreads the night shift fairly.

## Internal Notes

### Roles — What kinds of jobs does this persona have?

- VP Engineering, Head of Engineering, Director of Engineering, Senior Director of Platform
- Sometimes overlaps with CTO at the smaller end of the range, or Head of Reliability at the larger end
- Typically the person who owns the uptime number that appears in the board deck
- Owner of: delivery velocity, incident process, on-call policy and compensation, SLA commitments, engineering retention

### Goals — What is this persona trying to do?

- Cut MTTR to something she can state in a customer commitment without hedging
- Stop losing engineers to on-call burnout — after-hours load is the top-cited reason in her last four exit interviews
- Run one incident process across every team instead of reconciling three chat conventions and a spreadsheet rotation
- Know, without asking, which services page most and which teams carry the heaviest night load
- Make the retro a habit that produces tracked, closed action items — not a document nobody reopens
- Answer Sales' security-questionnaire and SLA questions from a system of record rather than from memory
- Show the executive team that reliability investment is paying down risk, not just spending budget (typical career goal for a VP Eng at this stage)

### Challenges — What gets in this persona's way?

- Incident overhead eats a "surprising fraction of the week" for her senior engineers — triaging pages that were never incidents, chasing owners, writing up the same failure twice
- Three-system patchwork during an incident (monitoring, chat, ticketing) means the timeline has to be reconstructed by hand afterward — 3–4 hours she resents
- On-call fairness is invisible: she suspects two teams carry most of the after-hours load and has no data to confirm it until someone resigns
- Retros sprawl across four documents and a manual checklist; action items aren't tracked to close
- Existing platforms offer "AI that summarizes your incident" — Hannah doesn't need a summary, she needs the page to reach the right owner in under a minute
- Budget shared with Platform and Security raises the bar on procurement
- Vendor fatigue — has likely lived through one or more migrations ({{COMPETITOR_D}} → {{COMPETITOR_B}}, {{COMPETITOR_B}} → {{COMPETITOR_A}}, or similar) and is wary of another rebuild mid-year

## Demographics

### Age

34–50, modal age around 40. Source docs do not state an age; inference is based on typical tenure trajectory for a VP Engineering at a 150–400 person company (usually 12–20 years of engineering and engineering-leadership experience).

### Income range

$230K–$330K base, plus equity. Reference: market data for VP Engineering at US-headquartered Series B/C companies. Higher in SF/NYC, lower in remote-first or non-coastal markets.

### Education

Bachelor's degree common (often in CS, EE, or a related technical field). A meaningful subset hold an MS in CS; a smaller subset came up through operations or QA without a CS degree and are sensitive to content that assumes one.

### Location

Predominantly US-based, where the company HQ is. Engineering teams are frequently distributed across two or three time zones, which shapes how she thinks about follow-the-sun rotations. Sales conversations should not assume HQ location — confirm via HubSpot company HQ field.

## Story (details)

Hannah's information diet is heavier on peers than on tooling content. She reads *The Pragmatic Engineer*, LeadDev, *Software Lead Weekly*, the Google SRE books she keeps recommending and re-reading, and public postmortems from companies she admires. She's in the Rands Leadership Slack and one or two VP-level Discords. She's active on LinkedIn — mostly as a reader of engineering-leadership pieces, occasionally as a poster. She attends one or two conferences a year (LeadDev, SREcon) and values hallway conversations with other VPs more than vendor demos.

In free time, she reads management and systems writing (Lenny's, *An Elegant Puzzle*, *Thinking in Systems*, *The Manager's Path*), and is the person in her friend group people text when they have an "is this normal at my job?" question about engineering culture.

The thing the docs make explicit and worth restating: **Hannah's real job isn't running incidents. It's delivery, retention, and the uptime number she signed.** The incident overhead is what's stealing time and people from the work she was hired to do. Marketing that lands with her acknowledges this directly: "You don't need braver engineers. You need fewer pages and a clear owner for the ones that are real."
