---
trigger: always_on
---
# Wave 2 rules (in addition to AGENTS.md)
1. Specs to follow: `docs/TASKS-WAVE2.md`, `docs/SETTINGS-SPEC.md`, `docs/DESIGN.md`, `docs/CONTRACTS-WAVE2.md`, `docs/PROMPT-SPEC.md`. Check `OWNERS` before editing.
2. Settings are about needs, never diagnoses. Never infer or store health conditions or personality traits. Presets are suggestions the person picks.
3. Tone notes (joke/irony/sarcasm) are tentative: text-only, evidence-quoted, `low|medium` confidence, "posibil … nesigur", off by default. Never infer emotion from voice or audio.
4. Do not claim benefits that research does not support (bionic reading, dyslexia fonts). They are optional preferences.
5. The server never rejects a profile with HTTP 422: normalise and warn. One settings schema (`docs/settings.schema.json`) is the source of truth.
6. Library/history, planner and settings stay on the device (localStorage), opt-in for saved content, with a visible "Șterge tot".
7. Audio, images and documents are processed in memory/temp files, deleted in `finally`, never stored or logged.
8. Pitch numbers come only from `docs/evidence/` (real measurements and real quotes).
