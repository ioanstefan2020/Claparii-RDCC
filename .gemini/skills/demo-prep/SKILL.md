---
name: demo-prep
description: Use in the final phase (last 20% of time) to prepare the README, pitch, demo script, fallbacks and rehearsal so the demo cannot fail.
---

# Demo and pitch prep

Judges see the demo for a few minutes. A working, rehearsed 3-minute demo beats ten half-working features.

## 1. Freeze
- Declare feature freeze. From here: only bug fixes on the demo path and demo prep. New ideas go to the Backlog.
- Tag the last known good commit: `git tag good-freeze`.

## 2. Demo script (write it in `docs/PROJECT.md` → Demo story)
- 30 s: problem and who has it (a concrete person or situation, not an abstraction).
- 90 s: live walkthrough of the happy path, 3–5 steps, exact inputs prepared in advance.
- 30 s: the technical depth worth bragging about (architecture, tests, how it was built, hard problem solved).
- 30 s: impact, what is next.
- Prepare **exact input data** and a reset command that returns the system to the starting state in one step.

## 3. Fallbacks (assume everything fails)
- Cached/mock responses for every external API or model on the demo path, switchable by one env var.
- A pre-recorded screen capture or screenshots of the working demo on the laptop.
- Offline mode, local ports, charged devices, spare cables, hotspot as Wi-Fi backup.

## 4. README (judges and teammates read this)
- One-paragraph pitch, screenshot/GIF, architecture in ≤ 10 lines (diagram if possible), install, run, test, demo instructions, tech stack, team/roles, limitations and what is next.
- Verify by following the README in a **fresh clone** in a clean directory/VM.

## 5. Rehearse
- Run the script end to end twice with a timer, out loud. Fix every hiccup. Assign who speaks and who drives.
- Prepare answers to likely questions: why this stack, what is hard here, how does it scale, what are the limits, how did you test it.

## 6. Final checks
- `./scripts/check.sh` green on a fresh clone. `.env.example` complete. No secrets in git. Repo link and slides ready, submission form filled before the deadline, not at the deadline.
