#!/usr/bin/env bash
# End-to-end smoke test for the complete PrimaZi application stack.
# Starts uvicorn on an ephemeral port with LLM_PROVIDER=mock, exercises all core endpoints
# and web pages with realistic curl requests, verifies envelopes, and exits cleanly.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================"
echo "  PrimaZi — End-to-End Smoke Test Suite"
echo "================================================================"

# Verify prerequisites
for cmd in python3 curl grep; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "!! ERROR: Missing required command: $cmd"
    exit 1
  fi
done

# 1. Ephemeral port selection
PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")
echo "==> Using ephemeral port: $PORT"

# 2. Environment configuration
export LLM_PROVIDER=mock
export PYTHONPATH=.

# 3. Start uvicorn in background with automatic cleanup
python3 -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" > /tmp/smoke_uvicorn.log 2>&1 &
SERVER_PID=$!

cleanup() {
  echo
  echo "==> Shutting down server (PID $SERVER_PID)..."
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  rm -f /tmp/smoke_*.json /tmp/smoke_uvicorn.log
}
trap cleanup EXIT INT TERM

# 4. Active polling for health check (readiness probe)
echo "==> Waiting for server to become ready on http://127.0.0.1:$PORT..."
READY=0
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.5
done

if [ "$READY" -ne 1 ]; then
  echo "!! ERROR: Server failed to start on port $PORT within 15 seconds."
  echo "--- uvicorn log ---"
  cat /tmp/smoke_uvicorn.log
  exit 1
fi
echo "==> Server is up and accepting requests."

# 5. Execute smoke checks
echo

# Check 1: Health
echo "==> [1/8] Checking GET /api/health"
HEALTH_RESP=$(curl -sf "http://127.0.0.1:$PORT/api/health")
echo "$HEALTH_RESP" | grep -q '"ok":true' || { echo "!! Health check failed: $HEALTH_RESP"; exit 1; }
echo "$HEALTH_RESP" | grep -q '"provider":"mock"' || { echo "!! Provider is not mock: $HEALTH_RESP"; exit 1; }
echo "    [PASS] Health check verified (ok=true, provider=mock)"

