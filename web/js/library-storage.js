/**
 * library-storage.js - Browser-Only Local Persistence for Saved Documents
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 * Spec: docs/plan/p3.md (Task N3.5)
 *
 * Rules:
 * - 100% client-side persistence in localStorage under key 'wp.library.v1'
 * - Resilient against private browsing and quota exceeded (in-memory fallback)
 * - Never transmits saved items to server (responsible-AI privacy)
 * - Safe against malformed or corrupted JSON
 */

export const LIBRARY_STORAGE_KEY = "wp.library.v1";
const MAX_STORED_SOURCE_CHARS = 12000;

let memoryFallbackLibrary = null;
let usingLibraryMemoryFallback = false;

/**
 * Safe probe to verify if localStorage is operational.
 * @returns {boolean}
 */
function isLocalStorageWorking() {
  try {
    if (typeof globalThis.localStorage === "undefined" || globalThis.localStorage === null) {
      return false;
    }
    const testKey = "__wp_lib_probe__";
    globalThis.localStorage.setItem(testKey, "1");
    globalThis.localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

/**
 * Returns true if storage is currently using the in-memory fallback.
 * @returns {boolean}
 */
export function isLibraryMemoryFallback() {
  return usingLibraryMemoryFallback;
}

/**
 * Returns all saved library items, sorted descending by createdAt.
 * Resilient against missing, empty or malformed storage.
 * @returns {Array<object>}
 */
export function getLibraryItems() {
  if (usingLibraryMemoryFallback && memoryFallbackLibrary !== null) {
    return [...memoryFallbackLibrary];
  }

  if (isLocalStorageWorking()) {
    try {
      const raw = globalThis.localStorage.getItem(LIBRARY_STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      // Sanitize and filter out invalid items
      const validItems = parsed.filter(item => Boolean(item && typeof item === "object" && item.id && item.title));
      validItems.sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime());
      return validItems;
    } catch {
      usingLibraryMemoryFallback = true;
      memoryFallbackLibrary = [];
      return [];
    }
  }

  usingLibraryMemoryFallback = true;
  if (memoryFallbackLibrary === null) {
    memoryFallbackLibrary = [];
  }
  return [...memoryFallbackLibrary];
}

/**
 * Internal helper to persist the array of items to localStorage or memory.
 * @param {Array<object>} items
 * @returns {boolean}
 */
function persistItems(items) {
  if (!usingLibraryMemoryFallback && isLocalStorageWorking()) {
    try {
      const serialized = JSON.stringify(items);
      globalThis.localStorage.setItem(LIBRARY_STORAGE_KEY, serialized);
      return true;
    } catch {
      usingLibraryMemoryFallback = true;
      memoryFallbackLibrary = [...items];
      return true;
    }
  }

  usingLibraryMemoryFallback = true;
  memoryFallbackLibrary = [...items];
  return true;
}

/**
 * Saves a new item or updates an existing item by id.
 * @param {object} item
 * @returns {object} The saved item
 */
export function saveLibraryItem(item = {}) {
  const safeItem = {
    id: item.id || `lib_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    mode: item.mode || "simplify",
    title: (item.title || "Document fără titlu").trim().slice(0, 100),
    createdAt: item.createdAt || new Date().toISOString(),
    sourceText: (item.sourceText || "").slice(0, MAX_STORED_SOURCE_CHARS),
    resultData: item.resultData && typeof item.resultData === "object" ? item.resultData : {},
    tags: Array.isArray(item.tags) && item.tags.length > 0 ? item.tags : [item.mode || "document"]
  };

  const items = getLibraryItems();
  const existingIdx = items.findIndex(it => it.id === safeItem.id);

  if (existingIdx !== -1) {
    items[existingIdx] = safeItem;
  } else {
    items.unshift(safeItem);
  }

  items.sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime());
  persistItems(items);
  return safeItem;
}

/**
 * Deletes an item by id.
 * @param {string} id
 * @returns {object|null} The deleted item, or null if not found.
 */
export function deleteLibraryItem(id) {
  if (!id) return null;
  const items = getLibraryItems();
  const idx = items.findIndex(it => it.id === id);
  if (idx === -1) return null;

  const [deleted] = items.splice(idx, 1);
  persistItems(items);
  return deleted;
}

/**
 * Restores a deleted item back into storage (used by Undo).
 * @param {object} item
 */
export function restoreLibraryItem(item) {
  if (!item || !item.id) return;
  const items = getLibraryItems();
  if (items.some(it => it.id === item.id)) return;

  items.unshift(item);
  items.sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime());
  persistItems(items);
}

/**
 * Clears all library items permanently.
 */
export function clearLibrary() {
  if (!usingLibraryMemoryFallback && isLocalStorageWorking()) {
    try {
      globalThis.localStorage.removeItem(LIBRARY_STORAGE_KEY);
    } catch {
      // ignore
    }
  }
  memoryFallbackLibrary = [];
}

