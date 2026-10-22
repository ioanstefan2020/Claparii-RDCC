#!/usr/bin/env bash
# Ship your work to main safely: commit -> rebase on origin/main -> ownership check -> gate -> push.
# Usage: ./scripts/ship.sh "feat: short message"      (run from your own branch, e.g. p1/work)
# If someone pushed meanwhile the push is rejected: just run it again.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

ME="$(git config --get hackathon.me || true)"
[ -z "$ME" ] && { echo "Set who you are first:  git config hackathon.me p1   (or p2 / p3)"; exit 1; }
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[ "$BRANCH" = "main" ] && { echo "Don't work on main. Run: git switch -c $ME/work"; exit 1; }

MSG="${1:-}"
if [ -n "$(git status --porcelain)" ]; then
  [ -z "$MSG" ] && { echo "You have uncommitted changes. Pass a commit message: ./scripts/ship.sh \"feat: ...\""; exit 1; }
  git add -A
  git commit -q -m "$MSG"
fi

git fetch -q origin
if ! git rebase origin/main; then
  echo; echo "REBASE CONFLICT. Fix the files, then: git add <files> && git rebase --continue && ./scripts/ship.sh"
  echo "(Or abort with: git rebase --abort). A conflict means someone edited your files: ask in the group chat."
  exit 1
fi

CHANGED="$(git diff --name-only origin/main...HEAD)"
if [ -z "$CHANGED" ]; then echo "Nothing to ship (no commits ahead of origin/main)."; exit 0; fi
# shellcheck disable=SC2086
python3 scripts/ownership.py "$ME" $CHANGED

./scripts/check.sh
git push origin HEAD:main
echo "SHIPPED to main. Teammates: run ./scripts/sync.sh"
