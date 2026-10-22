/**
 * adjustments.js - Workplace Adjustments Screen Module (F5)
 * Owner: p2
 * Conforms to docs/CONTRACTS.md §3.4, §3.5 and WCAG 2.2 AA
 *
 * Rules:
 * - NO diagnosis or medical condition fields anywhere (Responsible AI rule)
 * - Curated functional needs catalog sourced from P3 /api/adjustments/catalog
 * - Draft generation via POST /api/adjustments/draft with fallback fixtures
 * - Copy, Mailto, and .txt download actions
 * - Non-legal disclaimer clearly visible
 * - Zero window.alert() calls; uses status-live aria-live regions & error banners
 */

import { getAdjustmentsCatalog, draftAdjustments } from "../shared/api.js";
import { getA11yPrefs, applyA11yPrefs } from "../shared/profile.js";

/**
 * Safely escapes HTML special characters to prevent XSS.
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Triggers a browser download of a plain text file.
 */
export function downloadDraftFile(filename = "solicitare-adaptari.txt", content = "") {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  const cleanFilename = filename.endsWith(".txt") ? filename : `${filename}.txt`;
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.setAttribute("download", cleanFilename);
  link.setAttribute("aria-hidden", "true");
  link.style.display = "none";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Translates applies_to tags into accessible Romanian labels.
 */
function formatAppliesTo(tags = []) {
  const map = {
    cognitive: "Cognitiv / Ritm de lucru",
    hearing: "Auz / Comunicare",
    visual: "Vedere / Tehnologii asistive",
    motor: "Motor / Ergonomie",
    any: "Universal / Toți angajații"
  };
  return tags.map(t => map[t] || t).join(", ");
}

/**
 * Renders the adjustments catalog items into the container.
 *
 * @param {Array<object>} items - List of catalog items from /api/adjustments/catalog
 * @param {HTMLElement|object} container - Container element for items
 */
export function renderCatalogItems(items = [], container) {
  if (!container) return;

  if (!items || items.length === 0) {
    container.innerHTML = `<p class="meta-secondary" style="color: var(--text-muted);">Nu a fost găsită nicio adaptare în catalog.</p>`;
    return;
  }

  container.innerHTML = items
    .map(item => {
      const idEscaped = escapeHtml(item.id);
      const titleEscaped = escapeHtml(item.title);
      const descEscaped = escapeHtml(item.description);
      const exampleEscaped = escapeHtml(item.example_request || "");
      const tagsText = formatAppliesTo(item.applies_to || []);

      return `
        <label class="catalog-card" for="chk-adj-${idEscaped}">
          <input type="checkbox" id="chk-adj-${idEscaped}" name="need_ids" value="${idEscaped}" aria-describedby="desc-adj-${idEscaped}">
          <div style="flex: 1;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 1.05rem;">
              ${titleEscaped}
            </div>
            <p id="desc-adj-${idEscaped}" style="margin: 0.35rem 0; font-size: 0.9rem; color: var(--text-muted); line-height: 1.45;">
              ${descEscaped}
            </p>
            ${
              exampleEscaped
                ? `<div class="meta-secondary" style="font-size: 0.82rem; font-style: italic; color: var(--text-muted); margin-top: 0.25rem;">
                     „${exampleEscaped}”
                   </div>`
                : ""
            }
            ${
              tagsText
                ? `<span class="tag-badge">${escapeHtml(tagsText)}</span>`
                : ""
            }
          </div>
        </label>
      `;
    })
    .join("");
}

/**
 * Renders the generated draft results into the UI containers.
 *
 * @param {object} data - Draft data ({ subject, body_ro, checklist })
 * @param {HTMLElement|object} container - Results container element
 */
export function renderDraftResult(data, container) {
  if (!container || !data) return;

  const subject = data.subject || "Solicitare de adaptări rezonabile";
  const bodyRo = data.body_ro || "";
  const checklist = Array.isArray(data.checklist) ? data.checklist : [];

  const subjectEl = container.querySelector ? container.querySelector("#draft-subject") : null;
  const bodyEl = container.querySelector ? container.querySelector("#draft-body") : null;
  const checklistEl = container.querySelector ? container.querySelector("#checklist-list") : null;
  const mailtoBtn = container.querySelector ? container.querySelector("#btn-mailto") : null;

  if (subjectEl) subjectEl.textContent = subject;
  if (bodyEl) bodyEl.value = bodyRo;

  if (mailtoBtn) {
    mailtoBtn.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(bodyRo)}`;
  }

  if (checklistEl) {
    if (checklist.length === 0) {
      checklistEl.innerHTML = `<p class="meta-secondary" style="color: var(--text-muted);">Fără măsuri adiționale în listă.</p>`;
    } else {
      checklistEl.innerHTML = checklist
        .map(
          item => `
          <div class="checklist-item">
            <strong style="color: var(--text-main); font-size: 1rem; display: block; margin-bottom: 0.25rem;">
              ✓ ${escapeHtml(item.title)}
            </strong>
            <span style="font-size: 0.92rem; color: var(--text-muted); line-height: 1.45;">
              ${escapeHtml(item.why || "")}
            </span>
          </div>`
        )
        .join("");
    }
  }

  // Fallback for simple mock containers in unit tests
  if (!container.querySelector) {
    container.innerHTML = `
      <div class="subject">${escapeHtml(subject)}</div>
      <div class="body">${escapeHtml(bodyRo)}</div>
      <div class="checklist-count">${checklist.length}</div>
    `;
  }
}

/**
 * Initializes the Adjustments Page interactive logic.
 */
export function initAdjustmentsPage() {
  if (typeof document === "undefined") return;

  // Apply user visual accessibility preferences
  applyA11yPrefs(getA11yPrefs());

  // DOM Elements
  const form = document.getElementById("adjustments-form");
  const catalogContainer = document.getElementById("catalog-container");
  const contextSelect = document.getElementById("context-select");
  const toneSelect = document.getElementById("tone-select");
  const employerInput = document.getElementById("employer-name");
  const btnSubmit = document.getElementById("btn-submit");
  const liveRegion = document.getElementById("status-live");
  const errorBanner = document.getElementById("error-banner");
  const disclaimerBanner = document.getElementById("disclaimer-banner");
  const draftSection = document.getElementById("draft-section");
  const draftSubject = document.getElementById("draft-subject");
  const draftBody = document.getElementById("draft-body");
  const btnCopy = document.getElementById("btn-copy");
  const btnMailto = document.getElementById("btn-mailto");
  const btnDownload = document.getElementById("btn-download");
  const aiNotice = document.getElementById("ai-notice");

  let catalogItems = [];

  function announce(message) {
    if (liveRegion) {
      liveRegion.textContent = "";
      setTimeout(() => {
        liveRegion.textContent = message;
      }, 50);
    }
  }

  function showError(message) {
    if (errorBanner) {
      errorBanner.textContent = message;
      errorBanner.style.display = "block";
      errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    announce(`Eroare: ${message}`);
  }

  function clearError() {
    if (errorBanner) {
      errorBanner.textContent = "";
      errorBanner.style.display = "none";
    }
  }

  // 1. Fetch & Render Catalog
  async function loadCatalog() {
    clearError();
    try {
      const res = await getAdjustmentsCatalog();
      if (res.ok && res.data) {
        catalogItems = res.data.items || [];
        if (disclaimerBanner && res.data.disclaimer_ro) {
          disclaimerBanner.textContent = res.data.disclaimer_ro;
        }
        renderCatalogItems(catalogItems, catalogContainer);
        announce(`Catalogul de adaptări a fost încărcat. Sunt disponibile ${catalogItems.length} opțiuni.`);
      } else {
        const msg = (res.error && res.error.message_ro) || "Nu s-a putut încărca catalogul de adaptări.";
        showError(msg);
      }
    } catch (err) {
      showError("A apărut o eroare neașteptată la încărcarea catalogului.");
    }
  }

  loadCatalog();

  // 2. Handle Form Submission
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearError();

      const checkedInputs = form.querySelectorAll("input[name='need_ids']:checked");
      const selectedIds = Array.from(checkedInputs).map(chk => chk.value);

      if (selectedIds.length === 0) {
        showError("Te rugăm să bifezi cel puțin o adaptare din catalog.");
        const firstChk = form.querySelector("input[name='need_ids']");
        if (firstChk) firstChk.focus();
        return;
      }

      const context = contextSelect ? contextSelect.value : "onboarding";
      const tone = toneSelect ? toneSelect.value : "friendly";
      const employerName = employerInput && employerInput.value.trim() ? employerInput.value.trim() : null;

      // Set Loading State
      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Se redactează solicitarea...";
      }
      announce("Se generează solicitarea de adaptare, vă rugăm așteptați...");

      try {
        const res = await draftAdjustments(selectedIds, context, employerName, tone);

        if (!res.ok) {
          const msg = (res.error && res.error.message_ro) || "Nu s-a putut redacta solicitarea. Vă rugăm încercați din nou.";
          showError(msg);
          return;
        }

        const data = res.data;
        const meta = res.meta || {};

        if (aiNotice) {
          aiNotice.textContent = meta.ai_notice_ro || "Generat de AI — verifică datele importante.";
          aiNotice.style.display = "block";
        }

        if (draftSection) {
          renderDraftResult(data, draftSection);
          draftSection.style.display = "block";
          draftSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        announce("Solicitarea ta de adaptări a fost redactată cu succes.");
      } catch (err) {
        showError("A apărut o problemă la comunicarea cu serverul.");
      } finally {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Generează solicitarea către HR / Manager";
        }
      }
    });
  }

  // 3. Copy Action
  if (btnCopy && draftBody) {
    btnCopy.addEventListener("click", async () => {
      const textToCopy = draftBody.value;
      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
        btnCopy.textContent = "✓ Text copiat!";
        setTimeout(() => {
          btnCopy.textContent = "Copiază în clipboard";
        }, 2500);
        announce("Textul solicitării a fost copiat în clipboard.");
      } catch {
        // Fallback: select text in textarea
        draftBody.select();
        announce("Textul a fost selectat. Apăsați Ctrl+C pentru copiere.");
      }
    });
  }

  // 4. Download Action
  if (btnDownload && draftBody && draftSubject) {
    btnDownload.addEventListener("click", () => {
      const subject = draftSubject.textContent || "Solicitare adaptari";
      const body = draftBody.value || "";
      const fullDocument = `SUBIECT: ${subject}\n\n${body}\n\n---\nGenerat cu asistentul PrimaZi (Informativ, nu reprezintă consultanță juridică).`;
      downloadDraftFile("solicitare-adaptari-primazi.txt", fullDocument);
      announce("Documentul a fost descărcat pe dispozitivul tău.");
    });
  }
}

