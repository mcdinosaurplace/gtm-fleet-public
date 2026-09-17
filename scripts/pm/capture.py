#!/usr/bin/env python3
"""scripts/pm/capture.py — anchor-first deterministic parse of stand-up replies.

The deterministic half of the 'flexible in, rigid through' capture procedure:
group a thread's messages by roster member, split each reply into the four
sections by the template's labels OR emoji, and rule-parse the structured bits.
Anything that doesn't cleanly match is FLAGGED for the model-fallback step (which
the skill runs under a fixed prompt). The raw reply is always preserved. No model
here — this core only does the deterministic pass and the flagging.
"""

import json
import re
from datetime import date

SECTION_KEYS = ("last_week", "this_week", "blockers", "external_deps")

# keyword fragment (lowercased, decoration stripped) -> section
_KEYWORDS = [
    ("last week", "last_week"),
    ("this week", "this_week"),
    ("blocker", "blockers"),
    ("external dependenc", "external_deps"),
]
# emoji (shortcode + unicode) -> section
_EMOJI = [
    (":ballot_box_with_check:", "last_week"), ("☑", "last_week"),
    (":clipboard:", "this_week"), ("\U0001F4CB", "this_week"),
    (":warning:", "blockers"), ("⚠", "blockers"),
    (":grey_question:", "external_deps"), ("❔", "external_deps"),
]

_SHORTCODE_RE = re.compile(r":[a-z0-9_+\-]+:")
_DECORATION_RE = re.compile(r"^[\s>*_~`•\-]+")
_LINEAR_REF_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
_LINEAR_URL_RE = re.compile(r"linear\.app/")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MDY_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$")


def detect_section(line):
    """Return the section key if `line` is a section header (emoji OR keyword), else None."""
    raw = line.strip()
    if not raw:
        return None
    for token, key in _EMOJI:
        if token in raw:
            return key
    stripped = _SHORTCODE_RE.sub("", raw)
    stripped = _DECORATION_RE.sub("", stripped).replace("*", "").strip().lower()
    for kw, key in _KEYWORDS:
        if stripped.startswith(kw):
            return key
    return None


def has_linear_link(text):
    return bool(_LINEAR_REF_RE.search(text) or _LINEAR_URL_RE.search(text))


def split_sections(reply_text):
    """Anchor-split a reply: content = the lines after each header until the next header.
    Returns (sections: {key: text}, matched: int)."""
    sections = {}
    current = None
    buf = []
    for line in reply_text.splitlines():
        key = detect_section(line)
        if key:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = key
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections, len(sections)


# Signatures of the bot's OWN stand-up posts. The Slack connector posts the master and the
# tag as the operator's user_id (there is no separate bot account), so without this they
# would be folded into that member's captured reply. These substrings must track the
# templates in standup_post.py — the test renders the real templates to catch drift.
_BOT_POST_SIGNATURES = (
    "Weekly Marketing Standup - Week of",          # master broadcast
    "Reply in this thread by the end of the day",  # per-week tag preamble
)


def is_bot_post(text):
    """True if `text` is one of the bot's own posts (master or tag) rather than a human reply."""
    t = text or ""
    return any(sig in t for sig in _BOT_POST_SIGNATURES)


def aggregate_by_member(thread_messages, config):
    """Group thread messages by roster member (matched on slack_user_id), concatenating
    their text in order. The bot's own posts (master/tag) are skipped — they carry the
    operator's user_id but are not that person's reply. Multiple genuine messages from one
    member ARE kept and concatenated (a member may split their update across messages).
    Returns {owner_name: raw_reply}. Non-roster authors are ignored."""
    by_uid = {}
    for msg in thread_messages:
        if is_bot_post(msg.get("text", "")):
            continue
        by_uid.setdefault(msg.get("user_id"), []).append(msg.get("text", ""))
    out = {}
    for m in config.members:
        if m.slack_user_id in by_uid:
            out[m.name] = "\n".join(by_uid[m.slack_user_id]).strip()
    return out


def parse_reply(reply_text):
    """Anchor-parse one member's reply. needs_model is True when no anchors matched
    (a free-form reply — the model fallback handles the section split)."""
    sections, matched = split_sections(reply_text)
    return {
        "sections": sections,
        "matched": matched,
        "linear_links_present": has_linear_link(reply_text),
        "needs_model": matched == 0,
    }


