"""Tests for scripts/pm/config.py — the cadence config validator.

The validation logic (_build_config) is pure and is tested with plain dicts, so
these run without PyYAML. The real YAML-file load is exercised separately and
skipped cleanly if PyYAML is not installed.
"""
import copy

import pytest

from scripts.pm.config import (
    CadenceConfig,
    ConfigError,
    DEFAULT_CONFIG_PATH,
    _build_config,
    load_config,
)

VALID = {
    "team": {
        "monday_post_pt": "05:00",
        "monday_response_deadline_pt": "23:59",
        "weekday_pulse_pt": "08:00",
        "thursday_agenda_pt": "06:30",
    },
    "accountability_mode": "state_only",
    "team_channel_id": "C0DEMO0001",
    "default_external_owner": "Scott McKeighen",
    "dm_quiet_hours_default_local": ["19:00", "08:00"],
    "members": [
        {
            "name": "Scott McKeighen",
            "slack_user_id": "U0DEMO0001",
            "slack_alias": "Scott McKeighen",
            "timezone": "America/Los_Angeles",
            "standup_tag_local": "08:00",
        },
        {
            "name": "Priya Natarajan",
            "slack_user_id": "U0DEMO0003",
            "slack_alias": "Priya Natarajan",
            "timezone": "America/Chicago",
            "standup_tag_local": "10:00",
        },
    ],
}


def _cfg(**overrides):
    d = copy.deepcopy(VALID)
    d.update(overrides)
    return d


def test_valid_config_parses():
    cfg = _build_config(VALID)
    assert isinstance(cfg, CadenceConfig)
    assert cfg.accountability_mode == "state_only"
    assert cfg.team_channel_id == "C0DEMO0001"
    assert cfg.team.thursday_agenda_pt == "06:30"
    assert len(cfg.members) == 2
    assert cfg.member("Priya Natarajan").timezone == "America/Chicago"
    assert cfg.member("Scott McKeighen").slack_user_id == "U0DEMO0001"


def test_quiet_hours_default_applied():
    cfg = _build_config(VALID)
    assert cfg.member("Scott McKeighen").dm_quiet_hours_local == ("19:00", "08:00")


def test_member_override_quiet_hours():
    d = copy.deepcopy(VALID)
    d["members"][0]["dm_quiet_hours_local"] = ["20:00", "07:00"]
    cfg = _build_config(d)
    assert cfg.member("Scott McKeighen").dm_quiet_hours_local == ("20:00", "07:00")


@pytest.mark.parametrize("mode", ["", "off", "Hybrid", None, "tier1"])
def test_bad_accountability_mode_raises(mode):
    with pytest.raises(ConfigError):
        _build_config(_cfg(accountability_mode=mode))


def test_bad_timezone_raises():
    d = copy.deepcopy(VALID)
    d["members"][0]["timezone"] = "America/Bozeman"  # not a real IANA zone
    with pytest.raises(ConfigError):
        _build_config(d)


@pytest.mark.parametrize("bad", ["5:00", "25:00", "08:60", "0800", "8am", ""])
def test_bad_time_format_raises(bad):
    d = copy.deepcopy(VALID)
    d["team"]["monday_post_pt"] = bad
    with pytest.raises(ConfigError):
        _build_config(d)


@pytest.mark.parametrize("bad", ["", "u0demo0001", "12345", "U123", "X0DEMO0001"])
def test_bad_slack_user_id_raises(bad):
    d = copy.deepcopy(VALID)
    d["members"][0]["slack_user_id"] = bad
    with pytest.raises(ConfigError):
        _build_config(d)


@pytest.mark.parametrize("bad", ["", "c0demo0001", "X0DEMO0001", "0DEMO0001"])
def test_bad_team_channel_id_raises(bad):
    with pytest.raises(ConfigError):
        _build_config(_cfg(team_channel_id=bad))


def test_missing_team_channel_id_raises():
    d = copy.deepcopy(VALID)
    del d["team_channel_id"]
    with pytest.raises(ConfigError):
        _build_config(d)


def test_duplicate_member_raises():
    d = copy.deepcopy(VALID)
    d["members"].append(dict(d["members"][0]))  # same name + alias + user_id
    with pytest.raises(ConfigError):
        _build_config(d)


def test_duplicate_slack_user_id_raises():
    d = copy.deepcopy(VALID)
    dup = dict(d["members"][1])
    dup["name"] = "Someone Else"
    dup["slack_alias"] = "else"
    dup["slack_user_id"] = d["members"][0]["slack_user_id"]  # collide on id only
    d["members"].append(dup)
    with pytest.raises(ConfigError):
        _build_config(d)


def test_empty_members_raises():
    with pytest.raises(ConfigError):
        _build_config(_cfg(members=[]))


def test_missing_team_key_raises():
    d = copy.deepcopy(VALID)
    del d["team"]["weekday_pulse_pt"]
    with pytest.raises(ConfigError):
        _build_config(d)


def test_pulse_defaults_applied_when_absent():
    cfg = _build_config(VALID)  # VALID has no 'pulse' block
    assert cfg.pulse.stale_days == 10
    assert cfg.pulse.behind_pace_pct == 0.20
    assert cfg.pulse.blocker_age_business_days == 5
    assert cfg.pulse.due_soon_days == 7


def test_pulse_overrides_parse():
    cfg = _build_config(_cfg(pulse={"stale_days": 14, "behind_pace_pct": 0.30}))
    assert cfg.pulse.stale_days == 14
    assert cfg.pulse.behind_pace_pct == 0.30
    assert cfg.pulse.far_behind_pace_pct == 0.40  # default still applied


@pytest.mark.parametrize("bad", [{"stale_days": 0}, {"stale_days": -1}, {"behind_pace_pct": "x"}, {"due_soon_days": -3}])
def test_pulse_bad_value_raises(bad):
    with pytest.raises(ConfigError):
        _build_config(_cfg(pulse=bad))


def test_default_external_owner_required():
    d = copy.deepcopy(VALID)
    del d["default_external_owner"]
    with pytest.raises(ConfigError):
        _build_config(d)


def test_default_external_owner_must_be_roster_member():
    with pytest.raises(ConfigError):
        _build_config(_cfg(default_external_owner="Nonexistent Person"))


def test_real_cadence_file_is_valid():
    """The shipped cadence config must always validate (fail-closed regression guard)."""
    pytest.importorskip("yaml")  # skip if PyYAML is not installed
    cfg = load_config(DEFAULT_CONFIG_PATH)
    assert cfg.team_channel_id == "C0DEMO0001"
    assert cfg.default_external_owner == "Maya Lindqvist"
    assert cfg.pulse.stale_days == 10 and cfg.pulse.far_behind_pace_pct == 0.40
    assert {m.name for m in cfg.members} == {
        "Scott McKeighen",
        "Maya Lindqvist",
        "Priya Natarajan",
        "Tomas Reyes",
    }
    assert cfg.member("Tomas Reyes").timezone == "Europe/Madrid"
    assert cfg.member("Priya Natarajan").timezone == "America/Chicago"
    assert cfg.member("Scott McKeighen").slack_user_id == "U0DEMO0001"
    # every member has a deterministic Slack target
    assert all(m.slack_user_id.startswith(("U", "W")) for m in cfg.members)
