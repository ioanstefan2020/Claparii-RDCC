#!/usr/bin/env bash
# Single quality gate. Agents MUST run this before claiming anything is done.
# Auto-detects the stack. For monorepos or custom setups, create scripts/check.local.sh
# (it fully replaces the auto-detection). Exit code 0 = green.
set -uo pipefail
cd "$(dirname "$0")/.."

FAILED=0
DETECTED=0
have() { command -v "$1" >/dev/null 2>&1; }
run() { echo; echo "==> $*"; if ! "$@"; then echo "!! FAILED: $*"; FAILED=1; fi; }

if [ -f scripts/check.local.sh ]; then
  echo "==> using scripts/check.local.sh"
  bash scripts/check.local.sh
  rc=$?
  [ $rc -eq 0 ] && echo "GATE: PASS" || echo "GATE: FAIL"
  exit $rc
fi

# ---- Python ----
if [ -f pyproject.toml ] || [ -f requirements.txt ] || [ -f setup.py ] || compgen -G "tests/*.py" >/dev/null; then
  DETECTED=1
  if have ruff; then run ruff check .; fi
  # "python -m pytest" puts the project root on sys.path (plain "pytest" often cannot import your modules)
  PY=python3; have python3 || PY=python
  if "$PY" -c "import pytest" >/dev/null 2>&1; then run "$PY" -m pytest -q
  else echo "!! pytest not installed (pip install pytest)"; FAILED=1; fi
fi

# ---- Node / TypeScript ----
if [ -f package.json ]; then
  DETECTED=1
  PM=npm
  [ -f pnpm-lock.yaml ] && PM=pnpm
  [ -f yarn.lock ] && PM=yarn
  has_script() { node -e "process.exit(((require('./package.json').scripts)||{})['$1']?0:1)"; }
  has_script lint      && run "$PM" run lint
  has_script typecheck && run "$PM" run typecheck
  if has_script test; then run "$PM" test; else echo "!! package.json has no test script"; FAILED=1; fi
  has_script build     && run "$PM" run build
fi

# ---- Rust ----
if [ -f Cargo.toml ]; then
  DETECTED=1
  run cargo fmt --check
  run cargo clippy --all-targets -- -D warnings
  run cargo test
fi

# ---- Go ----
if [ -f go.mod ]; then
  DETECTED=1
  run go vet ./...
  run go test ./...
fi

# ---- Makefile test target (C/C++/HDL/other) ----
if [ -f Makefile ] && grep -qE '^test:' Makefile; then
  DETECTED=1
  run make test
fi

# ---- End-to-end smoke test (create scripts/smoke.sh for your demo path) ----
if [ -f scripts/smoke.sh ]; then
  DETECTED=1
  run bash scripts/smoke.sh
else
  echo; echo "NOTE: no scripts/smoke.sh — add an end-to-end smoke test for the demo path."
fi

if [ $DETECTED -eq 0 ]; then
  echo "!! No project type detected and no tests found. Add tests or create scripts/check.local.sh."
  FAILED=1
fi

echo
if [ $FAILED -eq 0 ]; then echo "GATE: PASS"; else echo "GATE: FAIL"; fi
exit $FAILED
