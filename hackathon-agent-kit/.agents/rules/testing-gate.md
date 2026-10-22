---
trigger: always_on
---
# Testing gate (applies to every agent and subagent)

Before you report any task as complete you MUST:
1. Run `./scripts/check.sh` and read the full output (not just the exit code).
2. Run the changed feature end to end (the real command/endpoint/UI path), not only unit tests.
3. Include the commands and actual results in your report.

If anything fails: fix it, re-run, repeat. Do not report partial work as complete. If something cannot be verified in this environment (real hardware, paid API, browser), say so explicitly and provide the exact manual check for the human.

Forbidden: skipping or deleting failing tests, weakening assertions, hard-coding expected values, swallowing exceptions, or editing the gate script to pass.
Required for bugs: a failing test that reproduces it, written before the fix.
