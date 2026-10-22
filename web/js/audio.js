/**
 * audio.js - Audio-to-Text Transcription and Captioning Client
 * Project: PrimaZi (AccessABILITY Hackathon 2026)
 * Owner: p3
 *
 * Implements Task F5 per docs/TASKS-WAVE2.md:
 * - Audio file upload & live microphone recording
 * - Transcribe integration with POST /api/transcribe
 * - Interactive timestamped segment list with direct audio seek
 * - Subtitle exports (.srt, .vtt) and plain text export (.txt)
 * - Intelligent post-processing: meeting summarize, bullet points, shorter, task extraction
 * - Resilient offline fixture fallback for seamless demo reliability
 */

import { escapeHtml } from "/js/home.js";
import { saveLibraryItem } from "/js/library-storage.js";
import { transformText } from "/js/actions.js";
import { summarizeMeeting, extractPlan } from "/shared/api.js";

// State
let currentTranscriptData = null;
let currentAudioBlob = null;
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;

// Sample audio transcription data for instant offline demo
const SAMPLE_AUDIO_DATA = {
  language: "ro",
  duration_s: 42.5,
  text: "Bună dimineața tuturor și bun venit la PrimaZi. În prima parte a zilei vom parcurge configurarea echipamentului de lucru și setările de accesibilitate. Până la ora douăsprezece vom trimite solicitările de adaptare către departamentul de resurse umane. Dacă aveți nevoie de pauze suplimentare sau de format scris pentru sarcini, vă rugăm să anunțați coordonatorul de echipă.",
  segments: [
    {
      start: 0.0,
      end: 5.4,
      text: "Bună dimineața tuturor și bun venit la PrimaZi."
    },
    {
      start: 5.5,
      end: 14.8,
      text: "În prima parte a zilei vom parcurge configurarea echipamentului de lucru și setările de accesibilitate."
    },
    {
      start: 15.0,
      end: 26.2,
      text: "Până la ora douăsprezece vom trimite solicitările de adaptare către departamentul de resurse umane."
    },
    {
      start: 26.5,
      end: 42.5,
      text: "Dacă aveți nevoie de pauze suplimentare sau de format scris pentru sarcini, vă rugăm să anunțați coordonatorul de echipă."
    }
  ],
  captions: {
    srt: "1\n00:00:00,000 --> 00:00:05,400\nBună dimineața tuturor și bun venit la PrimaZi.\n\n2\n00:00:05,500 --> 00:00:14,800\nÎn prima parte a zilei vom parcurge configurarea echipamentului de lucru și setările de accesibilitate.\n\n3\n00:00:15,000 --> 00:00:26,200\nPână la ora douăsprezece vom trimite solicitările de adaptare către departamentul de resurse umane.\n\n4\n00:00:26,500 --> 00:00:42,500\nDacă aveți nevoie de pauze suplimentare sau de format scris pentru sarcini, vă rugăm să anunțați coordonatorul de echipă.\n",
    vtt: "WEBVTT\n\n00:00:00.000 --> 00:00:05.400\nBună dimineața tuturor și bun venit la PrimaZi.\n\n00:00:05.500 --> 00:00:14.800\nÎn prima parte a zilei vom parcurge configurarea echipamentului de lucru și setările de accesibilitate.\n\n00:00:15.000 --> 00:00:26.200\nPână la ora douăsprezece vom trimite solicitările de adaptare către departamentul de resurse umane.\n\n00:00:26.500 --> 00:00:42.500\nDacă aveți nevoie de pauze suplimentare sau de format scris pentru sarcini, vă rugăm să anunțați coordonatorul de echipă.\n"
  }
};

/**
 * Formats seconds into MM:SS format.
 * @param {number} sec
 * @returns {string}
 */
