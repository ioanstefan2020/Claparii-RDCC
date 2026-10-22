---
name: implement-feature
description: Use when implementing a scoped task from a spec. Enforces test-first development, small green steps, the gate, and an end-to-end check before reporting done.
---

# Implement a feature task

## Loop
1. **Orient**: read the task in `docs/PLAN.md`, the interfaces it must respect, and the files you own. Run `./scripts/check.sh` to confirm you start from green. If it is red before you start, report that and stop.
2. **Red**: write a failing test for the next slice of behavior. Run it; confirm it fails for the right reason.
3. **Green**: write the minimum code to pass. Run the test.
4. **Refactor**: improve names, split functions, add the why-comments and module header. Re-run the tests.
5. **Repeat** 2–4 for each slice (happy path → edge cases → error cases).
6. **Gate**: `./scripts/check.sh` must pass with no warnings you introduced.
7. **End to end**: run the real feature once (CLI/HTTP/UI/serial). Capture the real output.
8. **Update docs**: tick the task, add the 3-line note (what / why / how to test), update README if usage changed.
9. **Commit** with a clear message.
10. **Report** (AGENTS.md §10) with pasted evidence.

## For code that is hard to unit-test (UI, hardware, external APIs)
- Put logic in pure functions and test those; keep the I/O layer thin.
- Use a fake/mock for the boundary and a recorded fixture for realistic data.
- Add a scripted smoke check and list the exact manual steps for what cannot be automated.

## Anti-patterns
- Writing a lot of code before running anything.
- Adding features "while you're here".
- Mocking the function under test, or asserting on whatever the code currently returns.
- Reporting done because it "should work".
