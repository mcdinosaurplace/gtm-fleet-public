"""Deterministic bucket classifier for proposed paid-media moves.

Every move performance-marketer proposes in an optimization dossier is sorted into
exactly one of three buckets by this module — *not* by the model:

    auto_3a   Mechanical, reversible, capped Google Ads change. Auto-applied
              after greenlight (add negatives, in-envelope bid nudge, additive
              match-type promotion, experiment *structure*).
    human_3b  High-blast-radius or non-auto change. Packaged for a human to
              apply (budgets, pauses, bid-strategy switches, cross-channel,
              LinkedIn, out-of-envelope bids, anything on a campaign under
              investigation).
    creative  Requires new/changed ad copy going live. Blocked on copy review;
              spawns a Linear task (default the content lead, reassignable).

Safety contract (see plan §2, §7):
  - Ambiguous or unrecognized input is NEVER auto. It falls to human_3b.
  - The most restrictive applicable rule wins; rules are evaluated in a fixed
    safety-first order.
  - 3a NEVER changes a budget and NEVER pauses anything. Budgets and pauses are
    always human_3b.
  - Per-run COUNT caps (<=50 negatives, <=25 ops, etc.) are enforced at
    execution time in scripts/google_ads_mutate.py, not here. This module
    classifies a single move by kind, platform, tier, and magnitude.

Pure and network-free: the same input always yields the same output, which is
what the golden tests in tests/paid/ pin.
"""

AUTO_3A = "auto_3a"
HUMAN_3B = "human_3b"
CREATIVE = "creative"

# Mechanical op kinds eligible for auto-execution on Google Ads (additive /
# structure-only). `set_bid` is eligible only within the bid envelope (handled
# separately because it depends on magnitude).
AUTO_OP_KINDS = frozenset({"add_negative", "match_type_promotion", "create_experiment"})

# Op kinds that are NEVER 3a — they change budgets, pause delivery, switch the
# bidding strategy, or move money across channels.
ALWAYS_3B_OP_KINDS = frozenset({"budget", "pause_ad", "bid_strategy", "cross_channel"})

DEFAULT_THRESHOLDS = {
    # Maximum absolute bid change (percent) still eligible for auto-execution.
    # A larger requested change is a human decision — we never silently clamp.
    "bid_change_pct_max": 20.0,
}

_TIER_ALIASES = {
    "research_spike": "research_spike",
    "research spike": "research_spike",
    "🔍": "research_spike",
    "act_now": "act_now",
    "act now": "act_now",
    "🔴": "act_now",
    "watch": "watch",
    "🟡": "watch",
    "performing": "performing",
    "🟢": "performing",
}


def _normalize_tier(tier):
    """Map an emoji or label to a canonical tier string, or None if unknown."""
    if tier is None:
        return None
    key = str(tier).strip().lower()
    return _TIER_ALIASES.get(key, key)


def _involves_new_copy(move):
    """True if the move puts new or changed ad copy in front of users."""
    return move.get("op_type") == "creative" or bool(move.get("involves_new_copy"))


def classify_move(move, thresholds=None):
    """Classify a single proposed move.

    `move` is a dict describing one proposed change. Recognized keys:
        platform           'google_ads' | 'linkedin' (others -> human_3b)
        op_type            'add_negative' | 'set_bid' | 'match_type_promotion'
                           | 'create_experiment' | 'pause_ad' | 'budget'
                           | 'bid_strategy' | 'cross_channel' | 'creative'
        campaign_tier      'act_now' | 'research_spike' | 'watch' | 'performing'
                           (emoji forms accepted); optional
        involves_new_copy  truthy if new/changed copy goes live; optional
        bid_change_pct     signed percent, for op_type == 'set_bid'; optional
        pauses_source      truthy if a match-type promotion also pauses the
                           broad source (then it is not pure-additive); optional

    Returns {'bucket': <AUTO_3A|HUMAN_3B|CREATIVE>, 'reason': <str>}.

    Missing or unrecognized fields resolve to human_3b — never auto.
    """
    if not isinstance(move, dict):
        raise TypeError(f"move must be a dict, got {type(move).__name__}")

    t = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        t.update(thresholds)

    tier = _normalize_tier(move.get("campaign_tier"))
    platform = move.get("platform")
    op_type = move.get("op_type")

    # 1. Never act on a campaign under active investigation — regardless of op.
    if tier == "research_spike":
        return {"bucket": HUMAN_3B,
                "reason": "research-spike campaign — investigate before any move"}

    # 2. New/changed copy must clear copy review before going live.
    if _involves_new_copy(move):
        return {"bucket": CREATIVE,
                "reason": "involves new/changed ad copy — copy review required"}

    # 3. Only Google Ads can be auto-executed in phase 1; LinkedIn is advisory.
    if platform != "google_ads":
        return {"bucket": HUMAN_3B,
                "reason": f"platform '{platform}' is human-applied in phase 1"}

    # 4. A promotion that also pauses its broad source is not pure-additive.
    if move.get("pauses_source"):
        return {"bucket": HUMAN_3B,
                "reason": "pauses the broad source — not pure-additive"}

    # 5. Budgets, pauses, strategy switches, cross-channel: never auto.
    if op_type in ALWAYS_3B_OP_KINDS:
        return {"bucket": HUMAN_3B,
                "reason": f"'{op_type}' is always human-applied (budget/pause/strategy/cross-channel)"}

    # 6. Bid nudges auto only within the envelope; larger or unknown -> human.
    if op_type == "set_bid":
        pct = move.get("bid_change_pct")
        cap = t["bid_change_pct_max"]
        if isinstance(pct, (int, float)) and abs(pct) <= cap:
            return {"bucket": AUTO_3A,
                    "reason": f"bid change {pct:+.1f}% within +/-{cap:g}% envelope"}
        if pct is None:
            return {"bucket": HUMAN_3B,
                    "reason": "bid change magnitude unknown — human decision"}
        return {"bucket": HUMAN_3B,
                "reason": f"bid change {pct:+.1f}% exceeds +/-{cap:g}% envelope — human decision"}

    # 7. Additive / structure-only mechanical ops on Google Ads -> auto.
    if op_type in AUTO_OP_KINDS:
        return {"bucket": AUTO_3A,
                "reason": f"'{op_type}' is additive/structure-only on Google Ads"}

    # 8. Anything unrecognized is ambiguous -> the safe side.
    return {"bucket": HUMAN_3B,
            "reason": f"unrecognized op_type '{op_type}' — defaulting to human"}


def classify_moves(moves, thresholds=None):
    """Classify a list of moves.

    Returns a list of dicts, each echoing the move's `summary`, `op_type`, and
    `campaign_name` for traceability alongside the `bucket` and `reason`.
    """
    results = []
    for move in moves:
        verdict = classify_move(move, thresholds=thresholds)
        results.append({
            "summary": move.get("summary"),
            "op_type": move.get("op_type"),
            "campaign_name": move.get("campaign_name"),
            "bucket": verdict["bucket"],
            "reason": verdict["reason"],
        })
    return results


def bucket_counts(results):
    """Return {'auto_3a': n, 'human_3b': n, 'creative': n} for classified results."""
    counts = {AUTO_3A: 0, HUMAN_3B: 0, CREATIVE: 0}
    for r in results:
        counts[r["bucket"]] += 1
    return counts
