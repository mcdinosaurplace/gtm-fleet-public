# brand-designer:dither-pack — Dither Treatment + Channel Graphics Package

**Status:** Active (M1, v0 engine)
**Engine:** `scripts/brand_designer_dither.py` (Pillow + numpy; `scripts/requirements.txt`)
**Reference:** {{DESIGN_LEAD_FIRST}}'s [Dithered Style Figma board](https://www.figma.com/design/{{FIGMA_BRAND_BOARD_KEY}}/Dithered-Style?node-id=0-1) and the
[Brand Image Generator Tool](https://linear.app/{{LINEAR_WORKSPACE_SLUG}}/project/brand-image-generator-tool-000000000000) Linear project.
Brand tokens: `context/visual-identity.yaml` (load before running).

Takes source imagery, applies {{COMPANY}}'s dither/halftone treatment (the
`imagery.styles.halftone_portraits` look, generalized), and emits a
channel-packaged graphics payload — social, paid display, web hero
(desktop + mobile), email — with manifest, alt text, and zip archive,
gated on human review.

---

## Invocation

```
/brand-designer dither-pack <source> [instructions in natural language]
```

Examples:

- `/brand-designer dither-pack localwork/inbox/founder-headshot.jpg — mono halftone for the events page`
- `/brand-designer dither-pack ~/Downloads/campaign-shots/ — primary ramp, chunky pixels (scale 4), full social + display pack`
- `/brand-designer dither-pack assets.zip — ink palette, crank contrast, web heroes only, deliver as zip for {{DESIGN_LEAD_FIRST}}`

Another agent invokes via handoff (see `docs/brand-designer-scope.md` → Fleet Integration):
the handoff entry names source path, desired channels, palette, deadline, and
approver. Agent-initiated requests are always Tier 2 ({{DESIGN_LEAD_FIRST}} approves via chief-of-staff).

---

## Inputs

| Type | Handling |
|------|----------|
| Single image (PNG/JPG/WebP/BMP/TIFF) | Direct |
| Multiple images / directory | Engine batches; one payload folder per source |
| Zip archive | Unpack to the session scratchpad, then treat as directory |
| Animated GIF | **M1 limitation:** first frame only, warned in output + manifest. Full per-frame animation dithering is M2 |
| Figma frame URL | **M3** — requires Figma MCP (not yet connected). Until then: ask the requester for an export |

Sources land in (or are copied to) `localwork/brand-designer/inbox/` if provided out-of-repo.
Never commit source or output imagery to git — `localwork/` is gitignored.

---

## Parameters — instruction → engine mapping

Parse the requester's natural-language instruction into engine flags. The controls
mirror the Figma-plugin UI on {{DESIGN_LEAD_FIRST}}'s theme board:

