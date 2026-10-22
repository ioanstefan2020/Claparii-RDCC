---
name: parallel-work
description: Use when splitting a feature across multiple subagents at once. Defines safe task partitioning, file ownership, interface freezing, integration and conflict handling.
---

# Running agents in parallel safely

Parallel agents are fast only if they cannot collide. Collisions cost more than they save.

## Preconditions (all must be true)
- A spec exists in `docs/plan/<me>.md` and the **interfaces are frozen** (types, signatures, endpoints, message formats).
- Tasks are independent: each can be built and tested without the others' code, using the frozen interface and a stub/fake of the other side.
- Each task **owns a disjoint set of files** (including its own test files). Shared files (config, routes registry, package manifests, `README`) are owned by the orchestrator only.

## Procedure
1. List tasks with owner files. Check for overlaps; if two tasks need the same file, merge them or sequence them.
2. Create stubs/fakes for cross-task interfaces first (the `api-contract` skill) and commit them. This is the single commit everyone starts from.
3. Launch up to **3 engineers** at once, each with a self-contained brief: goal, owned files, read-only files, interfaces, acceptance criteria, exact test command, "do not touch" list.
4. Optionally launch the `tester` in parallel on the acceptance criteria while engineers build (it writes tests against the contract).
5. As results arrive: read each report critically, then **integrate yourself**: merge, resolve conflicts, update shared files, run `./scripts/check.sh`.
6. Run the end-to-end path. If it fails, send the exact failing output back to the responsible engineer (or the `debugger`).
7. Run the `reviewer` on the integrated diff, then commit.

## Optional isolation
- If agents share one working directory, file ownership is the isolation. For stronger isolation use git worktrees: `git worktree add ../wt-<task> -b task/<name>`; merge branches in order of dependency.

## Don't parallelize when
- The design is still unclear, interfaces are changing, or the task is under ~20 minutes (coordination costs more than it saves).
- Tasks touch the same files or the same fragile piece of state (database schema, lockfile, build config).
- You are debugging. Use ONE debugger.

## Failure handling
- A subagent drifts out of its files: revert those changes and re-brief.
- A subagent reports success without evidence: treat as not done; re-run its tests.
- Two results are incompatible: the frozen contract wins; fix the side that violates it.
