"""The content-engine loop, headless in DEMO_MODE.

content-researcher (weekly) -> Scribe topic sync -> content-producer (daily) ->
brand-designer (queue). These cover the four places the loop used to stop: the
researcher's live-web skill had no demo behaviour, `notion-topic-sync` was not a
tickable mode, brand-designer's queue was empty, and there was no source image to
treat. Everything here runs against a throwaway FLEET_ROOT or tmp_path — never the
real workspace.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TICK = ROOT / "scripts" / "tick.py"
HERO_SOURCE = ROOT / "fixtures" / "brand" / "orrery-hero-source.png"


@pytest.fixture(scope="module")
def seeded_root(tmp_path_factory) -> Path:
    """A fresh seed into a throwaway FLEET_ROOT (same shape as tests/test_seed_demo_state.py)."""
    root = tmp_path_factory.mktemp("fleet") / "fleet"
    (root / "state/identity").mkdir(parents=True)
    for name in ("scribe-pm-cadence.yaml", "scribe.md"):  # the seeder rewrites the first; tick.py reads the second
        shutil.copy(ROOT / "state/identity" / name, root / "state/identity" / name)
    env = dict(os.environ, FLEET_ROOT=str(root))
    r = subprocess.run([sys.executable, str(ROOT / "scripts/seed_demo_state.py"), "--profile", "orrery",
                        "--as-of", "2026-08-21", "--seed", "7", "--force"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    return root


# --------------------------------------------------------------- notion-topic-sync mode
def test_tick_accepts_notion_topic_sync_for_scribe(seeded_root):
    env = dict(os.environ, FLEET_ROOT=str(seeded_root))
    env.pop("FLEET_REMOTE", None)
    r = subprocess.run([sys.executable, str(TICK), "--agent", "scribe", "--mode", "notion-topic-sync",
                        "--runner", "stub", "--dry-run"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Tick complete: scribe / notion-topic-sync" in r.stdout


def test_tick_still_rejects_an_unknown_mode(seeded_root):
    env = dict(os.environ, FLEET_ROOT=str(seeded_root))
    r = subprocess.run([sys.executable, str(TICK), "--agent", "scribe", "--mode", "topic-sync",
                        "--runner", "stub", "--dry-run"], capture_output=True, text=True, env=env)
    assert r.returncode != 0
    assert "invalid choice" in r.stderr


def test_notion_topic_sync_is_scribe_only(seeded_root):
    env = dict(os.environ, FLEET_ROOT=str(seeded_root))
    r = subprocess.run([sys.executable, str(TICK), "--agent", "brand-designer", "--mode", "notion-topic-sync",
                        "--runner", "stub", "--dry-run"], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "only supports" in r.stderr


# --------------------------------------------------------------- brand-designer queue work
def test_seed_plants_the_producer_to_designer_handoff(seeded_root):
    con = sqlite3.connect(seeded_root / "state/working/fleet.db")
    rows = con.execute("SELECT id, severity, status, subject, body FROM handoffs "
                       "WHERE from_agent = 'content-producer' AND to_agent = 'brand-designer'").fetchall()
    assert len(rows) == 1, rows
    hid, severity, status, subject, body = rows[0]
    assert (severity, status) == ("MED", "pending")
    assert "fixtures/brand/orrery-hero-source.png" in body
    for channel in ("social", "display", "web", "email"):
        assert channel in body
    # references a seeded artifact, not an invented one
    assert "brief-0001" in subject or "brief-0001" in body
    assert con.execute("SELECT COUNT(*) FROM content_drafts WHERE id = 1").fetchone()[0] == 1

    log = (seeded_root / "state/journal/handoffs.md").read_text()
    assert log.count(hid) == 1
    assert log.count("content-producer → brand-designer") == 1
    assert "fixtures/brand/orrery-hero-source.png" in log


# --------------------------------------------------------------- researcher demo behaviour
def test_social_listening_documents_the_demo_skip():
    text = (ROOT / "roster/content-researcher/skills/social-listening.md").read_text()
    assert "## DEMO_MODE" in text
    assert "social-listening: skipped (DEMO_MODE — live web sweeps disabled)" in text


# --------------------------------------------------------------- the dither engine end to end
def test_dither_engine_treats_the_hero_source(tmp_path):
    assert HERO_SOURCE.exists()
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(ROOT / "scripts/brand_designer_dither.py"), str(HERO_SOURCE),
                        "--out", str(out), "--package", "display-mrec", "--no-zip"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    produced = out / HERO_SOURCE.stem
    assert (produced / "master_bayer8.png").exists()
    assert (produced / "manifest.json").exists()

    from PIL import Image
    with Image.open(produced / "display-mrec.png") as img:
        assert img.size == (300, 250)
        assert {c[1] for c in img.convert("RGB").getcolors(maxcolors=1 << 16)} <= {(40, 40, 35), (249, 250, 249)}
