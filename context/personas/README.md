# {{COMPANY}} Personas

Persona definitions for the fleet. Each file is structured to map directly onto the
`~~crm` persona field schema (Name, Description, Internal Notes, Demographics, Story), so
a block can be pasted field-by-field without reformatting. Items marked **[INFERRED]** are
reasoned extrapolations rather than stated facts, and carry a short rationale in place.

## Persona registry

| File | Persona | Status | Buyer role |
|------|---------|--------|------------|
| `aaron-platform-engineer.md` | Aaron the Platform Engineer | Primary (content engine) | Technical champion / primary buyer at 50–500 engineers |
| `erin-technical-founder.md` | Erin the Technical Founder | Primary | Primary buyer and end-user (self-serve entry) |
| `hannah-vp-engineering.md` | Hannah the VP Engineering | Primary | Business buyer and end-user |
| `anna-finance-leader.md` | Anna the Finance Leader | Speculative | Co-buyer / required signoff (annual contracts) |
| `jake-ops-leader.md` | Jake the IT & SecOps Leader | Speculative | Influencer / blocker |
| `hubspot-filter-sets.md` | — | Reference | Property filter sets that map contacts to the `hs_persona` enum |

## Machine slugs are locked; filenames are not

Three personas carry a **machine slug** — `aaron`, `erin`, `hannah` — used as the
`target_persona` value in the content-engine tables and enforced by CHECK constraints in
`state/working/schema.sql`. Those three slugs cannot change without a migration.

Filenames keep the slug as their prefix and the current role as their suffix. A role rename
therefore renames the file, and every path reference in `roster/`, `skills/`, `context/`,
and `state/identity/` must move with it. Re-run a repo-wide grep for the old filename after
any rename.

## The three content-targeting personas

Aaron is the primary ICP for content topic scoring; Erin and Hannah are the secondary
audiences. Aaron is the technical champion and Hannah is the business buyer — at smaller
companies they are frequently the same conversation. Scoring weights that depend on this
ranking live in `roster/content-researcher/skills/topic-synthesizer.md`.

Anna and Jake sit a level deeper in messaging (pricing pages, trust center, integration
docs, sales enablement) rather than in the content topic mix.

## Validation checklist before publishing a persona in `~~crm`

- Pull job-title distributions for each persona's mapped titles and confirm the modal title
  and its adjacent titles
- Pull company-HQ geography for each persona to confirm the location assumptions
- Pull the engineering-headcount segment to confirm the stage assumptions
- Have sales review goals and challenges against active deal notes for accuracy and currency
- Decide whether Anna and Jake ship as standalone personas or as a sales-enablement
  appendix to Aaron and Hannah
- Clear every **[INFERRED]** field, or keep the marker so downstream readers know it is
  unvalidated
