#!/usr/bin/env bash
# Citation integrity pre-commit hook.
# Delegates to check_citation_integrity.py --pre-commit
# Install: cp .claude/scripts/pre-commit-citation-check.sh .git/hooks/pre-commit
#          chmod +x .git/hooks/pre-commit

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

python3 "$REPO_ROOT/.claude/scripts/check_citation_integrity.py" --pre-commit
