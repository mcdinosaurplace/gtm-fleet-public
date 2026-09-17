"""scripts/fleet_paths.py — root resolution contract."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import fleet_paths  # noqa: E402


def test_workspace_mode_resolves_to_plugin_root(monkeypatch):
    monkeypatch.delenv("FLEET_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert fleet_paths.fleet_root(strict=True) == fleet_paths.PLUGIN_ROOT
    assert fleet_paths.PLUGIN_ROOT == ROOT


def test_env_override_wins(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir()
    monkeypatch.setenv("FLEET_ROOT", str(tmp_path))
    assert fleet_paths.fleet_root(strict=True) == tmp_path.resolve()


def test_env_without_state_dir_is_a_hard_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FLEET_ROOT", str(tmp_path))
    with pytest.raises(SystemExit):
        fleet_paths.fleet_root(strict=True)
    assert fleet_paths.fleet_root(strict=False) == fleet_paths.PLUGIN_ROOT


def test_cli_root_and_status(tmp_path):
    (tmp_path / "state").mkdir()
    env = dict(os.environ, FLEET_ROOT=str(tmp_path), DEMO_MODE="1")
    out = subprocess.run([sys.executable, str(ROOT / "scripts/fleet_paths.py"), "--root"], capture_output=True, text=True, env=env)
    assert out.returncode == 0 and out.stdout.strip() == str(tmp_path.resolve())
    out = subprocess.run([sys.executable, str(ROOT / "scripts/fleet_paths.py"), "--status"], capture_output=True, text=True, env=env)
    assert "DEMO_MODE=1" in out.stdout and "db=MISSING" in out.stdout


def test_migrations_always_resolve_under_plugin_root(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir()
    monkeypatch.setenv("FLEET_ROOT", str(tmp_path))
    assert fleet_paths.MIGRATIONS_DIR == ROOT / "state" / "working" / "migrations"
    assert fleet_paths.MIGRATIONS_DIR.is_dir()
