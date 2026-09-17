"""Deterministic renderer for performance-marketer's optimization dossier (Block A2).

Turns a structured dossier object into the fixed-section markdown and writes it to
docs/publications/pending/performance-marketer/optimization_dossiers/<date>-optimization-dossier.md.

`render_dossier` is pure — the same input always yields byte-identical output,
which the golden test in tests/paid/ pins. `write_dossier` is the thin IO
wrapper. The model assembles the dossier object; it does not format the page.

Dossier object shape (all keys optional unless noted; missing lists -> empty):
    date_range       str   e.g. "Jun 2-15, 2026"
    dossier_date     str   YYYY-MM-DD (required — drives the output path)
    objective        str   Efficiency | Pipeline | Awareness | Custom
    thesis           str   one-line position
    confidence       str   Low | Medium | High
    wow_snapshot     list[{metric, last_week, this_week, delta}]
    campaign_health  list[{tier, campaign, metric, delta, diagnosis}]
    moves            list[ classified move dict ] (see scripts/paid/classify.py
                     output, plus optional expected_effect, reversal_if,
                     linear_ref, change)
    budget_view      str   read-only summary; all budget moves are 3b
    rollback         list[str]
    hypotheses       list[str]
"""

from pathlib import Path

from scripts.paid import publish

LINEAR_BASE = "https://linear.app/orrery/issue/"
DOSSIER_TYPE = "optimization_dossiers"
PENDING_ROOT = "docs/publications/pending/performance-marketer"
PUBLISHED_ROOT = "docs/publications/published/performance-marketer"

_NONE = "_None this run._"


def _linear_link(ref):
    """Render a Linear ref as a clickable markdown link (docs/linear-reference-formatting.md)."""
    if not ref:
        return None
    return f"[{ref}]({LINEAR_BASE}{ref})"


def _wow_table(rows):
    if not rows:
        return "_No metrics this run._"
    out = ["| Metric | Last wk | This wk | Δ |", "|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r.get('metric','—')} | {r.get('last_week','—')} | "
                   f"{r.get('this_week','—')} | {r.get('delta','—')} |")
    return "\n".join(out)


def _health_lines(rows):
    if not rows:
        return "_No campaigns analyzed._"
    return "\n".join(
        f"- {r.get('tier','')} **{r.get('campaign','—')}** — "
        f"{r.get('metric','—')} {r.get('delta','—')} — {r.get('diagnosis','—')}"
        for r in rows
    )


def _moves(moves, bucket):
    return [m for m in moves if m.get("bucket") == bucket]


def _auto_lines(moves):
    items = _moves(moves, "auto_3a")
    if not items:
        return _NONE
    return "\n".join(
        f"- {m.get('summary','—')} ({m.get('campaign_name','—')}) — "
        f"{m.get('expected_effect','—')} — reversal if {m.get('reversal_if','—')}"
        for m in items
    )


def _human_lines(moves):
    items = _moves(moves, "human_3b")
    if not items:
        return _NONE
    out = []
    for m in items:
        change = m.get("change") or m.get("target_value") or m.get("summary", "—")
        out.append(f"- {m.get('summary','—')} ({m.get('campaign_name','—')}) — "
                   f"gated: {m.get('reason','—')} — apply: {change}")
    return "\n".join(out)


def _creative_lines(moves):
    items = _moves(moves, "creative")
    if not items:
        return _NONE
    out = []
    for m in items:
        copy_ref = _linear_link(m.get("linear_ref")) or "task created on greenlight"
        out.append(f"- {m.get('summary','—')} ({m.get('campaign_name','—')}) — "
                   f"copy: {copy_ref} — owner: the content lead (reassignable)")
    return "\n".join(out)


def _bullets(items):
    if not items:
        return _NONE
    return "\n".join(f"- {x}" for x in items)


def render_dossier(d):
    """Render the dossier object to fixed-section markdown (pure, byte-stable)."""
    moves = d.get("moves", [])
    position = (f"**Position:** {d.get('objective','—')} — {d.get('thesis','—')}  ·  "
                f"Confidence: {d.get('confidence','—')}")
    if d.get("trigger_reason"):
        # Event-driven (off-cycle) dossier: record what tripped it.
        position += f"\n**Triggered by:** {d['trigger_reason']}"
    blocks = [
        f"# Paid Optimization Dossier — {d.get('date_range','—')}",
        position,
        "## WoW Snapshot\n" + _wow_table(d.get("wow_snapshot", [])),
        "## Campaign Health\n" + _health_lines(d.get("campaign_health", [])),
        "## Proposed Moves\n\n"
        "### 🟢 Auto on greenlight (Tier 3a — Google Ads, reversible)\n"
        + _auto_lines(moves)
        + "\n\n### 🟠 Human-applied (Tier 3b — you/operator applies)\n"
        + _human_lines(moves)
        + "\n\n### ✍️ Blocked on creative review\n"
        + _creative_lines(moves),
        "## Budget View (read-only)\n" + (d.get("budget_view") or "—"),
        "## Rollback / Abort\n" + _bullets(d.get("rollback", [])),
        "## Next-Week Hypotheses\n" + _bullets(d.get("hypotheses", [])),
    ]
    return "\n\n".join(blocks) + "\n"


def write_dossier(d, pending_root=PENDING_ROOT, published_root=PUBLISHED_ROOT):
    """Supersede the prior pending dossier, then render and write the new one.

    Moves any existing pending dossier to the published/ mirror first, so
    pending/ holds only the current dossier (supersession), then writes
    <pending_root>/optimization_dossiers/<date>-optimization-dossier.md.
    Returns the Path.
    """
    date = d["dossier_date"]
    publish.supersede(DOSSIER_TYPE, pending_root=pending_root, published_root=published_root)
    out_dir = Path(pending_root) / DOSSIER_TYPE
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}-optimization-dossier.md"
    path.write_text(render_dossier(d))
    return path
