"""Tests for scripts/google_ads_mutate.py guard/plan layer (Block E1).

Covers the pure, safety-critical core: the 3a allowlist, the ±20% bid envelope,
run caps, mode gating, and supported-vs-deferred routing. The API layer
(_build_*, execute's mutate calls) is exercised by shadow runs against the live
Google Ads API, not offline — so it is intentionally not tested here.

Runs under pytest AND standalone via `python3 tests/paid/test_mutate.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts import google_ads_mutate as gm  # noqa: E402
from scripts.paid import config, db  # noqa: E402


def _set_bid(pct, **o):
    return {"op_type": "set_bid", "platform": "google_ads",
            "campaign": "customers/1/campaigns/55", "entity": "customers/1/adGroupCriteria/2~3",
            "bid_change_pct": pct, "proposal_id": 1, **o}


def _negative(entity="customers/1/adGroups/9", text="free crm", **o):
    return {"op_type": "add_negative", "platform": "google_ads", "entity": entity,
            "keyword_text": text, "proposal_id": 1, **o}


# --- _check_op: allowlist + bounds ------------------------------------------

def _raises(fn):
    try:
        fn()
        return False
    except gm.GuardError:
        return True


def test_disallowed_op_raises():
    assert _raises(lambda: gm._check_op({"op_type": "budget", "entity": "x"}))
    assert _raises(lambda: gm._check_op({"op_type": "pause_ad", "entity": "x"}))


def test_set_bid_missing_campaign_raises():
    assert _raises(lambda: gm._check_op({"op_type": "set_bid", "bid_change_pct": 5}))


def test_op_missing_entity_raises():
    assert _raises(lambda: gm._check_op({"op_type": "add_negative"}))


def test_resolve_bid_lever():
    assert gm.resolve_bid_lever("MANUAL_CPC", 0, 0) == "manual_cpc"
    assert gm.resolve_bid_lever("TARGET_CPA", 65_000_000, 0) == "target_cpa"
    assert gm.resolve_bid_lever("MAXIMIZE_CONVERSIONS", 65_000_000, 0) == "target_cpa"  # has a target
    assert gm.resolve_bid_lever("TARGET_ROAS", 0, 3.5) == "target_roas"
    assert gm.resolve_bid_lever("MAXIMIZE_CONVERSIONS", 0, 0) is None  # this account
    assert gm.resolve_bid_lever("MAXIMIZE_CONVERSION_VALUE", 0, 0) is None


def test_set_bid_within_envelope_ok():
    assert gm._check_op(_set_bid(20.0)) is True
    assert gm._check_op(_set_bid(-20.0)) is True


def test_set_bid_over_envelope_raises():
    assert _raises(lambda: gm._check_op(_set_bid(20.1)))
    assert _raises(lambda: gm._check_op(_set_bid(-25.0)))


def test_set_bid_non_numeric_pct_raises():
    assert _raises(lambda: gm._check_op(_set_bid("a lot")))
    assert _raises(lambda: gm._check_op(_set_bid(True)))  # bool is not a valid pct


# --- plan_execution: mode gating --------------------------------------------

def test_off_mode_does_not_execute():
    p = gm.plan_execution([_negative()], mode="off")
    assert p["execute"] is False and p["will_apply"] is False


def test_shadow_executes_but_does_not_apply():
    p = gm.plan_execution([_negative()], mode="shadow")
    assert p["execute"] is True and p["will_apply"] is False


def test_live_applies():
    p = gm.plan_execution([_negative()], mode="live")
    assert p["execute"] is True and p["will_apply"] is True


def test_mode_arg_overrides_env():
    # Explicit mode wins regardless of $PERFORMANCE_MARKETER_EXECUTE.
    assert gm.plan_execution([], mode="live")["will_apply"] is True
    assert gm.plan_execution([], mode="off")["will_apply"] is False


# --- plan_execution: run caps + routing -------------------------------------

def test_too_many_ops_raises():
    ops = [_set_bid(5.0) for _ in range(config.MAX_OPS_PER_RUN + 1)]
    assert _raises(lambda: gm.plan_execution(ops, mode="shadow"))


def test_at_ops_cap_ok():
    ops = [_set_bid(5.0) for _ in range(config.MAX_OPS_PER_RUN)]
    assert gm.plan_execution(ops, mode="shadow")["counts"]["total"] == config.MAX_OPS_PER_RUN


def test_supported_vs_deferred_split():
    ops = [
        _set_bid(5.0),
        _negative(),
        {"op_type": "match_type_promotion", "platform": "google_ads",
         "entity": "customers/1/adGroups/9", "proposal_id": 1},
        {"op_type": "create_experiment", "platform": "google_ads",
         "entity": "customers/1/campaigns/4", "proposal_id": 1},
    ]
    p = gm.plan_execution(ops, mode="shadow")
    assert p["counts"]["supported"] == 2          # set_bid + add_negative
    assert p["counts"]["deferred"] == 2           # promotion + experiment
    assert {o["op_type"] for o in p["deferred_to_human"]} == {
        "match_type_promotion", "create_experiment"}


def test_guard_runs_even_in_off_mode():
    # A bad op raises during planning regardless of mode — no silent pass-through.
    assert _raises(lambda: gm.plan_execution([_set_bid(99.0)], mode="off"))


# --- wiring -----------------------------------------------------------------

def test_applied_changes_is_a_writable_paid_table():
    assert "applied_changes" in db.PAID_TABLES


def test_execute_off_mode_is_inert():
    # No conn, no client, no ops touched — must not raise or call anything.
    out = gm.execute([_negative()], mode="off")
    assert out["applied"] == [] and out["validated"] == []
    assert "disabled" in out["note"]


def test_rollback_off_mode_is_inert():
    # off mode returns before touching the Ads client.
    out = gm.rollback({"op_type": "set_bid", "entity": "x", "prior_value": "{}", "id": 1},
                      mode="off")
    assert out["rolled_back"] is False and "disabled" in out["note"]


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
