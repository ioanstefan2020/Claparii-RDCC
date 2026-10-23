/**
 * sw.js - Service Worker for PrimaZi Browser Extension
 * Manifest V3 background process.
 * Handles:
 *  - Backend API communication with automatic resilient fallback
 *  - Fallback error propagation to local deterministic engine
 *  - Settings sync and persistence via chrome.storage.local
 *  - Context menu and keyboard shortcut dispatch
 */

const FALLBACK_PUBLIC_BACKEND =
  "https://curves-relates-kenneth-pen.trycloudflare.com";

const DEFAULT_CONFIG = {
  backendUrl: "https://curves-relates-kenneth-pen.trycloudflare.com",
  token: "primazi-demo-2026",
  siteOrigins: [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://curves-relates-kenneth-pen.trycloudflare.com",
  ],
  localOnly: false,
  disabledSites: [],
};

const DEFAULT_PREFS = {
  version: 1,
  source: "extension",
  updatedAt: new Date().toISOString(),
  answers: {},
  prefs: {
    reading_level: 2,
    font_family: "lexend",
    font_scale: 1.0,
    line_spacing: "normal",
    theme: "default",
    bionic: false,
    ruler: false,
    read_aloud: true,
    highlight_numbers: true,
    highlight_important: true,
    speech_rate: 1.0,
  },
  overrides: [],
  freeText: "",
};

// Initialize storage and context menu on install
chrome.runtime.onInstalled.addListener(async () => {
  const current = await chrome.storage.local.get([
    "wp.ext.config",
    "wp.ext.prefs.v1",
  ]);
  if (!current["wp.ext.config"]) {
    await chrome.storage.local.set({ "wp.ext.config": DEFAULT_CONFIG });
  }
  if (!current["wp.ext.prefs.v1"]) {
    await chrome.storage.local.set({ "wp.ext.prefs.v1": DEFAULT_PREFS });
  }

  // Register context menu for text selections
  try {
    chrome.contextMenus.create({
      id: "primazi-make-clear",
      title: "Fă clar (PrimaZi)",
      contexts: ["selection"],
    });
  } catch (e) {
    // Context menu might already exist on re-install
  }
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "primazi-make-clear" && tab?.id) {
    chrome.tabs.sendMessage(tab.id, {
      type: "TRIGGER_SELECTION",
      selectedText: info.selectionText || "",
    });
  }
});

// Handle keyboard shortcuts (Alt+Shift+S)
chrome.commands.onCommand.addListener(async (command) => {
  if (command === "make-clear") {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (tab?.id) {
      chrome.tabs.sendMessage(tab.id, { type: "TRIGGER_SELECTION" });
    }
  }
});

