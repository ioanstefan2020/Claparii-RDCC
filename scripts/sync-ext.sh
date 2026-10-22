#!/usr/bin/env bash
# scripts/sync-ext.sh: Syncs shared accessibility & questionnaire code from web/ to extension/src/shared/
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Syncing shared accessibility code to extension/src/shared/..."

DEST="extension/src/shared"
mkdir -p "$DEST"

# 1. Copy web/a11y files
cp web/a11y/settings.js "$DEST/"
cp web/a11y/highlight.js "$DEST/"
cp web/a11y/tts.js "$DEST/"
cp web/a11y/tts-normalize-ro.js "$DEST/"
cp web/a11y/themes.css "$DEST/"
cp web/a11y/typography.css "$DEST/"
cp web/a11y/layouts.css "$DEST/"

# 2. Copy web/js/prefs files
mkdir -p "$DEST/prefs"
cp web/js/prefs/questionnaire.js "$DEST/prefs/"
cp web/js/prefs/derive.js "$DEST/prefs/"
cp web/js/prefs/migrate.js "$DEST/prefs/"
cp web/js/prefs/storage.js "$DEST/prefs/"
cp web/js/prefs/apply.js "$DEST/prefs/"
cp web/js/prefs/types.js "$DEST/prefs/"

echo "==> Sync complete! Shared files updated in $DEST"
