# CONTRACTS — frozen after kickoff (owner: P1 edits, only after all 3 agree in the group chat)

All endpoints: `POST` JSON unless noted, base path `/api`. The frontend can build against these with fixtures before the backend exists; the backend returns realistic mock data with `LLM_PROVIDER=mock`.

## 1. Conventions

**Request limits:** text fields ≤ `MAX_INPUT_CHARS` (12000), non-empty after trim.
**Profile** (sent with requests that adapt output; never stored by the server):

```json
{
  "reading_level": "simple",
  "format": "steps",
  "needs_notes": "Am nevoie de instrucțiuni scurte, scrise.",
  "max_sentence_words": 12
}
```

`reading_level`: `standard | simple | very_simple` · `format`: `steps | short_paragraphs` · `needs_notes`: free text ≤ 500 chars, user's own words, optional. **No diagnosis fields exist.** If omitted: `simple`, `steps`.

**Site Comfort Preferences Object (wp.prefs.v1 — Browser Storage Only, Never Sent to Server):**
Stored under localStorage key `wp.prefs.v1`.

```json
{
  "version": 1,
  "updatedAt": "2026-10-22T18:00:00Z",
  "answers": {
    "readingPace": "slow | medium | fast",
    "textAmount": "short | medium | full",
    "stepByStep": true,
    "visualNoise": "low | normal",
    "sensory": "quiet | normal",
    "language": "ro | en",
    "timeToDecide": "need-more-time | normal"
  },
  "prefs": {
    "theme": "light | dark | system",
    "textSize": "m | l | xl",
    "spacing": "comfortable | roomy",
    "contrast": "normal | high",
    "motion": "reduced | full",
    "font": "default | readable",
    "density": "focused | full",
    "language": "ro | en",
    "sidebar": "open | collapsed"
  },
  "overrides": ["textSize"]
}
```

**Success envelope**

```json
{
  "ok": true,
  "data": {},
  "meta": {
    "provider": "mock",
    "cached": false,
    "warnings": [],
    "ai_notice_ro": "Generat de AI — verifică datele importante."
  }
}
```

`meta.warnings` is a list of Romanian strings (e.g. `"1 element eliminat: citatul nu apare în text."`).

**Error envelope** (HTTP 400/422/502/503, never a stack trace)

```json
{
  "ok": false,
  "error": {
    "code": "empty_input",
    "message_ro": "Textul este gol. Lipește sau scrie ceva."
  }
}
```

Codes: `empty_input`, `too_long`, `bad_request`, `llm_unavailable`, `bad_llm_output`, `internal`.

**Grounding rule:** every item with a `source_quote` must have that quote appear verbatim in the input text (whitespace-normalised). The server drops items that fail and adds a warning. `due_iso` is `YYYY-MM-DD` or `null`; if the text is vague ("cât mai repede"), `due_iso=null`, `due_text` holds the original words, `needs_confirmation=true`. Relative dates are resolved with the client-supplied `today_iso`.

## 2. Backend conventions (P1 implements in the skeleton; others rely on them)

```python
# app/llm/__init__.py
async def generate_json(task: str, system: str, user: str, schema: type[BaseModel], mock: dict) -> tuple[BaseModel, dict]:
    """Returns (validated_model, meta_dict). provider=mock returns `mock` validated against schema.
    Real providers: JSON output, timeout, 1 retry on invalid JSON, cache by hash(task+system+user). Raises LLMUnavailable / BadLLMOutput."""
# app/guardrails.py
def verify_quotes(items: list[dict], source_text: str, key: str = "source_quote") -> tuple[list[dict], list[dict]]:
    """Returns (kept, dropped). Whitespace-normalised substring check."""
# app/routers/<name>.py  exports `router = APIRouter(prefix="/api/...")`   (auto-discovered by main.py)
# app/prompts/<task>.py  exports SYSTEM: str, build_user(**kw) -> str, MOCK: dict
# app/schemas/<task>.py  exports Request and Data pydantic models; envelope helpers live in app/schemas/common.py (P1)
```

`GET /api/health` → `{"ok": true, "provider": "mock"}`. The server also serves `web/` at `/` (StaticFiles, html=True).

## 3. Endpoints

### 3.1 `POST /api/simplify` (P1) — F2

Request: `{"text": "...", "profile": {…}}`

```json
{"ok": true, "data": {
  "summary": "Începi luni la 09:00. În prima săptămână ai 3 lucruri de făcut.",
  "steps": [
    {"n": 1, "text": "Luni la 09:00 mergi la recepția clădirii B și ceri cardul de acces.", "source_quote": "Luni, ora 09:00 – Te prezinți la recepția clădirii B"},
    {"n": 2, "text": "Până miercuri, 28 octombrie, completezi formularul F-12 în portalul intern.", "source_quote": "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12"}
  ],
  "key_terms": [{"term": "onboarding", "explanation": "Primele zile în care înveți cum funcționează firma."}],
  "questions_to_ask": ["Pot primi instrucțiunile și în scris, pas cu pas?"]},
 "meta": {…}}
```

### 3.2 `POST /api/plan/extract` (P1) — F3

Request: `{"text": "...", "today_iso": "2026-10-22", "profile": {…}}`

