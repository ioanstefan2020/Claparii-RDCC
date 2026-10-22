---
name: write-tests
description: Use when writing or reviewing tests. Covers what to test, naming, structure, determinism, mocking boundaries, smoke tests and how to prove a test is meaningful.
---

# Writing tests that actually protect you

## What to test (priority order for a hackathon)
1. The **demo path** end to end (smoke/integration test).
2. Core logic: happy path, edge cases (empty, one item, max, boundary), error cases (bad input, missing config, dependency failure).
3. Contracts between components (request/response shapes, message formats).
4. Every bug you fix (regression test).
Skip: trivial getters, framework internals, pixel-perfect UI.

## Structure
- Arrange / Act / Assert, one behavior per test, name = behavior (`test_returns_404_for_unknown_id`).
- Use fixtures/factories for setup; keep tests independent of order.
- Prefer testing through public interfaces.

## Determinism
- Seed randomness; freeze/inject time; never hit the real network, real LLM, or real hardware in unit tests; use fakes or recorded fixtures at the boundary.
- If you must test an LLM-backed step, test the parsing/validation/fallback logic around it with canned responses, and keep ONE opt-in live test (skipped by default, enabled by an env var).

## Prove the test is meaningful
- Temporarily break the code (flip a condition, return a wrong value). The test must fail. If it stays green, it is decoration — fix it.
- Never assert only that "no exception was raised" when a value can be checked.

## Smoke test pattern
- Start the app/pipeline in test mode, send one realistic input, assert the realistic output. Put the command in `scripts/smoke.sh` and keep it fast (< 30 s). `check.sh` runs it automatically if the file exists.

## Hardware / embedded / FPGA / ML notes
- HDL: self-checking testbench (assert on outputs, non-zero exit on mismatch), run in simulation (iverilog/Verilator/GHDL) from `check.sh`.
- Firmware: separate pure logic from register access so it can run on the host; mock the serial/I2C/SPI layer; test the protocol parser with captured byte streams.
- ML: golden-input/golden-output tests, shape/dtype assertions, a tiny fixed-seed sanity run, and a metric threshold test on a small held-out set.
