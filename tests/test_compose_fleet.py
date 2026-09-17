"""scripts/compose_fleet.py — a composed client fleet contains exactly what fleet.yaml selected."""
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import compose_fleet  # noqa: E402

COMPOSE = ROOT / "scripts" / "compose_fleet.py"
ALL_AGENTS = list(compose_fleet.AGENTS)
SUBSET = ["chief-of-staff", "revops-watchdog", "scribe"]


def write_fleet(path: Path, **fields) -> Path:
    f = path / "fleet.yaml"
    f.write_text(yaml.safe_dump({"profile": "orrery", **fields}, sort_keys=False))
    return f


def run_compose(fleet: Path, out: Path, *extra):
    return subprocess.run([sys.executable, str(COMPOSE), "--fleet", str(fleet), "--out", str(out), *extra],
                          capture_output=True, text=True)


def text_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() not in {".db", ".png", ".jpg", ".gif"}:
            try:
                yield p, p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue


# --------------------------------------------------------------- composed trees (built once)

@pytest.fixture(scope="module")
def full(tmp_path_factory):
    d = tmp_path_factory.mktemp("full")
    fleet = write_fleet(d, name="gtm-fleet", agents=ALL_AGENTS,
                        capabilities=list(compose_fleet.CAPABILITIES), skills="all")
    out = d / "out"
    r = run_compose(fleet, out)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


@pytest.fixture(scope="module")
def acme(tmp_path_factory):
    d = tmp_path_factory.mktemp("acme")
    fleet = write_fleet(d, name="acme", agents=SUBSET, capabilities=["funnel-stats"],
                        skills=["draft-content", "utm-builder"],
                        connectors={"crm": "project", "chat": "account"},
                        runner={"permission_mode": "acceptEdits", "max_turns": 80},
                        schedule={"enabled_entries": ["revops-watchdog-daily"]})
    out = d / "out"
    r = run_compose(fleet, out)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


@pytest.fixture(scope="module")
def solo(tmp_path_factory):
    d = tmp_path_factory.mktemp("solo")
    fleet = write_fleet(d, name="watchdog", agents=["revops-watchdog"], skills=[])
    out = d / "out"
    r = run_compose(fleet, out)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


# --------------------------------------------------------------- full compose

def test_full_compose_keeps_the_whole_fleet(full):
    # the profile rendered (profile_render exits 2 on any token it could not resolve)
    assert "Orrery" in (full / "README.md").read_text()
    assert "orrery.example" in (full / "context/brand-voice.yaml").read_text()
    registry = [l for l in (full / "CLAUDE.md").read_text().splitlines() if l.startswith("| ")]
    for name in ALL_AGENTS + list(compose_fleet.CAPABILITIES):
        assert any(l.split("|")[1].strip() == name for l in registry), name
    assert json.loads((full / ".claude-plugin/plugin.json").read_text())["name"] == "gtm-fleet"
    assert (full / "scripts/luma_mcp.py").exists() and (full / "agents/funnel-stats.md").exists()
    for agent in ALL_AGENTS:
        assert (full / "roster" / agent / "prompt.md").exists()
        assert (full / "skills" / agent / "SKILL.md").exists()


def test_full_compose_seeds_an_empty_but_migrated_fleet(full):
    con = sqlite3.connect(full / "state/working/fleet.db")
    assert con.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] > 0
    con.close()
    jd = full / "state/journal"
    for agent in ALL_AGENTS:
        body = (jd / f"{agent}.md").read_text()
        assert body.startswith("# ") and "Append-only journal." in body
        assert "\n## " not in body        # header only: no entries
    for shared in ("handoffs.md", "ops-incidents.md", "chief-of-staff-meditations.md",
                   "scribe_project_management.md"):
        assert (jd / shared).exists()


# --------------------------------------------------------------- subset compose

def test_subset_prunes_roster_skills_and_constitutions(acme):
    for gone in ("performance-marketer", "content-researcher", "content-producer", "brand-designer"):
        assert not (acme / "roster" / gone).exists()
        assert not (acme / "skills" / gone).exists()
        assert not (acme / "state/identity" / f"{gone}.md").exists()
    for kept in SUBSET:
        assert (acme / "roster" / kept / "prompt.md").exists()
        assert (acme / "skills" / kept / "SKILL.md").exists()
        assert (acme / "state/identity" / f"{kept}.md").exists()


def test_subset_keeps_knowledge_skills_and_operator_tools(acme):
    for kept in compose_fleet.KNOWLEDGE_SKILLS + compose_fleet.OPERATOR_SKILLS:
        assert (acme / "skills" / kept / "SKILL.md").exists(), kept
    assert (acme / "skills/draft-content/SKILL.md").exists()
    assert (acme / "skills/utm-builder/SKILL.md").exists()
    assert not (acme / "skills/campaign-plan").exists()
    assert not (acme / "skills/sop-gen").exists()


