/**
 * ics.js - RFC 5545 iCalendar Generator
 * Owner: p2
 *
 * Pure, unit-testable generator for calendar events (.ics).
 * Complies strictly with RFC 5545 formatting:
 * - Proper CRLF (\r\n) line terminators
 * - Escaping for commas, semicolons, backslashes, and newlines
 * - All-day events (VALUE=DATE) when due_iso is specified
 */

/**
 * Escapes characters per RFC 5545 section 3.3.11.
 */
export function escapeIcsText(str) {
  if (!str) return "";
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

/**
 * Formats a Date object or ISO string (YYYY-MM-DD) into YYYYMMDD.
 */
export function formatIcsDate(dateInput) {
  if (!dateInput) return "";
  if (typeof dateInput === "string") {
    const clean = dateInput.trim().replace(/[-:]/g, "");
    if (clean.length >= 8) {
      return clean.slice(0, 8);
    }
  }
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return "";
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * Folds lines longer than 75 octets per RFC 5545 section 3.1.
 */
export function foldIcsLine(line) {
  if (!line || line.length <= 75) return line;
  const parts = [];
  let remaining = line;
  parts.push(remaining.slice(0, 75));
  remaining = remaining.slice(75);
  while (remaining.length > 74) {
    parts.push(" " + remaining.slice(0, 74));
    remaining = remaining.slice(74);
  }
  if (remaining.length > 0) {
    parts.push(" " + remaining);
  }
  return parts.join("\r\n");
}

/**
 * Generates an RFC 5545 VCALENDAR string from a list of tasks.
 * Pure function: takes data, returns string.
 *
 * @param {Array<Object>} tasks - List of task objects
 * @param {Object} options - Optional metadata (prodId, calName)
 * @returns {string} - RFC 5545 compliant .ics string
 */
export function generateIcs(tasks = [], options = {}) {
  const prodId = options.prodId || "-//PrimaZi//Planificator Accesibil RO//RO";
  const calName = options.calName || "Planificator PrimaZi";
  const now = new Date();
  const dtStamp = now.toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";

  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    `PRODID:${prodId}`,
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${escapeIcsText(calName)}`
  ];

  for (const [idx, task] of tasks.entries()) {
    if (!task) continue;

    const title = task.title || task.text || `Sarcină #${idx + 1}`;
    const uid = task.id ? `primazi-${task.id}@primazi.ro` : `primazi-task-${Date.now()}-${idx}@primazi.ro`;

    // Compose description from steps and source quote
    const descParts = [];
    if (task.due_text && task.needs_confirmation) {
      descParts.push(`[NOTĂ]: Termen estimat în text: "${task.due_text}" (necesită confirmare)`);
    }
    if (Array.isArray(task.steps) && task.steps.length) {
      descParts.push("Pași:");
      task.steps.forEach((s, sIdx) => {
        descParts.push(`  ${sIdx + 1}. ${s}`);
      });
    }
    if (task.source_quote) {
      descParts.push(`Extras din document: "${task.source_quote}"`);
    }
    descParts.push("Generat de asistentul PrimaZi.");

    const description = escapeIcsText(descParts.join("\n"));
    const summary = escapeIcsText(task.needs_confirmation ? `[De confirmat] ${title}` : title);

    if (task.due_iso) {
      // Event with confirmed or tentative date
      const dtStartDate = formatIcsDate(task.due_iso);
      lines.push("BEGIN:VEVENT");
      lines.push(`UID:${uid}`);
      lines.push(`DTSTAMP:${dtStamp}`);
      lines.push(`SUMMARY:${summary}`);
      lines.push(`DESCRIPTION:${description}`);
      lines.push(`DTSTART;VALUE=DATE:${dtStartDate}`);
      // Per RFC 5545 §3.6.1, omitting DTEND for an all-day event (VALUE=DATE) defaults to 1 day duration.
      lines.push(task.needs_confirmation ? "STATUS:TENTATIVE" : "STATUS:CONFIRMED");
      lines.push("END:VEVENT");
    } else {
      // Task without confirmed calendar date: strictly export as VTODO without date per RFC 5545 §3.6.2
      // NEVER invent or guess a fake date (e.g. tomorrow) for unconfirmed tasks
      lines.push("BEGIN:VTODO");
      lines.push(`UID:${uid}`);
      lines.push(`DTSTAMP:${dtStamp}`);
      lines.push(`SUMMARY:${summary}`);
      lines.push(`DESCRIPTION:${description}`);
      lines.push("STATUS:NEEDS-ACTION");
      lines.push("END:VTODO");
    }
  }

  lines.push("END:VCALENDAR");

  // RFC 5545 requires CRLF line terminators
  return lines.join("\r\n") + "\r\n";
}

/**
 * Triggers a browser download of the generated .ics file.
 */
export function downloadIcsFile(filename = "primazi-plan.ics", icsContent = "") {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  const cleanFilename = filename.endsWith(".ics") ? filename : `${filename}.ics`;
  const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
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
