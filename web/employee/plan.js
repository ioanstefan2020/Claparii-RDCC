/**
 * plan.js - Tasks & Deadlines Planner Screen Module (F3)
 * Owner: p2
 * Conforms to docs/CONTRACTS.md §2 and WCAG 2.2 AA accessibility standards.
 */

import { extractPlan } from "../shared/api.js";
import { generateIcs, downloadIcsFile } from "../shared/ics.js";
import { getApiProfile } from "../shared/profile.js";

export const STORAGE_KEY = "primazi_planner_tasks";

export const SAMPLE_TASK_EMAIL = `Subiect: Raport lunar clienți – urgent

Salut,

Te rog să preiei raportul lunar pentru clienții din zona Muntenia. Din ce am văzut, ar trebui să iei datele din CRM, să le curățăm puțin (fără dubluri) și să le pui în șablonul de la Finanțe. Am nevoie de el cât mai repede, să zicem până joi la prânz, ca să îl pot trimite mai departe. Dacă nu reușești, dă-mi un semn din timp.

Mulțumesc!
Andrei`;

/**
 * Loads tasks from localStorage.
 */
export function loadStoredTasks() {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter(t => t && typeof t === "object") : [];
  } catch {
    return [];
  }
}

/**
 * Saves tasks list to localStorage.
 */
export function saveStoredTasks(tasks) {
  if (typeof localStorage === "undefined") return tasks;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  return tasks;
}

/**
 * Clears stored tasks from localStorage.
 */
