import re
from typing import Any, Type

from pydantic import BaseModel

from app.schemas.interview import InterviewPrepData
from app.schemas.meeting import MeetingSummarizeData
from app.schemas.plan import PlanExtractData
from app.schemas.simplify import SimplifyData
from app.schemas.tone import ToneSuggestData

RO_MONTHS = {
    "ianuarie": "01",
    "februarie": "02",
    "martie": "03",
    "aprilie": "04",
    "mai": "05",
    "iunie": "06",
    "iulie": "07",
    "august": "08",
    "septembrie": "09",
    "octombrie": "10",
    "noiembrie": "11",
    "decembrie": "12",
}


def parse_ro_date_iso(matched_text: str) -> str | None:
    """Parses ISO dates (YYYY-MM-DD) or Romanian verbal dates (e.g. 15 noiembrie 2026)."""
    m_iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", matched_text)
    if m_iso:
        return m_iso.group(0)

    m_verbal = re.search(
        r"\b(\d{1,2})\s+(ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)(?:\s+(\d{4}))?\b",
        matched_text,
        re.IGNORECASE,
    )
    if m_verbal:
        day = int(m_verbal.group(1))
        month = RO_MONTHS.get(m_verbal.group(2).lower(), "01")
        year = m_verbal.group(3) or "2026"
        return f"{year}-{month}-{day:02d}"

    return None