```json
{"ok": true, "data": {"tasks": [
  {"id": "t1", "title": "Completează formularul F-12", "due_iso": "2026-10-28", "due_text": "miercuri, 28 octombrie", "needs_confirmation": false,
   "priority": "high", "steps": ["Deschide portalul intern", "Completează datele personale și bancare"],
   "source_quote": "Până miercuri, 28 octombrie, trebuie să completezi în portalul intern formularul F-12"},
  {"id": "t2", "title": "Trimite raportul lunar", "due_iso": null, "due_text": "cât mai repede, până joi la prânz", "needs_confirmation": true,
   "priority": "normal", "steps": [], "source_quote": "până joi la prânz"}]}, "meta": {…}}
```

`priority`: `high | normal | low`. Ids are `t1…tn` per response (the client re-keys when merging into the planner).

### 3.3 `POST /api/meeting/summarize` (P1) — F4

Request: `{"transcript": "...", "today_iso": "2026-10-22", "profile": {…}}` (**text only; no audio, no emotion**)

```json
{"ok": true, "data": {
  "summary": "Echipa a hotărât lansarea paginii de produs vineri, 6 noiembrie.",
  "decisions": [{"text": "Lansăm vineri, 6 noiembrie.", "source_quote": "lansăm vineri, 6 noiembrie"}],
  "action_items": [{"who": "Ioana", "task": "Integrează textele finale", "due_iso": null, "due_text": "miercuri", "needs_confirmation": true,
                    "source_quote": "tu integrezi textele miercuri"}],
  "unclear_points": ["Nu e clar cine anunță clientul despre termen."]}, "meta": {…}}
```

`who` is a name from the transcript or `null`.

### 3.4 `GET /api/adjustments/catalog` (P3) — F5

```json
{
  "ok": true,
  "data": {
    "disclaimer_ro": "Informativ, nu reprezintă consultanță juridică.",
    "items": [
      {
        "id": "written_instructions",
        "title": "Instrucțiuni scrise, pas cu pas",
        "description": "Sarcinile îți sunt date și în scris, în pași scurți.",
        "applies_to": ["cognitive", "hearing"],
        "example_request": "Aș avea nevoie să primesc sarcinile și în scris.",
        "source": "<curated source or 'general good practice'>"
      }
    ]
  }
}
```

`applies_to` ⊆ `cognitive | visual | hearing | motor | any`. Minimum ids to ship: `written_instructions, extra_time, quiet_space, flexible_schedule, screen_reader_tools, captions_transcripts, plain_language_docs, regular_checkins, task_breakdown, advance_agenda, ergonomic_equipment, remote_option`.

### 3.5 `POST /api/adjustments/draft` (P3) — F5

Request: `{"need_ids": ["written_instructions", "extra_time"], "context": "onboarding", "employer_name": null, "tone": "friendly"}`
`context`: `interview | onboarding | ongoing` · `tone`: `formal | friendly`. **Only catalog ids are accepted — no free text, no diagnosis.** Unknown id → `bad_request`.

```json
{"ok": true, "data": {"subject": "Solicitare de adaptări în primele săptămâni",
  "body_ro": "Bună ziua, … Aș dori să discutăm câteva adaptări care mă ajută să lucrez eficient: instrucțiuni scrise, timp suplimentar la sarcini noi. …",
  "checklist": [{"id": "written_instructions", "title": "Instrucțiuni scrise, pas cu pas", "why": "Reduce nevoia de a reține informații spuse oral."}]屋},
 "meta": {…}}
```

### 3.6 `POST /api/employer/analyze` (P3) — F6

Request: `{"text": "...", "doc_type": "onboarding"}` · `doc_type`: `onboarding | job_ad | policy | other`

```json
{"ok": true, "data": {
  "readability": {"sentence_count": 14, "avg_sentence_words": 21.4, "long_sentences": [{"text": "…", "words": 41}], "score_0_100": 58},
  "issues": [{"kind": "jargon", "quote": "autonomie operațională", "fix": "Spune concret: „Poți lucra singur la sarcinile X și Y.”"}],
  "easy_read_ro": "Bine ai venit! …",
  "adjustment_checklist": [{"id": "plain_language_docs", "title": "Documente în limbaj simplu"}]},
 "meta": {…}}
```

`readability` is computed in code (deterministic, tested). `issues[].kind`: `jargon | long_sentence | missing_deadline | vague_instruction | missing_structure`. `quote` must appear in the input (guardrail). The score is about the **document**, never a person.

### 3.7 `POST /api/tone/suggest` (P1) — Stretch S2

Request: `{"text": "...", "context": "clarification", "tone_goal": "polite", "profile": {…}}`

```json
{"ok": true, "data": {
  "suggested_text": "Bună ziua! Vă rog să mă ajutați cu o scurtă clarificare privind ordinea sarcinilor de azi. Mulțumesc!",
  "alternative_phrasings": [
    "Salut! Aș avea nevoie de 2 minute pentru a confirma prioritățile pe proiectul curent."
  ],
  "uncertainty_notice_ro": "Sugestie pur orientativă. Comunicarea umană depinde de relația cu interlocutorul."},
 "meta": {…}}
```

## 4. Frontend ↔ backend rules

- Frontend always sends `today_iso` from the browser's local date.
- Frontend renders `meta.ai_notice_ro` near every AI result, shows `meta.warnings`, and offers "Arată în text" using `source_quote`.
- Errors: show `error.message_ro` in an `aria-live="assertive"` region with a "Încearcă din nou" button.
