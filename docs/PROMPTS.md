# Prompt library — AccessABILITY team edition (copy, paste, replace <…>)

Replace `<me>` with p1, p2 or p3. One task per thread. Reference files with `@`. Start EVERY new thread with prompt 0.

## 0. Start / resume a thread (always first)
```
I am <me> (check: git config --get hackathon.me). Read AGENTS.md, OWNERS, docs/PROJECT.md, docs/CONTRACTS.md, my section of docs/TASKS.md, docs/plan/<me>.md, then run `git log --oneline -15` and `git status`.
Summarize in 6 lines: who I am, which files I own, current phase, my current task, what is blocked, the next single step. Do not change any files yet.
```

## 1. Setup self-test (once, 3 minutes)
```
List the rules, skills and custom subagents you can see (names only). Then run ./scripts/check.sh and `python3 scripts/ownership.py <me> app/main.py` and tell me exactly what each printed. Tell me which of my files you may edit (from OWNERS) in one list.
```

## 2. Kickoff confirmation (whole team, ONE person runs it, others read the output)
```
Run the `kickoff` skill for the AccessABILITY challenge. docs/PROJECT.md, CONTRACTS.md, PLAN.md and TASKS.md are already drafted. Do NOT rewrite them. Review them against the brief and the jury criteria and give me: (1) the 5 biggest risks to finishing in 24h, (2) anything in the contract that is ambiguous or inconsistent (quote the lines), (3) features that have no validation evidence yet, (4) what I would cut first. Do not change files.
```

## 3. P1 — first task (skeleton) — ship within 45 min
```
I am p1. Do task T1.1 from docs/TASKS.md using the plan-feature + implement-feature skills. Build the FastAPI skeleton exactly per docs/CONTRACTS.md §2: router auto-discovery from app/routers/, error envelope, GET /api/health, serving web/, generate_json with the mock provider + disk cache, verify_quotes in app/guardrails.py, config from env. Tests first (envelope, mock provider, verify_quotes dropping a fabricated quote). Only touch files I own. Run ./scripts/check.sh, start the server and curl /api/health, paste the output, then ./scripts/ship.sh "feat: backend skeleton". Tell me what P2 and P3 can now rely on.
```

## 4. P2 — first task (shell + tokens) — ship within 90 min
```
I am p2. Do task T2.1 from docs/TASKS.md using the a11y-by-design skill. Build web/index.html (hub with two entries: employee and employer), web/shared/a11y.css (design tokens: light, dark, high-contrast; focus styles; text-size and spacing controls; reduced motion), api.js with ?mock=1 fixtures shaped EXACTLY like docs/CONTRACTS.md, profile.js (localStorage + delete my data), ics.js (valid RFC 5545 output with a unit-testable pure function). Semantic HTML, Romanian UI strings in web/i18n/ro.employee.json, no CDN. Run ./scripts/check.sh (includes tests/test_a11y_static.py), do a keyboard-only pass and describe it, then ./scripts/ship.sh "feat: web shell and a11y tokens".
```

## 5. P3 — first tasks (samples, catalog, interviews)
```
I am p3. Do T3.2: review data/samples/*.txt and write data/adjustments_ro.json with all 12 ids from docs/CONTRACTS.md §3.4 (title, description in plain Romanian, applies_to, example_request, source). For any legal/rights claim use the scout agent to verify against official Romanian sources and cite the URL; if it cannot be verified, set source to "bună practică generală" and make no legal claim. Add tests/backend/test_adjustments.py that validates the JSON shape and checks no diagnosis words appear. Run ./scripts/check.sh and ./scripts/ship.sh "feat: adjustments catalog".
```
```
I am p3. Use the validation-evidence skill. Create the structure in docs/evidence/ (interviews.md, summary.md, qa-prep.md) and give me 5 interview questions for each of: a person with a disability, an NGO/association staff member, an HR specialist. I will fill the real answers myself. NEVER invent interviews, quotes or statistics.
```

## 6. A feature task (the main loop) — any person
```
Implement task <T-id> from docs/TASKS.md. Follow AGENTS.md section 4: plan in docs/plan/<me>.md (show me 5 lines and wait for my OK) -> tests first -> implement only in files I own -> ./scripts/check.sh -> run the real path (curl or browser, keyboard-only for UI) -> reviewer subagent on my diff (plus a11y-by-design for UI / responsible-ai for AI endpoints) -> ./scripts/ship.sh "<type>: <message>". Report: Done / Evidence / Not verified / Needs from others (exact change + owner) / Next. Do not say done without pasted evidence.
```

## 7. Parallel subagents inside MY files
```
Use the parallel-work skill on task <T-id>. Split it into at most 3 subtasks with disjoint files, all inside files I own (list them). Freeze interfaces first, launch the subagents with self-contained briefs, integrate and run ./scripts/check.sh yourself. State which subagent/model you launched for each.
```

## 8. Sync (after a teammate ships)
```
Run ./scripts/sync.sh, then ./scripts/check.sh. Tell me what changed on main since my last sync (git log), whether anything affects my current task, and if check.sh is red whether the cause is in my files or someone else's.
```

