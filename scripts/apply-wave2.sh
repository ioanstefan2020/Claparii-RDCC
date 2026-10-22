#!/usr/bin/env bash
# Idempotently updates OWNERS for Wave 2. Run once (by one person) after unzipping the kit, then ship with FORCE=1.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python3 - <<'PY'
import glob, os
lines = open("OWNERS", encoding="utf-8").read().splitlines()
def drop(prefixes):
    global lines
    lines = [l for l in lines if not (l.strip() and not l.startswith("#") and l.split()[0] in prefixes)]
def add(entry):
    if entry not in lines: lines.append(entry)

# 1) frontend: all of web/ -> p3, except the accessibility engine (web/a11y/, web/shared/) -> p2
drop({"web/", "web/a11y/", "web/shared/", "web/fonts/"})
for e in ["web/ p3", "web/a11y/ p2", "web/shared/ p2", "web/fonts/ p3"]: add(e)
# 2) docs / ownership of spec files
drop({"README.md", "docs/ARCHITECTURE.md", "docs/evidence/", "docs/DEMO.md"})
for e in ["README.md p1", "docs/ARCHITECTURE.md p1", "docs/evidence/ p2", "docs/DEMO.md p3",
          "docs/TASKS-WAVE2.md frozen", "docs/PROMPTS-WAVE2.md frozen", "docs/RESEARCH-WAVE2.md frozen",
          "docs/SETTINGS-SPEC.md p2", "docs/settings.schema.json p2", "docs/DESIGN.md p3",
          "docs/CONTRACTS-WAVE2.md p1", "docs/PROMPT-SPEC.md p1", "Dockerfile p1", "tests/eval/ p1", "tests/web/ p2"]: add(e)
# 3) backend files that move to p2 (existing files found by glob, plus expected new ones)
p2_files = set(glob.glob("app/*/profile*.py")) | set(glob.glob("tests/backend/test_profile*.py"))
p2_files |= {"app/routers/transcribe.py", "app/schemas/transcribe.py", "app/routers/tts.py", "tests/backend/test_transcribe.py", "tests/backend/test_tts.py"}
drop(p2_files)
for f in sorted(p2_files): add(f + " p2")
for d in ["app/tts/", "app/audio/"]:
    drop({d}); add(d + " p2")
open("OWNERS", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("OWNERS updated. Review with: git diff OWNERS")
print("Matched existing p2 backend files:", sorted(p for p in p2_files if os.path.exists(p)) or "none found (names differ? add them to OWNERS by hand)")
PY
echo "Next: git add -A && git commit -m 'chore: wave 2 kit' && FORCE=1 ./scripts/ship.sh   # announce in the group chat, then everyone ./scripts/sync.sh"