def _parse_simple_date(s):
    """ISO (YYYY-MM-DD) or M/D/YY[YY] -> ISO string; else None. NL dates -> model fallback."""
    s = s.strip()
    if _ISO_RE.match(s):
        return s
    m = _MDY_RE.match(s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y += 2000 if y < 100 else 0
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None
    return None


def parse_external_dep_line(line):
    """Rule-parse a '/'-structured dep line (party / action / date). Returns a dict with
    parsed_by='rule', or None if it's not the structured form (-> model fallback)."""
    line = line.strip()
    parts = [p.strip() for p in line.split("/")]
    if len(parts) >= 3 and parts[0]:
        return {
            "external_party": parts[0],
            "owner_side_action": parts[1],
            "expected_delivery": _parse_simple_date(parts[2]),
            "raw_text": line,
            "parsed_by": "rule",
        }
    return None


# A whole line that's just a negative response ("None", "N/A", "No dependencies") means
# zero dependencies, not an unparseable one -- skip it rather than sending it to the
# model fallback. Anchored full-line match so real content that merely starts with "no"
# ("No, still waiting on Design...") is untouched.
_NEGATIVE_RESPONSE_RE = re.compile(
    r"^(none|no|n/?a|nothing|not applicable|no external dependenc(?:y|ies)|no dependenc(?:y|ies))[.!]?$",
    re.IGNORECASE,
)


def is_negative_response(line):
    """True if `line` is a bare negative response (no dependencies to report)."""
    return bool(_NEGATIVE_RESPONSE_RE.match(line.strip()))


def parse_external_deps(section_text):
    """Split the external-deps section into per-line deps. '/'-structured lines are
    rule-parsed; a bare negative response ("None", "N/A", ...) is dropped as zero
    dependencies; the rest are returned as raw lines for the model fallback."""
    rule, needs_model = [], []
    for line in (section_text or "").splitlines():
        line = line.strip().lstrip("•-* ").strip()
        if not line or is_negative_response(line):
            continue
        parsed = parse_external_dep_line(line)
        rule.append(parsed) if parsed else needs_model.append(line)
    return {"rule": rule, "needs_model": needs_model}


def capture(thread_messages, config):
    """Full anchor-first pass over a stand-up thread. A roster member's aggregated reply
    lands in one of two buckets:

    - `members`: at least one section anchor matched -- a real stand-up response. Goes
      through the normal write path (pm_standup_responses, commitment resolution).
    - `context`: zero anchors matched -- thread chatter (e.g. a reply to someone else's
      blocker question, cross-talk about a project). NOT a stand-up response: the member
      stays in `non_responders` and nothing is written to pm_standup_responses for them.
      The raw text is preserved for the skill's archive step and as input to the
      section-split model-fallback prompt, run over `context` (not `members` -- every
      `members` entry has matched >= 1 anchor by construction). A chatter reply that
      turns out to carry a real commitment ("I'll get X done by Friday") still flows into
      commitment resolution, tagged as thread-sourced -- it just never fabricates a
      response for someone who didn't give one.

    Pure; the skill does model-fill + DB writes."""
    members, context = [], []
    for owner, raw in aggregate_by_member(thread_messages, config).items():
        parsed = parse_reply(raw)
        if parsed["matched"] == 0:
            context.append({"owner": owner, "raw_text": raw})
            continue
        ext = parse_external_deps(parsed["sections"].get("external_deps", ""))
        members.append(
            {
                "owner": owner,
                "raw_text": raw,
                "responded": True,
                "sections": parsed["sections"],
                "linear_links_present": parsed["linear_links_present"],
                "external_deps_rule": ext["rule"],
                "external_deps_needs_model": ext["needs_model"],
            }
        )
    responded = {m["owner"] for m in members}
    non_responders = [m.name for m in config.members if m.name not in responded]
    return {"members": members, "non_responders": non_responders, "context": context}


def main(argv=None):
    """CLI: read thread JSON ({"thread_messages": [...]}) from stdin, print capture() JSON."""
    import sys

    from scripts.pm.config import load_config

    payload = json.load(sys.stdin)
    print(json.dumps(capture(payload["thread_messages"], load_config()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
