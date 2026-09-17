#!/usr/bin/env python3
"""scripts/pm/config.py — Marketing PM cadence config: loader + validator.

Deterministic and fail-closed. Reads state/identity/scribe-pm-cadence.yaml,
validates every field, and returns a typed CadenceConfig. Any malformed config
raises ConfigError so a PM Tick never proceeds on bad cadence data.

Design: all I/O is isolated in _read_yaml(); the validation lives in the pure
function _build_config(data: dict) -> CadenceConfig, which is unit-testable with
plain dicts (no PyYAML needed). yaml is imported lazily, only at the file-read
boundary. This matches the PM "pure cores" tenet.

Runtime dependency: PyYAML (see scripts/pm/requirements.txt).
"""

import re
from dataclasses import dataclass
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

REPO_ROOT = fleet_paths.FLEET_ROOT
DEFAULT_CONFIG_PATH = fleet_paths.IDENTITY_DIR / "scribe-pm-cadence.yaml"

ACCOUNTABILITY_MODES = ("state_only", "slack_first", "meeting_first", "hybrid")
TEAM_TIME_KEYS = (
    "monday_post_pt",
    "monday_response_deadline_pt",
    "weekday_pulse_pt",
    "thursday_agenda_pt",
)

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")     # 00:00-23:59
_SLACK_USER_RE = re.compile(r"^[UW][A-Z0-9]{6,}$")      # e.g. U0DEMO0001
_SLACK_CHANNEL_RE = re.compile(r"^[CGD][A-Z0-9]{6,}$")  # e.g. C0DEMO0001


class ConfigError(Exception):
    """Raised on any malformed cadence config. Fail closed."""


@dataclass(frozen=True)
class Member:
    name: str                      # full name (system of record)
    slack_user_id: str             # deterministic @-mention target (e.g. U0DEMO0001)
    slack_alias: str               # human-readable label / search fallback
    timezone: str                  # IANA timezone
    standup_tag_local: str         # "HH:MM" in the member's local timezone
    dm_quiet_hours_local: tuple    # ("HH:MM" start, "HH:MM" end), local


@dataclass(frozen=True)
class TeamDefaults:
    monday_post_pt: str
    monday_response_deadline_pt: str
    weekday_pulse_pt: str
    thursday_agenda_pt: str


@dataclass(frozen=True)
class PulseThresholds:
    stale_days: int = 10                  # orphan issue stale after N calendar days with no activity
    behind_pace_pct: float = 0.20         # >= this far behind expected pace -> at_risk
    far_behind_pace_pct: float = 0.40     # >= this + a stale blocker -> off_track
    blocker_age_business_days: int = 5    # open blocker older than this (business days) -> flag
    due_soon_days: int = 7                # current target within N calendar days -> proximity risk
    scope_window_days: int = 90           # pulse considers only work active/committed within this window
    brake_max_issues: int = 400           # >this many active-open issues in scope -> brake trips
    brake_max_projects: int = 60          # >this many active projects in scope -> brake trips
    brake_max_relation_fetches: int = 300 # >this many get_issue relation fetches -> brake trips (runtime backstop)


@dataclass(frozen=True)
class CadenceConfig:
    team: TeamDefaults
    accountability_mode: str
    team_channel_id: str
    default_external_owner: str           # roster member who owns/delegates external-led projects
    dm_quiet_hours_default_local: tuple
    pulse: PulseThresholds
    members: tuple                 # tuple[Member, ...]

    def member(self, name: str) -> Member:
        for m in self.members:
            if m.name == name:
                return m
        raise KeyError(f"No member named {name!r} in cadence config")


def _require(cond, msg):
    if not cond:
        raise ConfigError(msg)


def _validate_hhmm(value, label):
    _require(
        isinstance(value, str) and _HHMM_RE.match(value),
        f"{label} must be 'HH:MM' (00:00-23:59), got {value!r}",
    )
    return value


def _validate_tz(value, label):
    _require(isinstance(value, str) and value, f"{label} must be a non-empty IANA timezone string")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError) as e:
        raise ConfigError(f"{label} is not a valid IANA timezone: {value!r} ({e})")
    return value


def _validate_slack_id(value, label, regex, example):
    _require(
        isinstance(value, str) and regex.match(value),
        f"{label} must look like a Slack ID ({example}), got {value!r}",
    )
    return value


def _validate_quiet_hours(value, label):
    _require(
        isinstance(value, (list, tuple)) and len(value) == 2,
        f"{label} must be a [start, end] pair of HH:MM, got {value!r}",
    )
    return (_validate_hhmm(value[0], f"{label}[0]"), _validate_hhmm(value[1], f"{label}[1]"))


def _validate_number(value, label, *, minimum=None):
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} must be a number, got {value!r}",
    )
    if minimum is not None:
        _require(value >= minimum, f"{label} must be >= {minimum}, got {value}")
    return value


