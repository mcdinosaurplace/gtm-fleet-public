"""Tests for scripts/paid/config.py (Block E3) — caps + kill switch.

Runs under pytest AND standalone via `python3 tests/paid/test_config.py`.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid import classify, config  # noqa: E402


def _set_mode(val):
    if val is None:
        os.environ.pop(config.EXECUTE_ENV, None)
    else:
        os.environ[config.EXECUTE_ENV] = val


def test_default_mode_is_off():
    _set_mode(None)
    assert config.execution_mode() == "off"
    assert config.writes_enabled() is False


def test_shadow_never_writes():
    _set_mode("shadow")
    try:
        assert config.execution_mode() == "shadow"
        assert config.writes_enabled() is False
    finally:
        _set_mode(None)


def test_live_enables_writes():
    _set_mode("live")
    try:
        assert config.execution_mode() == "live"
        assert config.writes_enabled() is True
    finally:
        _set_mode(None)


def test_unrecognized_mode_falls_back_to_off():
    _set_mode("YOLO")
    try:
        assert config.execution_mode() == "off"
        assert config.writes_enabled() is False
    finally:
        _set_mode(None)


def test_mode_case_and_whitespace_insensitive():
    _set_mode("  LIVE ")
    try:
        assert config.execution_mode() == "live"
    finally:
        _set_mode(None)


def test_bid_cap_locked_at_20():
    assert config.BID_CHANGE_PCT_MAX == 20.0


def test_run_caps_present():
    assert config.MAX_OPS_PER_RUN == 25
    assert config.MAX_NEGATIVES_PER_RUN == 50


def test_allowlist_excludes_budgets_and_pauses():
    assert "budget" not in config.ALLOWED_OPS
    assert "pause_ad" not in config.ALLOWED_OPS
    assert set(config.ALLOWED_OPS) == {
        "add_negative", "set_bid", "match_type_promotion", "create_experiment"}


def test_classify_bid_envelope_matches_config():
    # Single source of truth: classify's default must equal config's locked cap.
    assert classify.DEFAULT_THRESHOLDS["bid_change_pct_max"] == config.BID_CHANGE_PCT_MAX


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
