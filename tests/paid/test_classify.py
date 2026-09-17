"""Golden tests for scripts/paid/classify.py (build plan Block A1).

Pins the bucket assigned to every move shape. Any change to a verdict must
update these goldens deliberately. The safety invariant is explicit: every move
gets exactly one of the three buckets, and anything ambiguous lands in human_3b
(never auto).

Runs under pytest (the future CI gate) AND standalone via
`python3 tests/paid/test_classify.py` (pytest is not installed in every env).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid.classify import (  # noqa: E402
    AUTO_3A,
    HUMAN_3B,
    CREATIVE,
    bucket_counts,
    classify_move,
    classify_moves,
)


def _bucket(move):
    return classify_move(move)["bucket"]


# --- 3a: mechanical, reversible, Google Ads, in-envelope ---------------------

def test_add_negative_google_is_auto():
    assert _bucket({"platform": "google_ads", "op_type": "add_negative",
                    "campaign_tier": "watch"}) == AUTO_3A


def test_bid_nudge_within_envelope_is_auto():
    assert _bucket({"platform": "google_ads", "op_type": "set_bid",
                    "campaign_tier": "performing", "bid_change_pct": 12.0}) == AUTO_3A


def test_bid_nudge_at_boundary_is_auto():
    # ±20% is the locked floor/ceiling protocol; the boundary itself is auto.
    assert _bucket({"platform": "google_ads", "op_type": "set_bid",
                    "bid_change_pct": -20.0}) == AUTO_3A


def test_match_type_promotion_is_auto():
    assert _bucket({"platform": "google_ads", "op_type": "match_type_promotion",
                    "campaign_tier": "watch"}) == AUTO_3A


def test_experiment_structure_only_is_auto():
    assert _bucket({"platform": "google_ads", "op_type": "create_experiment",
                    "involves_new_copy": False}) == AUTO_3A


# --- 3b: budgets, pauses, strategy, cross-channel, LinkedIn, out-of-envelope --

def test_any_budget_change_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "budget",
                    "budget_delta_weekly": 50.0}) == HUMAN_3B


def test_large_budget_change_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "budget",
                    "budget_delta_weekly": 2500.0}) == HUMAN_3B


def test_pause_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "pause_ad"}) == HUMAN_3B


def test_bid_strategy_switch_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "bid_strategy"}) == HUMAN_3B


def test_cross_channel_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "cross_channel"}) == HUMAN_3B


def test_linkedin_move_is_human():
    assert _bucket({"platform": "linkedin", "op_type": "add_negative"}) == HUMAN_3B


def test_bid_nudge_just_over_envelope_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "set_bid",
                    "bid_change_pct": 21.0}) == HUMAN_3B


def test_bid_nudge_out_of_envelope_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "set_bid",
                    "bid_change_pct": 40.0}) == HUMAN_3B


def test_bid_nudge_unknown_magnitude_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "set_bid"}) == HUMAN_3B


def test_promotion_that_pauses_source_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "match_type_promotion",
                    "pauses_source": True}) == HUMAN_3B


# --- research-spike gate beats op eligibility --------------------------------

def test_research_spike_blocks_auto_op():
    assert _bucket({"platform": "google_ads", "op_type": "add_negative",
                    "campaign_tier": "research_spike"}) == HUMAN_3B


def test_research_spike_emoji_form_blocks():
    assert _bucket({"platform": "google_ads", "op_type": "set_bid",
                    "campaign_tier": "🔍", "bid_change_pct": 5.0}) == HUMAN_3B


def test_research_spike_beats_creative():
    # Don't even spawn copy work on a campaign under investigation.
    assert _bucket({"platform": "google_ads", "op_type": "creative",
                    "campaign_tier": "research_spike"}) == HUMAN_3B


# --- creative: new copy gate -------------------------------------------------

def test_creative_op_is_creative():
    assert _bucket({"platform": "google_ads", "op_type": "creative",
                    "campaign_tier": "watch"}) == CREATIVE


def test_new_copy_flag_routes_to_creative():
    assert _bucket({"platform": "google_ads", "op_type": "create_experiment",
                    "involves_new_copy": True}) == CREATIVE


def test_linkedin_creative_still_routes_to_creative():
    # Copy-review delegation applies across channels, not just Google.
    assert _bucket({"platform": "linkedin", "op_type": "creative"}) == CREATIVE


# --- ambiguity always falls to human_3b --------------------------------------

def test_unknown_op_type_is_human():
    assert _bucket({"platform": "google_ads", "op_type": "frobnicate"}) == HUMAN_3B


def test_missing_op_type_is_human():
    assert _bucket({"platform": "google_ads"}) == HUMAN_3B


def test_missing_platform_is_human():
    assert _bucket({"op_type": "add_negative"}) == HUMAN_3B


def test_non_dict_move_raises():
    raised = False
    try:
        classify_move(["not", "a", "dict"])
    except TypeError:
        raised = True
    assert raised, "non-dict move should raise TypeError"


# --- aggregate invariants ----------------------------------------------------

_SAMPLE = [
    {"platform": "google_ads", "op_type": "add_negative", "campaign_tier": "watch",
     "summary": "Negate 'free crm'"},
    {"platform": "google_ads", "op_type": "set_bid", "bid_change_pct": 10.0,
     "summary": "Raise Nonbrand — Incident Mgmt bid 10%"},
    {"platform": "google_ads", "op_type": "budget", "budget_delta_weekly": 1500.0,
     "summary": "Shift $1.5k to Search-Brand"},
    {"platform": "google_ads", "op_type": "pause_ad", "summary": "Pause dead RSA"},
    {"platform": "linkedin", "op_type": "set_bid", "summary": "LI CPM tweak"},
    {"platform": "google_ads", "op_type": "creative", "summary": "Founder-POV RSA"},
    {"platform": "google_ads", "op_type": "set_bid", "campaign_tier": "research_spike",
     "bid_change_pct": 8.0, "summary": "Bid on collapsing campaign"},
]


def test_every_move_gets_exactly_one_known_bucket():
    results = classify_moves(_SAMPLE)
    assert len(results) == len(_SAMPLE)
    for r in results:
        assert r["bucket"] in (AUTO_3A, HUMAN_3B, CREATIVE)


def test_sample_bucket_counts_are_pinned():
    counts = bucket_counts(classify_moves(_SAMPLE))
    # add_negative + in-envelope bid = 2 auto; budget+pause+LI+research-spike = 4 human; 1 creative.
    assert counts == {AUTO_3A: 2, HUMAN_3B: 4, CREATIVE: 1}


def test_classify_moves_echoes_traceability_fields():
    r = classify_moves([_SAMPLE[0]])[0]
    assert r["summary"] == "Negate 'free crm'"
    assert r["op_type"] == "add_negative"
    assert "reason" in r and r["reason"]


# --- standalone runner (no pytest dependency) --------------------------------

if __name__ == "__main__":
    failures = 0
    for name in sorted(k for k in dict(globals()) if k.startswith("test_")):
        fn = globals()[name]
        if not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}: {e}")
    print(f"\n{'PASS' if not failures else 'FAIL'} — "
          f"{0 if not failures else failures} failure(s)")
    sys.exit(1 if failures else 0)
