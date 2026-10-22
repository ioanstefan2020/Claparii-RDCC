/**
 * actions.js - Result Action Bar and Content Transformation Engine
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 *
 * Implements Task F3 per docs/TASKS-WAVE2.md:
 * - Result Action Bar (Ascultă, Mai scurt, Puncte, Pe pași, Explică simplu, Adaugă în plan, Salvează)
 * - Integration with POST /api/transform (modes: shorter, bullets, steps, easy_read)
 * - Client-side deterministic fallback when offline or before backend router is active
 * - Transfer of action items into the Planner
 */

import { escapeHtml } from "/js/home.js";

/**
 * Calls POST /api/transform with graceful offline fallback.
 * @param {string} text - Source text to transform
 * @param {string} mode - "shorter" | "bullets" | "steps" | "easy_read"
 * @param {object} profile - Optional user profile
 * @returns {Promise<{ok: boolean, data: {mode: string, items: string[]|null, text: string|null}, meta?: object}>}
 */
export async function transformText(text, mode, profile = {}) {
  if (!text || !text.trim()) {
    return {
      ok: false,
      error: { code: "empty_text", message_ro: "Nu există text de transformat." }
    };
  }

  try {
    const res = await fetch("/api/transform", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        mode,
        max_items: 6,
        target_pct: 40,
        profile
      })
    });

    if (res.ok) {
      const json = await res.json();
      if (json && json.ok && json.data) {
        return json;
      }
    }
  } catch (err) {
    // Fall back to client-side deterministic transform
  }

  // Client-side fallback transformation
  return fallbackTransform(text, mode);
}

/**
 * Intelligent deterministic fallback transformation in plain Romanian.
 */
function fallbackTransform(text, mode) {
  // Split into clean non-empty sentences
  const rawSentences = text
    .split(/(?<=[.!?])\s+/)
    .map(s => s.trim())
    .filter(s => s.length > 5);

  if (mode === "bullets") {
    const items = rawSentences.slice(0, 5).map(s => {
      // Clean sentence for bullet point presentation
      return s.replace(/^[-•*]\s*/, "");
    });
    return {
      ok: true,
      data: {
        mode: "bullets",
        items: items.length > 0 ? items : [text.substring(0, 120)],
        text: null
      },
      meta: { provider: "client_fallback" }
    };
  }

  if (mode === "shorter") {
    // Pick the most information-dense sentences (containing numbers, dates or actions)
    const prioritized = rawSentences.filter(s => /\d+|luni|marți|miercuri|joi|vineri|termen|ora|urgent|formular/i.test(s));
    const selection = prioritized.length > 0 ? prioritized.slice(0, 2) : rawSentences.slice(0, 2);
    const shortText = selection.join(" ") || text.substring(0, 150);
    return {
      ok: true,
      data: {
        mode: "shorter",
        items: null,
        text: shortText
      },
      meta: { provider: "client_fallback" }
    };
  }

  if (mode === "steps") {
    const items = rawSentences.slice(0, 5).map((s, idx) => {
      let clean = s.replace(/^\d+[\.\)]\s*/, "").trim();
      return clean;
    });
    return {
      ok: true,
      data: {
        mode: "steps",
        items: items.length > 0 ? items : [text],
        text: null
      },
      meta: { provider: "client_fallback" }
    };
  }

  if (mode === "easy_read") {
    // Simplify sentence structure
    const simplified = rawSentences.slice(0, 4).map(s => {
      return s.replace(/în vederea|cu scopul de a|este necesar să/gi, "trebuie să");
    }).join(" ");
    return {
      ok: true,
      data: {
        mode: "easy_read",
        items: null,
        text: simplified || text
      },
      meta: { provider: "client_fallback" }
    };
  }

  return {
    ok: true,
    data: { mode, items: null, text: text.substring(0, 200) },
    meta: { provider: "client_fallback" }
  };
}

/**
 * Stores tasks from current analysis in localStorage and navigates to the planner.
 * @param {Array<{text: string, deadline?: string, source_quote?: string}>} tasks
 */
export function sendTasksToPlanner(tasks) {
  if (!Array.isArray(tasks) || tasks.length === 0) return false;

  try {
    const existing = JSON.parse(localStorage.getItem("wp.planner.tasks") || "[]");
    const newItems = tasks.map((t, i) => ({
      id: `task_${Date.now()}_${i}`,
      title: t.text || t.title || "Sarcină extrasă",
      deadline: t.deadline || null,
      source_quote: t.source_quote || null,
      completed: false,
      created_at: new Date().toISOString()
    }));

    const combined = [...newItems, ...existing].slice(0, 30);
    localStorage.setItem("wp.planner.tasks", JSON.stringify(combined));
    return true;
  } catch (err) {
    console.error("Nu s-au putut salva sarcinile în planificator:", err);
    return false;
  }
}