def extract_document_from_prompt(user_prompt: str) -> str:
    """Extracts raw user document text from structured prompt boundaries."""
    patterns = [
        r"---\s*ÎNCEPUT DOCUMENT.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT DOCUMENT",
        r"---\s*DOCUMENT.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT DOCUMENT",
        r"---\s*E-MAIL CU SARCINI.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT E-MAIL",
        r"---\s*TRANSCRIPT.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT TRANSCRIPT",
        r"---\s*DESCRIERE ANUNȚ SAU POST.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT DESCRIERE",
        r"---\s*MESAJ SCRIS DE ANGAJAT.*?---\s*\n(.*?)\n\s*---\s*SFÂRȘIT MESAJ",
    ]
    for pat in patterns:
        m = re.search(pat, user_prompt, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return user_prompt.strip()


def is_default_sample(text: str) -> bool:
    """Detects if input is one of the canned mock sample texts or test fixtures."""
    lower = text.lower()
    canned_keywords = [
        "recepția clădirii b",
        "cladirii b",
        "formularul f-12",
        "f-12",
        "28 octombrie",
        "joi la prânz",
        "joi la pranz",
        "lansăm vineri, 6 noiembrie",
        "lansam vineri, 6 noiembrie",
        "popa cnp",
        "1920304123459",
        "contractului de comodat",
        "registratura@primarie.ro",
        "ghiseul.ro",
    ]
    return any(k in lower for k in canned_keywords)


def generate_dynamic_v2_payload(
    text: str, situation: str, adaptations: Any
) -> dict[str, Any]:
    """Generates structured v2 analysis directly from user text in offline mock mode."""
    raw_sentences = [
        s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if len(s.strip()) > 8
    ]
    if not raw_sentences:
        raw_sentences = [text.strip() or "Document procesat cu succes."]

    summary = f"Pe scurt: {' '.join(raw_sentences[:2])}"

    action_keywords = [
        "trebuie",
        "rugăm",
        "depuneți",
        "trimiteți",
        "completați",
        "achitați",
        "conectați",
        "semnați",
        "urmați",
        "prezentați",
        "transmiteți",
        "solicităm",
        "clarificați",
        "participați",
    ]
    actions = []
    for s in raw_sentences:
        low = s.lower()
        if any(k in low for k in action_keywords):
            actions.append(
                {
                    "text": re.sub(r"^\d+[\.\)]\s*", "", s).strip(),
                    "quote": s,
                }
            )

    if not actions:
        actions.append(
            {
                "text": raw_sentences[0],
                "quote": raw_sentences[0],
            }
        )

    date_patterns = [
        r"\b(până la|până|în data de|la data de|termen)\s+([0-9]{1,2}\s+[a-zăâîșț]+(?:\s+[0-9]{4})?|[0-9]{4}-[0-9]{2}-[0-9]{2})\b",
        r"\b([0-9]{1,2}\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)(?:\s+[0-9]{4})?)\b",
        r"\b(cât mai repede|urgent|cât mai curând|până joi|până vineri|până miercuri|până marți|până luni)\b",
    ]
    deadlines = []
    for s in raw_sentences:
        for pat in date_patterns:
            m = re.search(pat, s, re.IGNORECASE)
            if m:
                matched_str = m.group(0)
                due_date = parse_ro_date_iso(matched_str)
                deadlines.append(
                    {
                        "date": due_date,
                        "text": matched_str,
                        "quote": s,
                    }
                )
                break

    words = re.findall(r"\b[A-Za-zăâîșțĂÂÎȘȚ]{8,}\b", text)
    unique_words = list(dict.fromkeys(words))[:3]
    glossary = [
        {
            "term": w,
            "plain": f"Termen specific identificat în textul documentului ({w.lower()}).",
        }
        for w in unique_words
    ] or [
        {
            "term": "termen de conformare",
            "plain": "Intervalul de timp acordat pentru îndeplinirea cerinței.",
        }
    ]

    checklist = []
    for idx, a in enumerate(actions[:5], start=1):
        checklist.append(
            {
                "step": idx,
                "text": a["text"],
                "est_minutes": 5 * idx,
            }
        )

    return {
        "summary": summary,
        "actions": actions[:4],
        "deadlines": deadlines[:3],
        "glossary": glossary,
        "checklist": checklist,
    }


def generate_dynamic_response(
    task: str,
    user_prompt: str,
    schema: Type[BaseModel],
    canned_mock: dict[str, Any],
) -> dict[str, Any]:
    """
    Dynamically extracts structured facts, real verbatim quotes, and plain language
    summaries from ANY user document in offline mock mode.
    """
    doc_text = extract_document_from_prompt(user_prompt)

    # If it's the known canned sample, return the curated human response
    if is_default_sample(doc_text) or len(doc_text) < 15:
        return canned_mock

    # Split into clean non-empty sentences
    raw_sentences = [
        s.strip() for s in re.split(r"(?<=[.?!])\s+", doc_text) if len(s.strip()) > 8
    ]
    if not raw_sentences:
        raw_sentences = [doc_text[:120]]

    # 1. SIMPLIFY
    if schema is SimplifyData:
        first_part = " ".join(raw_sentences[:2])
        summary = f"Pe scurt: {first_part}"

        action_keywords = [
            "trebuie",
            "rugăm",
            "depuneți",
            "trimiteți",
            "completați",
            "achitați",
            "conectați",
            "semnați",
            "urmați",
            "prezentați",
        ]
        selected_sentences = []
        for s in raw_sentences:
            low = s.lower()
            if any(k in low for k in action_keywords) or re.match(r"^\d+[\.\)]", s):
                selected_sentences.append(s)

        if not selected_sentences:
            selected_sentences = raw_sentences[:3]

        steps = []
        for idx, s in enumerate(selected_sentences[:4], start=1):
            clean_text = re.sub(r"^\d+[\.\)]\s*", "", s).strip()
            steps.append(
                {
                    "n": idx,
                    "text": clean_text,
                    "source_quote": s,
                }
            )

        words = re.findall(r"\b[A-Za-zăâîșțĂÂÎȘȚ]{8,}\b", doc_text)
        unique_words = list(dict.fromkeys(words))[:3]
        key_terms = [
            {
                "term": w,
                "explanation": f"Termen specific identificat în textul documentului ({w.lower()}).",
            }
            for w in unique_words
        ] or [
            {
                "term": "procedură",
                "explanation": "Ansamblu de pași obligatorii stabiliți prin document.",
            }
        ]

        return {
            "summary": summary,
            "steps": steps,
            "key_terms": key_terms,
            "questions_to_ask": [
                "Pot primi clarificări scrise referitoare la pașii menționați?",
                "Care este persoana de contact pentru confirmarea termenelor?",
            ],
        }

    # 2. PLAN EXTRACT
    if schema is PlanExtractData:
        tasks = []
        date_patterns = [
            r"\b(până la|până|în data de|la data de|termen)\s+([0-9]{1,2}\s+[a-zăâîșț]+(?:\s+[0-9]{4})?|[0-9]{4}-[0-9]{2}-[0-9]{2})\b",
            r"\b([0-9]{1,2}\s+(?:ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)(?:\s+[0-9]{4})?)\b",
            r"\b(cât mai repede|urgent|cât mai curând|până joi|până vineri|până miercuri|până marți|până luni)\b",
        ]

        task_idx = 1
        for s in raw_sentences:
            for pat in date_patterns:
                m = re.search(pat, s, re.IGNORECASE)
                if m:
                    matched_str = m.group(0)
                    due_iso = parse_ro_date_iso(matched_str)
                    needs_confirm = due_iso is None

                    title = s[:60].strip()
                    tasks.append(
                        {
                            "id": f"t{task_idx}",
                            "title": title,
                            "due_iso": due_iso,
                            "due_text": matched_str,
                            "needs_confirmation": needs_confirm,
                            "priority": "high"
                            if "urgent" in matched_str.lower()
                            else "normal",
                            "steps": [s],
                            "source_quote": s,
                        }
                    )
                    task_idx += 1
                    break

        if not tasks:
            tasks.append(
                {
                    "id": "t1",
                    "title": raw_sentences[0][:60],
                    "due_iso": None,
                    "due_text": "conform instrucțiunilor",
                    "needs_confirmation": True,
                    "priority": "normal",
                    "steps": [raw_sentences[0]],
                    "source_quote": raw_sentences[0],
                }
            )

        return {"tasks": tasks}

    # 3. MEETING SUMMARIZE
    if schema is MeetingSummarizeData:
        lines = [line.strip() for line in doc_text.splitlines() if line.strip()]
        decisions = []
        actions = []

        decision_words = [
            "lansăm",
            "decis",
            "stabilit",
            "hotărât",
            "agreat",
            "confirmăm",
        ]
        for line in lines:
            low = line.lower()
            if any(w in low for w in decision_words):
                decisions.append({"text": line, "source_quote": line})
            # Speaker check
            speaker_match = re.match(r"^([A-ZĂÂÎȘȚ][a-zăâîșț]+)\s*:\s*(.*)", line)
            if speaker_match:
                speaker = speaker_match.group(1)
                task_content = speaker_match.group(2)
                actions.append(
                    {
                        "who": speaker,
                        "task": task_content[:70],
                        "due_iso": None,
                        "due_text": "stabilit în ședință",
                        "needs_confirmation": True,
                        "source_quote": line,
                    }
                )

        if not decisions:
            decisions = [{"text": lines[0][:80], "source_quote": lines[0]}]
        if not actions:
            actions = [
                {
                    "who": "Echipa",
                    "task": "Parcurgerea punctelor agreate",
                    "due_iso": None,
                    "due_text": "termen deschis",
                    "needs_confirmation": True,
                    "source_quote": lines[0],
                }
            ]

        return {
            "summary": f"Ședință concentrată pe coordonarea activității. Au fost parcurse {len(lines)} intervenții ale echipei.",
            "decisions": decisions[:3],
            "action_items": actions[:4],
            "unclear_points": [
                "Detaliile organizatorice finale vor fi confirmate pe email."
            ],
        }

    # 4. TONE SUGGEST
    if schema is ToneSuggestData:
        clean_msg = doc_text.strip()
        return {
            "suggested_text": f"Bună ziua! Vă contactez referitor la următoarele aspecte: {clean_msg}. Vă rog să-mi transmiteți îndrumarea dumneavoastră. Mulțumesc!",
            "alternative_phrasings": [
                f"Salut! Aș avea nevoie de o confirmare rapidă pentru: {clean_msg}.",
                f"Stimate domnule / Stimată doamnă, vă rog să mă sprijiniți cu un răspuns pentru: {clean_msg}. Cu stimă,",
            ],
            "uncertainty_notice_ro": "Sugestie orientativă. Comunicarea eficientă depinde de contextul relației profesionale.",
        }

    # 5. INTERVIEW PREP
    if schema is InterviewPrepData:
        title_m = re.search(r"TITLU POST:\s*(.*?)\n", user_prompt)
        job_title = title_m.group(1).strip() if title_m else "postul solicitat"

        return {
            "overview_ro": f"Pregătire personalizată pentru interviul de {job_title}. Rolul pune accent pe aplicarea practică a procedurilor și colaborare clară.",
            "common_questions": [
                {
                    "question_ro": f"Ce te motivează să aplici pentru poziția de {job_title}?",
                    "why_asked_ro": "Angajatorul dorește să afle interesul tău autentic și cum te raportezi la echipă.",
                    "suggested_approach_ro": "Explică faptul că ești dornic(ă) să înveți sistematic și să urmezi instrucțiunile cu atenție la detalii.",
                },
                {
                    "question_ro": "Cum abordezi o sarcină nouă dacă nu ai toate informațiile clare din prima?",
                    "why_asked_ro": "Se verifică dacă eziți să ceri lămuriri sau dacă prefaci presupuneri.",
                    "suggested_approach_ro": "Menționează că soliciți un exemplu scris sau o scurtă confirmare înainte de a finaliza.",
                },
            ],
            "suggested_adjustments": [
                {
                    "id": "written_instructions",
                    "title": "Instrucțiuni scrise, pas cu pas",
                    "talking_point_ro": "„Lucrez cel mai eficient când pașii de lucru sunt confirmați și în format scris.”",
                },
                {
                    "id": "regular_checkins",
                    "title": "Scurte sesiuni periodice de îndrumare",
                    "talking_point_ro": "„Mă ajută un scurt check-in săptămânal cu mentorul pentru validarea priorităților.”",
                },
            ],
            "questions_to_ask_employer": [
                "Cum este organizat programul de mentorat în primele săptămâni?",
                "Cum sunt transmise sarcinile zilnice către echipă (tichete, email, ședințe)?",
            ],
        }

    return canned_mock