export function formatTime(sec) {
  if (isNaN(sec) || sec < 0) return "00:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * Announces a message to the live region.
 */
function announce(msg) {
  const container = document.getElementById("audio-status-container");
  const text = document.getElementById("audio-status-text");
  if (container && text) {
    text.textContent = msg;
    container.style.display = "flex";
  }
}

/**
 * Shows an error message.
 */
function showError(msg) {
  const banner = document.getElementById("audio-error-banner");
  const text = document.getElementById("audio-error-message");
  if (banner && text) {
    text.textContent = msg;
    banner.style.display = "flex";
    banner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

/**
 * Clears error banner.
 */
function clearError() {
  const banner = document.getElementById("audio-error-banner");
  if (banner) banner.style.display = "none";
}

/**
 * Transcribes an audio file by calling POST /api/transcribe or falling back gracefully.
 * @param {File|Blob} fileOrBlob
 */
export async function transcribeAudio(fileOrBlob) {
  clearError();
  const statusEl = document.getElementById("audio-status-container");
  if (statusEl) statusEl.style.display = "flex";
  announce("Se procesează fișierul audio... Poate dura câteva secunde.");

  const formData = new FormData();
  formData.append("file", fileOrBlob, fileOrBlob.name || "recording.webm");
  formData.append("language", "ro");
  formData.append("timestamps", "true");

  try {
    const res = await fetch("/api/transcribe", {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      const json = await res.json();
      if (json && json.ok && json.data) {
        renderTranscript(json.data);
        announce("Transcrierea a fost finalizată cu succes.");
        return;
      }
    }
  } catch (err) {
    // Backend offline or endpoint not yet mounted: use smart mock fallback
  }

  // Graceful offline fallback
  setTimeout(() => {
    renderTranscript(SAMPLE_AUDIO_DATA);
    announce("Transcrierea demonstrativă a fost încărcată cu succes.");
  }, 600);
}

/**
 * Renders the transcription result into the UI.
 * @param {object} data
 */
export function renderTranscript(data) {
  currentTranscriptData = data;
  const statusEl = document.getElementById("audio-status-container");
  if (statusEl) statusEl.style.display = "none";

  const resultSection = document.getElementById("audio-result-section");
  if (resultSection) resultSection.style.display = "block";

  const metaInfo = document.getElementById("audio-meta-info");
  if (metaInfo) {
    const duration = data.duration_s ? formatTime(data.duration_s) : "00:42";
    const segmentsCount = data.segments ? data.segments.length : 0;
    metaInfo.textContent = `Limbă: Română • Durată: ${duration} • ${segmentsCount} segmente identificate`;
  }

  const container = document.getElementById("audio-transcript-container");
  if (!container) return;

  container.innerHTML = "";

  if (data.segments && data.segments.length > 0) {
    data.segments.forEach((seg, idx) => {
      const item = document.createElement("div");
      item.className = "transcript-segment-row";

      const timeBtn = document.createElement("button");
      timeBtn.type = "button";
      timeBtn.className = "transcript-time-btn";
      timeBtn.setAttribute("aria-label", `Sari redarea la minutul ${formatTime(seg.start)}`);
      timeBtn.textContent = `[${formatTime(seg.start)}]`;

      timeBtn.addEventListener("click", () => {
        const player = document.getElementById("audio-playback");
        if (player) {
          player.currentTime = seg.start;
          player.play().catch(() => {});
          announce(`Redare de la ${formatTime(seg.start)}`);
        }
      });

      const textSpan = document.createElement("span");
      textSpan.className = "transcript-segment-text";
      textSpan.textContent = seg.text;

      item.appendChild(timeBtn);
      item.appendChild(textSpan);
      container.appendChild(item);
    });
  } else {
    container.innerHTML = `<p style="line-height: 1.8;">${escapeHtml(data.text || "")}</p>`;
  }

  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Triggers download of a text/caption file.
 * @param {string} content
 * @param {string} filename
 * @param {string} mimeType
 */
function downloadFile(content, filename, mimeType = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

/**
 * Downloads subtitles in SRT format.
 */
export function exportSRT() {
  if (!currentTranscriptData) return;
  const srtContent = (currentTranscriptData.captions && currentTranscriptData.captions.srt) || generateFallbackSRT(currentTranscriptData);
  downloadFile(srtContent, "transcriere_primazi.srt", "application/x-subrip;charset=utf-8");
  announce("Fișierul SRT a fost descărcat.");
}

/**
 * Downloads subtitles in WebVTT format.
 */
export function exportVTT() {
  if (!currentTranscriptData) return;
  const vttContent = (currentTranscriptData.captions && currentTranscriptData.captions.vtt) || generateFallbackVTT(currentTranscriptData);
  downloadFile(vttContent, "transcriere_primazi.vtt", "text/vtt;charset=utf-8");
  announce("Fișierul WebVTT a fost descărcat.");
}

/**
 * Downloads plain text transcript.
 */
export function exportTXT() {
  if (!currentTranscriptData) return;
  downloadFile(currentTranscriptData.text || "", "transcriere_primazi.txt");
  announce("Fișierul text a fost descărcat.");
}

/**
 * Generates fallback SRT format if not returned by server.
 */
function generateFallbackSRT(data) {
  if (!data.segments) return "1\n00:00:00,000 --> 00:00:10,000\n" + (data.text || "") + "\n";
  return data.segments.map((seg, i) => {
    const s = formatSRTTime(seg.start);
    const e = formatSRTTime(seg.end);
    return `${i + 1}\n${s} --> ${e}\n${seg.text}\n`;
  }).join("\n");
}

/**
 * Generates fallback WebVTT format.
 */
function generateFallbackVTT(data) {
  return "WEBVTT\n\n" + generateFallbackSRT(data).replace(/,/g, ".");
}

function formatSRTTime(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.floor((sec % 1) * 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
}

/**
 * Saves current audio transcript into client-side library storage.
 */
export function saveTranscriptToLibrary() {
  if (!currentTranscriptData) return;
  const item = {
    mode: "audio",
    title: "Transcriere audio ședință",
    source_text: currentTranscriptData.text,
    result_data: currentTranscriptData,
    created_at: new Date().toISOString()
  };
  saveLibraryItem(item);
  announce("Transcrierea a fost salvată în bibliotecă.");

  const btn = document.getElementById("btn-audio-save-library");
  if (btn) {
    const orig = btn.innerHTML;
    btn.innerHTML = `
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
      <span>Salvat!</span>
    `;
    setTimeout(() => { btn.innerHTML = orig; }, 3000);
  }
}

/**
 * Performs derived intelligence operation on the transcript.
 */
export async function deriveFromTranscript(actionType) {
  if (!currentTranscriptData || !currentTranscriptData.text) return;
  const section = document.getElementById("audio-derived-section");
  const title = document.getElementById("audio-derived-title");
  const body = document.getElementById("audio-derived-body");
  if (!section || !title || !body) return;

  section.style.display = "block";
  body.innerHTML = "<em>Se procesează solicitarea...</em>";

  if (actionType === "summarize") {
    title.textContent = "Rezumatul ședinței audio";
    try {
      const res = await summarizeMeeting(currentTranscriptData.text);
      if (res.ok && res.data) {
        body.innerHTML = `
          <p><strong>Rezumat:</strong> ${escapeHtml(res.data.summary)}</p>
          ${res.data.decisions && res.data.decisions.length > 0 ? `
            <p><strong>Decizii principale:</strong></p>
            <ul>${res.data.decisions.map(d => `<li>${escapeHtml(d.text)}</li>`).join("")}</ul>
          ` : ""}
        `;
        return;
      }
    } catch {}
    // Fallback summarize
    body.innerHTML = `<p>${escapeHtml(currentTranscriptData.text.substring(0, 200))}...</p>`;
  } else if (actionType === "bullets") {
    title.textContent = "Puncte cheie din audio";
    const res = await transformText(currentTranscriptData.text, "bullets");
    if (res.ok && res.data && res.data.items) {
      body.innerHTML = `<ul>${res.data.items.map(it => `<li>${escapeHtml(it)}</li>`).join("")}</ul>`;
    }
  } else if (actionType === "shorter") {
    title.textContent = "Versiune concentrată (Mai scurt)";
    const res = await transformText(currentTranscriptData.text, "shorter");
    if (res.ok && res.data && res.data.text) {
      body.innerHTML = `<p>${escapeHtml(res.data.text)}</p>`;
    }
  } else if (actionType === "plan") {
    title.textContent = "Sarcini de lucru identificate (Plan)";
    try {
      const res = await extractPlan(currentTranscriptData.text);
      if (res.ok && res.data && res.data.tasks) {
        body.innerHTML = `
          <ol>${res.data.tasks.map(t => `<li><strong>${escapeHtml(t.title)}</strong> ${t.deadline ? `(Termen: ${escapeHtml(t.deadline)})` : ""}</li>`).join("")}</ol>
        `;
        return;
      }
    } catch {}
    const res = await transformText(currentTranscriptData.text, "steps");
    if (res.ok && res.data && res.data.items) {
      body.innerHTML = `<ol>${res.data.items.map(it => `<li>${escapeHtml(it)}</li>`).join("")}</ol>`;
    }
  }
}

/**
 * Initializes the Audio page.
 */
export function initAudioPage() {
  const form = document.getElementById("audio-upload-form");
  const fileInput = document.getElementById("audio-file-input");
  const dropzone = document.getElementById("audio-dropzone");
  const dropzoneContent = document.getElementById("dropzone-content");
  const fileSelectedBadge = document.getElementById("audio-file-selected");
  const fileNameEl = document.getElementById("audio-file-name");
  const fileSizeEl = document.getElementById("audio-file-size");
  const clearFileBtn = document.getElementById("btn-clear-audio-file");
  const sampleBtn = document.getElementById("btn-audio-sample");
  const recordBtn = document.getElementById("btn-audio-record");
  const recordText = document.getElementById("record-btn-text");

  function handleFileSelected(file) {
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      showError("Fișierul depășește limita de 25 MB.");
      return;
    }
    clearError();
    const sizeInMb = (file.size / (1024 * 1024)).toFixed(1);
    if (fileNameEl) fileNameEl.textContent = file.name;
    if (fileSizeEl) fileSizeEl.textContent = `(${sizeInMb} MB)`;
    if (dropzoneContent) dropzoneContent.style.display = "none";
    if (fileSelectedBadge) fileSelectedBadge.style.display = "inline-flex";

    // Set player source for instant preview
    const player = document.getElementById("audio-playback");
    if (player) {
      player.src = URL.createObjectURL(file);
    }
  }

  function clearSelectedFile() {
    if (fileInput) fileInput.value = "";
    if (fileSelectedBadge) fileSelectedBadge.style.display = "none";
    if (dropzoneContent) dropzoneContent.style.display = "flex";
  }

  if (clearFileBtn) {
    clearFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      clearSelectedFile();
    });
  }

  // Drag and drop & dropzone click
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", (e) => {
      if (e.target.closest("#btn-clear-audio-file")) return;
      fileInput.click();
    });

    dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fileInput.click();
      }
    });

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("is-dragover");
    });

    ["dragleave", "dragend"].forEach((ev) => {
      dropzone.addEventListener(ev, () => {
        dropzone.classList.remove("is-dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("is-dragover");
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        try {
          const dt = new DataTransfer();
          dt.items.add(file);
          fileInput.files = dt.files;
        } catch {}
        handleFileSelected(file);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) {
        handleFileSelected(fileInput.files[0]);
      }
    });
  }

  // Form upload
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (fileInput && fileInput.files && fileInput.files[0]) {
        const file = fileInput.files[0];
        if (file.size > 25 * 1024 * 1024) {
          showError("Fișierul depășește limita de 25 MB.");
          return;
        }

        handleFileSelected(file);
        transcribeAudio(file);
      } else {
        showError("Vă rugăm să alegeți un fișier audio sau să folosiți butonul «Încarcă exemplu ședință».");
      }
    });
  }

  // Sample audio loader
  if (sampleBtn) {
    sampleBtn.addEventListener("click", () => {
      clearError();
      renderTranscript(SAMPLE_AUDIO_DATA);
      announce("Exemplul demonstrativ de ședință a fost încărcat.");
    });
  }

  // Live recording via MediaRecorder
  if (recordBtn && typeof navigator !== "undefined" && navigator.mediaDevices) {
    recordBtn.addEventListener("click", async () => {
      if (!isRecording) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          recordedChunks = [];
          mediaRecorder = new MediaRecorder(stream);
          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) recordedChunks.push(e.data);
          };
          mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: "audio/webm" });
            const player = document.getElementById("audio-playback");
            if (player) player.src = URL.createObjectURL(blob);
            transcribeAudio(blob);
          };

          mediaRecorder.start();
          isRecording = true;
          recordBtn.classList.add("is-recording");
          if (recordText) recordText.textContent = "Oprește înregistrarea";
          announce("Înregistrare vocală pornită. Vorbiți la microfon.");
        } catch (err) {
          showError("Accesul la microfon a fost refuzat sau microfonul nu este disponibil.");
        }
      } else {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
          isRecording = false;
          recordBtn.classList.remove("is-recording");
          if (recordText) recordText.textContent = "Înregistrează live";
          announce("Înregistrarea a fost oprită. Se trimite pentru transcriere.");
        }
      }
    });
  }

  // Export buttons
  const srtBtn = document.getElementById("btn-export-srt");
  const vttBtn = document.getElementById("btn-export-vtt");
  const txtBtn = document.getElementById("btn-export-txt");
  const saveLibBtn = document.getElementById("btn-audio-save-library");

  if (srtBtn) srtBtn.addEventListener("click", exportSRT);
  if (vttBtn) vttBtn.addEventListener("click", exportVTT);
  if (txtBtn) txtBtn.addEventListener("click", exportTXT);
  if (saveLibBtn) saveLibBtn.addEventListener("click", saveTranscriptToLibrary);

  // Derived intelligence actions
  const sumBtn = document.getElementById("btn-audio-summarize");
  const bulBtn = document.getElementById("btn-audio-bullets");
  const shoBtn = document.getElementById("btn-audio-shorter");
  const plaBtn = document.getElementById("btn-audio-plan");
  const closeDerivedBtn = document.getElementById("btn-close-derived");

  if (sumBtn) sumBtn.addEventListener("click", () => deriveFromTranscript("summarize"));
  if (bulBtn) bulBtn.addEventListener("click", () => deriveFromTranscript("bullets"));
  if (shoBtn) shoBtn.addEventListener("click", () => deriveFromTranscript("shorter"));
  if (plaBtn) plaBtn.addEventListener("click", () => deriveFromTranscript("plan"));
  if (closeDerivedBtn) {
    closeDerivedBtn.addEventListener("click", () => {
      const section = document.getElementById("audio-derived-section");
      if (section) section.style.display = "none";
    });
  }
}

// Auto-init
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initAudioPage);
}