async function fetchWithTimeout(url, token, payload, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Ext-Token": token,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timer);
    return res;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

/**
 * Perform backend call with 8s timeout and public server fallback
 */
async function callAdaptBackend(config, payload) {
  const token = config.token || "primazi-demo-2026";
  const primaryBase = (config.backendUrl || DEFAULT_CONFIG.backendUrl).replace(
    /\/+$/,
    "",
  );
  const primaryEndpoint = `${primaryBase}/api/v1/extension/adapt`;

  try {
    const res = await fetchWithTimeout(primaryEndpoint, token, payload, 8000);
    if (!res.ok) {
      let errBody = null;
      try {
        errBody = await res.json();
      } catch (_) {}

      const errCode = errBody?.error?.code || `http_${res.status}`;
      const msgRo =
        errBody?.error?.message_ro || `Eroare server (${res.status}).`;
      const msgEn =
        errBody?.error?.message_en || `Server error (${res.status}).`;

      return {
        ok: false,
        code: errCode,
        message_ro: msgRo,
        message_en: msgEn,
        status: res.status,
      };
    }

    const data = await res.json();
    return { ok: true, data };
  } catch (primaryErr) {
    // If primary failed and is not the fallback public backend, try the public backend
    if (primaryBase !== FALLBACK_PUBLIC_BACKEND) {
      try {
        const fallbackEndpoint = `${FALLBACK_PUBLIC_BACKEND}/api/v1/extension/adapt`;
        const fallbackRes = await fetchWithTimeout(
          fallbackEndpoint,
          token,
          payload,
          8000,
        );
        if (fallbackRes.ok) {
          const data = await fallbackRes.json();
          return { ok: true, data };
        }
      } catch (_) {
        // Fallback also failed, proceed to local fallback below
      }
    }

    const isAbort = primaryErr.name === "AbortError";
    return {
      ok: false,
      code: isAbort ? "timeout" : "network_error",
      message_ro: isAbort
        ? "Conexiunea a expirat. Folosim modul de bază pe dispozitiv."
        : "Serverul nu a răspuns. Folosim modul de bază pe dispozitiv.",
      message_en: isAbort
        ? "Request timed out. Falling back to local mode."
        : "Server unreachable. Falling back to offline local mode.",
      status: 0,
    };
  }
}

// Main message bus
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return false;

  (async () => {
    try {
      if (msg.type === "PREFS_GET") {
        const stored = await chrome.storage.local.get([
          "wp.ext.prefs.v1",
          "wp.ext.config",
        ]);
        const prefs = stored["wp.ext.prefs.v1"] || DEFAULT_PREFS;
        const config = stored["wp.ext.config"] || DEFAULT_CONFIG;
        sendResponse({ type: "PREFS", prefs, config });
        return;
      }

      if (msg.type === "PREFS_SET") {
        const toSave = {
          ...msg.prefs,
          updatedAt: new Date().toISOString(),
        };
        await chrome.storage.local.set({ "wp.ext.prefs.v1": toSave });
        sendResponse({ ok: true, prefs: toSave });
        return;
      }

      if (msg.type === "CONFIG_SET") {
        const current =
          (await chrome.storage.local.get(["wp.ext.config"]))[
            "wp.ext.config"
          ] || DEFAULT_CONFIG;
        const merged = { ...current, ...msg.config };
        await chrome.storage.local.set({ "wp.ext.config": merged });
        sendResponse({ ok: true, config: merged });
        return;
      }

      if (msg.type === "PREFS_FROM_SITE") {
        // Sync from web application site
        const current =
          (await chrome.storage.local.get(["wp.ext.prefs.v1"]))[
            "wp.ext.prefs.v1"
          ] || DEFAULT_PREFS;
        const sitePrefs = msg.prefs;
        const siteTime = new Date(msg.updatedAt || 0).getTime();
        const extTime = new Date(current.updatedAt || 0).getTime();

        // Newest updatedAt wins; keep user overrides if site was older
        if (siteTime >= extTime || current.source !== "extension_manual") {
          const merged = {
            ...current,
            source: "site",
            updatedAt: msg.updatedAt || new Date().toISOString(),
            answers: sitePrefs.answers || current.answers,
            freeText: sitePrefs.freeText || current.freeText || "",
            prefs: {
              ...current.prefs,
              ...(sitePrefs.prefs || {}),
            },
          };
          await chrome.storage.local.set({ "wp.ext.prefs.v1": merged });
          sendResponse({ ok: true, synced: true, prefs: merged });
        } else {
          sendResponse({ ok: true, synced: false, reason: "extension_newer" });
        }
        return;
      }

      if (msg.type === "ADAPT") {
        const stored = await chrome.storage.local.get([
          "wp.ext.config",
          "wp.ext.prefs.v1",
        ]);
        const config = stored["wp.ext.config"] || DEFAULT_CONFIG;
        const userPrefs = stored["wp.ext.prefs.v1"] || DEFAULT_PREFS;

        // Check local-only mode
        if (config.localOnly) {
          sendResponse({
            type: "ERROR",
            requestId: msg.requestId,
            code: "local_only",
            message_ro: "Mod offline activat de utilizator.",
            message_en: "User-enabled local only mode.",
            fallback: "local",
          });
          return;
        }

        // Build backend payload conforming to EXTENSION.md §5
        const payload = {
          text: msg.text || "",
          language: msg.language || "auto",
          action: msg.action || "simplify",
          style: {
            reading_level: Number(userPrefs.prefs?.reading_level) || 2,
            steps: msg.action === "steps" || !!userPrefs.prefs?.steps,
            glossary: userPrefs.prefs?.glossary !== false,
            literal_language: userPrefs.prefs?.literal_language !== false,
            length: userPrefs.prefs?.length || "medium",
            bullets: msg.action === "bullets",
          },
          preference_text: (userPrefs.freeText || "").trim().slice(0, 500),
          client: { name: "extension", version: "0.1.0" },
        };

        const result = await callAdaptBackend(config, payload);
        if (result.ok) {
          sendResponse({
            type: "RESULT",
            requestId: msg.requestId,
            data: result.data,
          });
        } else {
          sendResponse({
            type: "ERROR",
            requestId: msg.requestId,
            code: result.code,
            message_ro: result.message_ro,
            message_en: result.message_en,
            fallback: "local",
          });
        }
        return;
      }

      sendResponse({ error: "Unknown message type" });
    } catch (e) {
      sendResponse({
        type: "ERROR",
        requestId: msg.requestId,
        code: "internal_error",
        message_ro: "Eroare internă în extensie.",
        message_en: "Internal extension error.",
        fallback: "local",
      });
    }
  })();

  return true; // Keeps sendResponse channel open for async execution
});
