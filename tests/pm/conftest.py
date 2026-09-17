"""Pytest config for the PM test suite.

Ensures the repo root is importable so tests can `import scripts.pm.*`
regardless of pytest's rootdir resolution.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
