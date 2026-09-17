"""scripts/sanitize/verify.py — the zero-leak gate keeps catching what it is supposed to catch."""
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "scripts" / "sanitize" / "verify.py"


def run(root: Path, *extra):
    return subprocess.run([sys.executable, str(VERIFY), "--root", str(root), *extra], capture_output=True, text=True)


def git_repo(path: Path, *snapshots: str) -> Path:
    """A repo at `path` with one commit per snapshot of a.md — the last one is the working tree."""
    path.mkdir(parents=True, exist_ok=True)
    ident = ["-c", "user.email=t@example.com", "-c", "user.name=t", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    for i, body in enumerate(snapshots):
        (path / "a.md").write_text(body)
        subprocess.run(["git", "-C", str(path), "add", "a.md"], check=True)
        subprocess.run(["git", "-C", str(path), *ident, "commit", "-q", "--no-verify", "-m", f"c{i}"], check=True)
    return path


def banned_terms(path: Path) -> Path:
    path.write_text("terms:\n  - {id: co, regex: 'oldco'}\n")
    return path


def test_clean_tree_passes(tmp_path):
    (tmp_path / "a.md").write_text("nothing to see here, contact@example.com\n")
    r = run(tmp_path)
    assert r.returncode == 0 and "OK: 0 findings" in r.stdout


def test_secret_patterns_fail(tmp_path):
    (tmp_path / "notes.md").write_text("token pat-na1-" + "a1b2c3d4-" * 4 + "\n")
    r = run(tmp_path, "--secrets-only")
    assert r.returncode == 1 and "secret:hubspot-pat" in r.stdout


def test_terms_archives_and_db_are_scanned(tmp_path):
    terms = tmp_path / "terms.yaml"
    terms.write_text("terms:\n  - {id: co, regex: 'oldco'}\n")
    with zipfile.ZipFile(tmp_path / "bundle.plugin", "w") as z:
        z.writestr("oldco-skill/SKILL.md", "built for OldCo\n")
    con = sqlite3.connect(tmp_path / "x.db")
    con.execute("CREATE TABLE t (v TEXT)")
    con.execute("INSERT INTO t VALUES ('OLDCO rules')")
    con.commit(); con.close()
    r = run(tmp_path, "--terms", str(terms))
    assert r.returncode == 1
    assert "archive-member:co" in r.stdout and "term:co" in r.stdout and "x.db:t.v" in r.stdout


def test_placeholder_ids_are_not_findings(tmp_path):
    (tmp_path / "ids.md").write_text("collection://00000000-0000-4000-8000-000000000101 page 00000000000000000000000000000201 slack U0DEMO0001\n")
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout


def test_repo_itself_is_clean_with_generic_patterns():
    r = run(ROOT)
    assert r.returncode == 0, r.stdout[-2000:]


def test_skip_history_drops_a_finding_the_default_scan_makes(tmp_path):
    """A banned term in a PAST commit: found by default, invisible to --skip-history."""
    terms = banned_terms(tmp_path / "terms.yaml")
    repo = git_repo(tmp_path / "repo", "built for OldCo\n", "built for the client\n")
    r = run(repo, "--terms", str(terms))
    assert r.returncode == 1 and "git-history" in r.stdout
    r = run(repo, "--terms", str(terms), "--skip-history")
    assert r.returncode == 0 and "OK: 0 findings" in r.stdout, r.stdout


def test_skip_history_still_scans_the_tree(tmp_path):
    terms = banned_terms(tmp_path / "terms.yaml")
    repo = git_repo(tmp_path / "repo", "built for OldCo\n")
    r = run(repo, "--terms", str(terms), "--skip-history")
    assert r.returncode == 1 and "term:co" in r.stdout
    assert "git-history" not in r.stdout


def test_makefile_verify_gates_the_build_dir_strictly():
    """The build-dir scan must fail make — it used to end in `2>/dev/null || true`."""
    recipe = (ROOT / "Makefile").read_text().split("\nverify:\n", 1)[1].split("\n\n", 1)[0]
    assert "|| true" not in recipe and "2>/dev/null" not in recipe
    assert "--terms \"$(TERMS2)\" --skip-history" in recipe      # tier-2 runs, tree-only
