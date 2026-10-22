#!/usr/bin/env bash
# Pull the latest main into your working branch (run this often, and before starting any new task).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [ -n "$(git status --porcelain)" ]; then
  echo "You have uncommitted changes. Commit them first (git add -A && git commit -m wip) or stash."; exit 1
fi
git fetch -q origin
git rebase origin/main
echo "Up to date with main:"; git log --oneline -5
