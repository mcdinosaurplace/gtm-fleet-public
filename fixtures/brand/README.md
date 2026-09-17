# Brand fixtures

`orrery-hero-source.png` is the demo's dither-pack input: a 512×512 synthetic raster
generated with Pillow from the tokens in `context/visual-identity.yaml` — flat fills
only, an abstract orrery motif (concentric orbits, nodes, 45° hatching, blueprint
hairlines) in Orrery's ink and primary ramps. It is generated art, not a photograph and
not anyone's asset: nothing here depicts a real person, product, or company. It exists
so the content-engine loop has real queue work — `scripts/seed_demo_state.py` seeds a
pending handoff from content-producer to brand-designer naming this file as the source,
and `scripts/brand_designer_dither.py` treats it into the requested channel set on the
brand-designer queue tick. A source with genuine tonal range is the point: flat brand
colors span the luminance ramp, so the Bayer dither produces visible halftone texture
rather than a flat posterize.
