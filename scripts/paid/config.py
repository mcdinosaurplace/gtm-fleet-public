#!/usr/bin/env python3
"""scripts/paid/config.py — paid-execution caps, guardrails, and kill switch (Block E3).

Single source of truth for the Tier-3a auto-execution bounds (build plan §7,
locked). Enforced by scripts/google_ads_mutate.py; kept in sync with
scripts/paid/classify.py's bid envelope (pinned by a test). Caps are code, not
model judgment — a violated cap raises, it never silently clamps.
"""
import os

# --- Tier 3a auto-execution caps (LOCKED) ---

# ±20% per change: the floor/ceiling protocol. A single auto bid change may not
# move a bid more than this in either direction.
BID_CHANGE_PCT_MAX = 20.0

# Total auto-applied ops allowed in one execute run.
MAX_OPS_PER_RUN = 25

# Per-op-kind run caps.
MAX_NEGATIVES_PER_RUN = 50
MAX_MATCH_TYPE_PROMOTIONS_PER_RUN = 10

# Hours an applied change is auto-watched for its reversal condition.
ROLLBACK_WATCH_HOURS = 72

# The 3a allowlist — ops eligible for auto-execution. Budgets and pauses are
# NEVER here; they are human-applied (3b). Mirrors scripts/paid/classify.py.
ALLOWED_OPS = ("add_negative", "set_bid", "match_type_promotion", "create_experiment")

# --- kill switch ---
# PERFORMANCE_MARKETER_EXECUTE gates every ad-platform write. Default 'off'. Phase 2 ships
# 'off'; 'shadow' (validate_only only, never applies) precedes 'live' (applies),
# and the off/shadow -> live flip is an explicit operator decision after a
# shadow review — never automatic.
EXECUTE_ENV = "PERFORMANCE_MARKETER_EXECUTE"
_MODES = ("off", "shadow", "live")


def execution_mode():
    """Return 'off' | 'shadow' | 'live' from $PERFORMANCE_MARKETER_EXECUTE (default 'off').

    Unrecognized values fall back to 'off' — fail safe.
    """
    val = os.environ.get(EXECUTE_ENV, "off").strip().lower()
    return val if val in _MODES else "off"


def writes_enabled():
    """True only in 'live' mode — the one mode that actually applies changes."""
    return execution_mode() == "live"
