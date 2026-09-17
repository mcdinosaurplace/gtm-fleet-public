#!/usr/bin/env python3
"""scripts/paid/execute.py — pure helpers for performance-marketer:execute-approved (Block F2).

Turns greenlit paid_change_proposals into mutate ops, partitions them by bucket,
and renders the Tier-3b change-list a human applies. Pure and network-free — the
actual applying is scripts/google_ads_mutate.py and the orchestration is the
performance-marketer:execute-approved skill. Caller supplies timestamps; nothing here writes.
"""
import json
from datetime import datetime, timedelta

from scripts.paid import config

BUCKETS = ("auto_3a", "human_3b", "creative")


def partition_proposals(proposals):
    """Group proposals by bucket -> {auto_3a: [...], human_3b: [...], creative: [...]}."""
    out = {b: [] for b in BUCKETS}
    for p in proposals:
        b = p.get("bucket")
        if b in out:
            out[b].append(p)
    return out


def _params(proposal):
    """Decode a proposal's target_value (JSON string | dict | None) to a dict."""
    tv = proposal.get("target_value")
    if isinstance(tv, str) and tv:
        return json.loads(tv)
    if isinstance(tv, dict):
        return dict(tv)
    return {}


def proposal_to_op(proposal):
    """Build a mutate op dict from an auto_3a proposal.

    target_value carries the execution params (entity, bid_change_pct, or
    keyword_text + match_type); op_type/platform/proposal_id come from the row.
    The result is what scripts/google_ads_mutate.py expects.
    """
    op = _params(proposal)
    op["op_type"] = proposal.get("op_type")
    op["platform"] = proposal.get("platform", "google_ads")
    op["proposal_id"] = proposal.get("id")
    return op


def proposals_to_ops(proposals):
    return [proposal_to_op(p) for p in proposals]


def render_human_change_list(proposals, dossier_date=None):
    """Render the Tier-3b moves a human must apply, as a markdown change-list."""
    header = f"# Human-applied changes (Tier 3b) — {dossier_date or ''}".rstrip()
    if not proposals:
        return header + "\n\n_No human-applied (3b) moves this run._\n"
    lines = [header, "",
             "Apply these in the Google Ads / LinkedIn UI — performance-marketer does not auto-apply 3b.",
             ""]
    for p in proposals:
        lines.append(f"- **[{p.get('platform','—')}] {p.get('campaign_name','—')}** — "
                     f"{p.get('summary','—')}")
        if p.get("reason"):
            lines.append(f"  - why gated: {p['reason']}")
        params = _params(p)
        if params:
            lines.append(f"  - details: {json.dumps(params, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def _parse_iso(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def changes_under_watch(applied_changes, now_iso, watch_hours=None):
    """Return the applied_changes still inside the rollback watch window.

    A change is watched if it was applied **live** (not a shadow simulation), has
    not already been rolled back, and was applied within `watch_hours` of
    `now_iso`. Pure: the caller supplies `now_iso` (no clock read here). The daily
    spend-watch evaluates each returned change's reversal condition.
    """
    wh = config.ROLLBACK_WATCH_HOURS if watch_hours is None else watch_hours
    cutoff = _parse_iso(now_iso) - timedelta(hours=wh)
    out = []
    for c in applied_changes:
        if c.get("mode") != "live" or c.get("rolled_back_at"):
            continue
        applied = c.get("applied_at")
        if applied and _parse_iso(applied) >= cutoff:
            out.append(c)
    return out
