/**
 * api.js - Client API Layer for PrimaZi
 * Owner: p2
 * Conforms to docs/CONTRACTS.md §1-§3
 * Supports ?mock=1 offline fixture fallback.
 */

const FIXTURE_PATHS = {
  simplify: "/shared/fixtures/simplify.json",
  planExtract: "/shared/fixtures/plan_extract.json",
  meetingSummarize: "/shared/fixtures/meeting_summarize.json",
  adjustmentsCatalog: "/shared/fixtures/adjustments_catalog.json",
  adjustmentsDraft: "/shared/fixtures/adjustments_draft.json"
};

/**
 * Checks if mock mode is forced via URL parameter ?mock=1 or global flag.
 */
export function isMockMode() {
  if (typeof window === "undefined") return false;
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("mock") === "1" || window.USE_MOCK === true;
}

/**
 * Loads a fixture directly when in mock mode or when the backend is unreachable.
 */
async function loadFixture(key) {
  const path = FIXTURE_PATHS[key];
  if (!path) {
    throw new Error(`Fișier fixture necunoscut pentru cheia: ${key}`);
  }
  // Try absolute and relative paths for flexibility in various local setups
  const pathsToTry = [path, `.${path}`, `./fixtures/${key}.json`];
  for (const p of pathsToTry) {
    try {
      const res = await fetch(p);
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // try next path
    }
  }
  throw new Error(`Nu s-a putut încărca fișierul de test pentru: ${key}`);
}

/**
 * Unified request sender with standard error wrapping and mock fallback.
 */
async function sendRequest(url, options = {}, fixtureKey = null) {
  if (isMockMode() && fixtureKey) {
    return await loadFixture(fixtureKey);
  }

  try {
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });

    const data = await res.json();
    if (!res.ok && !data.error) {
      return {
        ok: false,
        error: {
          code: "server_error",
          message_ro: `Eroare server (${res.status}). Vă rugăm reîncercați.`
        }
      };
    }
    return data;
  } catch (err) {
    // If backend is unavailable or offline, and fixtureKey is provided, fall back gracefully
    if (fixtureKey) {
      console.warn(`Backend indisponibil la ${url}. Se comută automat pe date mock (${fixtureKey}).`);
      try {
        return await loadFixture(fixtureKey);
      } catch {
        // Fall through to error
      }
    }

    return {
      ok: false,
      error: {
        code: "network_error",
        message_ro: "Nu s-a putut contacta serverul. Verificați conexiunea la rețea."
      }
    };
  }
}

/**
 * Simplify a document / onboarding text (F2).
 * POST /api/simplify
 */
export async function simplifyDocument(text, profile = null) {
  if (!text || !text.trim()) {
    return {
      ok: false,
      error: { code: "empty_input", message_ro: "Textul este gol. Lipește sau scrie ceva." }
    };
  }
  return await sendRequest("/api/simplify", {
    method: "POST",
    body: JSON.stringify({ text, profile })
  }, "simplify");
}

/**
 * Extract structured tasks and deadlines (F3).
 * POST /api/plan/extract
 */
export async function extractPlan(text, todayIso = null, profile = null) {
  if (!text || !text.trim()) {
    return {
      ok: false,
      error: { code: "empty_input", message_ro: "Textul este gol. Lipește sau scrie ceva." }
    };
  }
  const today = todayIso || new Date().toISOString().slice(0, 10);
  return await sendRequest("/api/plan/extract", {
    method: "POST",
    body: JSON.stringify({ text, today_iso: today, profile })
  }, "planExtract");
}

/**
 * Summarize meeting transcript (F4).
 * POST /api/meeting/summarize
 */
export async function summarizeMeeting(transcript, todayIso = null, profile = null) {
  if (!transcript || !transcript.trim()) {
    return {
      ok: false,
      error: { code: "empty_input", message_ro: "Transcrierea este goală. Adaugă textul discuției." }
    };
  }
  const today = todayIso || new Date().toISOString().slice(0, 10);
  return await sendRequest("/api/meeting/summarize", {
    method: "POST",
    body: JSON.stringify({ transcript, today_iso: today, profile })
  }, "meetingSummarize");
}

/**
 * Fetch adjustments catalog (F5).
 * GET /api/adjustments/catalog
 */
export async function getAdjustmentsCatalog() {
  return await sendRequest("/api/adjustments/catalog", {
    method: "GET"
  }, "adjustmentsCatalog");
}

/**
 * Draft adjustment request letter (F5).
 * POST /api/adjustments/draft
 */
export async function draftAdjustments(needIds, context = "onboarding", employerName = null, tone = "friendly") {
  if (!needIds || !needIds.length) {
    return {
      ok: false,
      error: { code: "bad_request", message_ro: "Selectați cel puțin o adaptare din listă." }
    };
  }
  return await sendRequest("/api/adjustments/draft", {
    method: "POST",
    body: JSON.stringify({
      need_ids: needIds,
      context,
      employer_name: employerName,
      tone
    })
  }, "adjustmentsDraft");
}