def test_subset_drops_the_luma_capability_and_its_mcp_server(acme):
    assert not (acme / "skills/luma-events").exists()
    assert not (acme / "scripts/luma_mcp.py").exists()
    plugin = json.loads((acme / ".claude-plugin/plugin.json").read_text())
    assert "luma" not in (plugin.get("mcpServers") or {})
    assert (acme / "agents/funnel-stats.md").exists()      # funnel-stats was selected


def test_subset_schedule_keeps_selected_agents_and_enables_one(acme):
    data = yaml.safe_load((acme / "schedule.yaml").read_text())
    assert data["defaults"]["tz"] == "America/Los_Angeles"
    assert {e["agent"] for e in data["entries"]} == set(SUBSET)
    assert [e["name"] for e in data["entries"] if e["enabled"]] == ["revops-watchdog-daily"]


def test_subset_prunes_registry_preflight_and_diagram(acme):
    dropped = ["performance-marketer", "content-researcher", "content-producer",
               "brand-designer", "luma-events"]
    registry = [l for l in (acme / "CLAUDE.md").read_text().splitlines() if l.startswith("| ")]
    assert not [l for l in registry if l.split("|")[1].strip() in dropped]
    preflight = (acme / "docs/mcp-preflight.md").read_text()
    rows = [l for l in preflight.splitlines() if l.startswith("| ")]
    assert not [l for l in rows if l.split("|")[1].strip().lower() in dropped]
    assert "| Scribe | `~~knowledge base`" in preflight
    diagram = (acme / "docs/agent-fleet-diagram.mermaid").read_text()
    for name in dropped:
        assert name not in diagram
    lines = [l.strip() for l in diagram.splitlines()]
    assert sum(l.startswith("subgraph ") for l in lines) == sum(l == "end" for l in lines)


def test_subset_prunes_the_one_shot_skill_prose(acme):
    block = [b for b in (acme / "CLAUDE.md").read_text().split("\n\n")
             if "one-shot marketing skills" in b][0]
    assert "`draft-content`" in block and "`utm-builder`" in block
    assert "`campaign-plan`" not in block and "`sop-gen`" not in block
    assert "`brand-voice`" in block and "`gtm-ops`" in block      # knowledge skills stay
    assert ",," not in block and ", ," not in block


def test_subset_renames_the_plugin_everywhere(acme):
    offenders = [p.relative_to(acme).as_posix() for p, t in text_files(acme) if "gtm-fleet" in t]
    assert offenders == []
    assert "/acme-fleet:" in (acme / "skills/help-me/SKILL.md").read_text()
    assert json.loads((acme / ".claude-plugin/plugin.json").read_text())["name"] == "acme-fleet"


def test_subset_writes_its_own_fleet_yaml_and_manifest(acme):
    composed = yaml.safe_load((acme / "fleet.yaml").read_text())
    assert composed["name"] == "acme-fleet" and composed["profile"] == "orrery"
    assert composed["agents"] == SUBSET and composed["capabilities"] == ["funnel-stats"]
    assert composed["skills"] == ["draft-content", "utm-builder"]
    assert composed["connectors"] == {"crm": "project", "chat": "account"}
    assert composed["schedule"]["enabled_entries"] == ["revops-watchdog-daily"]

    m = json.loads((acme / "compose-manifest.json").read_text())
    assert m["plugin_name"] == "acme-fleet" and m["profile"] == "orrery" and m["seed"] == "empty"
    assert m["agents"] == SUBSET and m["skills"] == composed["skills"]
    assert m["gate"] == {"ran": False, "terms": None, "findings": 0}
    assert "roster/brand-designer" in m["pruned"]["roster"]
    assert "state/identity/content-producer.md" in m["pruned"]["identity"]
    assert m["schedule"]["enabled"] == ["revops-watchdog-daily"]
    assert m["files"] > 100
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", m["source_commit"])
    assert str(acme) not in json.dumps(m)                 # no absolute paths in the manifest


def test_subset_keeps_the_profile_for_reseeding(acme):
    assert (acme / "profiles/orrery/profile.yaml").exists()


def test_solo_prunes_companion_identity_files(solo):
    idd = solo / "state/identity"
    assert (idd / "revops-watchdog.md").exists()
    assert not (idd / "scribe.md").exists()
    assert not (idd / "scribe-pm.md").exists()
    assert not (idd / "scribe-pm-cadence.yaml").exists()


def test_composed_kit_carries_no_runtime_state_from_the_source(solo):
    # localwork/ (agents' scratch) never ships; wbr/ ships as an empty skeleton dir
    assert not (solo / "localwork").exists()
    assert (solo / "wbr").is_dir()
    assert [p.name for p in (solo / "wbr").iterdir()] == [".gitkeep"]


# --------------------------------------------------------------- validation

def test_unknown_agent_exits_2(tmp_path):
    fleet = write_fleet(tmp_path, name="acme", agents=["chief-of-staff", "wombat"])
    r = run_compose(fleet, tmp_path / "out")
    assert r.returncode == 2 and "unknown agent 'wombat'" in r.stderr


