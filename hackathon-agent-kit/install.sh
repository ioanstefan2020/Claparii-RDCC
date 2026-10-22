#!/usr/bin/env bash
# Usage: ./install.sh /path/to/your/repo   (copies the kit into an existing/new repo; never overwrites existing files)
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-}"
[ -z "$DEST" ] && { echo "usage: $0 /path/to/repo"; exit 1; }
mkdir -p "$DEST"
cd "$DEST"
[ -d .git ] || git init -q

copy() { # copy without overwriting
  local rel="$1"
  if [ -e "$DEST/$rel" ]; then echo "skip (exists): $rel"; else mkdir -p "$(dirname "$DEST/$rel")"; cp -a "$SRC/$rel" "$DEST/$rel"; echo "added: $rel"; fi
}
(cd "$SRC" && find AGENTS.md .agents docs scripts -type f) | while read -r f; do copy "$f"; done
chmod +x scripts/check.sh

# global personal rules (only if you do not have any yet)
if [ ! -f "$HOME/.gemini/AGENTS.md" ]; then
  mkdir -p "$HOME/.gemini" && cp "$SRC/global/AGENTS.md" "$HOME/.gemini/AGENTS.md" && echo "added: ~/.gemini/AGENTS.md"
else
  echo "skip (exists): ~/.gemini/AGENTS.md  (merge global/AGENTS.md by hand if you want)"
fi

touch .gitignore
for l in ".env" "__pycache__/" "node_modules/" ".venv/" "*.log"; do grep -qxF "$l" .gitignore || echo "$l" >> .gitignore; done
echo; echo "Done. Next: open the repo in Zed, start an agy thread, and run the kickoff prompt from docs/PROMPTS.md"
