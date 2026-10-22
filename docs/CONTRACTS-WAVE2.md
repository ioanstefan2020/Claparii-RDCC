# CONTRACTS-WAVE2 — additive endpoints and rules (owner: P1; old contracts keep working)

**Global rules:** (1) Requests with unknown fields are accepted (`extra=ignore`). (2) `profile` is loose: normalised server-side, never HTTP 422 (`meta.warnings` explains mapped values). (3) Every response uses the standard envelope. (4) Anything derived from the user's document keeps `source_quote` grounding. (5) No audio/image/document is stored; temp files are deleted in `finally`.

## `GET /api/llm/status`
```json
{"ok": true, "data": {"chain": ["groq","deepseek","ollama","mock"], "providers": [
  {"id":"groq","configured":true,"model":"…","circuit":"closed","last_ok":"2026-10-22T14:03:10Z","last_error":null,"p50_ms":820},
  {"id":"deepseek","configured":false,"reason":"DEEPSEEK_API_KEY missing"}]}}
```
Startup logs one line per provider (configured? key present? model?). `LLM_PROVIDER_CHAIN=groq,deepseek,ollama,mock`. A configured-but-failing provider is skipped with a clear reason (the "Groq config does nothing" class of bug).

## `POST /api/annotate`
Request: `{"text": "...", "layers": ["deterministic","semantic","tone","glossary"], "profile": {…}, "today_iso": "…"}`
```json
{"ok": true, "data": {
  "highlights": [{"start": 12, "end": 30, "category": "deadline", "text": "miercuri, 28 octombrie"}],
  "annotations": [{"start": 120, "end": 168, "kind": "indirect_request", "evidence_quote": "ar fi frumos să trimiți raportul", "note_ro": "(cerere politicoasă: se așteaptă să trimiți raportul)", "confidence": "medium"}],
  "glossary": [{"term": "KPI", "explanation": "Indicatori prin care se măsoară rezultatele."}]}, "meta": {…}}
```
`category` ∈ action, deadline, person, number, warning, term. `kind` ∈ joke, irony, figurative, indirect_request, urgency, softener. Offsets index the exact `text` sent. `deterministic` layer never calls the LLM (fast, free). `confidence` ∈ low, medium only.

## `POST /api/transform`
Request: `{"text": "...", "mode": "bullets|shorter|tldr|easy_read|steps|questions|glossary", "max_items": 6, "target_pct": 40, "profile": {…}}`
Response data: `{"mode": "bullets", "items": ["…"], "text": null}` (list modes → `items`; prose modes → `text`), plus `warnings`.

## `POST /api/extract-text` (multipart)
`file` (pdf, docx, txt, md, html; ≤ 10 MB) → `{"text": "...", "pages": 3, "truncated": false}`. Parsed in memory (pypdf / python-docx); scanned PDFs → `needs_ocr: true` (offer the image-description path).

## `POST /api/transcribe` (multipart) — audio file → text (for deaf / hard-of-hearing users, meetings, voice notes)
`file` (mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm, flac), form `language=ro` (default), `timestamps=true`.
```json
{"ok": true, "data": {"language": "ro", "duration_s": 312.4,
  "text": "…", "segments": [{"start": 0.0, "end": 4.2, "text": "Bun, să începem."}],
  "captions": {"srt": "1\n00:00:00,000 --> 00:00:04,200\nBun, să începem.\n", "vtt": "WEBVTT\n\n00:00:00.000 --> 00:00:04.200\nBun, să începem.\n"}}, "meta": {…}}
```
Primary: Groq `whisper-large-v3-turbo` (`/openai/v1/audio/transcriptions`, `verbose_json` for segments). **Groq's API does not return SRT/VTT, so we build them from the segments.** Free-tier upload limit is 25 MB: pre-shrink with ffmpeg (16 kHz mono) and chunk longer files with overlap; fallback to a local model (faster-whisper) if installed. Transcript = **text only**: no emotion or speaker-trait inference from voice; non-speech sounds only if the ASR emits them (`[muzică]`), labelled as such. Then the UI can call `/api/meeting/summarize`, `/api/transform` (bullets / shorter), `/api/annotate`.

## `POST /api/tts` → `audio/wav`
Request `{"text": "...", "voice": "ro-mihai", "rate": 0.95, "pause_ms": 350}`; server runs Piper `ro_RO-mihai-medium` (offline, CPU) after `tts_normalize_ro(text)` (dates, times, amounts, `F-12`, abbreviations → spoken Romanian). Limits: ≤ 2000 chars per call; client sends sentence by sentence and plays them back-to-back. The browser engine (Edge "Online (Natural)" Romanian voices) is preferred when present; this endpoint is the fallback.

## `POST /api/describe-image` (multipart; COULD)
`file` (jpg/png/webp ≤ 5 MB), `purpose`: `alt_text|read_text|chart|document` → `{"description_ro": "…", "text_found": "…", "confidence_note": "…"}` via a vision-capable provider. Never claims certainty; recommends checking important text.

## `POST /api/profile/recommend-adaptations` (exists; extend)
Request `{"needs_notes": "…", "chips": ["text_mare","pasi_scurti"]}` → `{"settings": {…SETTINGS-SPEC keys…}, "reasons": [{"key": "theme", "reason_ro": "…"}], "adaptations": [catalog ids]}`. Values are clamped to the allowed enums; diagnosis words are scrubbed before the LLM call and never echoed; heuristic fallback when the LLM is unavailable.

## `meta` additions
`meta.latency_ms`, `meta.prompt_version`, `meta.provider_chain_tried` (names only), `meta.warnings` (Romanian).