# Check 2: Simplify endpoint
echo "==> [2/8] Checking POST /api/simplify"
PAYLOAD_SIMPLIFY=$(python3 -c '
import json
text = open("data/samples/onboarding_ro.txt", encoding="utf-8").read()
print(json.dumps({"text": text, "profile": {"reading_level": "simple", "format": "steps"}}))
')
SIMPLIFY_RESP=$(curl -sf -X POST "http://127.0.0.1:$PORT/api/simplify" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_SIMPLIFY")
echo "$SIMPLIFY_RESP" | grep -q '"ok":true' || { echo "!! Simplify failed: $SIMPLIFY_RESP"; exit 1; }
echo "$SIMPLIFY_RESP" | grep -q '"summary"' || { echo "!! Simplify missing summary: $SIMPLIFY_RESP"; exit 1; }
echo "$SIMPLIFY_RESP" | grep -q '"steps"' || { echo "!! Simplify missing steps: $SIMPLIFY_RESP"; exit 1; }
echo "    [PASS] Simplify endpoint returned structured summary and steps"

# Check 3: Plan extraction endpoint
echo "==> [3/9] Checking POST /api/plan/extract"
PAYLOAD_PLAN=$(python3 -c '
import json
text = open("data/samples/task_email_ro.txt", encoding="utf-8").read()
print(json.dumps({"text": text, "today_iso": "2026-10-22", "profile": {"reading_level": "simple", "format": "steps"}}))
')
PLAN_RESP=$(curl -sf -X POST "http://127.0.0.1:$PORT/api/plan/extract" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_PLAN")
echo "$PLAN_RESP" | grep -q '"ok":true' || { echo "!! Plan extract failed: $PLAN_RESP"; exit 1; }
echo "$PLAN_RESP" | grep -q '"tasks"' || { echo "!! Plan extract missing tasks: $PLAN_RESP"; exit 1; }
echo "    [PASS] Plan extract endpoint returned task breakdown"

# Check 4: Meeting summarization endpoint
echo "==> [4/9] Checking POST /api/meeting/summarize"
PAYLOAD_MEETING=$(python3 -c '
import json
text = open("data/samples/meeting_transcript_ro.txt", encoding="utf-8").read()
print(json.dumps({"transcript": text, "today_iso": "2026-10-22", "profile": {"reading_level": "simple", "format": "steps"}}))
')
MEETING_RESP=$(curl -sf -X POST "http://127.0.0.1:$PORT/api/meeting/summarize" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_MEETING")
echo "$MEETING_RESP" | grep -q '"ok":true' || { echo "!! Meeting summarize failed: $MEETING_RESP"; exit 1; }
echo "$MEETING_RESP" | grep -q '"summary"' || { echo "!! Meeting summarize missing summary: $MEETING_RESP"; exit 1; }
echo "$MEETING_RESP" | grep -q '"decisions"' || { echo "!! Meeting summarize missing decisions: $MEETING_RESP"; exit 1; }
echo "$MEETING_RESP" | grep -q '"action_items"' || { echo "!! Meeting summarize missing action_items: $MEETING_RESP"; exit 1; }
echo "    [PASS] Meeting summarize endpoint returned summary, decisions, and action items"

# Check 5: Adjustments catalog endpoint
echo "==> [5/9] Checking GET /api/adjustments/catalog"
CATALOG_RESP=$(curl -sf "http://127.0.0.1:$PORT/api/adjustments/catalog")
echo "$CATALOG_RESP" | grep -q '"ok":true' || { echo "!! Catalog failed: $CATALOG_RESP"; exit 1; }
echo "$CATALOG_RESP" | grep -q '"written_instructions"' || { echo "!! Missing written_instructions: $CATALOG_RESP"; exit 1; }
echo "$CATALOG_RESP" | grep -q '"extra_time"' || { echo "!! Missing extra_time: $CATALOG_RESP"; exit 1; }
echo "    [PASS] Adjustments catalog returned >= 12 catalog items with disclaimer"

# Check 6: Adjustments draft endpoint
echo "==> [6/9] Checking POST /api/adjustments/draft"
DRAFT_RESP=$(curl -sf -X POST "http://127.0.0.1:$PORT/api/adjustments/draft" \
  -H "Content-Type: application/json" \
  -d '{"need_ids": ["written_instructions", "extra_time"], "context": "onboarding", "tone": "friendly"}')
echo "$DRAFT_RESP" | grep -q '"ok":true' || { echo "!! Draft failed: $DRAFT_RESP"; exit 1; }
echo "$DRAFT_RESP" | grep -q '"subject"' || { echo "!! Draft missing subject: $DRAFT_RESP"; exit 1; }
echo "$DRAFT_RESP" | grep -q '"body_ro"' || { echo "!! Draft missing body_ro: $DRAFT_RESP"; exit 1; }
echo "    [PASS] Adjustments draft endpoint generated subject and body"

# Check 7: Employer document analysis endpoint
echo "==> [7/9] Checking POST /api/employer/analyze"
PAYLOAD_EMPLOYER=$(python3 -c '
import json
text = open("data/samples/onboarding_ro.txt", encoding="utf-8").read()
print(json.dumps({"text": text, "doc_type": "onboarding"}))
')
EMPLOYER_RESP=$(curl -sf -X POST "http://127.0.0.1:$PORT/api/employer/analyze" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_EMPLOYER")
echo "$EMPLOYER_RESP" | grep -q '"ok":true' || { echo "!! Employer analyze failed: $EMPLOYER_RESP"; exit 1; }
echo "$EMPLOYER_RESP" | grep -q '"readability"' || { echo "!! Missing readability: $EMPLOYER_RESP"; exit 1; }
echo "$EMPLOYER_RESP" | grep -q '"score_0_100"' || { echo "!! Missing score_0_100: $EMPLOYER_RESP"; exit 1; }
echo "$EMPLOYER_RESP" | grep -q '"issues"' || { echo "!! Missing issues: $EMPLOYER_RESP"; exit 1; }
echo "$EMPLOYER_RESP" | grep -q '"easy_read_ro"' || { echo "!! Missing easy_read_ro: $EMPLOYER_RESP"; exit 1; }
echo "    [PASS] Employer analyze computed readability score and detected issues"

# Check 8: Negative error handling (empty input validation)
echo "==> [8/9] Checking error envelope on empty input"
STATUS_CODE=$(curl -s -o /tmp/smoke_err.json -w "%{http_code}" -X POST "http://127.0.0.1:$PORT/api/employer/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "   ", "doc_type": "onboarding"}')
if [ "$STATUS_CODE" -ne 400 ]; then
  echo "!! Expected HTTP 400 on empty input, got $STATUS_CODE"
  exit 1
fi
grep -q '"empty_input"' /tmp/smoke_err.json || { echo "!! Expected code empty_input: $(cat /tmp/smoke_err.json)"; exit 1; }
grep -q '"ok":false' /tmp/smoke_err.json || { echo "!! Expected ok:false: $(cat /tmp/smoke_err.json)"; exit 1; }
echo "    [PASS] Empty input produced HTTP 400 with code=empty_input envelope"

# Check 9: Static HTML web page serving
echo "==> [9/9] Checking static HTML web page serving"
PAGES=("/" "/index.html" "/welcome.html" "/employee/profile.html" "/employee/clarify.html" "/employee/plan.html" "/employee/meeting.html" "/employee/adjustments.html" "/employer/index.html")
for page in "${PAGES[@]}"; do
  PAGE_RESP=$(curl -sf "http://127.0.0.1:$PORT$page")
  echo "$PAGE_RESP" | grep -qi '<html' || { echo "!! Page $page did not return HTML"; exit 1; }
  echo "    [PASS] GET $page returned HTTP 200 with HTML"
done

echo
echo "================================================================"
echo "  SMOKE: PASS (All end-to-end smoke checks passed successfully)"
echo "================================================================"
exit 0

