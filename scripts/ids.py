#!/usr/bin/env python3
"""Unique id minter for agent-written records.

Handoffs, anomalies, and spendalerts are written by uncoordinated agents (and by
the same agent on divergent branches during a scheduled-tick divergence). Assigning
ids as MAX(id)+1 makes two writers collide on the same integer, which then has to be
renumbered by hand on merge. This mints ids that are unique without any coordination:

    {agent}_{kind}_{time}_{rand}

e.g.  revops-watchdog_handoff_01j9x8k2p7_a3f2z9

- {agent}/{kind} are human-readable slugs, so a log reader can tell what a record is
  at a glance without decoding a hash.
- {time} is the mint time (48-bit ms) in lowercase Crockford base32, fixed 10 chars,
  so ids sort chronologically as plain strings — the ordering the old ints gave us.
- {rand} is 6 chars of Crockford base32 (30 bits) from os.urandom.

Same-millisecond + same-agent + same-kind collision needs a 30-bit random clash:
negligible, and it never needs renumbering.

Usage:
  python3 scripts/ids.py <agent> <kind>            # print one id
  python3 scripts/ids.py revops-watchdog anomaly --count 3   # print N ids

Importable:
  from scripts.ids import mint
  hid = mint("chief-of-staff", "handoff")

Kinds in use: handoff, anomaly, spendalert, incident. Any lowercase alnum slug is
accepted; keep it to the record type.
"""
import argparse
import os
import re
import sys
import time

# Crockford base32, lowercase (no i, l, o, u — unambiguous when read by a human).
_ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
_AGENT_SLUG = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")  # internal hyphens ok; `_` is reserved as the id field separator
_KIND_SLUG = re.compile(r"^[a-z][a-z0-9]*$")
_TIME_CHARS = 10  # 50 bits of capacity; holds a 48-bit ms timestamp
_RAND_CHARS = 6   # 30 bits


def _b32(value: int, width: int) -> str:
    """Encode a non-negative int as a fixed-width lowercase Crockford base32 string."""
    chars = []
    for _ in range(width):
        chars.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(chars))


def mint(agent: str, kind: str, *, now_ms: int = None, rand_bytes: bytes = None) -> str:
    """Mint a unique id `{agent}_{kind}_{time}_{rand}`.

    agent is a lowercase slug that may contain internal hyphens (chief-of-staff);
    kind is lowercase-alnum. Underscore never appears inside a field — it is the id
    field separator, so ids still split unambiguously on `_`. now_ms and
    rand_bytes are injectable for deterministic tests.
    """
    if not _AGENT_SLUG.match(agent):
        raise ValueError(f"agent must be a lowercase slug (internal hyphens ok), got {agent!r}")
    if not _KIND_SLUG.match(kind):
        raise ValueError(f"kind must be a lowercase alnum slug, got {kind!r}")
    if now_ms is None:
        now_ms = time.time_ns() // 1_000_000
    if rand_bytes is None:
        rand_bytes = os.urandom(4)
    rand_int = int.from_bytes(rand_bytes, "big") & ((1 << (_RAND_CHARS * 5)) - 1)
    return f"{agent}_{kind}_{_b32(now_ms, _TIME_CHARS)}_{_b32(rand_int, _RAND_CHARS)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Mint unique record id(s).")
    parser.add_argument("agent", help="writing agent slug, e.g. revops-watchdog, performance-marketer, chief-of-staff")
    parser.add_argument("kind", help="record kind slug, e.g. handoff, anomaly, spendalert, incident")
    parser.add_argument("--count", type=int, default=1, help="how many ids to print")
    args = parser.parse_args()
    try:
        for _ in range(args.count):
            print(mint(args.agent, args.kind))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
