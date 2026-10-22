---
name: validation-evidence
description: Use to turn real interviews and feedback into validation evidence for the jury (problem, users, quotes, what changed in the product). Never fabricate evidence.
---

# Validation evidence (the jury's #1 criterion area)

**Hard rule: only real feedback goes in the evidence file. Never invent interviews, quotes, statistics, users or organisations.** If there is none yet, write "not yet collected". Personas must be labelled "illustrative persona (not a real person)".

## Collect (P3 leads; everyone contributes 1–2 conversations)
Talk to people with disabilities, NGO/association staff, HR/employers, career counsellors, university disability services, and team members with lived experience (only if they volunteer). 10–20 minutes each. Ask (adapt, do not lead):
1. What work document, message or process last confused or blocked you (or your employee)? What happened next?
2. What do you use today (tools, a colleague, ChatGPT, nothing)? What works, what does not?
3. If you pasted that document into an app, what would you want back, and in what format?
4. Would you ask for adjustments at work? What stops you? (privacy, fear, not knowing what to ask for)
5. (Employers/HR) How do you prepare onboarding material today? Who checks it is accessible?
Get consent to note what they say; do not record names or health details; paraphrase when unsure.

## Record in `docs/evidence/interviews.md` (one block per conversation)
```
### I-01 — <role/type, e.g. "HR specialist, mid-size company"> — <date/time> — by <p1|p2|p3>
Context: <where, how long>
Key quotes (verbatim, translated to English only if marked): "…"
Pain points: …
Current workarounds: …
Surprises / what we got wrong: …
Product change caused: <specific change or "none">
```

## Synthesize (`docs/evidence/summary.md`, P3)
- N conversations, who (types, not names), top 3 pain points with counts ("4 of 6 said …"), the strongest 2–3 quotes, what we changed because of it, what we could not validate yet (be honest), next validation steps (pilot with an NGO / HR team).
- Map each MVP feature to the pain point that justifies it. Cut features with no evidence.

## Use in the pitch
Open with one real quote (with permission), show 1 product decision it changed, close with the validation plan. The Q&A will probe this: know the numbers.