def _build_config(data) -> CadenceConfig:
    """Validate a parsed config mapping and return a typed CadenceConfig.

    Pure: no I/O. Raises ConfigError on any problem.
    """
    _require(isinstance(data, dict), "Top-level config must be a mapping")

    team_raw = data.get("team")
    _require(isinstance(team_raw, dict), "'team' section is required and must be a mapping")
    for k in TEAM_TIME_KEYS:
        _require(k in team_raw, f"team.{k} is required")
        _validate_hhmm(team_raw[k], f"team.{k}")
    team = TeamDefaults(**{k: team_raw[k] for k in TEAM_TIME_KEYS})

    mode = data.get("accountability_mode")
    _require(
        mode in ACCOUNTABILITY_MODES,
        f"accountability_mode must be one of {ACCOUNTABILITY_MODES}, got {mode!r}",
    )

    channel_id = _validate_slack_id(
        data.get("team_channel_id"), "team_channel_id", _SLACK_CHANNEL_RE, "C0DEMO0001"
    )

    default_external_owner = data.get("default_external_owner")
    _require(
        isinstance(default_external_owner, str) and default_external_owner,
        "default_external_owner is required (a roster member name)",
    )

    pulse_raw = data.get("pulse", {})
    _require(isinstance(pulse_raw, dict), "'pulse' must be a mapping if present")
    pulse = PulseThresholds(
        stale_days=int(_validate_number(pulse_raw.get("stale_days", 10), "pulse.stale_days", minimum=1)),
        behind_pace_pct=float(_validate_number(pulse_raw.get("behind_pace_pct", 0.20), "pulse.behind_pace_pct", minimum=0)),
        far_behind_pace_pct=float(_validate_number(pulse_raw.get("far_behind_pace_pct", 0.40), "pulse.far_behind_pace_pct", minimum=0)),
        blocker_age_business_days=int(_validate_number(pulse_raw.get("blocker_age_business_days", 5), "pulse.blocker_age_business_days", minimum=0)),
        due_soon_days=int(_validate_number(pulse_raw.get("due_soon_days", 7), "pulse.due_soon_days", minimum=0)),
        scope_window_days=int(_validate_number(pulse_raw.get("scope_window_days", 90), "pulse.scope_window_days", minimum=1)),
        brake_max_issues=int(_validate_number(pulse_raw.get("brake_max_issues", 400), "pulse.brake_max_issues", minimum=1)),
        brake_max_projects=int(_validate_number(pulse_raw.get("brake_max_projects", 60), "pulse.brake_max_projects", minimum=1)),
        brake_max_relation_fetches=int(_validate_number(pulse_raw.get("brake_max_relation_fetches", 300), "pulse.brake_max_relation_fetches", minimum=1)),
    )

    default_qh = _validate_quiet_hours(
        data.get("dm_quiet_hours_default_local", ["19:00", "08:00"]),
        "dm_quiet_hours_default_local",
    )

    members_raw = data.get("members")
    _require(isinstance(members_raw, list) and members_raw, "'members' must be a non-empty list")
    members = []
    seen_names = set()
    seen_aliases = set()
    seen_user_ids = set()
    for i, m in enumerate(members_raw):
        label = f"members[{i}]"
        _require(isinstance(m, dict), f"{label} must be a mapping")
        for key in ("name", "slack_user_id", "slack_alias", "timezone", "standup_tag_local"):
            _require(m.get(key), f"{label}.{key} is required")
        name, alias = m["name"], m["slack_alias"]
        uid = _validate_slack_id(m["slack_user_id"], f"{label}.slack_user_id", _SLACK_USER_RE, "U0DEMO0001")
        _require(name not in seen_names, f"duplicate member name {name!r}")
        _require(alias not in seen_aliases, f"duplicate slack_alias {alias!r}")
        _require(uid not in seen_user_ids, f"duplicate slack_user_id {uid!r}")
        seen_names.add(name)
        seen_aliases.add(alias)
        seen_user_ids.add(uid)
        qh = (
            _validate_quiet_hours(m["dm_quiet_hours_local"], f"{label}.dm_quiet_hours_local")
            if "dm_quiet_hours_local" in m
            else default_qh
        )
        members.append(
            Member(
                name=name,
                slack_user_id=uid,
                slack_alias=alias,
                timezone=_validate_tz(m["timezone"], f"{label}.timezone"),
                standup_tag_local=_validate_hhmm(m["standup_tag_local"], f"{label}.standup_tag_local"),
                dm_quiet_hours_local=qh,
            )
        )

    member_names = {m.name for m in members}
    _require(
        default_external_owner in member_names,
        f"default_external_owner {default_external_owner!r} must be a roster member name; have {sorted(member_names)}",
    )

    return CadenceConfig(
        team=team,
        accountability_mode=mode,
        team_channel_id=channel_id,
        default_external_owner=default_external_owner,
        dm_quiet_hours_default_local=default_qh,
        pulse=pulse,
        members=tuple(members),
    )


def _read_yaml(path) -> dict:
    """Read + YAML-parse a config file. The only I/O in this module."""
    p = Path(path)
    _require(p.exists(), f"Cadence config not found: {p}")
    try:
        import yaml  # lazy: keeps _build_config testable without the dependency
    except ImportError:
        raise ConfigError(
            "PyYAML is required to read the cadence config. "
            "Install it: pip install -r scripts/pm/requirements.txt"
        )
    try:
        return yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"Cadence config is not valid YAML: {e}")


def load_config(path=DEFAULT_CONFIG_PATH) -> CadenceConfig:
    """Load, parse, and validate the cadence config. Raises ConfigError on any problem."""
    return _build_config(_read_yaml(path))


def main(argv=None):
    import sys

    args = argv if argv is not None else sys.argv[1:]
    path = args[0] if args else DEFAULT_CONFIG_PATH
    try:
        cfg = load_config(path)
    except ConfigError as e:
        print(f"[config] INVALID: {e}", file=sys.stderr)
        return 1
    print(
        f"[config] OK: {len(cfg.members)} members, channel={cfg.team_channel_id}, "
        f"accountability_mode={cfg.accountability_mode}, default_external_owner={cfg.default_external_owner}, "
        f"stale_days={cfg.pulse.stale_days}, monday_post_pt={cfg.team.monday_post_pt}"
    )
    for m in cfg.members:
        print(
            f"  - {m.name} [{m.slack_user_id} / {m.slack_alias}] {m.timezone} "
            f"tag@{m.standup_tag_local} quiet {m.dm_quiet_hours_local[0]}-{m.dm_quiet_hours_local[1]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
