# brand-designer — Design Agent Scope & Roadmap

**Status:** M1 scaffold shipped. This document is the plan of record
for brand-designer's skill set, fleet integration, and ownership of {{COMPANY}}'s visual
identity. Decisions marked **[open]** need Scott + {{DESIGN_LEAD_FIRST}}.

**Humans:** {{DESIGN_LEAD}} (design owner, named Tier 2 reviewer, co-owner of the
visual identity references), Scott McKeighen (architect, backup reviewer).
**Linear anchor:** [Brand Image Generator Tool](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/project/brand-image-generator-tool-000000000000)
({{DESIGN_LEAD_FIRST}}'s project; includes the [Dithered Style Figma board](https://www.figma.com/design/{{FIGMA_BRAND_BOARD_KEY}}/Dithered-Style?node-id=0-1)
and a Google-Docs brief, which needs a live Google Drive connector to read).

---

## Mission

brand-designer is the fleet's design specialist and the authoritative source for visual
aesthetics inside agentic work. Two duties:

1. **Production:** turn source imagery and design intents into brand-compliant,
   channel-ready visual assets — directly for humans ({{DESIGN_LEAD_FIRST}}, Scott, the team) and
   as a service to other agents.
2. **Governance:** own, with {{DESIGN_LEAD_FIRST}}, the visual identity references
   (`context/visual-identity.yaml`, `sops/visual-identity-sop.md`,
   `assets/visual-identity/`) so that every agent producing anything visual has
   one ratified source of truth.

brand-designer never publishes. Payloads are drafts until a human approves; humans (or
future explicitly-authorized deploy steps) move assets to customer-facing surfaces.

---

## Skill Roadmap

### M1 — shipped

| Skill | What it does |
|---|---|
| `brand-designer:dither-pack` | Dither/halftone treatment (Bayer 2/4/8, theme-board parameter set: scale/strength/blur/contrast/levels) + brand palette ramps + 13-channel export matrix (social, IAB display, web hero desktop/mobile, email, OG) + manifest/alt-text/zip payload, human review loop. Engine: `scripts/brand_designer_dither.py` |

### M2 — treatment depth + optimization (no new MCPs required)

| Skill | What it does |
|---|---|
| `brand-designer:web-image-optimizer` | Standalone web optimization for any image (not just dithered): responsive size sets + `srcset` manifest, WebP/AVIF encoding, per-surface file-weight budgets (e.g., ≤150 KB Google Display cap, hero LCP budgets), lossless-vs-lossy policy. Callable by content-producer (blog images) and performance-marketer (ad creative) |
| `brand-designer:alt-text-writer` | Alt text for any image or batch — content-first, ≤125 chars, decorative-flagging. Auto-invoked inside every pack; standalone for retrofitting existing site/blog imagery |
| Engine upgrades | Animated GIF/short-loop dithering (per-frame, palette-stable), SVG export (theme-board parity), error-diffusion algorithms (Floyd–Steinberg, Atkinson), channel-matrix gaps from {{DESIGN_LEAD_FIRST}} (LinkedIn banner, X header, YouTube thumb, favicon set) |

### M3 — Figma + governance

| Skill | What it does |
|---|---|
| `brand-designer:figma-bridge` | **[open — needs Figma MCP selection + auth]** Pull frames/components as treatment inputs; push drafts to a designated "brand-designer Drafts" page (Tier 2, never production pages). Operationalizes palette swaps where Figma is the right surface |
| `brand-designer:brand-compliance-audit` | Run the visual compliance checklist against any asset, page screenshot, or deck export — pass/flag report per token (fonts, ramps, borders, prohibited list). The check other agents call before shipping anything visual; also powers a possible scheduled brand-audit Tick **[open]** |

### M4 — fleet service maturity

| Skill | What it does |
|---|---|
| `brand-designer:campaign-kit` | From a campaign brief (`sops/campaign-plan-sop.md` output or content-producer brief): the full visual kit — hero, social set, display set, email header — as one coordinated, palette-consistent payload |
| Deploy contract | Payloads deployed to a designated resource location that Framer/Figma tooling can scan and import, alongside the zip-for-human path |

### M5 — speculative (revisit after M2–M4 learnings)

| Skill | What it does |
|---|---|
| `brand-designer:framer-publish-package` | Framer-ready asset packages mirroring content-producer's publish-package pattern (field contract, naming, image slots). Requires the Framer conversation Scott deferred |
| `brand-designer:landing-page-aesthetics` | Aesthetic review of landing pages (live or staged): identity compliance + hierarchy/whitespace/imagery critique, structured as actionable notes for {{DESIGN_LEAD_FIRST}} |
| `brand-designer:asset-librarian` | Inventory of produced assets (manifests make this cheap): dedupe, staleness/refresh detection, "do we already have a graphic for this?" lookups |
| Generative imagery | The Linear project's full vision — generate *new* designed images from reference photos + descriptions in the stippled/pixelated style. Big capability + tooling/model decision; treat-and-package (M1) is the disciplined first step **[open]** |

