---
name: debug-systematically
description: Use when a test fails, something crashes, or behavior is wrong and the cause is not obvious after one attempt. Reproduce, isolate, hypothesize, verify, fix with a regression test.
---

# Systematic debugging

1. **Stop changing code.** Read the full error message and stack trace, bottom to top. Note the first line that is in OUR code.
2. **Reproduce** with one exact command. Write it down. If it is intermittent, find what varies (timing, order, data, env, version).
3. **Minimize**: smallest input and smallest code path that still fails. Use `git stash` / `git bisect` / commenting out to bisect.
4. **Check the boring things first**: wrong directory, venv not active, stale build/cache, env var missing, port in use, wrong branch, dependency version, file not saved, typo.
5. **Hypothesize**: write 2–4 candidates ranked by likelihood. For each, name a check that would confirm or kill it.
6. **Test one hypothesis at a time** with a targeted observation (assert, log, debugger, minimal script). Record the result. Revert experiments that did not help.
7. **Find the root cause**, not just where the error surfaces. Explain it in one plain sentence.
8. **Write a failing regression test**, fix, then run the full gate.
9. **Look for siblings**: grep for the same pattern elsewhere.
10. **Escalation**: 15 minutes or the same error 3 times → write down findings and ask for a different approach (simpler design, different library, cut the feature, roll back to the last `good-*` tag).

## Anti-patterns
- Shotgun edits ("try this, try that").
- Catching the exception to make the error go away.
- Blaming the library before ruling out our own code.
- Debugging for an hour without writing the findings down.
