# brand-designer review packet — dither-pack: brief-0001 hero channel set

**Created:** 2026-09-17T16:18:37Z
**Requested by:** content-producer (handoff `content-producer_handoff_01m1t08vvn_5c8ra5`, 2026-09-16T18:12:00Z)
**For:** `content_drafts` id=1 / `state/working/briefs/brief-0001.md` ("Runbooks that engineers actually open"): featured image + LinkedIn derivative (`derivative_assets` id=1)
**Tier gate:** 2 — Tomas Reyes approves via chief-of-staff (Scott backup)
**Revision:** 0/3

## Source
`fixtures/brand/orrery-hero-source.png`: 512×512 abstract orrery motif, flat brand fills, generated art. Prohibited-list screen: clear (no people, no stock, no gradients, no 3D).

## Settings (as requested = brand defaults)
`--palette ink` (#282823 / #F9FAF9) · `--algorithm bayer8` · `--scale 2` · strength 1.0 · blur 0 · contrast 1.0 · levels 12 / 0.89 / 198 · no border.
Master checked by eye first: full tonal range held (sun, spheres, hatched quadrant all distinct), no washout, so no tuning passes.

## Outputs
Payload: `localwork/brand-designer/2026-09-17-brief-0001-hero-pack/orrery-hero-source/` · zip: `localwork/brand-designer/2026-09-17-brief-0001-hero-pack/orrery-hero-source_brand_designer_pack.zip` (gitignored, not committed).

- social: social-square 1080×1080, social-portrait 1080×1350, social-landscape 1600×900
- display: mrec 300×250, leaderboard 728×90, skyscraper 160×600, halfpage 300×600, billboard 970×250, mobile 320×50
- web: web-hero-desktop 2880×1280 (PNG+WebP), web-hero-mobile 828×1024 (PNG+WebP), og 1200×630 (PNG+WebP)
- email: email-header 1200×400 (PNG+WebP)
- master_bayer8.png 512×512 (review surface)

## Compliance log
- Dimensions: 18/18 files exact to the channel matrix (checked by opening each file).
- Palette: every file contains exactly 2 colors, #282823 and #F9FAF9. Nothing off-ramp.
- Dithered per channel at final size; nothing resampled after dithering (engine contract).
- Checklist: no gradients, stock, 3D, or shadows; neutrals from the warm ink ramp; no people shown.
- Alt text: `alt-text.md` + mirrored into `manifest.json`. Content descriptions ≤125 chars; the 6 display banners are decorative crops with `alt_text: ""`.
- Flag for review: the tight crops (leaderboard, mobile 320×50, skyscraper) read as pure texture. Fine as decorative display. If they need to be recognisable, that is a crop change, not a settings change.

## Decision needed
Tomas: `approved` → content-producer attaches the zip to the brief-0001 publish package · `changes` → revision 1/3 with notes.