---

## Fleet Integration Contract

How brand-designer is called. Two paths, one record:

**1. Direct human invocation** — `/brand-designer <skill> [args]`. The invoking human
reviews drafts in-session; their approval closes the loop (self-gating).

**2. Agent-initiated handoff** — the standard fleet mechanism, no new
infrastructure: the requesting agent writes a handoff entry addressed to brand-designer in
`state/journal/handoffs.md` carrying **source path(s), desired treatment/palette,
target channels, deadline, and where the result is needed**. brand-designer processes it on
next invocation, produces the payload, writes the review packet to
`state/pending/`, and hands off to chief-of-staff for {{DESIGN_LEAD_FIRST}}'s Tier 2 approval. The
approved payload path is handed back to the requester. Agent-initiated work is
always Tier 2 — no agent-to-agent visual asset ships without {{DESIGN_LEAD_FIRST}}'s (or Scott's)
pass.

Anticipated callers:

| Caller | Use case |
|---|---|
| **content-producer** | Featured images for publish packages; derivative-post graphics (M2+: web-image-optimizer + alt-text on every blog image) |
| **performance-marketer** | Ad-creative refresh sets inside the weekly position pass / optimization dossier; creative variants sized to IAB matrix |
| **Scribe / chief-of-staff** | WBR and brief visuals (charts stay with `dataviz` conventions; brand-designer supplies treated imagery) |
| **content-researcher** | Rarely direct; topic-backlog items that imply visual content get routed through content-producer |
| **Humans** | {{DESIGN_LEAD_FIRST}} (production accelerant), Scott/{{HEAD_OF_MARKETING_FIRST}}/{{CONTENT_LEAD_FIRST}} (self-serve on-brand graphics) |

**[open]** Whether brand-designer gets a scheduled Tick (e.g., weekly brand-audit sweep of
recently shipped surfaces) or stays purely on-demand. Recommendation: stay
on-demand through M2; revisit when `brand-compliance-audit` exists.

---

## Visual Identity Ownership

brand-designer + {{DESIGN_LEAD_FIRST}} become the authoritative pair for visual aesthetics in agentic work:

- `context/visual-identity.yaml` (canonical tokens), `sops/visual-identity-sop.md`
  (human twin), and `assets/visual-identity/` (exemplars) move under their joint
  stewardship. Other agents keep loading the YAML exactly as CLAUDE.md already
  instructs — nothing changes for consumers.
- **Change protocol:** anyone (human or agent) proposing a token change routes it
  to {{DESIGN_LEAD_FIRST}} via the Decision Queue. brand-designer drafts the edit, {{DESIGN_LEAD_FIRST}} ratifies, the SOP
  version bumps. brand-designer never edits the references unilaterally.
- The SOP's §8 open list (v1.0 is reverse-engineered from the live site, awaiting
  {{DESIGN_LEAD_FIRST}}'s confirmation) becomes brand-designer's first governance backlog: walk it with
  {{DESIGN_LEAD_FIRST}}, ratify or correct each item, bump to v1.1.
- Engine palettes in `scripts/brand_designer_dither.py` are derived from the YAML and carry
  a keep-in-sync comment; a ratified token change updates both in one commit.

---

## MCP / Tooling Dependencies

| Dependency | Status | Needed for |
|---|---|---|
| Linear | required | Design-project context, clickable refs |
| Google Drive | required; re-auth per `docs/connector-reauth-runbook.md` when a token expires | {{DESIGN_LEAD_FIRST}}'s brief; asset intake from Drive |
| Figma MCP | not yet selected **[open]** — server choice + OAuth | M3 figma-bridge, palette-swap operationalization |
| Framer | deferred by Scott | M5 framer-publish-package |
| Pillow + numpy | required; declared in `scripts/requirements.txt` | Dither engine |

---

## Open Questions (Scott + {{DESIGN_LEAD_FIRST}})

1. Figma MCP: which server, whose auth, and which file/page is the sanctioned
   "brand-designer Drafts" surface.
2. Reconcile `dither-pack` spec against {{DESIGN_LEAD_FIRST}}'s brief doc once Drive access lands.
3. Channel-matrix gaps + ad file-weight caps: {{DESIGN_LEAD_FIRST}} to confirm the M2 list.
4. Scheduled brand-audit Tick: yes/no, cadence.
5. Generative imagery (the Linear project's end vision): scope, tooling, and
   whether it lives in brand-designer or a companion capability.
