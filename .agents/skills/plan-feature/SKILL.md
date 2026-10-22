---
name: plan-feature
description: Use before implementing any feature that touches more than one file or takes more than ~30 minutes. Produces a spec with tasks, interfaces, acceptance criteria and risks in your own docs/plan/<me>.md.
---

# Plan a feature

## Steps
1. Read `AGENTS.md`, `docs/PROJECT.md`, `docs/plan/<me>.md`, and the code the feature will touch.
2. Write the spec into `docs/plan/<me>.md` as `## Feature: <name>` using this template:

```
## Feature: <name>
**Goal:** one sentence of user-visible behavior.
**Non-goals:** what we are deliberately not doing.
**Design:** 5–10 lines. Which modules change, data flow, why this approach over the simplest alternative.
**Interfaces:** exact signatures / schemas / endpoints / message formats.
**Tasks:**
- [ ] T1 (owns: path/a.py, tests/test_a.py) — description — test: <what proves it>
- [ ] T2 (owns: path/b.py) — ... — depends on: T1 interface only
**Acceptance criteria:**
1. <observable behavior> — verify: `<exact command>`
**Risks / fallbacks:** risk → fallback
**Parallelizable:** T1 ∥ T2, then T3.
```

3. Sanity-check the plan: Can each task be done in ≤ 45 minutes? Do tasks own disjoint files? Is there a test for every acceptance criterion? Is anything in the plan outside the MVP? (If yes, cut it.)
4. Prefer a **vertical slice** (thin but end to end) over a horizontal layer (all the models, then all the routes).
5. Show the plan to the human in 5 lines or fewer and proceed unless they object, except for large or risky designs, where you wait for approval.
