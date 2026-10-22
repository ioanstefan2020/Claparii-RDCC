#!/usr/bin/env bash
# scripts/build-ext.sh - Builds the PrimaZi browser extension and packages clar-extension.zip
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1. Syncing shared accessibility and questionnaire modules..."
./scripts/sync-ext.sh

echo "==> 2. Bundling content script with esbuild (IIFE format)..."
mkdir -p extension/dist
npx esbuild extension/src/content/content.js --bundle --format=iife --outfile=extension/dist/content.js

echo "==> 3. Creating distribution zip package (clar-extension.zip)..."
rm -f clar-extension.zip
(
  cd extension
  zip -r ../clar-extension.zip manifest.json dist/ icons/ src/ README.md
)

echo "==> Build complete! Output: clar-extension.zip and extension/dist/content.js ready for 'Load unpacked' in Chrome."
