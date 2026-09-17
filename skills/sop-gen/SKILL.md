---
name: sop-gen
description: Generate a {{COMPANY}}-standard SOP document from rough notes or a process description. Outputs a structured Markdown file with YAML frontmatter that is both human-readable and AI-parseable.
allowed-tools: Read Write
disable-model-invocation: true
---

# /sop-gen

Load the `gtm-ops` skill and read `${CLAUDE_PLUGIN_ROOT}/skills/gtm-ops/references/sop-template.md` before generating any SOP. The template defines the required structure, YAML frontmatter fields, and field conventions — follow it exactly.

## What to Ask

Ask the user to provide:
1. **Process description**: A rough description, bullet notes, or brain dump of the process. It doesn't need to be organized — that's what this command is for.
2. **Process name**: What should this SOP be called?
3. **Owner**: Who runs this process (name or role)?
4. **Team**: Which team owns it? (default: Marketing & Revenue Operations)
5. **Tools involved**: Which tools are used? (`~~crm`, `~~enrichment`, {{ENRICHMENT_VENDOR}}, `~~knowledge base`, `~~automation`, `~~issue tracker`, etc.)
6. **Trigger**: What event or condition starts this process?
7. **Frequency**: How often does it run?

If the user says "just draft it from context," use the gtm-ops skill's knowledge of {{COMPANY}}'s workflows to produce the most likely draft and ask for corrections afterward.

## What to Produce

Apply the SOP template from `references/sop-template.md` exactly. Key principles:

**Human-friendly**:
- Each step has a clear, imperative title (verb-first: "Review", "Update", "Notify", not "Reviewing" or "The review of")
- Decision points are explicit: "If X → go to Step N. If Y → go to Edge Cases."
- Prerequisites are a checklist so a new team member can follow without prior context
- Plain language — no internal jargon without a definition on first use

**AI-consumable**:
- YAML frontmatter is fully populated with structured metadata
- Consistent field names across all SOPs (owner, tools_required, triggers, frequency)
- Steps have explicit Input → Action → Output structure
- Decision branches are formatted as conditionals, not buried in prose
- Edge cases are in a table, not paragraph form

## SOP ID Generation

Generate the `sop_id` following the convention: `sop-{team}-{slug}-v1.0`

- Team abbreviations: `mops` (Marketing Ops), `sales`, `mktg`, `cs`, `ops`
- Slug: lowercase, hyphens, 3–5 words max derived from the process name
- Example: `sop-mops-lead-routing-assignment-v1.0`

## Quality Check Before Saving

Before saving, verify:
- [ ] All required YAML frontmatter fields are populated
- [ ] Every step has Owner, Tool, Input, and Output labeled
- [ ] Every decision point is explicit (no implicit "usually" or "sometimes")
- [ ] Edge cases table has at least one row
- [ ] Quality Checks section has at least two items

## Output

Save as `{sop-id}.md` in the user's outputs folder (e.g., `sop-mops-lead-routing-assignment-v1.0.md`) and present the file link. Display the frontmatter metadata block and step summary inline in chat for a quick review before the user opens the file.