def test_enabled_entry_for_a_pruned_agent_exits_2(tmp_path):
    fleet = write_fleet(tmp_path, name="acme", agents=["chief-of-staff"],
                        schedule={"enabled_entries": ["revops-watchdog-daily"]})
    r = run_compose(fleet, tmp_path / "out")
    assert r.returncode == 2 and "revops-watchdog-daily" in r.stderr


def test_demo_seed_needs_the_full_roster(tmp_path):
    fleet = write_fleet(tmp_path, name="acme", agents=SUBSET)
    r = run_compose(fleet, tmp_path / "out", "--seed", "demo")
    assert r.returncode == 2 and "demo seed requires the full roster" in r.stderr


# --------------------------------------------------------------- diagram pruning

def test_diagram_drops_a_subgraph_that_lost_every_member(tmp_path):
    d = tmp_path / "fleet.mermaid"
    d.write_text("flowchart TB\n"
                 "    subgraph Specialists[\"Specialists\"]\n"
                 "        scribe[\"Scribe\"]\n"
                 "    end\n\n"
                 "    subgraph Hub[\"Steward\"]\n"
                 "        chief-of-staff((\"chief-of-staff\"))\n"
                 "    end\n\n"
                 "    Note[\"describes the subscriber funnel\"]\n")
    compose_fleet.prune_diagram(d, ["scribe"])
    body = d.read_text()
    assert "Specialists" not in body and "chief-of-staff" in body
    assert "describes the subscriber funnel" in body     # word-boundary match, not substring
    lines = [l.strip() for l in body.splitlines()]
    assert sum(l.startswith("subgraph ") for l in lines) == sum(l == "end" for l in lines) == 1


# --------------------------------------------------------------- identity-notes overlay

def _identity_tree(tmp_path, note: str, override: str | None = None):
    profile = tmp_path / "profiles" / "acme"
    (profile / "identity-notes").mkdir(parents=True)
    (profile / "identity-notes" / "scribe.md").write_text(note)
    if override is not None:
        d = profile / "overrides" / "state" / "identity"
        d.mkdir(parents=True)
        (d / "scribe.md").write_text(override)
    out = tmp_path / "out"
    (out / "state" / "identity").mkdir(parents=True)
    (out / "state" / "identity" / "scribe.md").write_text("# Scribe — constitution\n\nBase text.\n")
    return profile, out


def test_identity_note_is_appended_to_the_constitution(tmp_path):
    profile, out = _identity_tree(tmp_path, "## Client note\n\nWBR ships Thursdays.\n")
    assert compose_fleet.apply_identity_notes(profile, out, ["scribe", "revops-watchdog"]) == ["scribe"]
    body = (out / "state/identity/scribe.md").read_text()
    assert body == "# Scribe — constitution\n\nBase text.\n\n---\n\n## Client note\n\nWBR ships Thursdays.\n"


def test_whole_file_override_suppresses_the_identity_note(tmp_path):
    profile, out = _identity_tree(tmp_path, "## Client note\n", override="# replaced\n")
    assert compose_fleet.apply_identity_notes(profile, out, ["scribe"]) == []
    assert "Client note" not in (out / "state/identity/scribe.md").read_text()


# --------------------------------------------------------------- tier-2 gate (--terms2)

def _terms(path: Path, regex: str) -> Path:
    f = path / "terms.yaml"
    f.write_text(yaml.safe_dump({"terms": [{"id": "probe", "regex": regex}]}))
    return f


def test_terms2_gate_is_recorded_and_clean_when_nothing_matches(tmp_path):
    fleet = write_fleet(tmp_path, name="watchdog", agents=["revops-watchdog"], skills=[])
    out = tmp_path / "out"
    r = run_compose(fleet, out, "--terms2", str(_terms(tmp_path, "zz-no-such-string-zz")))
    assert r.returncode == 0, r.stdout + r.stderr
    m = json.loads((out / "compose-manifest.json").read_text())
    assert m["gate"] == {"ran": True, "terms": None, "findings": 0, "terms2": "terms.yaml", "findings2": 0}
    assert "gate (tier-2): 0 findings" in r.stdout


def test_terms2_gate_fails_the_compose_when_a_term_survives(tmp_path):
    fleet = write_fleet(tmp_path, name="watchdog", agents=["revops-watchdog"], skills=[])
    out = tmp_path / "out"
    r = run_compose(fleet, out, "--terms2", str(_terms(tmp_path, "revops-watchdog")))
    assert r.returncode != 0
    m = json.loads((out / "compose-manifest.json").read_text())   # manifest is written before the gate fails
    assert m["gate"]["terms2"] == "terms.yaml" and m["gate"]["findings2"] > 0 and m["gate"]["findings"] == 0
    assert "zero-leak gate found" in r.stdout + r.stderr