export function clearStoredTasks() {
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

/**
 * Pure mutation: Adds a new task.
 */
export function addTask(tasks = [], taskData = {}) {
  const newTask = {
    id: taskData.id || `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: (taskData.title || "").trim() || "Sarcină nouă",
    due_iso: taskData.due_iso || null,
    due_text: taskData.due_text || null,
    needs_confirmation: Boolean(taskData.needs_confirmation),
    priority: ["high", "normal", "low"].includes(taskData.priority) ? taskData.priority : "normal",
    steps: Array.isArray(taskData.steps) ? [...taskData.steps] : [],
    source_quote: taskData.source_quote || null,
    completed: Boolean(taskData.completed)
  };
  return [...tasks, newTask];
}

/**
 * Pure mutation: Updates an existing task.
 */
export function updateTask(tasks = [], id, updates = {}) {
  return tasks.map(t => (t.id === id ? { ...t, ...updates } : t));
}

/**
 * Pure mutation: Deletes a task by id.
 */
export function deleteTask(tasks = [], id) {
  return tasks.filter(t => t.id !== id);
}

/**
 * Pure mutation: Toggles completed status.
 */
export function toggleTaskCompletion(tasks = [], id) {
  return tasks.map(t => (t.id === id ? { ...t, completed: !t.completed } : t));
}

/**
 * Pure mutation: Confirms an ambiguous deadline with an explicit ISO date.
 */
export function confirmTaskDate(tasks = [], id, dateIso) {
  return tasks.map(t => {
    if (t.id === id) {
      return {
        ...t,
        due_iso: dateIso || null,
        needs_confirmation: false
      };
    }
    return t;
  });
}

/**
 * Safely escapes HTML special characters to prevent XSS.
 */
export function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Formats ISO date YYYY-MM-DD into accessible Romanian localized format.
 */
export function formatDateRo(isoStr) {
  if (!isoStr || typeof isoStr !== "string") return "";
  const parts = isoStr.trim().split("-");
  if (parts.length !== 3) return isoStr;

  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);

  const dateObj = new Date(year, month, day);
  if (isNaN(dateObj.getTime())) return isoStr;

  const daysRo = ["duminică", "luni", "marți", "miercuri", "joi", "vineri", "sâmbătă"];
  const monthsRo = [
    "ianuarie", "februarie", "martie", "aprilie", "mai", "iunie",
    "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"
  ];

  const dayName = daysRo[dateObj.getDay()];
  const monthName = monthsRo[dateObj.getMonth()];

  return `${isoStr} (${dayName}, ${day} ${monthName})`;
}

/**
 * Priority styling helper.
 */
function getPriorityMeta(priority) {
  switch (priority) {
    case "high":
      return {
        label: "Prioritate ridicată",
        badgeStyle: "background-color: var(--error-bg); color: var(--error-text); border-color: var(--error-border);"
      };
    case "low":
      return {
        label: "Prioritate scăzută",
        badgeStyle: "background-color: var(--bg-surface-alt); color: var(--text-muted); border-color: var(--border-color);"
      };
    case "normal":
    default:
      return {
        label: "Prioritate normală",
        badgeStyle: "background-color: var(--bg-surface-alt); color: var(--primary); border-color: var(--primary);"
      };
  }
}

/**
 * Renders the task items into the container.
 */
export function renderTasks(tasks, container, callbacks = {}) {
  if (!container) return;
  container.innerHTML = "";

  if (!tasks || tasks.length === 0) {
    const empty = document.createElement("div");
    empty.className = "card";
    empty.style.textAlign = "center";
    empty.style.padding = "2.5rem 1.5rem";
    empty.style.color = "var(--text-muted)";
    empty.innerHTML = `
      <p style="font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--text-main);">
        Nu ai nicio sarcină în planificator.
      </p>
      <p class="meta-secondary" style="margin: 0; font-size: 0.95rem;">
        Lipește un e-mail sau text de instrucțiuni mai sus și apasă pe „Extrage sarcini și termene”, sau adaugă una manual prin butonul de mai sus.
      </p>
    `;
    container.appendChild(empty);
    return;
  }

  tasks.forEach((task, idx) => {
    const article = document.createElement("article");
    article.className = "card";
    article.style.marginBottom = "1rem";
    article.style.padding = "1.25rem";
    article.setAttribute("data-task-id", task.id);

    const prio = getPriorityMeta(task.priority);
    const titleEscaped = escapeHtml(task.title);

    // Header with checkbox, title, badge, delete button
    const headerDiv = document.createElement("div");
    headerDiv.style.display = "flex";
    headerDiv.style.alignItems = "flex-start";
    headerDiv.style.gap = "0.75rem";
    headerDiv.style.flexWrap = "wrap";
    headerDiv.style.marginBottom = "0.75rem";

    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.id = `task-chk-${task.id}`;
    chk.checked = Boolean(task.completed);
    chk.setAttribute("aria-label", `Marchează ca ${task.completed ? "nefinalizat" : "finalizat"}: ${task.title}`);
    chk.style.width = "22px";
    chk.style.height = "22px";
    chk.style.cursor = "pointer";
    chk.style.marginTop = "0.2rem";

    chk.addEventListener("change", () => {
      if (callbacks.onToggle) callbacks.onToggle(task.id);
    });

    const titleLabel = document.createElement("label");
    titleLabel.htmlFor = `task-chk-${task.id}`;
    titleLabel.style.flex = "1";
    titleLabel.style.fontSize = "1.15rem";
    titleLabel.style.fontWeight = "700";
    titleLabel.style.margin = "0";
    titleLabel.style.cursor = "pointer";
    if (task.completed) {
      titleLabel.style.textDecoration = "line-through";
      titleLabel.style.opacity = "0.7";
    }
    titleLabel.textContent = task.title;

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.setAttribute("style", prio.badgeStyle);
    badge.textContent = prio.label;

    const btnDelete = document.createElement("button");
    btnDelete.type = "button";
    btnDelete.className = "btn btn-secondary";
    btnDelete.setAttribute("aria-label", `Șterge sarcina: ${task.title}`);
    btnDelete.style.padding = "0.35rem 0.75rem";
    btnDelete.style.minHeight = "36px";
    btnDelete.style.fontSize = "0.85rem";
    btnDelete.textContent = "Șterge";
    btnDelete.addEventListener("click", () => {
      if (callbacks.onDelete) callbacks.onDelete(task.id);
    });

    headerDiv.appendChild(chk);
    headerDiv.appendChild(titleLabel);
    headerDiv.appendChild(badge);
    headerDiv.appendChild(btnDelete);
    article.appendChild(headerDiv);

    // Due date display / ambiguous deadline warning
    if (task.needs_confirmation) {
      const warnBox = document.createElement("div");
      warnBox.className = "status-message status-warning";
      warnBox.style.margin = "0.75rem 0";
      warnBox.style.padding = "0.85rem 1rem";
      warnBox.style.fontSize = "0.95rem";

      const warnTitle = document.createElement("div");
      warnTitle.style.fontWeight = "700";
      warnTitle.style.marginBottom = "0.35rem";
      warnTitle.textContent = `⚠️ Termen neconfirmat / ambiguu: "${task.due_text || 'Fără dată exactă'}"`;
      warnBox.appendChild(warnTitle);

      const warnDesc = document.createElement("p");
      warnDesc.className = "meta-secondary";
      warnDesc.style.fontSize = "0.88rem";
      warnDesc.style.marginBottom = "0.6rem";
      warnDesc.style.color = "var(--text-muted)";
      warnDesc.textContent = "Asistentul AI nu ghicește date calendaristice. Te rugăm să stabilești o dată clară agreată:";
      warnBox.appendChild(warnDesc);

      const formRow = document.createElement("div");
      formRow.style.display = "flex";
      formRow.style.gap = "0.5rem";
      formRow.style.alignItems = "center";
      formRow.style.flexWrap = "wrap";

      const lbl = document.createElement("label");
      lbl.htmlFor = `confirm-date-${task.id}`;
      lbl.style.fontWeight = "600";
      lbl.style.margin = "0";
      lbl.style.fontSize = "0.9rem";
      lbl.textContent = "Confirmă data:";
      formRow.appendChild(lbl);

      const dateInput = document.createElement("input");
      dateInput.type = "date";
      dateInput.id = `confirm-date-${task.id}`;
      dateInput.style.width = "auto";
      dateInput.style.minHeight = "38px";
      dateInput.style.padding = "0.3rem 0.5rem";
      dateInput.setAttribute("aria-label", `Alege data confirmată pentru ${task.title}`);
      formRow.appendChild(dateInput);

      const btnConfirm = document.createElement("button");
      btnConfirm.type = "button";
      btnConfirm.className = "btn";
      btnConfirm.style.minHeight = "38px";
      btnConfirm.style.padding = "0.35rem 0.85rem";
      btnConfirm.style.fontSize = "0.9rem";
      btnConfirm.textContent = "Salvează data";
      btnConfirm.addEventListener("click", () => {
        const val = dateInput.value;
        if (!val) {
          if (callbacks.onError) {
            callbacks.onError("Te rugăm să selectezi o dată validă înainte de salvare.");
          }
          dateInput.focus();
          return;
        }
        if (callbacks.onConfirmDate) callbacks.onConfirmDate(task.id, val);
      });
      formRow.appendChild(btnConfirm);

      warnBox.appendChild(formRow);
      article.appendChild(warnBox);
    } else if (task.due_iso) {
      const dueBox = document.createElement("div");
      dueBox.style.margin = "0.5rem 0";
      dueBox.style.fontSize = "0.95rem";
      dueBox.innerHTML = `<strong>Termen:</strong> <span>${escapeHtml(formatDateRo(task.due_iso))}</span>`;
      article.appendChild(dueBox);
    } else {
      const noDue = document.createElement("div");
      noDue.style.margin = "0.5rem 0";
      noDue.style.fontSize = "0.9rem";
      noDue.style.color = "var(--text-muted)";
      noDue.textContent = "Fără termen limită specificat.";
      article.appendChild(noDue);
    }

    // Sub-steps list
    if (task.steps && task.steps.length > 0) {
      const stepsDiv = document.createElement("div");
      stepsDiv.style.margin = "0.75rem 0";
      const stepsHeading = document.createElement("strong");
      stepsHeading.style.fontSize = "0.95rem";
      stepsHeading.textContent = "Sub-pași:";
      stepsDiv.appendChild(stepsHeading);

      const ol = document.createElement("ol");
      ol.style.margin = "0.35rem 0 0 1.25rem";
      ol.style.padding = "0";
      ol.style.fontSize = "0.95rem";
      task.steps.forEach(stepText => {
        const li = document.createElement("li");
        li.style.marginBottom = "0.2rem";
        li.textContent = stepText;
        ol.appendChild(li);
      });
      stepsDiv.appendChild(ol);
      article.appendChild(stepsDiv);
    }

    // Verbatim source quote block
    if (task.source_quote) {
      const quoteDiv = document.createElement("div");
      quoteDiv.className = "source-quote";
      quoteDiv.style.marginTop = "0.75rem";
      quoteDiv.style.fontSize = "0.9rem";
      quoteDiv.innerHTML = `
        <span style="font-weight: 600; display: block; margin-bottom: 0.2rem;">Extras din document:</span>
        &ldquo;${escapeHtml(task.source_quote)}&rdquo;
      `;
      article.appendChild(quoteDiv);
    }

    container.appendChild(article);
  });
}

/**
 * Initializes the Planner page controls, storage, and API interactions.
 */
export function initPlanPage() {
  if (typeof document === "undefined") return;

  const planForm = document.getElementById("plan-form");
  const planText = document.getElementById("plan-text");
  const btnLoadSample = document.getElementById("btn-load-sample");
  const btnClearInput = document.getElementById("btn-clear-input");
  const btnExtractPlan = document.getElementById("btn-extract-plan");
  const btnExportIcs = document.getElementById("btn-export-ics");
  const btnClearTasks = document.getElementById("btn-clear-tasks");
  const btnToggleAdd = document.getElementById("btn-toggle-add");
  const formAddTask = document.getElementById("form-add-task");
  const btnCancelAddTask = document.getElementById("btn-cancel-add-task");
  const tasksList = document.getElementById("tasks-list");
  const statusLive = document.getElementById("status-live");
  const errorBanner = document.getElementById("error-banner");
  const aiNotice = document.getElementById("ai-notice");
  const warningsContainer = document.getElementById("warnings-container");

  // In-memory task state
  let currentTasks = loadStoredTasks();

  function announce(msg) {
    if (statusLive) {
      statusLive.textContent = "";
      setTimeout(() => {
        statusLive.textContent = msg;
      }, 50);
    }
  }

  function showError(msg) {
    if (errorBanner) {
      errorBanner.textContent = msg;
      errorBanner.style.display = "block";
    }
    announce(`Eroare: ${msg}`);
  }

  function clearError() {
    if (errorBanner) {
      errorBanner.textContent = "";
      errorBanner.style.display = "none";
    }
  }

  function render() {
    renderTasks(currentTasks, tasksList, {
      onError: (msg) => {
        showError(msg);
      },
      onToggle: (id) => {
        currentTasks = toggleTaskCompletion(currentTasks, id);
        saveStoredTasks(currentTasks);
        render();
        const updated = currentTasks.find(t => t.id === id);
        announce(`Sarcina „${updated?.title}” a fost marcată ca ${updated?.completed ? "finalizată" : "nefinalizată"}.`);
      },
      onDelete: (id) => {
        const toDelete = currentTasks.find(t => t.id === id);
        currentTasks = deleteTask(currentTasks, id);
        saveStoredTasks(currentTasks);
        render();
        announce(`Sarcina „${toDelete?.title || id}” a fost ștearsă din planificator.`);
      },
      onConfirmDate: (id, dateIso) => {
        currentTasks = confirmTaskDate(currentTasks, id, dateIso);
        saveStoredTasks(currentTasks);
        render();
        const updated = currentTasks.find(t => t.id === id);
        announce(`Data pentru „${updated?.title}” a fost confirmată: ${dateIso}.`);
      }
    });
  }

  // Load sample task email
  if (btnLoadSample && planText) {
    btnLoadSample.addEventListener("click", () => {
      clearError();
      planText.value = SAMPLE_TASK_EMAIL;
      planText.focus();
      announce("E-mailul de exemplu a fost încărcat în formular.");
    });
  }

  // Clear input
  if (btnClearInput && planText) {
    btnClearInput.addEventListener("click", () => {
      planText.value = "";
      planText.focus();
      announce("Câmpul de text a fost golit.");
    });
  }

  // Extract tasks form submission
  if (planForm) {
    planForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearError();

      const raw = planText ? planText.value.trim() : "";
      if (!raw) {
        showError("Te rugăm să lipești sau să scrii textul documentului înainte de extragere.");
        if (planText) planText.focus();
        return;
      }

      if (btnExtractPlan) {
        btnExtractPlan.disabled = true;
        btnExtractPlan.textContent = "Se extrag sarcinile...";
      }
      announce("Se extrag sarcinile și termenele din text. Vă rugăm așteptați...");

      try {
        const todayIso = new Date().toISOString().slice(0, 10);
        const profile = getApiProfile();
        const res = await extractPlan(raw, todayIso, profile);

        if (!res.ok) {
          const errMsg = res.error?.message_ro || "A apărut o problemă la comunicarea cu serverul.";
          showError(errMsg);
          return;
        }

        const extracted = res.data?.tasks || [];
        if (extracted.length === 0) {
          showError("Nu a fost identificată nicio sarcină clară în textul furnizat.");
          return;
        }

        // Append newly extracted tasks, re-keying each task per CONTRACTS.md §3.2
        extracted.forEach((rawTask, idx) => {
          const rekeyed = {
            ...rawTask,
            id: `task_${Date.now()}_${idx}_${Math.random().toString(36).slice(2, 7)}`
          };
          currentTasks = addTask(currentTasks, rekeyed);
        });
        saveStoredTasks(currentTasks);

        // Show AI transparency notice
        if (aiNotice) {
          aiNotice.style.display = "block";
          if (res.meta?.ai_notice_ro) {
            aiNotice.textContent = res.meta.ai_notice_ro;
          }
        }

        // Show warnings if any
        if (warningsContainer) {
          if (res.meta?.warnings && res.meta.warnings.length > 0) {
            warningsContainer.innerHTML = res.meta.warnings
              .map(w => `<div class="status-message status-warning" style="margin-bottom: 0.5rem;">${escapeHtml(w)}</div>`)
              .join("");
            warningsContainer.style.display = "block";
          } else {
            warningsContainer.style.display = "none";
          }
        }

        render();
        announce(`Extragere finalizată. Au fost adăugate ${extracted.length} sarcini în planificator.`);
      } catch (err) {
        console.error("Eroare la extragerea sarcinilor:", err);
        showError("A apărut o eroare neașteptată la procesarea cererii.");
      } finally {
        if (btnExtractPlan) {
          btnExtractPlan.disabled = false;
          btnExtractPlan.textContent = "Extrage sarcini și termene";
        }
      }
    });
  }

  // Export ICS
  if (btnExportIcs) {
    btnExportIcs.addEventListener("click", () => {
      clearError();
      if (!currentTasks || currentTasks.length === 0) {
        showError("Nu există nicio sarcină de exportat în calendar.");
        return;
      }

      try {
        const icsContent = generateIcs(currentTasks, {
          prodId: "-//PrimaZi//Planificator Sarcini//RO",
          calName: "Sarcini PrimaZi"
        });
        downloadIcsFile("primazi-plan.ics", icsContent);
        announce("Fișierul calendaristic .ics a fost descărcat cu succes.");
      } catch (err) {
        console.error("Eroare la generarea fișierului ICS:", err);
        showError("A apărut o eroare la generarea calendarului .ics.");
      }
    });
  }

  // Clear all tasks
  if (btnClearTasks) {
    btnClearTasks.addEventListener("click", () => {
      if (!currentTasks || currentTasks.length === 0) return;
      const confirmed = window.confirm("Sigur dorești să ștergi toate sarcinile din planificator?");
      if (!confirmed) return;

      currentTasks = [];
      clearStoredTasks();
      render();
      announce("Toate sarcinile au fost șterse din planificator.");
    });
  }

  // Toggle manual add task form
  if (btnToggleAdd && formAddTask) {
    btnToggleAdd.addEventListener("click", () => {
      const isHidden = formAddTask.style.display === "none" || !formAddTask.style.display;
      formAddTask.style.display = isHidden ? "block" : "none";
      btnToggleAdd.setAttribute("aria-expanded", isHidden ? "true" : "false");
      if (isHidden) {
        const titleInput = document.getElementById("new-task-title");
        if (titleInput) titleInput.focus();
      }
    });
  }

  if (btnCancelAddTask && formAddTask && btnToggleAdd) {
    btnCancelAddTask.addEventListener("click", () => {
      formAddTask.style.display = "none";
      btnToggleAdd.setAttribute("aria-expanded", "false");
      btnToggleAdd.focus();
    });
  }

  // Submit manual add task form
  if (formAddTask) {
    formAddTask.addEventListener("submit", (e) => {
      e.preventDefault();
      clearError();

      const titleInput = document.getElementById("new-task-title");
      const dueInput = document.getElementById("new-task-due");
      const priorityInput = document.getElementById("new-task-priority");

      const title = titleInput ? titleInput.value.trim() : "";
      if (!title) {
        showError("Te rugăm să introduci un titlu pentru sarcină.");
        if (titleInput) titleInput.focus();
        return;
      }

      const dueIso = dueInput && dueInput.value ? dueInput.value : null;
      const priority = priorityInput && priorityInput.value ? priorityInput.value : "normal";

      currentTasks = addTask(currentTasks, {
        title,
        due_iso: dueIso,
        due_text: dueIso ? formatDateRo(dueIso) : null,
        needs_confirmation: false,
        priority,
        steps: []
      });

      saveStoredTasks(currentTasks);
      render();

      // Reset & hide form
      formAddTask.reset();
      formAddTask.style.display = "none";
      if (btnToggleAdd) {
        btnToggleAdd.setAttribute("aria-expanded", "false");
        btnToggleAdd.focus();
      }
      announce(`Sarcina „${title}” a fost adăugată cu succes.`);
    });
  }

  // Initial render
  render();
}