| Theme-board control | Flag | Default | Notes |
|---|---|---|---|
| Algorithm | `--algorithm` | `bayer8` | `bayer2` / `bayer4` / `bayer8`. Bayer 8×8 = most tonal range ({{DESIGN_LEAD_FIRST}}'s reference setting). Error-diffusion (Floyd–Steinberg, Atkinson) is M2 |
| Scale | `--scale` | `2` | Dither pixel size. 1 = fine grain, 4+ = chunky retro pixels |
| Strength | `--strength` | `1.0` | 0 = flat posterize, 1 = full Bayer, up to 2 exaggerates |
| Blur | `--blur` | `0` | Pre-dither gaussian radius; softens photographic noise |
| Contrast | `--contrast` | `1.0` | Pre-dither contrast multiplier |
| Levels: Black / Gamma / White | `--black` / `--gamma` / `--white` | `12` / `0.89` / `198` | Theme-board reference values. **Color temperature and tonal balance live here + palette choice** |
| Colors (count + swatches) | `--palette` | `ink` | Preset ramp name or explicit comma-separated hexes |
| Border | `--border`, `--border-color` | `0` (off) | Inset border, defaults to darkest ramp color |
| PNG / SVG export | (PNG/WebP built in) | — | SVG export is M2 |

Sanctioned palette ramps (`--list-palettes`; tokens from the identity YAML — keep in sync):

| Preset | Ramp | Use for |
|---|---|---|
| `mono` | #000000 → #FFFFFF | Theme-board look; portraits/halftones |
| `ink` | #282823 → #F9FAF9 | **Default.** Brand warm ink on off-white |
| `paper` | #282823 → #FFFBF5 | Warm/cream surfaces (charts, editorial) |
| `primary` | #0B4F47 → #0F766E → #7FC4BC → #D5EFEB | Product/abstract imagery, primary-flood moments |
| `primary-ink` | #282823 → #0F766E → #F9FAF9 | Ink imagery with brand accent |
| `dark` | #131415 → #282823 → #BCBAB3 → #FFFFFF | Dark-mode / event surfaces |
| `ink-ramp` | 5-step warm grayscale | Higher-fidelity halftones |

**Palette-swap requests** ("dither it AND put it in brand primary") are just ramp
selection — the engine maps luminance onto whatever ramp is chosen. A requested
palette outside these ramps requires the requester's explicit override and a flag
in the review packet. People get `mono`/`ink`/`ink-ramp` only (identity rule:
B&W halftone portraits), unless {{DESIGN_LEAD_FIRST}} approves an exception.

---

## Order of Operations

1. **Intake.** Resolve source(s) per the Inputs table. Reject unsupported formats
   plainly. Screen sources against `visual-identity.yaml → prohibited`
   (stock-photo look, gradients-as-subject, etc.) — flag violations to the
   requester instead of treating-and-shipping.
2. **Parse instruction → settings.** Fill the parameter table; state the resolved
   settings back in one line before running (assumption surfacing). Unspecified
   parameters use defaults; "make it warmer/darker/chunkier" style language maps to
   levels/palette/scale adjustments.
3. **Master render.** Run the engine without `--package` first. **Inspect the
   rendered master visually** — tonal balance, banding, whether the source washed
   out (light UI sources need black/white/contrast tuning; see Identity Notes).
   Tune and re-render until the master is right. This is the cheap loop; don't
   package a bad master.
4. **Package.** Re-run with `--package <channels>` per the request (groups:
   `social`, `display`, `web`, `email`, `all`; or specific keys). The engine
   dithers **per channel at final dimensions** — never scales a dithered master.
   Output root: `localwork/brand-designer/YYYY-MM-DD-<slug>/`.
5. **Verify mechanically.** Every output: exact target dimensions; color set ⊆
   declared palette; manifest parses. (The scaffold-session check pattern lives in
   the scaffold entry in my journal.)
6. **Author alt text.** Vocabulary for the orrery motif: the central body is the *sun*, the
   orbiting bodies are *spheres*, *orbs*, or *nodes*, on *rings* or *orbits* — never the
   everyday astronomical noun for an orbiting body (the zero-leak gate rejects that word).
   For each channel output, write alt text into
   `alt-text.md` alongside the manifest (and mirror into `manifest.json`
   `outputs[].alt_text`). Describe the image's *content*, not its treatment —
   "Founder portrait of X" not "dithered primary image". ≤ 125 chars, no
   "image of" prefix. Decorative-only outputs (e.g., abstract display
   backgrounds) get `alt_text: ""` explicitly, not null.
7. **Deliver drafts.** Direct human invocation: present the master + 2–3
   representative channel renders in-session, name the payload path and zip.
   Agent-initiated or publish-bound: write the review packet to
   `state/pending/YYYY-MM-DD/brand-designer-dither-pack.md` (settings, compliance log,
   payload path) + handoff entry for chief-of-staff → {{DESIGN_LEAD_FIRST}} (Tier 2).
8. **Review loop.** Approved → done; the zip (`<name>_brand_designer_pack.zip`) is the
   deliverable. Changes → adjust settings, re-render, re-verify (steps 3–7).
   Max 3 revision cycles, then stop and request a working session with {{DESIGN_LEAD_FIRST}}.
9. **Journal + commit.** One journal block per payload: request → settings →
   outputs → compliance result → review state. Commit state files only — never
   the imagery.

---

## Channel Matrix (v0)

| Key | Size | Formats | Surface |
|---|---|---|---|
| `og` | 1200×630 | PNG + WebP | Open Graph / link cards |
| `social-square` | 1080×1080 | PNG | LinkedIn/IG feed |
| `social-portrait` | 1080×1350 | PNG | IG/LinkedIn portrait |
| `social-landscape` | 1600×900 | PNG | X / LinkedIn landscape |
| `display-mrec` | 300×250 | PNG | IAB medium rectangle |
| `display-leaderboard` | 728×90 | PNG | IAB leaderboard |
| `display-skyscraper` | 160×600 | PNG | IAB wide skyscraper |
| `display-halfpage` | 300×600 | PNG | IAB half page |
| `display-billboard` | 970×250 | PNG | IAB billboard |
| `display-mobile` | 320×50 | PNG | IAB mobile banner |
| `web-hero-desktop` | 2880×1280 | PNG + WebP | Site hero @2x |
| `web-hero-mobile` | 828×1024 | PNG + WebP | Site hero mobile @2x |
| `email-header` | 1200×400 | PNG + WebP | Email header |

Gaps to close with {{DESIGN_LEAD_FIRST}} (M2): LinkedIn company banner, X header, YouTube thumb,
favicon/app-icon derivatives, AVIF for web, ad-platform file-weight caps
(e.g., ≤150 KB for Google Display) enforced by the optimizer skill.

## Payload Contract

```
localwork/brand-designer/YYYY-MM-DD-<slug>/
  <source-stem>/
    master_<algorithm>.png      # review surface, native resolution
    <channel>.png [.webp]       # one per requested channel
    manifest.json               # source, settings, palette, outputs incl. alt_text
    alt-text.md                 # human-readable alt text per output
  <source-stem>_brand_designer_pack.zip  # the deliverable archive
```

Future (M4+): deploy the payload folder to a designated resource location that
Framer/Figma tooling scans, instead of (or alongside) the zip-for-human handoff.

---

## Failure Modes

- **Source violates brand `prohibited` list** → flag to requester, don't ship.
- **Animated source** → first frame + warning (M1); offer M2 follow-up.
- **Off-ramp palette without override** → stop, present sanctioned options.
- **Washed/blocked master after 3 tuning passes** → deliver best master with the
  finding, ask for a better source or a working session; don't package garbage.
- **Engine error** → journal it; if invoked via handoff, write the failure back as
  a handoff so the requesting agent isn't left waiting.
