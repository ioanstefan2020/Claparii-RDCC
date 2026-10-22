/**
 * PrimaZi — Focus & Layout Modes Engine (Wave 2)
 * Manages overview, guided, and card layouts, with focus levels 0–3.
 * Ref: docs/TASKS-WAVE2.md A7, docs/SETTINGS-SPEC.md §2, §3
 */

import { getSetting } from "./settings.js";

let currentItems = [];
let currentStepIndex = 0;
let hostContainer = null;
let currentOptions = {};

function announce(msg) {
  const live = document.getElementById("status-live");
  if (live) {
    live.textContent = "";
    setTimeout(() => { live.textContent = msg; }, 50);
  }
}

/**
 * Mounts result items into the target container according to layout and focus settings.
 * @param {HTMLElement} container
 * @param {Array} items
 * @param {object} [options]
 */
export function mountResults(container, items = [], options = {}) {
  if (!container) return;
  hostContainer = container;
  currentItems = items || [];
  currentStepIndex = options.initialStep || 0;
  currentOptions = options;

  renderActiveLayout();
}

export function nextStep() {
  if (currentStepIndex + 1 < currentItems.length) {
    currentStepIndex++;
    renderActiveLayout();
    if (typeof currentOptions.onStepChange === "function") {
      currentOptions.onStepChange(currentStepIndex, currentItems[currentStepIndex]);
    }
  }
}

export function prevStep() {
  if (currentStepIndex > 0) {
    currentStepIndex--;
    renderActiveLayout();
    if (typeof currentOptions.onStepChange === "function") {
      currentOptions.onStepChange(currentStepIndex, currentItems[currentStepIndex]);
    }
  }
}

export function goToStep(idx) {
  if (idx >= 0 && idx < currentItems.length) {
    currentStepIndex = idx;
    renderActiveLayout();
    if (typeof currentOptions.onStepChange === "function") {
      currentOptions.onStepChange(currentStepIndex, currentItems[currentStepIndex]);
    }
  }
}

function renderActiveLayout() {
  if (!hostContainer) return;
  hostContainer.textContent = "";

  const layout = currentOptions.layout || getSetting("layout") || "overview";
  const focusLevel = typeof currentOptions.focus === "number" ? currentOptions.focus : (getSetting("focus_level") || 0);

  if (currentItems.length === 0) {
    const empty = document.createElement("p");
    empty.className = "a11y-empty-notice";
    empty.textContent = "Nu există elemente de afișat.";
    hostContainer.appendChild(empty);
    return;
  }

  if (layout === "guided" || focusLevel === 2) {
    renderGuidedLayout();
  } else if (layout === "card" || focusLevel === 3) {
    renderCardLayout();
  } else {
    renderOverviewLayout();
  }
}

function renderOverviewLayout() {
  const wrap = document.createElement("div");
  wrap.className = "a11y-overview-layout";

  currentItems.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className = "a11y-result-card card";
    card.setAttribute("tabindex", "0");

    const header = document.createElement("div");
    header.className = "card-header";
    header.innerHTML = `<strong>Pasul ${idx + 1}</strong>`;

    const body = document.createElement("div");
    body.className = "card-body";
    body.textContent = typeof item === "string" ? item : (item.text || item.title || JSON.stringify(item));

    card.appendChild(header);
    card.appendChild(body);
    wrap.appendChild(card);
  });

  hostContainer.appendChild(wrap);
}

function renderGuidedLayout() {
  const wrap = document.createElement("div");
  wrap.className = "a11y-guided-layout";

  const total = currentItems.length;
  const current = currentItems[currentStepIndex];

  // Progress Bar & Counter
  const progressHeader = document.createElement("div");
  progressHeader.className = "a11y-progress-header";
  progressHeader.innerHTML = `
    <span class="a11y-step-counter">Pasul ${currentStepIndex + 1} din ${total}</span>
    <progress class="a11y-progress-bar" value="${currentStepIndex + 1}" max="${total}" aria-label="Progres sarcini"></progress>
  `;

  // Focused Card
  const card = document.createElement("div");
  card.className = "a11y-result-card card a11y-focused-step";
  card.setAttribute("tabindex", "0");
  card.setAttribute("role", "region");
  card.setAttribute("aria-label", `Pasul ${currentStepIndex + 1} din ${total}`);

  const body = document.createElement("div");
  body.className = "card-body";
  body.textContent = typeof current === "string" ? current : (current.text || current.title || "");
  card.appendChild(body);

  // Nav Controls
  const navRow = document.createElement("div");
  navRow.className = "a11y-nav-row";

  const btnPrev = document.createElement("button");
  btnPrev.type = "button";
  btnPrev.className = "btn btn-secondary";
  btnPrev.textContent = "← Înapoi";
  btnPrev.disabled = currentStepIndex === 0;
  btnPrev.onclick = prevStep;

  const btnNext = document.createElement("button");
  btnNext.type = "button";
  btnNext.className = "btn btn-primary";
  btnNext.textContent = currentStepIndex + 1 < total ? "Următorul pas →" : "Finalizează ✓";
  btnNext.onclick = nextStep;

  navRow.appendChild(btnPrev);
  navRow.appendChild(btnNext);

  wrap.appendChild(progressHeader);
  wrap.appendChild(card);
  wrap.appendChild(navRow);

  hostContainer.appendChild(wrap);
  announce(`Pasul ${currentStepIndex + 1} din ${total}`);
}

function renderCardLayout() {
  const wrap = document.createElement("div");
  wrap.className = "a11y-card-fullscreen-layout";

  const total = currentItems.length;
  const current = currentItems[currentStepIndex];

  const card = document.createElement("div");
  card.className = "a11y-max-card card";
  card.setAttribute("tabindex", "0");
  card.setAttribute("role", "region");

  const stepBadge = document.createElement("span");
  stepBadge.className = "a11y-max-badge";
  stepBadge.textContent = `${currentStepIndex + 1} / ${total}`;

  const textEl = document.createElement("p");
  textEl.className = "a11y-max-text";
  textEl.textContent = typeof current === "string" ? current : (current.text || current.title || "");

  card.appendChild(stepBadge);
  card.appendChild(textEl);

  const controls = document.createElement("div");
  controls.className = "a11y-max-controls";

  const btnPrev = document.createElement("button");
  btnPrev.type = "button";
  btnPrev.className = "btn btn-secondary btn-large";
  btnPrev.textContent = "Pasul anterior";
  btnPrev.disabled = currentStepIndex === 0;
  btnPrev.onclick = prevStep;

  const btnNext = document.createElement("button");
  btnNext.type = "button";
  btnNext.className = "btn btn-primary btn-large";
  btnNext.textContent = currentStepIndex + 1 < total ? "Următorul pas" : "Gata";
  btnNext.onclick = nextStep;

  controls.appendChild(btnPrev);
  controls.appendChild(btnNext);

  wrap.appendChild(card);
  wrap.appendChild(controls);

  hostContainer.appendChild(wrap);
  announce(`Pasul ${currentStepIndex + 1} din ${total}`);
}
