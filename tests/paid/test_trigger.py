"""Golden tests for scripts/paid/trigger.py (build plan Block B2).

Pins the off-cycle trigger decision: HIGH or clustered MED fires; a normal day
does not. Runs under pytest AND standalone via `python3 tests/paid/test_trigger.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid.trigger import should_form_position  # noqa: E402


def _alert(sev, **over):
    a = {"severity": sev, "surface": "spend", "campaign_name": "Search - Generic"}
    a.update(over)
    return a


def test_high_triggers():
    r = should_form_position([_alert("HIGH", description="Zero spend on Nonbrand — Incident Mgmt")])
    assert r["trigger"] is True
    assert r["severity"] == "HIGH"
    assert "Nonbrand — Incident Mgmt" in r["reason"]


def test_three_med_cluster_triggers():
    r = should_form_position([_alert("MED"), _alert("MED"), _alert("MED")])
    assert r["trigger"] is True
    assert r["severity"] == "MED"


def test_two_med_does_not_trigger():
    r = should_form_position([_alert("MED"), _alert("MED")])
    assert r["trigger"] is False
    assert r["severity"] is None


def test_low_only_does_not_trigger():
    r = should_form_position([_alert("LOW"), _alert("LOW"), _alert("LOW"), _alert("LOW")])
    assert r["trigger"] is False


def test_empty_day_does_not_trigger():
    assert should_form_position([])["trigger"] is False
    assert should_form_position(None)["trigger"] is False


def test_high_beats_med_cluster_in_severity():
    r = should_form_position([_alert("HIGH"), _alert("MED"), _alert("MED"), _alert("MED")])
    assert r["severity"] == "HIGH"  # HIGH reported even when MED cluster also present


def test_triggering_list_carries_the_anomalies():
    highs = [_alert("HIGH", description="boom")]
    r = should_form_position(highs + [_alert("LOW")])
    assert r["triggering"] == highs


def test_custom_cluster_threshold():
    alerts = [_alert("MED"), _alert("MED")]
    assert should_form_position(alerts, med_cluster=2)["trigger"] is True
    assert should_form_position(alerts, med_cluster=3)["trigger"] is False


def test_severity_case_insensitive():
    assert should_form_position([_alert("high")])["trigger"] is True


def test_ranking_anomaly_label_used_in_reason():
    r = should_form_position([{"severity": "HIGH", "keyword": "open source project management"}])
    assert "open source project management" in r["reason"]


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
