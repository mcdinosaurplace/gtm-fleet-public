"""Tests for scripts/paid/execute.py (Block F2) — pure execute helpers.

Runs under pytest AND standalone via `python3 tests/paid/test_execute.py`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid import execute  # noqa: E402
from scripts import google_ads_mutate as gm  # noqa: E402


def _proposal(**over):
    p = {"id": 1, "platform": "google_ads", "bucket": "auto_3a", "op_type": "set_bid",
         "campaign_name": "Nonbrand — Incident Mgmt", "summary": "Raise bid 12%", "reason": "in envelope",
         "target_value": json.dumps({"entity": "customers/1/adGroupCriteria/2~3",
                                     "campaign": "customers/1/campaigns/55",
                                     "bid_change_pct": 12.0})}
    p.update(over)
    return p


def test_partition_groups_by_bucket():
    props = [_proposal(), _proposal(id=2, bucket="human_3b", op_type="budget"),
             _proposal(id=3, bucket="creative", op_type="creative")]
    parts = execute.partition_proposals(props)
    assert [p["id"] for p in parts["auto_3a"]] == [1]
    assert [p["id"] for p in parts["human_3b"]] == [2]
    assert [p["id"] for p in parts["creative"]] == [3]


def test_proposal_to_op_parses_json_target_value():
    op = execute.proposal_to_op(_proposal())
    assert op["op_type"] == "set_bid"
    assert op["platform"] == "google_ads"
    assert op["proposal_id"] == 1
    assert op["entity"] == "customers/1/adGroupCriteria/2~3"
    assert op["bid_change_pct"] == 12.0


def test_proposal_to_op_accepts_dict_target_value():
    op = execute.proposal_to_op(_proposal(target_value={"entity": "x", "bid_change_pct": 5.0}))
    assert op["entity"] == "x" and op["bid_change_pct"] == 5.0


def test_proposal_to_op_handles_missing_target_value():
    op = execute.proposal_to_op({"id": 9, "op_type": "add_negative", "platform": "google_ads"})
    assert op["op_type"] == "add_negative" and op["proposal_id"] == 9
    assert "entity" not in op  # nothing fabricated


def test_built_ops_pass_the_mutate_guard():
    # The op a greenlit auto_3a proposal produces must clear plan_execution.
    ops = execute.proposals_to_ops([_proposal()])
    plan = gm.plan_execution(ops, mode="shadow")
    assert plan["counts"]["supported"] == 1
    assert plan["execute"] is True and plan["will_apply"] is False


def test_over_envelope_proposal_is_rejected_by_guard():
    # Defense in depth: even if a bad proposal reaches execute, the guard raises.
    ops = execute.proposals_to_ops([_proposal(
        target_value=json.dumps({"entity": "x", "campaign": "customers/1/campaigns/55",
                                 "bid_change_pct": 50.0}))])
    raised = False
    try:
        gm.plan_execution(ops, mode="shadow")
    except gm.GuardError:
        raised = True
    assert raised


def test_render_human_change_list_with_items():
    props = [_proposal(id=2, bucket="human_3b", op_type="budget",
                       summary="Shift $1.5k", reason="budget is always 3b",
                       target_value=json.dumps({"weekly_delta": 1500}))]
    out = execute.render_human_change_list(props, dossier_date="2026-06-17")
    assert "Human-applied changes (Tier 3b)" in out
    assert "Shift $1.5k" in out
    assert "why gated" in out
    assert "weekly_delta" in out


def test_render_human_change_list_empty():
    out = execute.render_human_change_list([])
    assert "No human-applied (3b) moves" in out


# --- rollback watch window --------------------------------------------------

_WATCH_NOW = "2026-06-17T12:00:00Z"


def _change(**over):
    c = {"id": 1, "mode": "live", "applied_at": "2026-06-17T11:00:00Z",
         "rolled_back_at": None, "op_type": "set_bid", "entity": "x"}
    c.update(over)
    return c


def test_watch_includes_recent_live_change():
    assert len(execute.changes_under_watch([_change()], _WATCH_NOW)) == 1


def test_watch_excludes_change_past_window():
    old = _change(applied_at="2026-06-10T12:00:00Z")  # >72h before now
    assert execute.changes_under_watch([old], _WATCH_NOW) == []


def test_watch_excludes_rolled_back():
    rb = _change(rolled_back_at="2026-06-17T11:30:00Z")
    assert execute.changes_under_watch([rb], _WATCH_NOW) == []


def test_watch_excludes_shadow_simulations():
    assert execute.changes_under_watch([_change(mode="shadow")], _WATCH_NOW) == []


def test_watch_custom_window():
    c = _change(applied_at="2026-06-17T09:00:00Z")  # 3h before now
    assert len(execute.changes_under_watch([c], _WATCH_NOW, watch_hours=2)) == 0
    assert len(execute.changes_under_watch([c], _WATCH_NOW, watch_hours=4)) == 1


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
