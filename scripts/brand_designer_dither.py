#!/usr/bin/env python3
"""brand-designer dither engine — ordered (Bayer) dithering + brand palette mapping
+ per-channel export packaging.

Core of the `brand-designer:dither-pack` skill (roster/brand-designer/skills/dither-pack.md).
Produces the halftone/dither treatment defined in
context/visual-identity.yaml (imagery.styles.halftone_portraits) and
the design lead's Dithered Style Figma board.

Order of operations (per output target):
  load -> luminance -> preprocess (blur, contrast, levels) -> cover-crop
  resize to working size (target / scale) -> Bayer threshold quantize to
  palette ramp -> nearest-neighbor upscale x scale -> crop to exact target
  -> optional border -> export.

Dithering happens LAST, at final pixel dimensions. Never resample a dithered
image with anything but integer nearest-neighbor — it moirés.

Usage:
  python3 scripts/brand_designer_dither.py INPUT [INPUT...] [options]

  INPUT             image file(s) or directory(ies) of images
  --out DIR         output root (default: brand-designer-out/ next to first input)
  --algorithm A     bayer2 | bayer4 | bayer8 (default bayer8)
  --scale N         dither pixel size, >=1 (default 2)
  --strength F      dither strength 0-2 (default 1.0; 0 = flat posterize)
  --blur F          pre-blur gaussian radius in px (default 0)
  --contrast F      pre-contrast multiplier (default 1.0)
  --black N         levels black point 0-255 (default 12)
  --gamma F         levels gamma (default 0.89)
  --white N         levels white point 0-255 (default 198)
  --palette P       preset name or comma-separated hex ramp (default ink)
  --list-palettes   print preset palettes and exit
  --package C...    channel names/groups to export: social display web email
                    og all, or specific channel keys (default: master only)
  --border N        inset border width in px, 0 = off (default 0)
  --border-color H  border hex (default: darkest palette color)
  --no-zip          skip the .zip archive when packaging

Requires: Pillow, numpy (scripts/requirements.txt).
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np


def _repo_relative(path: Path) -> str:
    """The manifest cites the source image by a repo-relative path, never an absolute machine path
    (absolute paths in run outputs trip the zero-leak gate)."""
    p = Path(path).resolve()
    for base in (Path(__file__).resolve().parents[1], Path.cwd().resolve()):
        try:
            return p.relative_to(base).as_posix()
        except ValueError:
            continue
    return p.name
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

# ---------------------------------------------------------------------------
# Brand palettes — ramps dark->light. Tokens from context/visual-identity.yaml
# (audited). Keep in sync with that file; it is the source of truth.
# ---------------------------------------------------------------------------
PALETTES = {
    "mono": ["#000000", "#FFFFFF"],                                  # theme-board default
    "ink": ["#282823", "#F9FAF9"],                                   # brand default
    "paper": ["#282823", "#FFFBF5"],                                 # warm/cream
    "primary": ["#0B4F47", "#0F766E", "#7FC4BC", "#D5EFEB"],          # primary ramp
    "primary-ink": ["#282823", "#0F766E", "#F9FAF9"],                 # ink + brand accent
    "dark": ["#131415", "#282823", "#BCBAB3", "#FFFFFF"],            # dark-mode surfaces
    "ink-ramp": ["#282823", "#6C6C66", "#A8A69E", "#E4E4E1", "#F9FAF9"],
}

# Channel export matrix — (width, height). Web/email also emit WebP.
CHANNELS = {
    "og": (1200, 630),
    "social-square": (1080, 1080),
    "social-portrait": (1080, 1350),
    "social-landscape": (1600, 900),
    "display-mrec": (300, 250),
    "display-leaderboard": (728, 90),
    "display-skyscraper": (160, 600),
    "display-halfpage": (300, 600),
    "display-billboard": (970, 250),
    "display-mobile": (320, 50),
    "web-hero-desktop": (2880, 1280),
    "web-hero-mobile": (828, 1024),
    "email-header": (1200, 400),
}
CHANNEL_GROUPS = {
    "social": ["og", "social-square", "social-portrait", "social-landscape"],
    "display": ["display-mrec", "display-leaderboard", "display-skyscraper",
                "display-halfpage", "display-billboard", "display-mobile"],
    "web": ["web-hero-desktop", "web-hero-mobile"],
    "email": ["email-header"],
}
CHANNEL_GROUPS["all"] = [c for g in ("social", "display", "web", "email")
                         for c in CHANNEL_GROUPS[g]]
WEBP_CHANNELS = set(CHANNEL_GROUPS["web"] + CHANNEL_GROUPS["email"] + ["og"])

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def bayer_matrix(n):
    """Normalized n x n Bayer threshold matrix, n in {2, 4, 8}."""
    m = np.array([[0, 2], [3, 1]], dtype=np.float64)
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size  # values in (0, 1)


def preprocess(img, args):
    """Flatten to luminance and apply blur / contrast / levels. Returns 'L' image."""
    if img.mode in ("RGBA", "LA", "P"):
        base = Image.new("RGBA", img.size, "#FFFFFF")
        base.paste(img.convert("RGBA"), (0, 0), img.convert("RGBA"))
        img = base.convert("RGB")
    gray = img.convert("L")
    if args.blur > 0:
        gray = gray.filter(ImageFilter.GaussianBlur(args.blur))
    if args.contrast != 1.0:
        gray = ImageEnhance.Contrast(gray).enhance(args.contrast)
    arr = np.asarray(gray, dtype=np.float64)
    span = max(args.white - args.black, 1)
    arr = np.clip((arr - args.black) / span, 0.0, 1.0)
    arr = arr ** (1.0 / max(args.gamma, 0.01))
    return arr  # float64 in [0, 1]


def cover_resize(arr, target_w, target_h):
    """Cover-crop resize a [0,1] float array to exactly (target_w, target_h)."""
    img = Image.fromarray((arr * 255).astype(np.uint8), "L")
    w, h = img.size
    factor = max(target_w / w, target_h / h)
    img = img.resize((max(round(w * factor), target_w),
                      max(round(h * factor), target_h)), Image.LANCZOS)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    return np.asarray(img, dtype=np.float64) / 255.0


def dither_to_palette(arr, palette_rgb, matrix, strength):
    """Ordered-dither a [0,1] luminance array onto a palette ramp.

    index = floor(v * (K-1) + t') with t' = 0.5 + (threshold - 0.5) * strength,
    so strength 0 degrades to plain posterization and 1 is full Bayer dither.
    """
    h, w = arr.shape
    k = len(palette_rgb)
    n = matrix.shape[0]
    tiled = np.tile(matrix, (h // n + 1, w // n + 1))[:h, :w]
    t = 0.5 + (tiled - 0.5) * strength
    idx = np.clip(np.floor(arr * (k - 1) + t), 0, k - 1).astype(np.uint8)
    lut = np.array(palette_rgb, dtype=np.uint8)
    return Image.fromarray(lut[idx], "RGB")


def render_target(arr, target_w, target_h, palette_rgb, matrix, args):
    """Produce one dithered output at exactly (target_w, target_h)."""
    s = max(args.scale, 1)
    work_w = max((target_w + s - 1) // s, 1)
    work_h = max((target_h + s - 1) // s, 1)
    work = cover_resize(arr, work_w, work_h)
    img = dither_to_palette(work, palette_rgb, matrix, args.strength)
    if s > 1:
        img = img.resize((work_w * s, work_h * s), Image.NEAREST)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    if args.border > 0:
        draw = ImageDraw.Draw(img)
        color = hex_to_rgb(args.border_color) if args.border_color else palette_rgb[0]
        for i in range(args.border):
            draw.rectangle([i, i, target_w - 1 - i, target_h - 1 - i], outline=color)
    return img


def resolve_palette(spec):
    if spec in PALETTES:
        hexes = PALETTES[spec]
    elif spec.startswith("#") or "," in spec:
        hexes = [h.strip() for h in spec.split(",") if h.strip()]
    else:
        sys.exit(f"Unknown palette '{spec}'. Presets: {', '.join(PALETTES)} "
                 "or pass comma-separated hex values.")
    if len(hexes) < 2:
        sys.exit("Palette needs at least 2 colors.")
    rgb = sorted((hex_to_rgb(h) for h in hexes), key=luminance)  # dark -> light
    return hexes, rgb


def resolve_channels(specs):
    keys = []
    for spec in specs:
        if spec in CHANNEL_GROUPS:
            keys.extend(CHANNEL_GROUPS[spec])
        elif spec in CHANNELS:
            keys.append(spec)
        else:
            sys.exit(f"Unknown channel '{spec}'. Groups: {', '.join(CHANNEL_GROUPS)}; "
                     f"channels: {', '.join(CHANNELS)}.")
    return list(dict.fromkeys(keys))  # dedupe, keep order


def collect_inputs(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir()
                                if f.suffix.lower() in SUPPORTED_EXT))
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"Input not found: {p}")
    if not files:
        sys.exit("No supported images found in input(s).")
    return files


def process_file(path, out_root, palette_hexes, palette_rgb, matrix, channels, args):
    img = Image.open(path)
    animated = bool(getattr(img, "is_animated", False))
    if animated:
        img.seek(0)
        print(f"  ! {path.name} is animated — dithering first frame only "
              "(animation support is on the roadmap)", file=sys.stderr)
    arr = preprocess(img, args)
    src_h, src_w = arr.shape

    out_dir = out_root / path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    def save(image, name, fmt="PNG"):
        f = out_dir / name
        image.save(f, fmt, **({"lossless": True} if fmt == "WEBP" else {}))
        outputs.append({"file": f.name, "width": image.width, "height": image.height,
                        "format": fmt, "bytes": f.stat().st_size, "alt_text": None})
        return f

    # Master: dither at native resolution (no resize), review surface.
    master = render_target(arr, src_w, src_h, palette_rgb, matrix, args)
    save(master, f"master_{args.algorithm}.png")

    for key in channels:
        tw, th = CHANNELS[key]
        rendered = render_target(arr, tw, th, palette_rgb, matrix, args)
        save(rendered, f"{key}.png")
        if key in WEBP_CHANNELS:
            save(rendered, f"{key}.webp", "WEBP")

    manifest = {
        "source": _repo_relative(path),
        "generated_by": "scripts/brand_designer_dither.py",
        "animated_source": animated,
        "settings": {
            "algorithm": args.algorithm, "scale": args.scale,
            "strength": args.strength, "blur": args.blur,
            "contrast": args.contrast,
            "levels": {"black": args.black, "gamma": args.gamma, "white": args.white},
            "palette": palette_hexes, "border": args.border,
        },
        "outputs": outputs,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if channels and not args.no_zip:
        zip_path = out_root / f"{path.stem}_brand_designer_pack.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out_dir.iterdir()):
                z.write(f, f"{path.stem}/{f.name}")
        print(f"  packaged -> {zip_path}")
    print(f"  {path.name}: master + {len(outputs) - 1} channel files -> {out_dir}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", help="image file(s) or directory(ies)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--algorithm", default="bayer8", choices=["bayer2", "bayer4", "bayer8"])
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--blur", type=float, default=0.0)
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--black", type=int, default=12)
    ap.add_argument("--gamma", type=float, default=0.89)
    ap.add_argument("--white", type=int, default=198)
    ap.add_argument("--palette", default="ink")
    ap.add_argument("--list-palettes", action="store_true")
    ap.add_argument("--package", nargs="*", default=[],
                    help="channel groups/keys to export (see CHANNELS)")
    ap.add_argument("--border", type=int, default=0)
    ap.add_argument("--border-color", default=None)
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args()

    if args.list_palettes:
        for name, hexes in PALETTES.items():
            print(f"{name:12s} {' '.join(hexes)}")
        return
    if not args.inputs:
        ap.error("at least one INPUT is required")

    files = collect_inputs(args.inputs)
    out_root = Path(args.out) if args.out else files[0].parent / "brand-designer-out"
    out_root.mkdir(parents=True, exist_ok=True)
    palette_hexes, palette_rgb = resolve_palette(args.palette)
    matrix = bayer_matrix(int(args.algorithm[-1]))
    channels = resolve_channels(args.package)

    print(f"brand-designer-dither: {len(files)} input(s), palette={args.palette} "
          f"({len(palette_rgb)} colors), {args.algorithm}, scale={args.scale}")
    for f in files:
        process_file(f, out_root, palette_hexes, palette_rgb, matrix, channels, args)


if __name__ == "__main__":
    main()
