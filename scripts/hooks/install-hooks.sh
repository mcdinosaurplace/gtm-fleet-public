#!/usr/bin/env bash
# Install the path-scoped PM pre-commit hook as a symlink (so edits to the
# committed hook propagate without re-installing). Run once per clone:
#   bash scripts/hooks/install-hooks.sh
#
# Note: overwrites any existing .git/hooks/pre-commit. This repo ships none by
# default, but check first if your clone has a custom one.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
src="scripts/hooks/pre-commit"
dest="$repo_root/.git/hooks/pre-commit"

chmod +x "$repo_root/$src"
ln -sf "../../$src" "$dest"
echo "Installed PM pre-commit hook -> .git/hooks/pre-commit (symlink to $src)"