## 9. Bug / failing test
```
<paste exact command + full error>
Use debug-systematically. Reproduce, write a failing regression test (in a test file I own), find the ROOT CAUSE in one sentence, fix it in files I own, run ./scripts/check.sh. If the cause is in a file I do not own, do not edit it: write the exact change request for the owner. Stop after 15 minutes without progress and give me 2 alternatives.
```

## 10. "Prove it"
```
You said this is done. Prove it: run ./scripts/check.sh and show the output; run the feature the way a judge would (curl / browser steps / keyboard-only) and show what happened; list what you did NOT verify; then try 5 edge cases (empty input, huge input, Romanian diacritics ăâîșț, prompt injection inside the document, provider down).
```

## 11. Accessibility audit (P2 mainly; P3 for employer pages)
```
Use the a11y-by-design skill on web/<pages>. Run ./scripts/check.sh. Then walk the whole flow keyboard-only and describe the tab order, any trap, and any control without a visible focus. Then list what a screen reader would announce for each step (from the markup). Check contrast of every token pair in a11y.css (compute ratios), 200% zoom, 320 px width, reduced motion. Give me a prioritized fix list. Fix only files I own; for others write exact requests.
```

## 12. Responsible-AI audit (P1 and P3 on their endpoints)
```
Use the responsible-ai skill on <endpoint/prompt files>. Verify: document is treated as untrusted data in the prompt, JSON schema enforced, source_quote verified in code, ambiguous dates not invented, no diagnosis/emotion/legal-advice behavior, no content logged, errors are friendly Romanian. Write missing tests (fabricated quote, injection sample, deny-list). Report gaps with severity.
```

## 13. Independent second opinion (use DeepSeek / the other model in Zed, READ-ONLY)
```
You are an independent reviewer. Read AGENTS.md, docs/CONTRACTS.md and OWNERS, then review `git diff origin/main...HEAD`. Look for: contract violations, wrong assumptions, edge cases (Romanian diacritics, empty input), tests that would pass even if the feature were broken, accessibility problems, privacy leaks, files edited that I do not own. Do not edit files. List findings with file:line and severity.
```

## 14. Real-LLM check (P1, M3)
```
With LLM_PROVIDER=<gemini|deepseek>, run each sample in data/samples/ through its endpoint 3 times. Report per endpoint: schema validity, how many source_quotes were dropped by the guardrail, wrong or invented dates, Romanian quality problems (quote the sentence), latency. Propose prompt fixes in the prompt files I own. Do not change contracts.
```

## 15. Employer-side tasks (P3)
```
I am p3. Do T3.4. Readability statistics must be deterministic Python (sentence splitting that handles Romanian abbreviations and numbers like 6.5; words per sentence; long sentences > 25 words; a simple 0-100 score) with unit tests, separate from the LLM part. The LLM part returns issues with verbatim quotes (verified by verify_quotes), an easy-read rewrite in plain Romanian, and an adjustment checklist using catalog ids only. The score is about the DOCUMENT, never a person. Tests first, then run on data/samples/onboarding_ro.txt and show the results.
```

## 16. Smoke test (P3)
```
I am p3. Do T3.6. Write scripts/smoke.sh and tests/test_smoke.py: start the app with LLM_PROVIDER=mock on a free port, call every endpoint in docs/CONTRACTS.md with the files in data/samples/, assert envelope + shape, fetch / and every web/**/*.html (200 + contains <h1>), then stop the server. It must exit non-zero if anything is broken (prove it by temporarily breaking one endpoint). Keep it under 30 seconds.
```

## 17. Freeze + demo prep (everyone, own files; P3 coordinates)
```
We are at FREEZE. No new features. Use the demo-prep and ship-checklist skills. For my files: fix known bugs, remove dead code, make sure mock/cached mode works with no network, check every user-facing string is correct Romanian (diacritics), run ./scripts/check.sh, ship. List anything on the demo path that could still fail and its fallback.
```
```
I am p3. Write docs/evidence/qa-prep.md: the 15 hardest jury questions with 2-sentence answers using only what is true in this repo (why not ChatGPT or existing tools, privacy and GDPR, hallucinations, legal information, who pays, how it scales, what we did not validate, accessibility testing done, why no emotion detection). Then draft the 8-slide deck outline for a 6-minute pitch from docs/PROJECT.md. Mark anything unverified as such.
```

## 18. Cut scope (when time is running out)
```
We have <N> hours left. Read docs/PROJECT.md, docs/TASKS.md and git log. List what is done, in progress and not started per person. Propose the smallest set of work that still gives a complete, accessible, honest demo of F2, F3, F5 and F6, using the cut list. For each cut say what we fake (honestly labeled) or drop. Do not change files until the team agrees.
```

## 19. Fresh-clone check (P3 before submission; also each person once)
```
Clone the repo into /tmp/fresh from origin, create a venv, pip install -r requirements.txt, copy .env.example to .env (LLM_PROVIDER=mock), run ./scripts/check.sh, start the server, open the pages described in the README, and follow the README exactly. Report every place the README was wrong or incomplete.
```
